# MESH MASTER v2.5 — Off-Grid AI Operations Suite

**MESH MASTER** is a resilient AI copilot for Meshtastic LoRa mesh networks. It remembers conversations, relays messages across networks, handles async messaging, runs games, and maintains operations even when internet is unavailable.

> **Disclaimer:** This is a community project, not affiliated with the official Meshtastic project. Always maintain backup communication paths for emergencies.

---

## 🚀 Quick Start

### Install (One Command)
```bash
rm -rf Mesh-Master && git clone https://github.com/Snail3D/Mesh-Master.git && cd Mesh-Master && ./setup.sh
```

**What it does:**
- ✅ Auto-detects your platform (macOS, Linux, Raspberry Pi, Windows)
- ✅ Installs Python 3, Ollama, and all dependencies
- ✅ Creates config.json and desktop shortcut
- ✅ Prompts for optional setup (Ollama model, etc.)

### After Installation
1. Double-click the **Mesh Master** desktop icon
2. Open dashboard: http://localhost:5001/dashboard
3. Edit config.json to set your radio connection

### Install as System Service (Auto-Start)
```bash
./scripts/universal/install_service.sh
```

### Uninstall
```bash
curl -sSL https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/universal/uninstall.sh | bash
```

---

## Key Features

### Network Relay
Send messages to any node by shortname:
_(snmo here is the radio shortname. Put the shortname
first while DM'ing the bot with or without the '/'
in order to send the relay)_
```
snmo how's the weather?
/snmo how's the weather?
```
- Real-time ACK tracking with 20-second timeout
- Multi-chunk support for long messages
- Auto-delivery queue when recipient is offline
- Privacy controls: `/optout` and `/optin`

### Mesh Mail
Async messaging system (like email on the mesh):

### 20+ Games
Chess, Blackjack, Hangman, Wordle, Morse code, Quizzes, and more. All DM-friendly.

### AI Assistant
Ask questions, get help, adjust personality: _(note that while DMing the bot, you can just speak naturally without the '/' commands to trigger the AI responses)_
```
/ai How do I configure my node?
/aipersonality set scholar
/save mission_context
/recall mission_context
```

### Offline Knowledge
- `/offline wiki <topic>` — Local Wikipedia mirror
- `/meshtastic <question>` — Curated field guide
- `/find <query>` — Search logs, reports, wiki, web cache

### Logs & Reports
- `/log my_entry` — Private notes (DM-only)
- `/report findings` — Public searchable reports
- `/find query` — Fuzzy search everything

### Dashboard
Real-time web interface for monitoring and control:
- Activity feed with emoji categories
- Per-channel message metrics with 30-day charts
- Radio configuration (names, roles, presets)
- Ollama model management
- Command browser
- GitHub version control

### Telegram Bot
Control your mesh from Telegram:
- Send commands remotely: `/nodes`, `/ai question`, `/relay message`
- Receive relay ACK notifications
- Monitor system health

### Security & Privacy
- Message content redacted from logs
- PIN-protected mailboxes with bcrypt hashing
- Encrypted conversation contexts per user
- URL filter blocks adult/warez sites
- All user data excluded from git
- Security audit trail with Telegram alerts

---

## Commands (Quick Reference)
[COMMANDS.md](COMMANDS.md) (all commands),

**Network & Relay**
- `<shortname> <msg>` — Relay message to shortname
- `/nodes` — List all reachable nodes
- `/node <shortname>` — Show signal details
- `/optout`, `/optin` — Control relay receipt

**Mesh Mail**
- `/m <box> <msg>` — Send to mailbox
- `/c [box]` — Check mail (with optional search)
- `/emailhelp` — Mail system help

**Notes & Search**
- `/log <title>` — Create private log entry
- `/report <title>` — Create public report
- `/find <query>` — Search across everything

**AI & Personality**
- `/ai <question>` — Ask AI
- `/aipersonality` — List/set/prompt personalities
- `/vibe [tone]` — Adjust conversation tone
- `/save [name]` — Capture context
- `/recall [name]` — Restore context

**Games & Fun**
- `/games` — List all games
- `/hangman start`, `/wordle start`, `/adventure start`
- `/masterquiz`, `/meshtasticquiz`
- `/rps`, `/coinflip`, `/yahtzee`, `/blackjack`

**Knowledge**
- `/offline wiki <topic>` — Local Wikipedia mirror
- `/wiki <topic>` — Fetch from online Wikipedia
- `/web <query>` — DuckDuckGo search (with URL caching)
- `/web <url>` — Fetch single webpage
- `/web crawl <domain> [pages]` — Crawl site and extract contacts
- `/meshtastic <question>` — LoRa field guide
- `/find <query>` — Search logs, reports, wiki, and crawl cache
- `/bible [topic]` — Bible verses
- `/weather` — Weather forecast

**Admin (DM-only)**
- `/menu` — Main menu
- `/about` — Version info
- `/help` — Help system
- `/status` — System status
- `/update` — Pull latest from GitHub
- `/stop`, `/reboot` — System control

---

## Installation Details

### Platform-Specific Notes
- **Raspberry Pi:** Takes 5-10 minutes (uses system packages)
- **macOS:** Auto-installs Python and Ollama (Homebrew preferred, .pkg fallback)
- **Windows:** Download Python and Ollama manually (setup.sh will guide)
- **Linux:** Fully automatic with sudo

---

## Security Notes

**Before making code changes, read:**
1. [SECURITY_INSTRUCTIONS.md](SECURITY_INSTRUCTIONS.md) — Security guidelines
2. [CLAUDE.md](CLAUDE.md) — Full project context

**Never commit:**
- `config.json` — Contains passwords and API keys
- `data/` — User logs, mail, conversations
- `*.log`, `*.db` files — Runtime data
- SSH keys — `*.pem`, `*.key`, `*_rsa`, `*_ed25519`

**Protected files are gitignored automatically.**

---

## Dashboard

Access at: **http://localhost:5001/dashboard**

Features:
- Real-time activity feed 
- Per-channel metrics with 30-day charts
- Relay tracking and ACK telemetry
- Radio configuration controls
- Ollama model management
- Command browser with descriptions
- GitHub branch/version selector
- Redacted Log, Activity feed, and telegram
 output for user privacy on managed systems. 
- Configuration editor

---

## Development

**Initial Setup:**
```bash
git clone https://github.com/Snail3D/Mesh-Master.git
cd Mesh-Master
./setup.sh
nano config.json  # Edit configuration
```

**Project Structure:**
- `mesh-master.py` — Main application (~28k lines)
- `mesh_master/` — Package modules
  - `relay_manager.py` — Network relay system
  - `mail_manager.py` — Mesh mail system
  - `system_context.py` — AI help system
  - `games/game_manager.py` — 20+ games
  - `offline_wiki.py`, `offline_crawl.py`, `offline_ddg.py` — Offline knowledge
- `static/` — Dashboard frontend
- `scripts/` — Installation scripts
- `data/` — User data (gitignored)

**Tech Stack:**
- Language: Python 3.11+
- Framework: Flask (dashboard)
- Mesh: Meshtastic
- AI: Ollama (local LLMs)
- Database: SQLite
- Platform: macOS, Linux, Raspberry Pi, Windows

---

## Support

- 📖 **Docs:** [COMMANDS.md](COMMANDS.md) (all commands), [README_SERVICE.md](README_SERVICE.md) (systemd/LaunchAgent), `docs/mail_readme.md` (mail internals)
- 🐛 **Issues:** Report on GitHub
- 💙 **Support Development:** [buymeacoffee.com/Snail3D](https://buymeacoffee.com/Snail3D)
- ⭐ **Star the Project:** [github.com/Snail3D/Mesh-Master](https://github.com/Snail3D/Mesh-Master)

---

## License

MIT License — See [LICENSE](LICENSE)

Meshtastic is a trademark of Meshtastic LLC.

---

## Acknowledgements

- Original Mesh Master by [MR_TBOT](https://github.com/mr-tbot/mesh-master)
- Meshtastic community for hardware, testing, and feedback
