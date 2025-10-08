"""
System Context Builder for Context-Aware AI Help

Generates comprehensive context package (~50k tokens) for:
- Onboarding process interactive help
- /system command queries
- Troubleshooting with full system awareness

Context includes:
- All command documentation
- Architecture overview
- Current user settings
- System state (version, channels, nodes)
- Feature explanations
"""

import time
from typing import Dict, Any, Optional
from .help_database import HELP_DATABASE


def get_github_version() -> str:
    """Get current GitHub version/commit if available."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "v2.1-unknown"


def get_active_channels(interface) -> str:
    """Get comma-separated list of active channels."""
    channel_names = []
    try:
        if interface and hasattr(interface, "channels") and interface.channels:
            channels = interface.channels
            if isinstance(channels, dict):
                for ch_idx, ch_data in channels.items():
                    if isinstance(ch_data, dict):
                        settings = ch_data.get("settings", {})
                        if isinstance(settings, dict):
                            ch_name = settings.get("name", "")
                            if ch_name and ch_name not in channel_names:
                                channel_names.append(ch_name)
    except Exception:
        pass
    return ", ".join(channel_names) if channel_names else "None detected"


def get_modem_preset_name(preset_num: Optional[int]) -> str:
    """Convert modem preset number to readable name."""
    presets = {
        0: "LONG_FAST",
        1: "LONG_SLOW",
        2: "VERY_LONG_SLOW",
        3: "MEDIUM_SLOW",
        4: "MEDIUM_FAST",
        5: "SHORT_SLOW",
        6: "SHORT_FAST",
        7: "LONG_MODERATE",
        8: "SHORT_TURBO"
    }
    return presets.get(preset_num, f"Unknown ({preset_num})")


def build_commands_section() -> str:
    """Build comprehensive commands documentation from help database."""
    sections = {
        "AI & Conversation": [],
        "Network": [],
        "Logs & Reports": [],
        "Wiki & Knowledge": [],
        "System": [],
        "Other": []
    }

    for cmd, info in sorted(HELP_DATABASE.items()):
        category = info.get("category", "Other")
        if category not in sections:
            sections[category] = []

        desc = info.get("description", "No description")
        usage = info.get("usage", cmd)
        examples = info.get("examples", [])
        aliases = info.get("aliases", [])

        cmd_doc = f"  {cmd}: {desc}\n    Usage: {usage}"
        if examples:
            cmd_doc += f"\n    Examples: {', '.join(examples)}"
        if aliases:
            cmd_doc += f"\n    Aliases: {', '.join(aliases)}"

        sections[category].append(cmd_doc)

    output = "AVAILABLE COMMANDS\n" + "=" * 80 + "\n\n"
    for category, commands in sections.items():
        if commands:
            output += f"\n[{category}]\n" + "-" * 80 + "\n"
            output += "\n\n".join(commands) + "\n"

    return output


def build_architecture_section() -> str:
    """Build architecture and system flow documentation."""
    return """
SYSTEM ARCHITECTURE
================================================================================

MESSAGE FLOW
------------
1. on_receive() - Entry point for all incoming Meshtastic packets
   - Filters ROUTING_APP packets for ACK tracking
   - Extracts text from TEXT_MESSAGE_APP packets
   - Routes to appropriate handler based on content

2. route_message() - Message routing logic
   - Checks for built-in commands (/help, /node, /relay, etc.)
   - Detects shortname relay syntax (e.g., "lucy: hello")
   - Auto-routes replies to last relay sender
   - Falls through to AI handler if no command match

3. handle_ai() - AI conversation processing
   - Loads conversation history from memory
   - Injects system prompts and context
   - Calls configured LLM (OpenAI, Anthropic, Ollama, etc.)
   - Streams response back in chunks
   - Saves to conversation history

RELAY SYSTEM
------------
Multi-Network Message Bridging with ACK Tracking

Architecture:
- Uses daemon threads for non-blocking sends
- Tracks pending ACKs in PENDING_RELAY_ACKS dict (keyed by packet_id)
- 20-second timeout per message chunk
- Multi-chunk support for long messages (splits at ~200 chars)

Flow:
1. User sends: "shortname: message"
2. System extracts target shortname and message
3. Looks up node_id from shortname cache
4. Splits message into chunks if needed
5. Sends each chunk via sendText(wantAck=True) in separate thread
6. Extracts packet_id from MeshPacket.id field
7. Creates threading.Event per chunk for ACK waiting
8. on_receive() detects ROUTING_APP packets with matching requestId
9. Sets event to signal ACK received
10. Worker waits for all chunks to ACK or timeout

Auto-Reply Feature:
- When user receives relay, system stores sender in LAST_RELAY_SENDER
- Next plain message (not starting with shortname) auto-routes to that sender
- Enables natural conversation flow without re-typing shortname
- Clears after one use

ACK Detection Fix:
- ACK packets are ROUTING_APP (portnum=3)
- requestId is in decoded.get('requestId'), NOT packet.get('requestId')
- This was the key bug fix that made ACK tracking work

DASHBOARD
---------
Real-time Operations Center

Architecture:
- Flask web server on port 5000
- EventSource (SSE) streaming for live updates
- SQLite metrics database for graphs
- JavaScript polling for metrics (10s interval)
- Activity feed limited to 20 lines for mobile

Features:
- Live activity log with auto-scroll
- System metrics (CPU, memory, uptime, messages/hour)
- Connected nodes visualization
- Settings management
- Onboarding wizard with 9-step tour

Mobile Optimization:
- Activity feed capped at 20 lines (LOG_STREAM_MAX)
- Responsive layout for small screens
- Auto-scroll detection with manual override

LOGS vs REPORTS
---------------
Two types of persistent knowledge:

Logs (Private):
- Created with /log <name> or "remember this as <name>"
- Only visible to creator (sender_id check)
- Searchable by creator with /find
- Listed with /logs
- Retrieved with /readlog <name>

Reports (Public):
- Created with /report <name>
- Visible to everyone on mesh
- Searchable by anyone with /find
- Listed with /reports
- Retrieved with /readreport <name>

Storage:
- Both stored in mesh_master/memories/ directory
- JSON format with metadata (sender, timestamp, etc.)
- Automatically indexed for search

WIKI SYSTEM
-----------
Persistent knowledge base with web crawling

Features:
- Add entries: /wiki <topic>: <content>
- Search: /wikisearch <query>
- Crawl web: /wikicrawl <url>
- Full-text search across all wiki entries and crawled pages

Storage:
- wiki_database.json for manual entries
- web_crawl_cache/ for crawled content
- Markdown formatting preserved

NODE TRACKING
-------------
Automatic discovery and caching

Data Sources:
- NODE_FIRST_SEEN: Tracks first contact timestamp
- interface.nodes: Live node database from Meshtastic
- Shortname cache: Maps shortname -> node_id for relay

Commands:
- /nodes: List all nodes seen in last 24 hours (newest first)
- /node <shortname>: Detailed info (SNR, signal strength, last heard, hops)
- /networks: List all connected channels

SNR Thresholds (Modem-Aware):
- LONG presets (0,1,2,7): Excellent ≥10dB, Good ≥5dB
- MEDIUM presets (3,4): Excellent ≥5dB, Good ≥0dB
- SHORT presets (5,6,8): Excellent ≥0dB, Good ≥-5dB

ONBOARDING SYSTEM
-----------------
9-step interactive tour for new users

Steps:
1. Welcome & overview
2. LLM configuration
3. Connection setup (serial/wifi)
4. Channel management
5. Basic commands intro
6. Relay system demo
7. Logs & reports
8. Wiki & knowledge
9. Dashboard tour

Features:
- Progress tracking in ONBOARDING_STATE
- Step validation before advancement
- /skip to skip steps
- /restart to restart tour
- Context-aware help (coming soon)

PRIVACY & SECURITY
------------------
- Logs are private (creator-only access)
- Reports are public (mesh-wide visibility)
- Relay messages show sender identity
- No message content in activity feed (coming soon)
- /optout and /optin for relay privacy (coming soon)

API INTEGRATIONS
----------------
Supported LLM Providers:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude 3.5 Sonnet, etc.)
- Ollama (local models)
- OpenRouter (multi-model proxy)

Configuration:
- API keys stored in mesh_master/llm_config.json
- Model selection per provider
- Temperature, max_tokens configurable
- Streaming support for all providers
"""


def build_settings_section(config: Dict[str, Any], interface=None) -> str:
    """Build current settings snapshot."""

    # LLM Settings
    llm_provider = config.get("llm_provider", "unknown")
    llm_model = config.get("llm_model", "unknown")
    api_key_status = "Configured" if config.get("api_key") else "Not set"

    # Connection Settings
    connection_type = config.get("connection_type", "unknown")
    if connection_type == "serial":
        conn_detail = f"Serial: {config.get('serial_port', 'auto-detect')}"
    else:
        conn_detail = f"WiFi: {config.get('wifi_host', '192.168.0.1')}"

    # Channel Info
    channels = get_active_channels(interface)

    # Modem Preset
    modem_preset = None
    if interface and hasattr(interface, "localNode"):
        local_node = interface.localNode
        if hasattr(local_node, "localConfig"):
            lora_config = getattr(local_node.localConfig, "lora", None)
            if lora_config:
                modem_preset = getattr(lora_config, "modem_preset", None)

    modem_name = get_modem_preset_name(modem_preset)

    # Relay Status
    relay_enabled = "Enabled (ACK tracking active)" if config.get("relay_enabled", True) else "Disabled"

    # Dashboard
    dashboard_port = config.get("dashboard_port", 5000)

    return f"""
CURRENT SETTINGS
================================================================================

VERSION
-------
GitHub Build: {get_github_version()}
Install Date: {config.get('install_date', 'Unknown')}

LLM CONFIGURATION
-----------------
Provider: {llm_provider}
Model: {llm_model}
API Key: {api_key_status}
Temperature: {config.get('temperature', 0.7)}
Max Tokens: {config.get('max_tokens', 500)}

CONNECTION
----------
Type: {connection_type}
Details: {conn_detail}
Status: {"Connected" if interface else "Disconnected"}

NETWORK
-------
Channels: {channels}
Modem Preset: {modem_name}

FEATURES
--------
Relay System: {relay_enabled}
Dashboard: http://localhost:{dashboard_port}/dashboard
Onboarding: {config.get('onboarding_completed', 'Not completed')}
"""


def build_features_section() -> str:
    """Build detailed feature explanations."""
    return """
FEATURE DEEP-DIVE
================================================================================

RELAY SYSTEM - Cross-Network Message Bridge
--------------------------------------------
The relay system allows messages to be sent between nodes on different mesh
networks, effectively turning MESH-MASTER into a network bridge.

Syntax:
  <shortname>: <message>

Example:
  User on Network A: "lucy: hey how are you?"
  → System relays to lucy on Network B
  → Lucy receives: "📨 Relay from SenderName: hey how are you?"
  → Lucy replies: "good thanks!"
  → System auto-routes reply back to original sender

Technical Details:
- Multi-chunk support (messages split at ~200 chars)
- ACK tracking per chunk with 20s timeout
- Threading for non-blocking sends
- Auto-reply tracking for conversational flow
- Modem-aware signal strength estimation

Network Bridge Capability:
If you're connected to multiple channels (e.g., "Main Channel" and "SnailNet"),
and two users are each only on one of those channels, they can communicate
through you via relay. This is a MAJOR feature for connecting isolated networks.

LOGS vs REPORTS - Privacy-Aware Knowledge Storage
--------------------------------------------------
Two types of persistent memory with different visibility:

LOGS (Private to Creator):
- Purpose: Personal notes, observations, data only you should see
- Create: /log <name> or "remember this as <name>"
- View: /readlog <name> or /logs (lists all YOUR logs)
- Search: /find <query> (only searches YOUR logs)
- Use Case: "remember this as water level data" for personal tracking

REPORTS (Public to Mesh):
- Purpose: Information meant to be shared with everyone
- Create: /report <name> or "make a report called <name>"
- View: /readreport <name> or /reports (lists ALL reports)
- Search: /find <query> (searches ALL reports)
- Use Case: "make a report called weather forecast" for community info

Privacy Note:
The system respects creator privacy for logs. Only you can see your logs.
Reports are intentionally public for mesh-wide knowledge sharing.

WIKI SYSTEM - Persistent Knowledge Base
----------------------------------------
The wiki acts as a collective knowledge repository with web crawling support.

Manual Entries:
  /wiki <topic>: <content>
  Example: /wiki python: Python is a programming language

Web Crawling:
  /wikicrawl <url>
  Example: /wikicrawl https://meshtastic.org/docs/getting-started
  → System fetches page, extracts text, stores in cache
  → Content becomes searchable

Search:
  /wikisearch <query>
  Example: /wikisearch meshtastic range
  → Searches both manual entries and crawled pages
  → Returns relevant excerpts with sources

Use Case:
Build a knowledge base of technical docs, troubleshooting guides, or community
resources that persists across reboots and is searchable by anyone.

DASHBOARD - Real-Time Operations Center
----------------------------------------
Web-based interface for monitoring and management.

Access:
  http://localhost:5000/dashboard
  (For mobile: need to bind to 0.0.0.0 - coming soon)

Features:
  - Live Activity Feed: Real-time message stream (20 line limit for mobile)
  - System Metrics: CPU, memory, uptime, message rate
  - Node Visualization: Connected nodes with signal strength
  - Settings Management: Change LLM, connection, features
  - Onboarding Wizard: Interactive setup tour

Mobile Optimization:
  - Responsive layout
  - Activity feed capped at 20 lines
  - Auto-scroll with manual override
  - Touch-friendly controls

NODE DISCOVERY - Automatic Network Mapping
-------------------------------------------
System automatically tracks all nodes it sees on any connected channel.

Discovery:
  - Listens to all Meshtastic packets
  - Extracts shortname, longname, node_id
  - Records first seen timestamp
  - Updates last heard timestamp
  - Caches for relay lookup

Commands:
  /nodes: List all nodes seen in last 24 hours
    → Sorted by most recently active
    → Shows shortnames only for quick reference

  /node <shortname>: Detailed info for specific node
    → Signal strength estimate (Excellent/Good/Weak/Poor)
    → SNR in dB (modem preset aware)
    → Last heard timestamp
    → Hop count if available
    → Longname if available

  /networks: List all connected channels
    → Shows which mesh networks you're bridging

Use Case:
Before relaying to someone, check /nodes to see if they're online.
Use /node <shortname> to check signal quality before sending large messages.

ONBOARDING - Interactive Setup Tour
------------------------------------
9-step guided tour for new users to configure and learn the system.

Steps:
  1. Welcome & System Overview
  2. LLM Configuration (choose provider, enter API key)
  3. Connection Setup (serial port or WiFi)
  4. Channel Management (connect to mesh networks)
  5. Basic Commands Introduction
  6. Relay System Demo & Practice
  7. Logs & Reports Tutorial
  8. Wiki & Knowledge Base
  9. Dashboard Tour & Completion

Features:
  - Progress tracking (resume where you left off)
  - Step validation (can't proceed until configured)
  - /skip to skip optional steps
  - /restart to start over
  - Context-aware help (ask questions anytime)

Auto-Start:
  - Triggers on first run for new installations
  - Can be manually started with /onboarding

AI CONVERSATION - Contextual Intelligence
------------------------------------------
Every message that doesn't match a command or relay syntax goes to the AI.

Context Awareness:
  - Remembers conversation history per user
  - Knows current system settings
  - Can access logs, reports, wiki for knowledge
  - Can search web if configured
  - Understands Meshtastic environment

Conversation Memory:
  - Stored in mesh_master/memories/conversations/
  - Keyed by sender_id for privacy
  - Persists across reboots
  - Can be cleared with /clear or /forget

Streaming:
  - Responses sent in chunks for faster perceived response
  - Long responses automatically split for Meshtastic limits
  - Handles network interruptions gracefully

PRIVACY CONTROLS (Coming Soon)
-------------------------------
/optout: Disable relay for your node
  → Others can't relay through you
  → You can still send relays

/optin: Re-enable relay participation
  → Default state for new nodes

OFFLINE MESSAGE QUEUE (Coming Soon)
------------------------------------
When relay ACK fails (recipient offline):
  - Message stored in queue
  - Delivered when recipient comes back online
  - Notification sent to original sender

This enables asynchronous messaging across mesh networks.
"""


def build_system_context(config: Dict[str, Any], interface=None, user_query: Optional[str] = None) -> str:
    """
    Build complete system context for AI injection.

    Args:
        config: Current system configuration dict
        interface: Meshtastic interface object (optional)
        user_query: User's question for context (optional)

    Returns:
        Complete context string (~50k tokens)
    """

    context_parts = [
        "=" * 80,
        "MESH-MASTER SYSTEM CONTEXT",
        "=" * 80,
        "",
        "This is comprehensive system documentation to help answer user questions",
        "about MESH-MASTER features, commands, and architecture.",
        "",
        build_settings_section(config, interface),
        "",
        build_commands_section(),
        "",
        build_architecture_section(),
        "",
        build_features_section(),
        "",
        "=" * 80,
    ]

    if user_query:
        context_parts.extend([
            "",
            f"USER QUERY: {user_query}",
            "",
            "Please answer the user's question using the system context above.",
            "Be specific, cite relevant commands and features, and provide examples.",
            "=" * 80,
        ])

    return "\n".join(context_parts)


# Context activation state
SYSTEM_CONTEXT_ACTIVE = False
SYSTEM_CONTEXT_TIMESTAMP = 0
SYSTEM_CONTEXT_TIMEOUT = 1800  # 30 minutes
SYSTEM_CONTEXT_SINGLE_USE = False  # Single-use mode for /help and /menu follow-ups


def activate_system_context():
    """Activate system context for onboarding or /system command (persistent)."""
    global SYSTEM_CONTEXT_ACTIVE, SYSTEM_CONTEXT_TIMESTAMP, SYSTEM_CONTEXT_SINGLE_USE
    SYSTEM_CONTEXT_ACTIVE = True
    SYSTEM_CONTEXT_TIMESTAMP = time.time()
    SYSTEM_CONTEXT_SINGLE_USE = False
    print(f"[CONTEXT DEBUG] activate_system_context() called: ACTIVE={SYSTEM_CONTEXT_ACTIVE}, ts={SYSTEM_CONTEXT_TIMESTAMP}")


def activate_system_context_singleuse():
    """Activate system context for one question only (/help and /menu follow-ups)."""
    global SYSTEM_CONTEXT_ACTIVE, SYSTEM_CONTEXT_TIMESTAMP, SYSTEM_CONTEXT_SINGLE_USE
    SYSTEM_CONTEXT_ACTIVE = True
    SYSTEM_CONTEXT_TIMESTAMP = time.time()
    SYSTEM_CONTEXT_SINGLE_USE = True


def deactivate_system_context():
    """Deactivate system context (onboarding complete or timeout)."""
    global SYSTEM_CONTEXT_ACTIVE, SYSTEM_CONTEXT_TIMESTAMP, SYSTEM_CONTEXT_SINGLE_USE
    SYSTEM_CONTEXT_ACTIVE = False
    SYSTEM_CONTEXT_TIMESTAMP = 0
    SYSTEM_CONTEXT_SINGLE_USE = False


def is_system_context_active() -> bool:
    """Check if system context should be injected."""
    global SYSTEM_CONTEXT_ACTIVE, SYSTEM_CONTEXT_TIMESTAMP

    if not SYSTEM_CONTEXT_ACTIVE:
        return False

    # Check timeout
    if time.time() - SYSTEM_CONTEXT_TIMESTAMP > SYSTEM_CONTEXT_TIMEOUT:
        deactivate_system_context()
        return False

    return True


def consume_system_context() -> bool:
    """
    Check if context is active and consume it if single-use.
    Returns True if context should be injected.
    """
    global SYSTEM_CONTEXT_SINGLE_USE

    active = is_system_context_active()
    # Debug: print state
    print(f"[CONTEXT DEBUG] consume_system_context() called: ACTIVE={SYSTEM_CONTEXT_ACTIVE}, active={active}, single_use={SYSTEM_CONTEXT_SINGLE_USE}")

    if not active:
        return False

    # If single-use mode, deactivate after this use
    if SYSTEM_CONTEXT_SINGLE_USE:
        deactivate_system_context()

    return True


def refresh_system_context_timeout():
    """Refresh timeout when user interacts (only for persistent mode)."""
    global SYSTEM_CONTEXT_TIMESTAMP, SYSTEM_CONTEXT_SINGLE_USE
    if SYSTEM_CONTEXT_ACTIVE and not SYSTEM_CONTEXT_SINGLE_USE:
        SYSTEM_CONTEXT_TIMESTAMP = time.time()
