"""
mesh_master/meshcore_manager.py
MeshCore device integration for Mesh Master.

Runs a MeshCore connection in a dedicated asyncio event loop thread,
exposing a synchronous interface to the rest of the application.

MeshCore is an alternative mesh protocol/firmware (github.com/ripplebiz/MeshCore).
"""

import asyncio
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("meshcore_manager")

# Attempt to import meshcore; gracefully degrade if not installed
try:
    from meshcore import MeshCore, EventType, SerialConnection, TCPConnection  # type: ignore
    try:
        from meshcore import BLEConnection  # type: ignore
        _BLE_AVAILABLE = True
    except ImportError:
        _BLE_AVAILABLE = False
    MESHCORE_AVAILABLE = True
except ImportError:
    MESHCORE_AVAILABLE = False
    _BLE_AVAILABLE = False
    logger.warning("meshcore package not installed; MeshCore support disabled. Run: pip install meshcore")


class MeshCoreManager:
    """
    Manages a MeshCore device connection in a dedicated asyncio thread.

    Usage:
        manager = MeshCoreManager(
            on_message=my_message_callback,
            connection_type='serial',
            serial_port='/dev/ttyUSB0',
        )
        manager.start()
        ...
        manager.send_direct('pubkey_prefix_hex', 'Hello!')
        manager.send_channel(0, 'Broadcast message')
        manager.stop()

    The on_message callback receives a normalized dict:
        {
            'type':        'direct' | 'channel',
            'sender_id':   'mc_<pubkey_prefix>',  # unique ID for pipeline
            'sender_name': 'ShortName',            # from contacts lookup
            'sender_key':  '<pubkey_prefix>',      # raw hex prefix
            'text':        'message text',
            'channel_idx': 0,                      # channel messages only
            'is_direct':   True/False,
            'timestamp':   <unix int>,
            'raw':         {...},                  # original MeshCore payload
        }
    """

    def __init__(
        self,
        on_message: Callable[[Dict[str, Any]], None],
        on_status_change: Optional[Callable[[str], None]] = None,
        connection_type: str = "serial",
        serial_port: str = "",
        serial_baud: int = 115200,
        tcp_host: str = "",
        tcp_port: int = 4403,
        ble_address: str = "",
        auto_reconnect: bool = True,
        reconnect_delay: float = 10.0,
        debug: bool = False,
    ):
        if not MESHCORE_AVAILABLE:
            raise RuntimeError("meshcore package is not installed. Run: pip install meshcore")

        self._on_message = on_message
        self._on_status_change = on_status_change
        self._connection_type = connection_type.lower()
        self._serial_port = serial_port
        self._serial_baud = serial_baud
        self._tcp_host = tcp_host
        self._tcp_port = tcp_port
        self._ble_address = ble_address
        self._auto_reconnect = auto_reconnect
        self._reconnect_delay = reconnect_delay
        self._debug = debug

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._mc: Optional[Any] = None  # MeshCore instance
        self._running = False
        self._connected = False
        self._status = "Disconnected"
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public synchronous API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the MeshCore connection in a background thread."""
        if self._running:
            return
        if not MESHCORE_AVAILABLE:
            logger.error("Cannot start MeshCoreManager: meshcore not installed")
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="MeshCoreThread",
        )
        self._thread.start()
        logger.info("MeshCoreManager started")

    def stop(self) -> None:
        """Stop the MeshCore connection gracefully."""
        self._running = False
        if self._loop and self._mc:
            try:
                asyncio.run_coroutine_threadsafe(self._mc.disconnect(), self._loop)
            except Exception:
                pass
        self._set_status("Disconnected")
        logger.info("MeshCoreManager stopped")

    def send_direct(self, dst_key: str, text: str, timeout: float = 15.0) -> bool:
        """
        Send a direct message to a contact identified by public key prefix.
        Thread-safe; blocks until sent or timeout.
        """
        if not self._is_ready():
            logger.warning("send_direct called but MeshCore not connected")
            return False
        try:
            print(f"[DEBUG] send_direct called: dst_key={dst_key[:8] if dst_key else 'None'}, text_len={len(text)}, _is_ready={self._is_ready()}, _mc={self._mc is not None}, _loop={self._loop is not None}")
            
            # Check if event loop is closed before attempting send
            if self._loop and self._loop.is_closed():
                logger.error("send_direct failed: event loop is closed")
                return False
                
            future = asyncio.run_coroutine_threadsafe(
                self._mc.commands.send_msg(dst_key, text),
                self._loop,
            )
            result = future.result(timeout=timeout)
            print(f"[DEBUG] send_direct result: type={result.type}, error={result.type == EventType.ERROR}")
            logger.info(f"send_direct: result.type={result.type}, EventType.ERROR={EventType.ERROR}")
            
            # If result is ERROR, log the reason
            if result.type == EventType.ERROR:
                logger.error(f"send_msg returned ERROR: {result.payload}, {result.attributes}")
                
            return result.type != EventType.ERROR
        except Exception as exc:
            import traceback
            tb_str = traceback.format_exc()
            exc_str = str(exc) if str(exc) else "(empty message)"
            exc_type = type(exc).__name__
            print(f"[DEBUG] send_direct exception: type={exc_type}, msg={exc_str}")
            logger.error(f"send_direct failed: type={exc_type}, msg={exc_str}\n{tb_str}")
            return False

    def send_direct_with_retry(self, dst_key: str, text: str, timeout: float = 30.0) -> bool:
        """Send a direct message with automatic retry on failure."""
        if not self._is_ready():
            return False
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._mc.commands.send_msg_with_retry(dst_key, text, max_attempts=3),
                self._loop,
            )
            result = future.result(timeout=timeout)
            return result is not None and result.type != EventType.ERROR
        except Exception as exc:
            logger.error(f"send_direct_with_retry failed: {exc}")
            return False

    def send_channel(self, channel_idx: int, text: str, timeout: float = 15.0) -> bool:
        """
        Broadcast a message to a MeshCore channel.
        Thread-safe; blocks until sent or timeout.
        """
        if not self._is_ready():
            logger.warning("send_channel called but MeshCore not connected")
            return False
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._mc.commands.send_chan_msg(channel_idx, text),
                self._loop,
            )
            result = future.result(timeout=timeout)
            return result.type != EventType.ERROR
        except Exception as exc:
            logger.error(f"send_channel failed: {exc}")
            return False

    def get_contacts(self) -> Dict[str, Any]:
        """Return the current contact list (keyed by public key)."""
        if self._mc:
            return dict(self._mc.contacts)
        return {}

    def get_contact_by_prefix(self, prefix: str) -> Optional[Dict[str, Any]]:
        """Look up a contact by public key prefix."""
        if self._mc:
            return self._mc.get_contact_by_key_prefix(prefix)
        return None

    def get_contact_name(self, pubkey_prefix: str) -> str:
        """Return a human-readable name for a contact prefix, or the prefix itself."""
        contact = self.get_contact_by_prefix(pubkey_prefix)
        if contact:
            return (
                contact.get("adv_name")
                or contact.get("name")
                or contact.get("public_key", pubkey_prefix)[:8]
            )
        return pubkey_prefix[:8]

    def refresh_contacts(self, timeout: float = 10.0) -> bool:
        """Force a contacts refresh from the device."""
        if not self._is_ready():
            return False
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._mc.ensure_contacts(follow=True),
                self._loop,
            )
            future.result(timeout=timeout)
            return True
        except Exception as exc:
            logger.error(f"refresh_contacts failed: {exc}")
            return False

    def send_advert(self) -> bool:
        """Broadcast an advertisement to announce this node."""
        if not self._is_ready():
            return False
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._mc.commands.send_advert(),
                self._loop,
            )
            result = future.result(timeout=10)
            return result.type != EventType.ERROR
        except Exception as exc:
            logger.error(f"send_advert failed: {exc}")
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._mc is not None

    @property
    def status(self) -> str:
        return self._status

    @property
    def self_info(self) -> Dict[str, Any]:
        if self._mc:
            return dict(self._mc.self_info)
        return {}

    @property
    def node_name(self) -> str:
        info = self.self_info
        return info.get("adv_name") or info.get("name") or "MeshCore Node"

    @property
    def node_key(self) -> str:
        """Return the first 12 hex chars of this node's public key."""
        info = self.self_info
        pk = info.get("public_key") or ""
        return pk[:12] if pk else ""

    # ------------------------------------------------------------------
    # Internal async machinery
    # ------------------------------------------------------------------

    def _is_ready(self) -> bool:
        return (
            self._running
            and self._connected
            and self._mc is not None
            and self._loop is not None
        )

    def _set_status(self, status: str) -> None:
        self._status = status
        if self._on_status_change:
            try:
                self._on_status_change(status)
            except Exception:
                pass

    def _run_event_loop(self) -> None:
        """Entry point for the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connection_manager())
        except Exception as exc:
            logger.error(f"MeshCore event loop crashed: {exc}")
        finally:
            self._connected = False
            self._loop.close()
            self._loop = None

    async def _connection_manager(self) -> None:
        """Outer loop: connect, run, reconnect if needed."""
        while self._running:
            try:
                await self._connect_and_run()
            except Exception as exc:
                logger.error(f"MeshCore connection error: {exc}")
                self._connected = False
                self._mc = None
                self._set_status(f"Error: {exc}")

            if not self._running:
                break

            if self._auto_reconnect:
                logger.info(f"MeshCore reconnecting in {self._reconnect_delay}s…")
                self._set_status(f"Reconnecting in {int(self._reconnect_delay)}s…")
                await asyncio.sleep(self._reconnect_delay)
            else:
                break

    async def _connect_and_run(self) -> None:
        """Create the connection and run until disconnected or stopped."""
        self._set_status("Connecting…")
        logger.info(f"MeshCore connecting via {self._connection_type}…")

        mc = await self._create_connection()
        if mc is None:
            raise ConnectionError(f"Failed to connect via {self._connection_type}")

        self._mc = mc
        self._connected = True
        self._set_status("Connected")
        logger.info(f"MeshCore connected. Node: {self.node_name} ({self.node_key})")

        # Subscribe to incoming messages
        mc.subscribe(EventType.CONTACT_MSG_RECV, self._handle_contact_message)
        mc.subscribe(EventType.CHANNEL_MSG_RECV, self._handle_channel_message)
        mc.subscribe(EventType.DISCONNECTED, self._handle_disconnect)

        # Fetch contacts
        try:
            await mc.commands.get_contacts()
        except Exception as exc:
            logger.warning(f"Failed to fetch initial contacts: {exc}")

        # Start auto-fetching pending messages
        try:
            await mc.start_auto_message_fetching()
        except Exception as exc:
            logger.warning(f"Failed to start auto message fetching: {exc}")

        # Keep running until stopped or disconnected
        while self._running and self._connected:
            await asyncio.sleep(0.5)

    async def _create_connection(self) -> Optional[Any]:
        """Create and return a MeshCore instance for the configured transport."""
        try:
            if self._connection_type == "tcp":
                if not self._tcp_host:
                    raise ValueError("tcp_host not configured")
                return await MeshCore.create_tcp(
                    self._tcp_host,
                    self._tcp_port,
                    debug=self._debug,
                    auto_reconnect=False,  # we handle reconnect ourselves
                    default_timeout=10.0,
                )
            elif self._connection_type == "ble":
                if not _BLE_AVAILABLE:
                    raise RuntimeError("BLEConnection not available; install bleak")
                return await MeshCore.create_ble(
                    address=self._ble_address or None,
                    debug=self._debug,
                    auto_reconnect=False,
                    default_timeout=10.0,
                )
            else:
                # serial (default)
                if not self._serial_port:
                    raise ValueError("serial_port not configured")
                return await MeshCore.create_serial(
                    self._serial_port,
                    self._serial_baud,
                    debug=self._debug,
                    auto_reconnect=False,
                    default_timeout=10.0,
                )
        except Exception as exc:
            logger.error(f"MeshCore _create_connection failed: {exc}")
            return None

    async def _handle_contact_message(self, event: Any) -> None:
        """Process an incoming direct (contact) message."""
        try:
            payload = event.payload
            pubkey_prefix = payload.get("pubkey_prefix", "")
            text = payload.get("text", "").strip()
            if not text:
                return

            sender_name = self.get_contact_name(pubkey_prefix)
            sender_id = f"mc_{pubkey_prefix}"

            normalized = {
                "type": "direct",
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_key": pubkey_prefix,
                "text": text,
                "channel_idx": None,
                "is_direct": True,
                "timestamp": payload.get("sender_timestamp", int(time.time())),
                "raw": payload,
            }
            logger.debug(f"MeshCore DM from {sender_name}: [{len(text)} chars]")
            self._on_message(normalized)
        except Exception as exc:
            logger.error(f"Error handling contact message: {exc}")

    async def _handle_channel_message(self, event: Any) -> None:
        """Process an incoming channel broadcast message."""
        try:
            payload = event.payload
            text = payload.get("text", "").strip()
            channel_idx = payload.get("channel_idx", 0)
            if not text:
                return

            # Channel messages don't include a sender pubkey in the payload
            # Use a placeholder; the text may contain a callsign prefix
            sender_id = f"mc_chan{channel_idx}"
            sender_name = f"Channel {channel_idx}"

            normalized = {
                "type": "channel",
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_key": "",
                "text": text,
                "channel_idx": channel_idx,
                "is_direct": False,
                "timestamp": payload.get("sender_timestamp", int(time.time())),
                "raw": payload,
            }
            logger.debug(f"MeshCore CH{channel_idx}: [{len(text)} chars]")
            self._on_message(normalized)
        except Exception as exc:
            logger.error(f"Error handling channel message: {exc}")

    async def _handle_disconnect(self, event: Any) -> None:
        """Handle a disconnect event from MeshCore."""
        reason = event.payload.get("reason", "unknown") if isinstance(event.payload, dict) else str(event.payload)
        logger.warning(f"MeshCore device disconnected: {reason}")
        self._connected = False
        self._set_status("Disconnected")
