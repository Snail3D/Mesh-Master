"""
Relay Manager - Handles shortname-based message relaying with ACK tracking.

Provides cross-network message relay functionality where users can send messages
to any node by shortname (e.g., "snmo hello" or "/snmo hello"). The system tracks
ACKs from all chunks and provides real-time confirmation.

Features:
- Multi-chunk message support with per-chunk ACK tracking
- Queue-based architecture (3 workers, 100-item queue)
- 20-second ACK timeout
- Thread-safe shortname cache
- Cross-network bridge capabilities
"""

import queue
import threading
import time
from typing import Any, Dict, Optional

# Global state
SHORTNAME_TO_NODE_CACHE: Dict[str, str] = {}
SHORTNAME_CACHE_LOCK = threading.Lock()

RELAY_QUEUE: queue.Queue = queue.Queue(maxsize=100)
RELAY_WORKERS_COUNT = 3
RELAY_WORKERS_STARTED = False

PENDING_RELAY_ACKS: Dict[int, Dict[str, Any]] = {}
RELAY_ACK_LOCK = threading.Lock()
RELAY_ACK_TIMEOUT = 20  # seconds


def update_shortname_cache(node_id, shortname=None, get_node_shortname_func=None):
    """Update the shortname-to-node_id cache. Auto-extracts shortname if not provided."""
    global SHORTNAME_TO_NODE_CACHE
    if not node_id:
        return

    # Auto-extract shortname if not provided
    if shortname is None and get_node_shortname_func:
        shortname = get_node_shortname_func(node_id)

    # Only cache real shortnames (not "Node_xxx" fallbacks)
    if shortname and not shortname.startswith("Node_"):
        with SHORTNAME_CACHE_LOCK:
            SHORTNAME_TO_NODE_CACHE[shortname.lower()] = str(node_id)


def get_node_id_from_shortname(shortname, interface=None, update_cache_func=None):
    """Lookup node_id by shortname (case-insensitive). Returns None if not found."""
    if not shortname:
        return None

    # First check cache
    with SHORTNAME_CACHE_LOCK:
        cached = SHORTNAME_TO_NODE_CACHE.get(shortname.lower())
    if cached:
        return cached

    # Fallback: search interface.nodes directly
    if interface and hasattr(interface, "nodes"):
        shortname_lower = shortname.lower()
        for node_id, node_data in interface.nodes.items():
            user_dict = node_data.get("user", {})
            node_short = user_dict.get("shortName", "")
            if node_short.lower() == shortname_lower:
                # Cache it for next time
                if update_cache_func:
                    update_cache_func(node_id, node_short)
                return str(node_id)

    return None


def _relay_worker(interface, split_message_func, send_direct_chunks_func,
                  get_node_shortname_func, same_node_id_func, clean_log_func):
    """Worker thread that processes relay queue items."""
    while True:
        try:
            # Get relay task from queue (blocks until available)
            relay_task = RELAY_QUEUE.get(timeout=1)

            sender_id = relay_task['sender_id']
            target_shortname = relay_task['target_shortname']
            target_node_id = relay_task['target_node_id']
            relay_text = relay_task['relay_text']
            message = relay_task['message']

            # Send message and track packet ID for ACK monitoring
            try:
                if not interface:
                    send_direct_chunks_func(interface, "❌ Radio interface not available", sender_id)
                    continue

                # Split message into chunks to handle long messages
                chunks = split_message_func(relay_text)
                if not chunks:
                    failure_msg = f"❌ Failed to prepare relay to {target_shortname}"
                    send_direct_chunks_func(interface, failure_msg, sender_id)
                    continue

                # Send all chunks and collect packet IDs
                packet_ids = []
                send_errors = []

                for chunk_idx, chunk in enumerate(chunks):
                    send_result = {'packet_id': None, 'error': None}

                    def _send_relay_chunk(chunk_text=chunk):
                        try:
                            mesh_packet = interface.sendText(chunk_text, destinationId=target_node_id, wantAck=True)
                            # Extract packet ID from MeshPacket object
                            if hasattr(mesh_packet, 'id'):
                                send_result['packet_id'] = mesh_packet.id
                            elif isinstance(mesh_packet, int):
                                send_result['packet_id'] = mesh_packet
                        except Exception as e:
                            send_result['error'] = str(e)

                    send_thread = threading.Thread(target=_send_relay_chunk, daemon=True)
                    send_thread.start()
                    send_thread.join(timeout=2.0)

                    if send_result['packet_id']:
                        packet_ids.append(send_result['packet_id'])
                        clean_log_func(f"Relay chunk {chunk_idx + 1}/{len(chunks)} sent (ID={send_result['packet_id']})", "📨", show_always=False)
                    elif send_result['error']:
                        send_errors.append(f"Chunk {chunk_idx + 1}: {send_result['error']}")

                    # Small delay between chunks
                    if chunk_idx < len(chunks) - 1:
                        time.sleep(0.5)

                if not packet_ids:
                    # All chunks failed
                    failure_msg = f"❌ Failed to send to {target_shortname}"
                    send_direct_chunks_func(interface, failure_msg, sender_id)
                    clean_log_func(f"Relay send error: {'; '.join(send_errors)}", "⚠️")
                    continue

                # Create shared ACK tracking event for all chunks
                ack_events = []
                for packet_id in packet_ids:
                    chunk_ack_event = threading.Event()
                    ack_events.append(chunk_ack_event)
                    with RELAY_ACK_LOCK:
                        PENDING_RELAY_ACKS[packet_id] = {
                            'sender_id': sender_id,
                            'target_shortname': target_shortname,
                            'target_node_id': target_node_id,
                            'message': message,
                            'ack_event': chunk_ack_event,
                            'ack_node': None,
                            'timestamp': time.time()
                        }

                # Wait up to 20 seconds for ACKs from all chunks
                start_time = time.time()
                final_ack_node = None
                all_acks_received = False

                while (time.time() - start_time) < RELAY_ACK_TIMEOUT:
                    # Check if all chunks have ACKed
                    all_acked = all(event.is_set() for event in ack_events)

                    if all_acked:
                        # All chunks ACKed - get the ACK node from any chunk
                        with RELAY_ACK_LOCK:
                            for packet_id in packet_ids:
                                if packet_id in PENDING_RELAY_ACKS:
                                    ack_node = PENDING_RELAY_ACKS[packet_id].get('ack_node')
                                    if ack_node:
                                        final_ack_node = ack_node
                                        if same_node_id_func(ack_node, target_node_id):
                                            # Full ACK from intended recipient
                                            all_acks_received = True
                                            break

                        if all_acks_received:
                            break

                        # Got ACKs but not from target - keep waiting
                        if final_ack_node:
                            all_acks_received = True
                            break

                    time.sleep(1.0)

                # Clean up tracking entries
                with RELAY_ACK_LOCK:
                    for packet_id in packet_ids:
                        ack_info = PENDING_RELAY_ACKS.pop(packet_id, None)
                        if ack_info and not final_ack_node:
                            final_ack_node = ack_info.get('ack_node')

                if all_acks_received and final_ack_node:
                    # All chunks ACKed
                    ack_shortname = get_node_shortname_func(final_ack_node)
                    success_msg = f"✅ ACK by {ack_shortname}"

                    # Check if sender is Telegram user - send ACK via Telegram instead of mesh
                    if isinstance(sender_id, str) and sender_id.startswith("telegram_"):
                        try:
                            from mesh_master.telegram_notify import send_telegram_notification
                            send_telegram_notification(sender_id, success_msg)
                        except Exception as e:
                            clean_log_func(f"Telegram ACK notify failed: {e}", "❌")
                    else:
                        send_direct_chunks_func(interface, success_msg, sender_id)

                    clean_log_func(f"Relay ACK: {ack_shortname} ({len(packet_ids)} chunks)", "✅")
                else:
                    # Timeout or partial ACKs
                    failure_msg = f"❌ No ACK from {target_shortname}\n\nMessage: \"{message}\""

                    # Check if sender is Telegram user
                    if isinstance(sender_id, str) and sender_id.startswith("telegram_"):
                        try:
                            from mesh_master.telegram_notify import send_telegram_notification
                            send_telegram_notification(sender_id, failure_msg)
                        except Exception as e:
                            clean_log_func(f"Telegram ACK notify failed: {e}", "❌")
                    else:
                        send_direct_chunks_func(interface, failure_msg, sender_id)

                    clean_log_func(f"Relay timeout: {target_shortname} (no ACK after {RELAY_ACK_TIMEOUT}s)", "⏱️")

            except Exception as e:
                # Unexpected error in worker
                print(f"Relay worker exception: {e}")
                failure_msg = f"❌ Relay error to {target_shortname}"
                send_direct_chunks_func(interface, failure_msg, sender_id)

        except queue.Empty:
            # Queue empty, loop will continue
            continue
        finally:
            try:
                RELAY_QUEUE.task_done()
            except Exception:
                pass


def start_relay_workers(interface, split_message_func, send_direct_chunks_func,
                       get_node_shortname_func, same_node_id_func, clean_log_func):
    """Start relay worker pool (called once at startup)."""
    global RELAY_WORKERS_STARTED
    if RELAY_WORKERS_STARTED:
        return

    for i in range(RELAY_WORKERS_COUNT):
        worker = threading.Thread(
            target=_relay_worker,
            args=(interface, split_message_func, send_direct_chunks_func,
                  get_node_shortname_func, same_node_id_func, clean_log_func),
            daemon=True,
            name=f"RelayWorker-{i+1}"
        )
        worker.start()

    RELAY_WORKERS_STARTED = True
    clean_log_func(f"Started {RELAY_WORKERS_COUNT} relay workers", "📨", show_always=False)


def handle_shortname_relay(sender_id, sender_key, target_shortname, target_node_id,
                           message, get_node_shortname_func, start_workers_func):
    """Handle shortname-first relay: 'snmo hello' -> relay to SnMo with reply option."""
    sender_short = get_node_shortname_func(sender_id)

    # Ensure relay workers are started
    start_workers_func()

    # Send the relay message to target - no mail system involvement
    relay_text = f"📨 Relay from {sender_short}:\n{message}\n\n💬 To reply: {sender_short.lower()} <your message>"

    # Add to relay queue (non-blocking with timeout)
    relay_task = {
        'sender_id': sender_id,
        'target_shortname': target_shortname,
        'target_node_id': target_node_id,
        'relay_text': relay_text,
        'message': message
    }

    try:
        RELAY_QUEUE.put(relay_task, block=False)
    except queue.Full:
        # Queue is full - reject relay
        from mesh_master.replies import PendingReply
        return PendingReply(f"⚠️ Relay queue full. Try again in a moment.", "shortname relay")

    # Return None - no immediate response
    # User will get "✅ ACK by {shortname}" or "❌ No ACK from {shortname}" async
    return None


def handle_relay_ack(request_id, sender_node):
    """Handle incoming ACK packet for relay tracking."""
    if not request_id:
        return

    with RELAY_ACK_LOCK:
        if request_id in PENDING_RELAY_ACKS:
            # This is an ACK for a relay we're tracking
            relay_info = PENDING_RELAY_ACKS[request_id]
            # Convert sender_node to string to avoid unhashable type issues
            relay_info['ack_node'] = str(sender_node) if sender_node else None
            ack_event = relay_info.get('ack_event')
            if ack_event:
                ack_event.set()  # Signal the waiting relay worker
