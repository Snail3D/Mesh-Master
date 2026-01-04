<div align="center">

<img src="static/mesh-master-banner.png" alt="Mesh Master" width="600">

[![Watch the video](https://img.youtube.com/vi/X034-Q5VDd8/0.jpg)](https://www.youtube.com/watch?v=X034-Q5VDd8)

### v2.5 — Off-Grid AI Operations Suite

**MESH MASTER** is a resilient copilot for Meshtastic LoRa mesh networks. It remembers conversations, relays messages across networks, handles async messaging, runs games, and maintains operations even when internet is unavailable.

> **Disclaimer:** This is a community project, not affiliated with the official Meshtastic project. Always maintain backup communication paths for emergencies.

</div>

---

## 🚀 Quick Start

#### Installation

**macOS / Linux / Raspberry Pi:**
```bash
rm -rf ~/Mesh-Master && git clone https://github.com/Snail3D/Mesh-Master.git ~/Mesh-Master && cd ~/Mesh-Master && bash setup.sh
```

**Windows (Automatic - Recommended):**
> 🎯 **One-Click Install** - Automatically downloads Git, Python, and Mesh Master

1. Right-click PowerShell → **Run as Administrator**
2. Copy and paste this command:

```powershell
irm https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/windows/install.ps1 | iex
```

**What it does:**
- ✅ Auto-installs Git for Windows if needed
- ✅ Auto-installs Python 3.11+ if needed
- ✅ Downloads Mesh Master and all dependencies
- ✅ Creates Windows service (auto-start on boot)
- ✅ Creates desktop shortcuts

### After Installation
1. Double-click the **Mesh Master** desktop icon (or service starts automatically if installed)

**Tip:** Install as system service later from the dashboard (Operations Center)

### Uninstall

#### Complete Removal (Deletes Everything)

**macOS / Linux / Raspberry Pi:**
```bash
AUTO_DELETE=true bash ~/Mesh-Master/scripts/universal/uninstall.sh
```

**Windows:**
```powershell
$env:AUTO_DELETE="true"; powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Mesh-Master\scripts\windows\uninstall.ps1"
```

**This will remove:** Service, shortcuts, processes, AND the entire directory (including config.json and data).

#### Keep Config & Data (Remove Service Only)

**macOS / Linux / Raspberry Pi:**
```bash
bash ~/Mesh-Master/scripts/universal/uninstall.sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Mesh-Master\scripts\windows\uninstall.ps1"
```

**This will remove:** Service, shortcuts, processes. **Preserves:** Directory, config.json, data folder.

You can also use the **Complete Uninstall** button in the dashboard (Operations Center).

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
- Respects no nag quiet hours _(set in dashboard)_
- Auto-delivery queue when recipient is offline
- Privacy controls: `/optout` and `/optin`

### Mesh Mail
Async messaging system (like email on the mesh)

### 20+ Games
Chess, Blackjack, Hangman, Wordle, Morse code, Quizzes, and more. All DM-friendly.

### AI Assistant (With conversation memory!)
Ask questions, get help, adjust personality. Use any Ollama model!
```
```
### Offline Knowledge

### Logs & Reports

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
- Send commands remotely
- Receive relay ACK notifications
- Monitor system health

### Security & Privacy
- Message content redacted from logs
- PIN-protected mailboxes with bcrypt hashing
- Encrypted conversation contexts per user
- URL filter blocks adult/warez sites
- All user data excluded from git
- Security audit trail with Telegram alerts
- **Self-service blocking:** Users can blacklist themselves to stop all bot replies (DM `blacklist me` and confirm with Y). Unblock anytime with `/unblock`.
- **Data deletion:** Users can permanently delete all their data with `/deleteme` (logs, reports, sole-owner mailboxes, conversation history, AI settings).

---

## Commands (Quick Reference)
[COMMANDS.md](COMMANDS.md) (all commands),

**Network & Relay**
- `<shortname> <msg>` — Relay message to shortname
- `/nodes` — List all reachable nodes
- `/node <shortname>` — Show signal details
- `/optout`, `/optin` — Control relay receipt

**Mesh Mail**
- `/m <box> <msg>` — Send to mailbox _(sending a message to a mailbox that doesn't exist yet will prompt the user to open a new mailbox)_
- `/c <box> PIN` — Check mail _(pin only needed if one was set when the mailbox was created and for opening for the first time from the radio)_
- `/emailhelp` — Mail system help

**Notes & Search**
- `/log <title>` — Create private log entry
- `/report <title>` — Create public report
- `/find <query>` — Search across everything

**AI & Personality**
- `/ai <question>` — Ask AI (no /ai prefix needed in DM mode, just speak normally)
- `/vibe [tone]` — Adjust conversation tone
- `/save [name]` — Capture context
- `/recall [name]` — Restore context

**Games & Fun**
- `/games` — List all games
- `/hangman start`, `/wordle start`, 
- `/masterquiz`, `/meshtasticquiz`
- `/rps`, `/coinflip`, `/yahtzee`, `/blackjack`

**Knowledge**
- `/offline wiki <topic>` — Local Wikipedia mirror
- `/wiki <topic>` — Fetch from online Wikipedia
- `/web <query>` — DuckDuckGo search (with URL caching)
- `/web <url>` — Fetch single webpage
- `/web crawl <domain>` — Crawl site and extract contacts
- `/meshtastic <question>` — LoRa field guide
- `/find <query>` — Search logs, reports, wiki, and crawl cache
- `/bible [topic]` — Bible verses
- `/weather` — Weather forecast

**User Controls**
- `/stop` — Pause AI replies (DM your messages without responses)
- `/resume` — Re-enable AI replies
- `blacklist me` — Block all bot replies (reply Y/N to confirm)
- `/unblock` — Restore bot replies after blacklist
- `/deleteme` or `delete me` — Delete ALL your data permanently (logs, reports, mailboxes, history)

**Admin (DM-only)**
- `/menu` — Main menu
- `/about` — Version info
- `/help` — Help system
- `/status` — System status
- `/update` — Pull latest from GitHub
- `/reboot` — Restart server (reply Y/N to confirm)
- `/ban <shortname>` — Permanently ban a user
- `/timeout <shortname>` — Timeout a user for 24 hours
- `/unban <shortname>` — Remove ban or timeout
- `/showbanned` — View all banned and timed-out users

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

## Telegram Bot

Control your mesh remotely via Telegram. Setup is in the dashboard:

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Open dashboard → **Telegram panel**
3. Paste bot token and authorize your chat ID
4. Send commands: `/nodes`, `/ai question`, `/relay message`, `/status`, etc.

**Features:** Remote command control, real-time notifications, system monitoring, bidirectional messaging. Only authorized chat IDs can control.

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

## Support

- 📖 **Docs:** [COMMANDS.md](COMMANDS.md) (all commands), [README_SERVICE.md](README_SERVICE.md) (systemd/LaunchAgent), `docs/mail_readme.md` (mail internals)
- 🐛 **Issues:** Report on GitHub
- ⭐ **Star the Project:** [github.com/Snail3D/Mesh-Master](https://github.com/Snail3D/Mesh-Master)

---

## License

MIT License — See [LICENSE](LICENSE)

Meshtastic is a trademark of Meshtastic LLC
---

- Original Mesh-AI by [MR_TBOT](https://github.com/mr-tbot/mesh-ai)
- Meshtastic community for hardware, testing, and feedback

---
