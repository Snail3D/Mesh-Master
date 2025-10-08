"""
Mesh Master Help Database - Searchable documentation for all commands and features
"""

from typing import Dict, List, Optional, Tuple
import re

# Help entry structure: {command: {category, description, usage, examples, aliases, keywords}}
HELP_DATABASE: Dict[str, Dict[str, any]] = {
    # === MAIL SYSTEM ===
    "/m": {
        "category": "Mail",
        "description": "Send a message to a mailbox. Anyone subscribed to that mailbox will receive it.",
        "usage": "/m <mailbox> <message>",
        "examples": [
            "/m general Hello everyone!",
            "/m team Meeting at 3pm"
        ],
        "aliases": ["/mail"],
        "keywords": ["email", "inbox", "send", "subscribe", "mailbox"]
    },
    "/c": {
        "category": "Mail",
        "description": "Check your mail. Shows unread messages from mailboxes you're subscribed to.",
        "usage": "/c [mailbox]",
        "examples": [
            "/c",
            "/c general"
        ],
        "aliases": ["/check", "/checkmail"],
        "keywords": ["mail", "inbox", "read", "messages", "unread"]
    },
    "/snooze": {
        "category": "Mail",
        "description": "Stop heartbeat notifications for a mailbox until new messages arrive.",
        "usage": "/snooze <mailbox>",
        "examples": [
            "/snooze general"
        ],
        "aliases": [],
        "keywords": ["notifications", "mute", "pause", "mail", "stop"]
    },
    "reply": {
        "category": "Mail",
        "description": "Reply to a recent mail sender using their shortname.",
        "usage": "reply <shortname> <message>",
        "examples": [
            "reply lucy Thanks for the message!",
            "reply snmo Got it"
        ],
        "aliases": [],
        "keywords": ["mail", "respond", "answer", "message"]
    },

    # === SHORTNAME RELAY ===
    "shortname_relay": {
        "category": "Relay",
        "description": "Relay a message to another node by starting with their shortname. The bot acts as a relay between nodes.",
        "usage": "<shortname> <message>",
        "examples": [
            "snmo how are you doing?",
            "lucy got your message"
        ],
        "aliases": [],
        "keywords": ["relay", "forward", "send", "node", "shortname", "dm"]
    },
    "/nodes": {
        "category": "Network",
        "description": "List all nodes seen in the last 24 hours, sorted by most recently active.",
        "usage": "/nodes",
        "examples": [
            "/nodes"
        ],
        "aliases": [],
        "keywords": ["network", "list", "nodes", "mesh", "available", "online"]
    },
    "/node": {
        "category": "Network",
        "description": "Show detailed info about a specific node: signal strength, SNR, last heard, hop count.",
        "usage": "/node <shortname>",
        "examples": [
            "/node snmo",
            "/node lucy"
        ],
        "aliases": [],
        "keywords": ["node", "info", "signal", "snr", "status", "details", "rssi"]
    },
    "/networks": {
        "category": "Network",
        "description": "List all channels/networks this node is connected to.",
        "usage": "/networks",
        "examples": [
            "/networks"
        ],
        "aliases": [],
        "keywords": ["channels", "networks", "list", "connected"]
    },
    "/optout": {
        "category": "Network",
        "description": "Opt out of relay - others cannot relay messages to you (DM only). You can still send relays.",
        "usage": "/optout",
        "examples": ["/optout"],
        "aliases": [],
        "keywords": ["relay", "privacy", "opt-out", "disable", "block"]
    },
    "/optin": {
        "category": "Network",
        "description": "Opt back in to relay - allow others to relay messages to you again (DM only).",
        "usage": "/optin",
        "examples": ["/optin"],
        "aliases": [],
        "keywords": ["relay", "privacy", "opt-in", "enable", "allow"]
    },

    # === AI & CHAT ===
    "/ai": {
        "category": "AI",
        "description": "Ask the AI assistant a question or have a conversation.",
        "usage": "<message>",
        "examples": [
            "What's the weather like?",
            "Tell me a joke",
            "How do I configure my radio?"
        ],
        "aliases": [],
        "keywords": ["chatgpt", "ollama", "assistant", "question", "ask"]
    },
    "/system": {
        "category": "AI",
        "description": "Ask questions with full system context (commands, settings, architecture). AI has comprehensive knowledge of your config and all features.",
        "usage": "/system <question>",
        "examples": [
            "/system how does the relay work?",
            "/system what LLM am I using?",
            "/system how do I search logs?",
            "/system explain the onboarding process"
        ],
        "aliases": [],
        "keywords": ["help", "documentation", "settings", "config", "troubleshoot", "explain", "how"]
    },
    "/vibe": {
        "category": "AI",
        "description": "Set AI personality/tone for your conversation (DM only).",
        "usage": "/vibe <personality>",
        "examples": [
            "/vibe professional",
            "/vibe funny",
            "/vibe technical"
        ],
        "aliases": ["/aipersonality"],
        "keywords": ["personality", "tone", "style", "mood"]
    },
    "/save": {
        "category": "AI",
        "description": "Save your current conversation for later recall.",
        "usage": "/save [title]",
        "examples": [
            "/save",
            "/save radio config discussion"
        ],
        "aliases": [],
        "keywords": ["memory", "store", "remember", "context"]
    },
    "/recall": {
        "category": "AI",
        "description": "Recall a previously saved conversation.",
        "usage": "/recall [search]",
        "examples": [
            "/recall",
            "/recall radio config"
        ],
        "aliases": [],
        "keywords": ["memory", "load", "remember", "history"]
    },

    # === BIBLE ===
    "/bible": {
        "category": "Bible",
        "description": "Look up Bible verses. Supports auto-scroll mode.",
        "usage": "/bible <reference>",
        "examples": [
            "/bible John 3:16",
            "/bible Genesis 1:1-3",
            "/bible Psalm 23"
        ],
        "aliases": [],
        "keywords": ["scripture", "verse", "passage", "chapter"]
    },
    "/biblehelp": {
        "category": "Bible",
        "description": "Shows detailed help for Bible commands and features.",
        "usage": "/biblehelp",
        "examples": ["/biblehelp"],
        "aliases": [],
        "keywords": ["scripture", "help", "guide"]
    },

    # === GAMES ===
    "/games": {
        "category": "Games",
        "description": "List available games.",
        "usage": "/games",
        "examples": ["/games"],
        "aliases": [],
        "keywords": ["play", "entertainment", "fun"]
    },
    "/blackjack": {
        "category": "Games",
        "description": "Play blackjack (21).",
        "usage": "/blackjack",
        "examples": ["/blackjack"],
        "aliases": [],
        "keywords": ["cards", "21", "casino", "game"]
    },
    "/hangman": {
        "category": "Games",
        "description": "Play hangman word guessing game.",
        "usage": "/hangman",
        "examples": ["/hangman"],
        "aliases": [],
        "keywords": ["word", "guess", "letters", "game"]
    },
    "/wordle": {
        "category": "Games",
        "description": "Play Wordle word puzzle.",
        "usage": "/wordle",
        "examples": ["/wordle"],
        "aliases": [],
        "keywords": ["word", "puzzle", "guess", "game"]
    },

    # === UTILITIES ===
    "/weather": {
        "category": "Utilities",
        "description": "Get weather forecast for your location or a specified place.",
        "usage": "/weather [location]",
        "examples": [
            "/weather",
            "/weather El Paso TX"
        ],
        "aliases": [],
        "keywords": ["forecast", "temperature", "conditions", "climate"]
    },
    "/whereami": {
        "category": "Utilities",
        "description": "Get your current location coordinates.",
        "usage": "/whereami",
        "examples": ["/whereami"],
        "aliases": [],
        "keywords": ["location", "gps", "coordinates", "position"]
    },
    "/alarm": {
        "category": "Utilities",
        "description": "Set an alarm for a specific time.",
        "usage": "/alarm <time> [message]",
        "examples": [
            "/alarm 3:00pm",
            "/alarm 15:00 Meeting reminder"
        ],
        "aliases": [],
        "keywords": ["reminder", "notification", "schedule", "time"]
    },
    "/timer": {
        "category": "Utilities",
        "description": "Set a countdown timer.",
        "usage": "/timer <duration> [message]",
        "examples": [
            "/timer 5m",
            "/timer 1h30m Pizza is ready"
        ],
        "aliases": [],
        "keywords": ["countdown", "reminder", "notification"]
    },

    # === INFORMATION ===
    "/wiki": {
        "category": "Information",
        "description": "Search offline Wikipedia database.",
        "usage": "/wiki <search>",
        "examples": [
            "/wiki meshtastic",
            "/wiki radio propagation"
        ],
        "aliases": [],
        "keywords": ["wikipedia", "search", "knowledge", "encyclopedia"]
    },
    "/web": {
        "category": "Information",
        "description": "Fetch and summarize web content.",
        "usage": "/web <url>",
        "examples": [
            "/web https://example.com"
        ],
        "aliases": [],
        "keywords": ["internet", "url", "website", "fetch"]
    },
    "/meshinfo": {
        "category": "Information",
        "description": "Get information about the mesh network and connected nodes.",
        "usage": "/meshinfo",
        "examples": ["/meshinfo"],
        "aliases": [],
        "keywords": ["network", "nodes", "status", "info"]
    },

    # === SYSTEM ===
    "/menu": {
        "category": "System",
        "description": "Show interactive menu of features and commands.",
        "usage": "/menu",
        "examples": ["/menu"],
        "aliases": [],
        "keywords": ["browse", "navigation", "explore"]
    },
    "/onboard": {
        "category": "System",
        "description": "Start or continue the onboarding tour for new users.",
        "usage": "/onboard",
        "examples": ["/onboard"],
        "aliases": [],
        "keywords": ["tutorial", "guide", "getting started", "intro"]
    },
    "/stop": {
        "category": "System",
        "description": "Pause all responses and notifications. Use /start to resume.",
        "usage": "/stop",
        "examples": ["/stop"],
        "aliases": [],
        "keywords": ["pause", "mute", "silence", "halt"]
    },
    "/start": {
        "category": "System",
        "description": "Resume responses after using /stop.",
        "usage": "/start",
        "examples": ["/start"],
        "aliases": ["/resume", "/continue"],
        "keywords": ["unpause", "unmute", "continue"]
    },
    "/about": {
        "category": "System",
        "description": "Information about Mesh Master and its capabilities.",
        "usage": "/about",
        "examples": ["/about"],
        "aliases": ["/bot"],
        "keywords": ["info", "version", "credits"]
    },

    # === LOGGING ===
    "/log": {
        "category": "Logging",
        "description": "Create a private log entry (only you can search these).",
        "usage": "/log <message>",
        "examples": [
            "/log Checked batteries, all good",
            "/log Radio range test at park - 2.5km"
        ],
        "aliases": [],
        "keywords": ["notes", "diary", "record", "private"]
    },
    "/report": {
        "category": "Logging",
        "description": "Create a public report (searchable by everyone).",
        "usage": "/report <message>",
        "examples": [
            "/report Road closed on Main St",
            "/report Repeater offline at hilltop"
        ],
        "aliases": [],
        "keywords": ["public", "announce", "share", "alert"]
    },
    "/checklog": {
        "category": "Logging",
        "description": "List all your private logs, or read a specific log by name.",
        "usage": "/checklog [log name]",
        "examples": [
            "/checklog",
            "/checklog battery check"
        ],
        "aliases": ["/checklogs", "/readlog", "/readlogs"],
        "keywords": ["list", "view", "read", "private", "logs", "my"]
    },
    "/checkreport": {
        "category": "Logging",
        "description": "List all public reports, or read a specific report by name.",
        "usage": "/checkreport [report name]",
        "examples": [
            "/checkreport",
            "/checkreport road closure"
        ],
        "aliases": ["/checkreports", "/readreport", "/readreports"],
        "keywords": ["list", "view", "read", "public", "reports", "all"]
    },
    "/find": {
        "category": "Logging",
        "description": "Search your private logs and public reports.",
        "usage": "/find <search>",
        "examples": [
            "/find battery",
            "/find range test"
        ],
        "aliases": [],
        "keywords": ["search", "query", "lookup", "history"]
    },
}


def search_help(query: str, max_results: int = 5) -> List[Tuple[str, Dict]]:
    """
    Search help database for commands/features matching the query.
    Returns list of (command_name, help_entry) tuples sorted by relevance.
    """
    if not query:
        return []

    query_lower = query.lower().strip()
    results = []

    for cmd, entry in HELP_DATABASE.items():
        score = 0

        # Exact command match (highest priority)
        if cmd.lower() == query_lower or cmd.lower() == f"/{query_lower}":
            score += 100

        # Command contains query
        if query_lower in cmd.lower():
            score += 50

        # Alias match
        for alias in entry.get("aliases", []):
            if query_lower in alias.lower():
                score += 40

        # Category match
        if query_lower in entry.get("category", "").lower():
            score += 30

        # Keyword match
        for keyword in entry.get("keywords", []):
            if query_lower in keyword.lower():
                score += 20

        # Description match
        if query_lower in entry.get("description", "").lower():
            score += 10

        if score > 0:
            results.append((cmd, entry, score))

    # Sort by score (descending)
    results.sort(key=lambda x: x[2], reverse=True)

    # Return top results without score
    return [(cmd, entry) for cmd, entry, score in results[:max_results]]


def format_help_entry(command: str, entry: Dict, include_examples: bool = True) -> str:
    """Format a help entry for display."""
    lines = []

    # Header
    lines.append(f"📖 {command}")

    # Category
    category = entry.get("category", "General")
    lines.append(f"Category: {category}")

    # Description
    desc = entry.get("description", "No description available.")
    lines.append(f"\n{desc}")

    # Usage
    usage = entry.get("usage")
    if usage:
        lines.append(f"\n💡 Usage: {usage}")

    # Examples
    if include_examples:
        examples = entry.get("examples", [])
        if examples:
            lines.append("\n📝 Examples:")
            for example in examples[:3]:  # Limit to 3 examples
                lines.append(f"  {example}")

    # Aliases
    aliases = entry.get("aliases", [])
    if aliases:
        lines.append(f"\n🔀 Aliases: {', '.join(aliases)}")

    return "\n".join(lines)


def get_all_categories() -> List[str]:
    """Get all unique categories in the help database."""
    categories = set()
    for entry in HELP_DATABASE.values():
        cat = entry.get("category", "General")
        categories.add(cat)
    return sorted(categories)


def get_commands_by_category(category: str) -> List[str]:
    """Get all commands in a specific category."""
    commands = []
    for cmd, entry in HELP_DATABASE.items():
        if entry.get("category", "General") == category:
            commands.append(cmd)
    return sorted(commands)
