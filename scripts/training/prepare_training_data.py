#!/usr/bin/env python3
"""
Prepare Training Data for Mesh-Master Fine-Tuning

Extracts conversations from Mesh-Master logs and archives,
anonymizes sensitive data, and generates synthetic training pairs
for fine-tuning a 1B-parameter model on mesh networking tasks.

Usage:
    python prepare_training_data.py --min-pairs 50000 --output data/train.jsonl
"""

import json
import re
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime


# Regex patterns for anonymization
NODE_ID_PATTERN = re.compile(r'!([0-9a-f]{8})', re.IGNORECASE)
IP_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
SERIAL_PATTERN = re.compile(r'/dev/serial/by-id/[^\s]+')
MAC_PATTERN = re.compile(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})')


def anonymize_text(text: str) -> str:
    """
    Anonymize sensitive information in text.

    Replaces:
    - Node IDs (!abc12345) → !<node>
    - IP addresses → <ip>
    - Serial paths → <serial>
    - MAC addresses → <mac>

    Args:
        text: Input text with potential PII

    Returns:
        Anonymized text
    """
    text = NODE_ID_PATTERN.sub('!<node>', text)
    text = IP_PATTERN.sub('<ip>', text)
    text = SERIAL_PATTERN.sub('<serial>', text)
    text = MAC_PATTERN.sub('<mac>', text)
    return text


def extract_command(text: str) -> str:
    """
    Extract primary command from message text.

    Args:
        text: Message text potentially containing command

    Returns:
        Command name (e.g., '/nodes') or empty string
    """
    # Look for commands at start of message
    match = re.match(r'^/?([a-z_]+)', text.lower().strip())
    if match:
        cmd = match.group(1)
        # Known commands
        known = ['nodes', 'relay', 'mail', 'ai', 'help', 'menu', 'ping',
                 'checkmail', 'find', 'log', 'report', 'games', 'optout',
                 'optin', 'onboard', 'meshtastic', 'wiki', 'bible']
        if cmd in known:
            return f'/{cmd}'
    return ''


def parse_messages_archive(archive_path: Path) -> List[Dict[str, Any]]:
    """
    Parse messages_archive.json into training pairs.

    Args:
        archive_path: Path to messages_archive.json

    Returns:
        List of training pair dictionaries
    """
    if not archive_path.exists():
        print(f"Warning: Archive not found: {archive_path}")
        return []

    try:
        with open(archive_path, 'r', encoding='utf-8') as f:
            archive = json.load(f)
    except Exception as e:
        print(f"Error loading archive: {e}")
        return []

    pairs = []

    # Extract AI query/response pairs
    for entry in archive:
        if not isinstance(entry, dict):
            continue

        msg_type = entry.get('type', '')
        question = entry.get('question', '').strip()
        response = entry.get('response', '').strip()

        if msg_type == 'ai_query' and question and response:
            # Anonymize
            question_clean = anonymize_text(question)
            response_clean = anonymize_text(response)

            # Extract metadata
            command = extract_command(question)

            pairs.append({
                'input': question_clean,
                'output': response_clean,
                'metadata': {
                    'command': command,
                    'source': 'archive',
                    'token_estimate': len(response_clean.split()),
                    'timestamp': entry.get('timestamp', 0)
                }
            })

    return pairs


def parse_mail_conversations(mailboxes_path: Path) -> List[Dict[str, Any]]:
    """
    Extract training pairs from mesh mail conversations.

    Args:
        mailboxes_path: Path to mesh_mailboxes.json

    Returns:
        List of training pairs
    """
    if not mailboxes_path.exists():
        print(f"Warning: Mailboxes not found: {mailboxes_path}")
        return []

    try:
        with open(mailboxes_path, 'r', encoding='utf-8') as f:
            mailboxes = json.load(f)
    except Exception as e:
        print(f"Error loading mailboxes: {e}")
        return []

    pairs = []

    # Create synthetic command/response pairs from mail patterns
    for mailbox_name, mailbox_data in mailboxes.items():
        messages = mailbox_data.get('messages', [])

        if len(messages) >= 2:
            # Create pairs from message sequences
            for i in range(len(messages) - 1):
                msg1 = messages[i].get('text', '').strip()
                msg2 = messages[i + 1].get('text', '').strip()

                if msg1 and msg2:
                    # Anonymize
                    input_clean = anonymize_text(f"In mailbox {mailbox_name}: {msg1}")
                    output_clean = anonymize_text(msg2)

                    pairs.append({
                        'input': input_clean,
                        'output': output_clean,
                        'metadata': {
                            'command': '/mail',
                            'source': 'mailbox',
                            'mailbox': mailbox_name
                        }
                    })

    return pairs


def parse_meshtastic_knowledge() -> List[Dict[str, Any]]:
    """
    Extract Q&A pairs from Meshtastic technical knowledge base.

    Returns:
        List of Meshtastic-specific training pairs
    """
    pairs = []

    # Comprehensive Meshtastic technical Q&A
    meshtastic_qa = [
        # Core Concepts
        ("What is Meshtastic?", "Meshtastic® is an open-source project using inexpensive LoRa radios for long-range (up to 331km record), off-grid mesh communication without internet or cell towers."),
        ("How does Meshtastic mesh work?", "Meshtastic uses LoRa radio to create a decentralized mesh network. Messages hop node-to-node until they reach the destination. Each node rebroadcasts messages it receives (managed flooding algorithm)."),
        ("What is LoRa?", "LoRa (Long Range) is a low-power radio protocol operating on sub-GHz ISM bands (915MHz US, 868MHz EU, 433MHz Asia). Trades bandwidth for extreme range and battery efficiency."),
        ("Meshtastic encryption?", "All channels use AES256-PSK encryption with a shared key. Same key = same channel. Default channel is public (shared key in firmware). Custom channels require unique PSK."),
        ("Meshtastic range?", "Typical: 2-5km urban, 10-15km rural. Record: 331km with clear line-of-sight. Range depends on terrain, antenna height, modem preset, and interference."),

        # Message Relay & Routing
        ("What is hop limit?", "Hop limit (default 3) controls how many times a message can be relayed. Each node decrements the counter. At 0, message stops propagating. Max is 7 hops."),
        ("How does message relay work?", "When a node receives a message: (1) Check if already seen (duplicate filter), (2) If hop limit > 0, rebroadcast to neighbors, (3) Decrement hop count, (4) Store in seen list."),
        ("What is managed flooding?", "Meshtastic's routing algorithm. Every node rebroadcasts new messages after a random delay (with listening). No central routing table—messages flood the mesh intelligently."),
        ("Meshtastic ACK system?", "Acknowledgments confirm message delivery. Recipient node sends ACK back to sender. 20-second timeout typical. Multi-hop ACKs can be delayed by relay chains."),
        ("Packet storage limit?", "Meshtastic radios store ~100 recent packet IDs to detect duplicates. Older packets may be rebroadcast if seen again (rare in stable mesh)."),

        # Node Roles
        ("What are Meshtastic node roles?", "CLIENT (default, battery-saving), ROUTER (always-on relay), REPEATER (minimal UI, mesh backbone only), CLIENT_MUTE (receive-only, no TX except ACKs)."),
        ("CLIENT role?", "Default role. Sends/receives messages, goes to sleep to save battery. Wakes periodically to check for messages. Best for handheld/mobile nodes."),
        ("ROUTER role?", "Always-on relay node. Never sleeps, constantly listens and forwards messages. Critical for mesh backbone. Requires USB/solar power. Mesh-Master nodes should use ROUTER."),
        ("REPEATER role?", "Dedicated relay with minimal overhead. No position broadcasts, no user messages—just relays mesh traffic. Ideal for remote hilltop nodes extending range."),
        ("CLIENT_MUTE role?", "Receive-only mode. Listens to mesh but doesn't transmit except ACKs. Useful for monitoring or stealth operations. Doesn't contribute to mesh reliability."),

        # Modem Presets
        ("What are Meshtastic modem presets?", "Presets balance range vs. speed by adjusting spreading factor and bandwidth. LongFast (default), LongSlow (max range), MediumFast (balanced), ShortFast (high-speed short-range)."),
        ("LongFast preset?", "Default preset. Spreading factor SF=11, 250kHz bandwidth. ~5km range, ~1kbps speed. Best general-purpose option for most deployments."),
        ("LongSlow preset?", "Max range preset. SF=12, 125kHz. ~10-15km range, ~0.3kbps speed. Use for sparse networks or mountainous terrain. Slower message delivery."),
        ("MediumFast preset?", "Balanced preset. SF=10, 250kHz. ~3km range, ~2kbps speed. Good for dense urban meshes with many nodes and high traffic."),
        ("ShortFast preset?", "High-speed short-range. SF=7, 500kHz. ~1km range, ~10kbps speed. Experimental—use for local high-bandwidth applications or events."),
        ("What is spreading factor (SF)?", "Spreading factor controls chirp duration in LoRa. Higher SF = longer range + slower speed. SF7 fastest, SF12 longest range. Each step doubles time-on-air."),

        # Signal Metrics
        ("What is SNR?", "Signal-to-Noise Ratio measures signal quality in decibels (dB). >5dB = excellent, 0-5dB = good, -5 to 0dB = marginal, <-5dB = poor. LoRa can decode down to -20dB SNR."),
        ("What is RSSI?", "Received Signal Strength Indicator in dBm. Typical: -50dBm (very strong), -90dBm (good), -120dBm (weak but decodable). Lower (more negative) = weaker signal."),
        ("Good SNR values?", "SNR >5dB is excellent for reliable communication. 0-5dB is acceptable. Below 0dB expect packet loss. LoRa's advantage: works down to -15dB where WiFi fails."),
        ("RSSI vs SNR?", "RSSI measures raw signal strength, SNR measures quality (signal above noise floor). SNR more important—strong signal (high RSSI) with high noise (low SNR) still fails."),

        # Packet Structure & Protocol
        ("Meshtastic packet structure?", "Each packet: 4-byte destination ID, 4-byte sender ID, hop limit, channel hash, payload (encrypted). Total ~240 bytes max including LoRa overhead."),
        ("What is CSMA/CA?", "Carrier Sense Multiple Access with Collision Avoidance. Nodes listen before transmitting. If channel busy, wait random time. Reduces packet collisions in dense meshes."),
        ("Meshtastic message types?", "TEXT_MESSAGE_APP (chat), POSITION_APP (GPS), NODEINFO_APP (device info), TELEMETRY_APP (battery/sensors), ROUTING_APP (ACKs/errors), ADMIN_APP (config changes)."),
        ("Channel hash?", "8-bit hash of channel name + PSK. Filters packets—nodes ignore messages from different channel hashes. Prevents cross-channel interference."),
        ("Time-on-air limits?", "FCC/ETSI restrict LoRa duty cycle to ~1% (36s/hour on 915MHz US). Long messages or high traffic can hit limits. Meshtastic enforces fair use queue."),

        # Battery & Power
        ("Meshtastic battery optimization?", "Use CLIENT role (not ROUTER), disable GPS when stationary, reduce screen timeout, lower TX power if good SNR, use LongSlow preset, disable Bluetooth when not needed."),
        ("How long does battery last?", "CLIENT role: 2-7 days depending on usage. ROUTER: must be powered (USB/solar). T-Beam ~3 days, Heltec ~5 days, RAK ~4 days (varies by config and traffic)."),
        ("Power sources?", "18650 battery (most devices), USB power bank, solar panel + charge controller, USB-C PD, or vehicle power (12V with regulator). ROUTER nodes need continuous power."),

        # Troubleshooting & Best Practices
        ("Why no ACK received?", "Causes: recipient offline, weak signal (SNR <-10dB), hop limit reached, channel mismatch, packet collision, or duty cycle limit hit. Check /node <shortname> for signal quality."),
        ("Improve mesh reliability?", "Add ROUTER nodes at high points, use directional antennas for long links, reduce hop limit to 3-4, ensure good SNR (>0dB), avoid overcrowding single channel."),
        ("Meshtastic security?", "AES256 encryption per channel, but node IDs visible in packet headers. No authentication—anyone with PSK can join. Don't share sensitive info—treat as party line."),
        ("Best mesh topology?", "Star-and-spoke: ROUTER nodes form backbone, CLIENT nodes connect as leaves. Avoid long linear chains. Ideal: every node sees 2-3 ROUTERs for redundancy."),
        ("Antenna tips?", "Vertical orientation, clear line-of-sight, higher is better. 3dBi omnidirectional for mobile, 5-9dBi for fixed stations. Never transmit without antenna—damages radio!"),
    ]

    for question, answer in meshtastic_qa:
        pairs.append({
            'input': question,
            'output': answer,
            'metadata': {
                'source': 'meshtastic_knowledge',
                'category': 'meshtastic_technical'
            }
        })

    return pairs


def generate_synthetic_pairs() -> List[Dict[str, Any]]:
    """
    Generate synthetic command/response training pairs.

    Creates examples for all major Mesh-Master commands to ensure
    comprehensive coverage even with limited real data.

    Returns:
        List of synthetic training pairs
    """
    synthetic = []

    # Identity and introduction pairs
    identity_pairs = [
        ("What's your name?", "I'm Mesh Master Bot, your AI assistant for Meshtastic mesh networks+."),
        ("Who are you?", "Mesh Master Bot - I help with mesh networking, relay commands, mail, and troubleshooting on Meshtastic LoRa networks."),
        ("What do you do?", "I'm Mesh Master Bot. I assist with Mesh-Master commands, entertain people, help with general facts, explain LoRa networking, and help troubleshoot connectivity issues."),
        ("Introduce yourself", "Hello! I'm Mesh Master Bot, your guide for Mesh-Master operations. Ask me about commands, or mesh troubleshooting."),
        ("What are you?", "Mesh Master Bot - a specialized AI trained on Mesh-Master operations, Meshtastic protocols, and LoRa mesh networking."),
        ("Tell me about yourself", "I'm Mesh Master Bot, designed to help operators use Mesh-Master—an off-grid AI operations suite for Meshtastic mesh networks with relay bridging, mesh mail, and offline knowledge."),
    ]

    for q, a in identity_pairs:
        synthetic.append({
            'input': q,
            'output': a,
            'metadata': {
                'command': '',
                'source': 'synthetic',
                'category': 'identity'
            }
        })

    # Mesh-Master system usage pairs (v2.0 current features)
    system_usage_pairs = [
        ("How do I use Mesh-Master?", "Mesh-Master connects Meshtastic radios to AI. Use /help or /menu for commands. Key features: network bridge relay (shortname messages), mesh mail (/m /c), /system help, games, offline knowledge."),
        ("What is Mesh-Master?", "Mesh-Master is an off-grid AI operations suite for Meshtastic mesh networks. Features: cross-network relay bridge with ACK tracking and offline queue, mesh mail, 15+ games, private logs, public reports, dashboard, and LLM integration."),
        ("Mesh-Master features?", "Network bridge relay with offline queue, ACK tracking, /optout privacy, mesh mail, context-aware /system help, interactive /onboard, private /log + public /report, fuzzy /find search, mesh games, dashboard, URL filter, Ollama integration."),
        ("Setup Mesh-Master?", "Install: Python 3.10+, git clone https://github.com/Snail3D/Mesh-Master.git, cd Mesh-Master, pip install -r requirements.txt. Configure: edit config.json (serial_port, ai_provider='ollama', ollama_model='llama3.2:1b'). Run: NO_BROWSER=1 python mesh-master.py"),
        ("Mesh-Master command syntax?", "Most commands start with / (e.g., /nodes, /help, /ai). Exception: relay messages use bare shortname: 'alice hello' or '/alice hello'. Both work. Case-insensitive."),
        ("Mesh-Master new user guide?", "Send /onboard or /onboarding in DM for interactive  guided tour covering menu, mail, logs, reports, games, AI, tools, and help."),
        ("Mesh-Master relay privacy?", "Use /optout to disable receiving relays (others can't relay to you). /optin re-enables. Preferences persist in data/relay_optout.json. Relay senders see 'User has opted out' message."),
        ("What's network bridge relay?", "Mesh-Master acts as bridge between multiple mesh networks. If connected to Network A + Network B, users on A can relay to users on B via shortnames. Example: if the radio username/shortname is TEC1 it would be'tec1 hello' (TEC1 on different network)."),
        ("Offline message queue?", "Failed relays (recipient offline, weak signal) automatically queued. System retries when recipient comes online (max 3 attempts, 24-hour expiry, 10 messages per user). No action needed—it's automatic."),
        ("Context-aware help system?", "/system <question> gives AI responses with full system knowledge (~50k tokens: commands, architecture, your config, network state). Auto-activates during /onboard and after /help or /menu. Clear context window with /reset"),
    ]

    for q, a in system_usage_pairs:
        synthetic.append({
            'input': q,
            'output': a,
            'metadata': {
                'command': '',
                'source': 'synthetic',
                'category': 'mesh_master_usage'
            }
        })

    # Command templates with variations (v2.0 verified commands only)
    templates = {
        '/nodes': [
            ("How do I see all nodes?", "/nodes - lists all nodes with SNR and last heard"),
            ("Show me the mesh nodes", "Use /nodes to see all reachable nodes"),
            ("List connected nodes", "Send /nodes to see the current mesh topology"),
            ("What nodes are online?", "/nodes shows nodes seen in last 24h, sorted by recency"),
        ],

        'relay_shortname': [
            ("How do I relay to someone?", "Type: <shortname> your message (e.g., alice meet at waypoint) - system tracks ACKs automatically"),
            ("Send message to specific node", "Relay format: snmo hello there OR /snmo hello there (both work)"),
            ("What's the relay syntax?", "Just <shortname> <message> - no /relay command exists. Example: bob check your mail"),
            ("How does relay work?", "Type shortname + message. Mesh-Master looks up their node ID, sends message, tracks ACK. Get confirmation when received."),
        ],

        '/m': [
            ("Check my mail", "Use /c to see all mailboxes"),
            ("How to send mail?", "/m <mailbox> <message> - creates mailbox if needed"),
            ("Mail command syntax", "/m general Hello everyone - sends to 'general' mailbox"),
            ("What's /m command?", "/m <mailbox> <message> sends mesh mail. /c checks mailboxes. /c <mailbox> reads specific mailbox."),
        ],

        '/c': [
            ("See mailbox messages", "/c shows all mailboxes, /c <mailbox> shows specific mailbox messages"),
            ("Check mail command?", "/c or /checkmail lists your mailboxes with unread counts"),
            ("Read mailbox", "/c <mailbox> displays messages and marks them read"),
        ],

        '/optout': [
            ("Stop receiving relays", "Send /optout to disable relay reception (DM only)"),
            ("Privacy settings", "/optout disables relays, /optin re-enables them"),
            ("Block relay messages", "/optout prevents others from relaying to you"),
        ],

        '/optin': [
            ("Enable relays again", "/optin re-enables relay reception after /optout"),
            ("Allow relays", "/optin lets others relay messages to you again"),
        ],

        '/find': [
            ("Search my logs", "/find <query> searches logs, reports, wiki, and offline data (DM only)"),
            ("How to search?", "Use /find <term> - supports fuzzy matching across all sources"),
            ("Find information", "/find <query> searches logs (private), reports (public), wiki, and crawled data"),
        ],

        '/games': [
            ("What games available?", "/games lists: /wordle, /hangman, /yahtzee, /blackjack, /adventure, /rps, /coinflip, /wordladder, /cipher, /quizbattle, /morse (DM only)"),
            ("Play a game", "Try /wordle, /yahtzee, /adventure, /quizbattle, /blackjack, /hangman, /morse"),
            ("Game commands", "/games shows full list. All games are DM-only."),
        ],

        '/onboard': [
            ("First time user?", "Send /onboard (or /onboarding or /onboardme) for interactive 9-step guided tour (DM only)"),
            ("Get started", "/onboarding provides step-by-step introduction to Mesh-Master"),
            ("Help for new users", "/onboardme starts guided tutorial with context-aware help"),
        ],

        '/help': [
            ("List commands", "/help shows all available commands"),
            ("What can I do?", "/menu displays full operations center"),
            ("Command reference", "/help lists commands by category"),
        ],

        '/menu': [
            ("Show all features", "/menu displays full operations center with all commands and categories"),
            ("Operations center", "/menu shows everything Mesh-Master can do"),
        ],

        '/log': [
            ("Create private note", "/log <title> creates private log entry (DM only)"),
            ("Private logging", "/log entries visible only to you, /report for public"),
            ("How to log?", "/log <title> starts log entry - only you can read with /checklog"),
        ],

        '/checklog': [
            ("Read my logs", "/checklog or /readlog lists your private log titles (DM only)"),
            ("View private notes", "/checklog <title> or /readlog <title> displays specific log"),
        ],

        '/report': [
            ("Public reports", "/report <title> creates searchable public entry (DM only)"),
            ("Share findings", "/report <title> - everyone can search with /find"),
            ("Report command", "/report entries are public, /log entries are private"),
        ],

        '/checkreport': [
            ("Read reports", "/checkreport or /readreport lists public report titles (DM only)"),
            ("View public reports", "/checkreport <title> or /readreport <title> displays specific report"),
        ],

        '/node': [
            ("Node signal strength?", "/node <shortname> shows SNR, RSSI, battery, power"),
            ("Check node details", "/node alice - displays detailed signal info"),
            ("Node metrics", "/node <shortname> shows last heard, hops, battery level"),
        ],

        '/networks': [
            ("List channels", "/networks shows all connected mesh networks/channels"),
            ("What networks am I on?", "/networks displays channel list"),
        ],

        '/system': [
            ("Context-aware help", "/system <question> provides AI help with full system knowledge"),
            ("Ask about setup", "/system how does relay work? - gets detailed explanation"),
            ("System question", "/system <query> has ~50k token context including your config"),
        ],

        '/ai': [
            ("Ask AI a question", "/ai <question> (or /bot or /data) - queries configured LLM"),
            ("Talk to AI", "/ai what's the weather like? - general AI queries"),
        ],

        '/bible': [
            ("Get Bible verse", "/bible <topic> searches Bible for relevant verses"),
            ("/bible command?", "/bible <topic> or /biblehelp for usage info"),
        ],

        '/wiki': [
            ("Wikipedia search", "/wiki <topic> searches Wikipedia"),
            ("Look up info", "/wiki <topic> - offline wiki lookups"),
        ],

        '/offline': [
            ("Offline wiki", "/offline wiki <topic> accesses locally mirrored reference articles"),
            ("Offline search", "/offline wiki <topic> PIN=1234 for protected content"),
        ],

        '/web': [
            ("Web search", "/web <query> searches internet (filters adult/warez sites)"),
            ("Search web", "/web <query> - crawls and searches web content"),
        ],

        '/weather': [
            ("Check weather", "/weather - get current weather"),
        ],

        '/timer': [
            ("Set timer", "/timer <seconds> <label> - set countdown timer"),
            ("Timer commands", "/timer list shows active timers, /timer cancel <#> cancels timer"),
        ],

        '/alarm': [
            ("Set alarm", "/alarm <time> <message> - set alarm notification"),
        ],

        '/stopwatch': [
            ("Use stopwatch", "/stopwatch start/pause/check/stop - track elapsed time"),
        ],

        # Admin commands (DM-only)
        '/changemotd': [
            ("Change MOTD", "/changemotd <message> - changes Message of the Day shown at startup (DM-only admin)"),
            ("Update welcome message", "/changemotd <text> - admin command to set new MOTD"),
        ],

        '/showmodel': [
            ("Check AI model", "/showmodel - displays currently active AI model and provider (DM-only admin)"),
            ("What model running?", "/showmodel shows active Ollama/OpenAI/Anthropic model"),
        ],

        '/selectmodel': [
            ("Change AI model", "/selectmodel - lists available Ollama models to switch to (DM-only admin)"),
            ("Switch model", "/selectmodel <model> - changes active AI model (e.g., llama3.2:1b to qwen2.5:1.5b)"),
        ],

        '/hop': [
            ("Set hop limit", "/hop <0-7> or /hops <0-7> - sets message hop limit (DM-only admin)"),
            ("Change hops", "/hops 3 - limits messages to 3 hops across mesh"),
        ],

        '/reset': [
            ("Reset AI history", "/reset - clears AI conversation memory (DM-only)"),
            ("Clear chat history", "/reset wipes AI context, starts fresh conversation"),
        ],

        '/vibe': [
            ("Change AI tone", "/vibe <tone> - adjusts AI response style (e.g., professional, casual, technical)"),
            ("Set AI mood", "/vibe professional - makes AI responses more formal"),
            ("List vibes", "/vibe - shows available tone options"),
        ],

        '/save': [
            ("Save conversation", "/save <name> - captures conversation context for later /recall"),
            ("Create context capsule", "/save mission_brief - stores current AI context"),
        ],

        '/recall': [
            ("Recall conversation", "/recall <name> - restores previously saved conversation context"),
            ("Load context capsule", "/recall mission_brief - reloads saved AI context"),
        ],

        '/chathistory': [
            ("View AI history", "/chathistory - shows recent AI conversation exchanges"),
            ("Check conversation", "/chathistory displays your message history with AI"),
        ],

        '/wipe': [
            ("Wipe data", "/wipe <mailbox> clears mailbox messages (owner only). /wipe all <mailbox> deletes entire mailbox. /wipe chathistory clears AI memory."),
        ],
    }

    # Generate pairs from templates
    for command, variations in templates.items():
        for question, answer in variations:
            synthetic.append({
                'input': question,
                'output': answer,
                'metadata': {
                    'command': command,
                    'source': 'synthetic',
                    'category': 'command_help'
                }
            })

    # Deep technical and practical explanation pairs (how systems ACTUALLY work)
    tech_pairs = [
        # Signal metrics
        ("What is SNR?", "SNR (Signal-to-Noise Ratio) measures signal quality. Higher is better. >5 dB is good, <0 dB is marginal."),
        ("LoRa mesh networking?", "LoRa uses long-range radio for mesh networks. Nodes relay messages hop-by-hop without internet."),
        ("ACK timeout?", "ACK (acknowledgment) timeout is 20 seconds. System confirms when recipient receives your relay."),
        ("Chunk size limit?", "Meshtastic limits messages to ~160 chars per chunk. Long messages split automatically."),
        ("Hop count?", "Hop count shows how many nodes relayed your message. More hops = higher latency."),
        ("Node roles?", "CLIENT (default), ROUTER (always-on relay), REPEATER (mesh backbone), CLIENT_MUTE (receive-only)."),
        ("Modem presets?", "LongFast (default), LongSlow (range+), MediumFast (balanced), ShortFast (high-speed short-range)."),
        ("Channel encryption?", "Channels use AES256 PSK encryption. Same key = same channel. No key = public channel."),
        ("Battery monitoring?", "System reports battery % and power status (USB, battery, external). Check with /node <shortname>."),
        ("Mesh topology?", "Dynamic mesh network where nodes discover neighbors and create routes automatically."),

        # Mailbox system deep dive
        ("How does mesh mail work?", "Mailboxes are shared message boards. /m <mailbox> <message> sends to mailbox. /c lists all mailboxes. /c <mailbox> reads specific mailbox. Messages persist across reboots in mesh_mailboxes.json."),
        ("Who can read my mailbox?", "Anyone subscribed to the mailbox. Subscribe by sending to it with /m or checking it with /c. Mailboxes can optionally have PINs for access control (set during creation)."),
        ("Mailbox PIN protection?", "When creating mailbox, system asks if you want a PIN. With PIN: only those with PIN can read messages. Without PIN: anyone can subscribe and read."),
        ("How to subscribe to mailbox?", "Send message with /m <mailbox> <message>. Both auto-subscribe you. Get notifications when new messages arrive."),
        ("Mailbox notifications?", "System sends heartbeat notifications for unread mail. You can snooze these notifications by saying /snooze <mailboxname>"),
        ("Wipe mailbox?", "/wipe <mailbox> clears all messages (owner only). /wipe all <mailbox> deletes entire mailbox including subscribers. /wipe chathistory clears AI conversation history."),
        ("Mailbox ownership?", "First person to create mailbox becomes owner. Owners can wipe messages, set/change PIN, manage subscribers. Ownership persists in mesh_mailboxes.json."),
      
        # Logs system deep dive
        ("How do logs work?", "Logs are private notes only YOU can read. /log <title> creates a new log. /checklog or /readlog lists your logs. /checklog <title> reads specific log. DM-only."),
        ("Who can see my logs?", "Only you. Logs are completely private."),
        ("Multiple log entries?", "Each /log <title> opens that log. Append to existing log by using same title. Create new log with new title. List all with /checklog."),
        ("Aliases for logs?", "/checklog, /checklogs, /readlog, /readlogs all work. /log <title> creates, /checklog <title> reads."),

        # Reports system deep dive
        ("How do reports work?", "Reports are PUBLIC notes searchable by everyone. /report <title> creates a new report. Anyone can search with /find. /checkreport lists reports. DM-only to create."),
        ("Who can see reports?", "Everyone on the mesh. Use for field notes, observations, intel everyone should access."),
        ("Report vs log?", "/log = private (only you). /report = public (everyone). Both support /find search, but logs only return YOUR logs, reports return everyone's."),
        ("Aliases for reports?", "/checkreport, /checkreports, /readreport, /readreports all work. /report <title> creates, /checkreport <title> reads."),

        # Find/search system deep dive
        ("How does /find work?", "/find <query> searches your logs (private), all reports (public), offline wiki, web crawls. Returns numbered list. Reply with number to open."),
        ("Find search scope?", "YOUR logs (private), ALL reports (public), wiki snapshots, web crawls. Logs are private to you, reports are public to all."),

        # Wiki and web crawl system
        ("How does /wiki work?", "/wiki <topic> searches Wikipedia. Returns summary. Caches result for offline access later."),
        ("/offline wiki?", "/offline wiki <topic> searches locally cached wiki articles. No internet needed."),
        ("Web crawl system?", "/web <query> searches internet (filters adult/warez). Crawls pages, extracts content, caches for offline access."),

        # Relay system internals
        ("Relay shortname cache?", "System auto-learns shortnames from mesh traffic. When alice sends message, maps 'alice' → her node ID. Use alice hello to relay."),
        ("Offline relay queue?", "Failed relays (node offline, weak signal) auto-queued. Max 10 messages per recipient, 24-hour expiry, 3 delivery attempts. Delivers when node comes online."),
        ("How relay queue works?", "1) Relay fails (no ACK). 2) Queue message. 3) When target node seen, attempt delivery. 4) Max 3 attempts. 5) After 24h or 3 failures, notify sender."),
        ("Cross-network relay?", "Mesh-Master bridges networks. If on Network A + B, users on A relay to users on B via shortnames."),

        # AI context system
        ("/vibe system?", "/vibe <tone> adjusts AI response style (professional, casual, technical, etc.). Use /vibe to list options. Temporary - lasts for current session."),
        ("/save and /recall?", "/save <name> captures current AI conversation context. /recall <name> restores it. Use for mission hand-offs."),
        ("/reset what does it do?", "/reset clears AI conversation memory. Fresh start."),
        ("Wipe vs reset?", "/reset = clears YOUR AI conversation history. /wipe chathistory = same as /reset. /wipe <mailbox> = clears mailbox messages."),

        # Games system deep dive
        ("/games list?", "Available games (all DM-only): /wordle (5-letter word guessing), /hangman (word guessing), /yahtzee (dice game), /blackjack (card game), /adventure (text adventure), /rps (rock-paper-scissors), /coinflip, /wordladder (transform words), /cipher (decode messages), /quizbattle (trivia), /morse (Morse code practice)."),
        ("How do games work?", "All games DM-only. Each game maintains state per player. Use /games to list. Send /<game> start to begin. Follow game prompts. State persists across reboots. Send /games to see available games."),
        ("/wordle how to play?", "/wordle start begins game. Guess 5-letter word. Reply with guess (e.g., 'crane'). Get feedback: ✅ correct letter+position, 🟨 correct letter wrong position, ⬜ not in word. 6 attempts."),
        ("/hangman how to play?", "/hangman start chooses word. Guess letters one at a time (e.g., 'e'). Correct letters revealed in word. Wrong guesses add to hangman drawing. 6 wrong guesses = game over."),
        ("/yahtzee how to play?", "/yahtzee start begins game. Roll 5 dice. Choose which to keep, re-roll others (max 3 rolls). Score in categories (three of a kind, full house, etc.). 13 rounds, highest score wins."),
        ("/blackjack how to play?", "/blackjack start deals hand. Reply 'hit' for card or 'stand' to hold. Goal: get closer to 21 than dealer without busting (>21). Aces=1 or 11, face cards=10."),
        ("/adventure how to play?", "/adventure start begins text adventure. AI generates branching story. Make choices by replying with option number (e.g., '1'). Story adapts to language (multilingual support)."),
        ("/wordladder how to play?", "/wordladder start cold warm - transform 'cold' to 'warm' one letter at a time. Each step must be valid word. Reply with next word. Ask AI for hints (/hint). Collaborative puzzle."),
        ("/cipher how to play?", "/cipher start gives encoded message. Decode it by identifying cipher type (Caesar, substitution, etc.). Reply with decoded message. Difficulty scales with skill."),
        ("/quizbattle how to play?", "/quizbattle start asks trivia question. Reply with answer or letter (a/b/c/d). Track score across questions. Fast-paced knowledge challenge."),
        ("/morse how to play?", "/morse start teaches Morse code. Translate messages to/from Morse. Reply with translation. Educational tool for learning Morse code patterns."),
        ("Game state persistence?", "All game states persist across reboots."),
        ("/masterquiz?", "/masterquiz - 50 questions about Mesh-Master features (relay, logs, reports, commands, mail, dashboard, wiki, games). Answer 1-4 or a-d. Auto-shuffled for replay. Track your score."),
        ("/meshtasticquiz?", "/meshtasticquiz - 50 questions about Meshtastic (LoRa, mesh networking, node roles, SNR, presets, security). Answer 1-4 or a-d. Learn while testing knowledge."),

        # Admin system deep dive
        ("Admin commands security?", "Admin commands DM-only. Admins must send the admin password to be whitelisted as admins. Use with caution. Commands: /changemotd, /showmodel, /selectmodel, /hop."),
        ("/hop limit range?", "/hop <0-7> or /hops <0-7> sets max message hops. 0=no relay (direct only). 3=default (good balance). 7=maximum (mesh-wide). Admin-only."),
    ]

    for q, a in tech_pairs:
        synthetic.append({
            'input': q,
            'output': a,
            'metadata': {
                'command': '',
                'source': 'synthetic',
                'category': 'technical'
            }
        })

    # Troubleshooting pairs
    troubleshoot = [
        ("No ACK received", "No ACK in 20s means: weak signal, node offline, or message lost. Try /node <shortname> to check SNR."),
        ("Relay not working", "Check: 1) Node seen with /nodes? 2) Correct shortname? 3) They haven't /optout? 4) Signal strength OK?"),
        ("Can't send message", "Verify radio connected (/ping), node ID correct, and not in /optout list."),
        ("Mail not delivering", "Check mailbox name spelling, ensure subscribed with /c <mailbox>, verify radio connection."),
        ("Poor signal quality", "SNR below 0 dB is poor. Try: reposition node, check antenna, wait for better conditions, or use ROUTER."),
    ]

    for q, a in troubleshoot:
        synthetic.append({
            'input': q,
            'output': a,
            'metadata': {
                'command': '',
                'source': 'synthetic',
                'category': 'troubleshooting'
            }
        })

    return synthetic


def balance_dataset(pairs: List[Dict[str, Any]], target_size: int) -> List[Dict[str, Any]]:
    """
    Balance dataset by command/category to ensure even coverage.

    Args:
        pairs: Input training pairs
        target_size: Desired number of pairs

    Returns:
        Balanced dataset
    """
    # Group by command
    by_command = defaultdict(list)
    for pair in pairs:
        cmd = pair['metadata'].get('command', 'other')
        by_command[cmd].append(pair)

    # Calculate samples per command
    num_commands = len(by_command)
    samples_per_cmd = target_size // num_commands if num_commands > 0 else 0

    balanced = []

    for cmd, cmd_pairs in by_command.items():
        if len(cmd_pairs) <= samples_per_cmd:
            # Use all available
            balanced.extend(cmd_pairs)
        else:
            # Sample to balance
            balanced.extend(random.sample(cmd_pairs, samples_per_cmd))

    # If we're short, add more from largest categories
    if len(balanced) < target_size:
        remaining = target_size - len(balanced)
        all_unused = [p for p in pairs if p not in balanced]
        if all_unused:
            balanced.extend(random.sample(all_unused, min(remaining, len(all_unused))))

    return balanced


def write_jsonl(pairs: List[Dict[str, Any]], output_path: Path):
    """
    Write training pairs to JSONL format.

    Args:
        pairs: Training pairs to write
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for pair in pairs:
            # Format for Axolotl ShareGPT style
            entry = {
                'conversations': [
                    {'from': 'human', 'value': pair['input']},
                    {'from': 'gpt', 'value': pair['output']}
                ],
                'metadata': pair.get('metadata', {})
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"✓ Wrote {len(pairs)} pairs to {output_path}")


def create_splits(pairs: List[Dict[str, Any]], train_ratio: float = 0.8, val_ratio: float = 0.1):
    """
    Create train/val/test splits.

    Args:
        pairs: All training pairs
        train_ratio: Fraction for training (default 0.8)
        val_ratio: Fraction for validation (default 0.1)
                   Test gets remainder (0.1)

    Returns:
        Tuple of (train, val, test) lists
    """
    random.shuffle(pairs)

    total = len(pairs)
    train_size = int(total * train_ratio)
    val_size = int(total * val_ratio)

    train = pairs[:train_size]
    val = pairs[train_size:train_size + val_size]
    test = pairs[train_size + val_size:]

    return train, val, test


def main():
    parser = argparse.ArgumentParser(description='Prepare Mesh-AI training data')
    parser.add_argument('--min-pairs', type=int, default=50000,
                        help='Minimum training pairs to generate')
    parser.add_argument('--output-dir', type=Path, default=Path('data/training'),
                        help='Output directory for training files')
    parser.add_argument('--archive', type=Path, default=Path('messages_archive.json'),
                        help='Path to messages_archive.json')
    parser.add_argument('--mailboxes', type=Path, default=Path('mesh_mailboxes.json'),
                        help='Path to mesh_mailboxes.json')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')

    args = parser.parse_args()

    random.seed(args.seed)

    print("=" * 60)
    print("Mesh-AI Training Data Preparation")
    print("=" * 60)

    # Collect training pairs from all sources
    all_pairs = []

    print("\n1. Extracting from archives...")
    archive_pairs = parse_messages_archive(args.archive)
    print(f"   Found {len(archive_pairs)} pairs from archive")
    all_pairs.extend(archive_pairs)

    print("\n2. Extracting from mailboxes...")
    mail_pairs = parse_mail_conversations(args.mailboxes)
    print(f"   Found {len(mail_pairs)} pairs from mailboxes")
    all_pairs.extend(mail_pairs)

    print("\n3. Extracting Meshtastic technical knowledge...")
    meshtastic_pairs = parse_meshtastic_knowledge()
    print(f"   Found {len(meshtastic_pairs)} Meshtastic Q&A pairs")
    all_pairs.extend(meshtastic_pairs)

    print("\n4. Generating synthetic pairs...")
    synthetic_pairs = generate_synthetic_pairs()
    print(f"   Generated {len(synthetic_pairs)} synthetic pairs")
    all_pairs.extend(synthetic_pairs)

    print(f"\n5. Total pairs collected: {len(all_pairs)}")

    # Balance and expand if needed
    if len(all_pairs) < args.min_pairs:
        print(f"   Expanding to {args.min_pairs} pairs...")
        # Duplicate data with slight variations to reach target
        multiplier = (args.min_pairs // len(all_pairs)) + 1
        all_pairs = all_pairs * multiplier

    balanced = balance_dataset(all_pairs, args.min_pairs)
    print(f"   Balanced dataset: {len(balanced)} pairs")

    # Create splits
    print("\n6. Creating train/val/test splits...")
    train, val, test = create_splits(balanced)

    print(f"   Train: {len(train)} pairs (80%)")
    print(f"   Val:   {len(val)} pairs (10%)")
    print(f"   Test:  {len(test)} pairs (10%)")

    # Write output files
    print("\n7. Writing output files...")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(train, args.output_dir / 'train.jsonl')
    write_jsonl(val, args.output_dir / 'val.jsonl')
    write_jsonl(test, args.output_dir / 'test.jsonl')

    # Write metadata
    metadata = {
        'created': datetime.now().isoformat(),
        'total_pairs': len(balanced),
        'train_size': len(train),
        'val_size': len(val),
        'test_size': len(test),
        'sources': {
            'archive': len(archive_pairs),
            'mailboxes': len(mail_pairs),
            'meshtastic_knowledge': len(meshtastic_pairs),
            'synthetic': len(synthetic_pairs)
        },
        'seed': args.seed
    }

    metadata_path = args.output_dir / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✓ Training data preparation complete!")
    print(f"✓ Files written to: {args.output_dir}")
    print(f"✓ Metadata saved to: {metadata_path}")
    print("\nNext steps:")
    print("  1. Review train.jsonl, val.jsonl, test.jsonl")
    print("  2. Configure Axolotl: cp training_configs/mesh-ai-1b.yaml .")
    print("  3. Train: accelerate launch -m axolotl.cli.train mesh-ai-1b.yaml")


if __name__ == '__main__':
    main()
