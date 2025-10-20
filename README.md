# MESH MASTER v2.0 — Off-Grid AI Operations Suite

**MESH MASTER 2.0** is the next evolution of the Mesh-AI project: a resilient AI copilot for Meshtastic LoRa meshes that remembers conversations, coordinates teams, and keeps the network moving even when the wider internet is gone. Version 2.0 introduces context-aware AI help, offline relay queuing, enhanced privacy controls, URL content filtering, and fuzzy search—all while maintaining the Mesh Mail hub, network bridge relay system, llama-powered games for morale and training, rich offline knowledge, and a comprehensive web command center.

> **Disclaimer**
> This project is an independent community effort and is **not associated** with the official Meshtastic project. Always maintain backup communication paths for real emergencies.

![Mesh Master Banner](docs/mesh-master-banner.png)

---

## 🚀 Quick Install (One Command)

Copy, paste, press Enter — you're done!

**macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/macos/install_service.sh | bash
```

**Linux/Raspberry Pi:**
```bash
curl -sSL https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/linux/install_service.sh | sudo bash
```

**Windows:** (Run as Administrator in PowerShell)
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/windows/install_service.bat" -OutFile "$env:TEMP\install_mesh.bat"; & "$env:TEMP\install_mesh.bat"
```

**What happens:**
- ✅ Finds or downloads Mesh Master automatically
- ✅ Installs Python dependencies
- ✅ Creates system service (auto-start on boot, auto-restart on crashes)
- ✅ Opens dashboard in your browser
- ✅ **Zero configuration needed** — just plug in your Meshtastic device!

**Next step:** Configure your radio connection at `http://localhost:5001/dashboard`

### 🗑️ Quick Uninstall (One Command)

**macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/macos/uninstall_service.sh | bash
```

**Linux/Raspberry Pi:**
```bash
curl -sSL https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/linux/uninstall_service.sh | sudo bash
```

**Windows:** (Run as Administrator in PowerShell)
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/windows/uninstall_service.bat" -OutFile "$env:TEMP\uninstall_mesh.bat"; & "$env:TEMP\uninstall_mesh.bat"
```

Completely removes Mesh Master service — no leftovers.

---

## 2.0 Headline Upgrades

### Latest Updates (October 2025)
- **Per-Channel Message Tracking** — Activity dashboard now shows message counts for each configured channel with 30-day historical charts on hover. Channel names auto-populate from radio settings (e.g., "LongFast", "SnailNet").
- **Relay Message Metrics** — Track relay messages sent with 24-hour counts, deltas, and 30-day trend charts. Monitor network bridge activity from the dashboard.
- **Remote Dashboard Access (Tailscale)** — New config section for easy Tailscale VPN setup. Access your dashboard securely from anywhere with automatic hostname detection and passwordless SSH support.
- **Security Audit Trail** — All config changes logged to `data/config_audit.json` with timestamps. Security-sensitive changes (passwords, tokens, auth keys) trigger instant Telegram alerts with masked values.
- **Activity Feed Cleanup** — Startup/shutdown alerts filtered from dashboard activity feed for cleaner monitoring. Only real events and user activity displayed.
- **Enhanced Activity Metrics** — All metrics now persist across reboots with 30-day historical charts: messages (total, direct, AI-authored, email, relay), per-channel activity, new nodes, ACK telemetry, games, and more.
- **Mobile-Optimized Charts** — Responsive chart popups with touch-device detection, dynamic positioning, and mobile-friendly sizing for all metrics.

### Core Features
- **Network Bridge Relay with ACK Tracking** — Forward messages to any node by shortname: `snmo hello there` or `/snmo hello there`. Real-time ACK confirmation shows which node acknowledged. Multi-chunk support for long messages. Acts as a bridge across multiple mesh networks—if this node sees networks A and B, users on network A can relay to users on network B seamlessly. **NEW:** Offline message queue stores failed relays and automatically delivers when recipient comes online (up to 3 attempts, 24-hour expiry).
- **Relay Privacy Controls** — `/optout` disables receiving relays (others can't relay to the user), `/optin` re-enables. Privacy preferences persist across reboots and updates in `data/relay_optout.json`.
- **Cross-Network Node Discovery** — `/nodes` lists all nodes seen in the last 24 hours across all channels/networks (sorted newest first). `/node <shortname>` shows detailed signal info (SNR, signal strength, last heard, hops, battery level, power status) with modem-aware thresholds. `/networks` lists all connected channels.
- **Interactive Onboarding** — New users receive a guided 9-step tour via `/onboard` (or `/onboarding`, `/onboardme`) covering the main menu, mesh mail, logs & reports, games, AI assistance, and helpful tools. Fully customizable welcome messages through the dashboard.
- **Private Logs & Public Reports** — `/log` creates private entries visible only to the author; `/report` creates public entries searchable by everyone via `/find`. **NEW:** Fuzzy matching with "Did you mean" suggestions for misspelled names. Command aliases: `/readlog`, `/readlogs`, `/checklog`, `/checklogs` (logs) and `/readreport`, `/readreports`, `/checkreport`, `/checkreports` (reports).
- **Enhanced Privacy & Security** — Message content redacted in all debug/info logs (shows `[X chars]` instead of full text). URL filter blocks adult and warez sites from crawling and search results with humorous error message. Security audit trail with Telegram alerts for sensitive changes. All sensitive user data gitignored.
- **Enhanced Dashboard** — Real-time activity feed (20-line mobile-optimized view), per-channel metrics with 30-day charts, relay tracking, radio configuration controls (node names, roles, modem presets, frequency slots), Ollama model management, collapsible command categories, and GitHub version selector. Accessible remotely via Tailscale or locally at `http://<your-ip>:5001/dashboard`.
- **Data Persistence** — All user data (logs, reports, mail, settings, game states, relay preferences) now protected by `.gitignore` and persists across git updates and system reboots.
- **Mesh Mail** — PIN-protected inboxes, multi-user notifications, and one-shot llama summaries keep longer messages flowing across the mesh.
- **Game Hub** — Chess & Checkers duels, Blackjack, Yahtzee rounds, Tic-Tac-Toe, Hangman, Wordle, Word Ladder, Adventure stories, Cipher drills, Bingo, Morse, Rock–Paper–Scissors, Coinflip, Quiz Battle, **Mesh Master Quiz** (`/masterquiz` - 50 comprehensive questions), **Meshtastic Quiz** (`/meshtasticquiz` - 50 detailed questions), and more—all DM-friendly and multilingual.
- **Adaptive Personalities & Context Capsules** — `/aipersonality` and `/save`/`/recall` tune the assistant instantly while persistent archives keep continuity across restarts.
- **Offline Knowledge on Tap** — Trimmed MeshTastic handbook, offline wiki lookups, and cached expert answers deliver verified guidance without leaving the mesh.
- **Simplified Activity Logs** — Icon-based notifications (📨 incoming, 📖 Bible, 🎮 Game, 🤖 AI, etc.) with no message content or node names for privacy and reduced clutter.
- **Hardening for the Field** — Automatic orphaned process cleanup, improved serial port lock handling, larger async queues, smarter retry logic, strict single-instance locks, and heartbeat-driven health reporting for container or bare-metal deployments.

---

## Feature Overview

### Network Bridge Relay System
MESH MASTER 2.0 can act as a relay bridge between multiple mesh networks, enabling communication across network boundaries.

**How It Works:**
- Send messages to any node by shortname: `snmo hello there` or `/snmo hello there`
- Real-time ACK tracking with 20-second timeout
- Confirmation shows which node acknowledged: `✅ ACK by NodeName` or `❌ No ACK from NodeName`
- Multi-chunk support automatically handles long messages (tracks ACKs for all chunks)
- Queue-based architecture handles relay bursts safely (3 concurrent workers, 100-item queue)
- **Offline message queue:** Failed relays automatically stored and delivered when recipient comes online (max 10 messages per user, 24-hour expiry, 3 delivery attempts)
- **Privacy controls:** `/optout` to disable receiving relays, `/optin` to re-enable (preferences persist in `data/relay_optout.json`)

**Cross-Network Bridge:**
If MESH MASTER is connected to multiple networks (e.g., SnailNet + MainChannel), it acts as a bridge:
- Users on SnailNet can relay to users on MainChannel and vice versa
- `/nodes` command shows all reachable nodes across all networks
- Seamless multi-network communication without manual routing

**Example Use Case:**
```
Network A: Alice, Bob, MESH-MASTER
Network B: Charlie, MESH-MASTER

Alice (on Network A): "charlie how's the weather?"
MESH-MASTER relays across network boundary
Charlie receives message, ACKs back
Alice gets: "✅ ACK by Charlie"
```

### AI Assistant Features
- End-to-end message history survives restarts (`messages_archive.json`) with configurable limits.
- Background async workers keep RX/TX responsive while Ollama generates replies.
- Tone and personalities can be adjusted at runtime with `/vibe`; the core system prompt is fixed. MOTD can be updated via DM-only admin commands.

### Mesh Mail & Collaboration
- Direct-message `/m mailbox message` to drop mail; guided flow creates boxes, sets optional PINs, and captures owner metadata.  
- `/c mailbox [question]` shows the latest entries and, when a question is provided, uses the bundled `llama3.2:1b` model to pull a concise answer.  
- `/wipe mailbox`, `/wipe chathistory`, `/wipe personality`, and `/wipe all <mailbox>` keep things tidy.  
- Notification engine flags subscribers on heartbeat with unread counts while respecting PIN security and brute-force throttling.  
- See `docs/mail_readme.md` for deep-dive internals.

### Game Hub & Morale Tools
- `/games` lists every title with quick descriptions and command hints.
- Story-driven `/adventure` adapts to the chat language and offers branching outcomes.
- `/wordladder` teammates can collaboratively bridge start/end words, asking the llama for hints on demand.
- Manage risk in `/blackjack`, push streaks in `/yahtzee`, or rally the squad with `/games` for the full list.
- Fast laughs with `/rps`, `/coinflip`, and `/quizbattle`; puzzle practice with `/cipher`, `/morse`, `/hangman`, `/wordle`.
- **Comprehensive Quiz Games:**
  - `/masterquiz` — 50 questions covering all Mesh Master features (relay, logs, reports, commands, mail, offline queue, dashboard, wiki, games)
  - `/meshtasticquiz` — 50 questions about Meshtastic (LoRa, mesh networking, node roles, SNR, presets, security, best practices)
  - Answer with 1-4 or a-d, check score anytime, auto-shuffled questions for replay value

### Knowledge & Research Aids
- `/meshtastic <question>` consults a curated ~25k token field guide with a warm cache for instant follow-ups.
- `/offline wiki <topic>` or `/offline wiki <topic> PIN=1234` taps locally mirrored reference articles.
- `/save` captures conversation context capsules for later `/recall`—perfect for mission hand-offs.
- `/find <query>` searches across private logs, public reports, wiki entries, and web crawl data with fuzzy matching.
- **URL Content Filter:** `/web` commands automatically block adult and warez sites from crawling and search results.
- **Fuzzy Search:** When log/report names are misspelled, get "Did you mean?" suggestions with top 3 matches.

### Web Dashboard & APIs
- Real-time log viewer with emoji categories (📡 connection, 📨 messages, 🤖 AI, ⚠️ warnings, 🔧 admin).  
- Three-column mesh console surfaces broadcasts, direct messages, and nearby nodes; quick-send form handles DM routing and chunking.  
- Health endpoints: `GET /ready`, `/live`, `/healthz`, `/heartbeat`, plus `/dashboard` and `/logs` frontends.  
- `/send` and `/ui_send` POST endpoints enable automated workflows; optional `/discord_webhook` bridge for cross-platform relays.

### Telegram Integration
MESH MASTER 2.0 includes full Telegram bot integration for remote mesh control and monitoring.

**Features:**
- **Remote Command Control** — Send any mesh command from Telegram (same permissions as dashboard)
- **Real-time Notifications** — Receive relay ACK confirmations, system alerts, and activity updates
- **Secure Access Control** — Whitelist specific Telegram chat IDs for authorized control
- **Bidirectional Communication** — Send messages to mesh from Telegram, receive mesh messages in Telegram
- **Status Monitoring** — Check mesh health, node status, and system metrics remotely

**Setup:**
1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Copy the bot token
3. Get your Chat ID (message the bot, then check `/dashboard` → Telegram panel)
4. Configure in `config.json`:
   ```json
   {
     "telegram_bot_enabled": true,
     "telegram_bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
     "telegram_chat_ids": [123456789, 987654321]
   }
   ```
5. Restart Mesh Master

**Usage:**
- Send commands directly: `/nodes`, `/ai how's the weather?`, `/relay hello`
- Receive notifications when relays are acknowledged
- Monitor system health and errors
- Control mesh operations from anywhere with internet access

**Security:**
- Only whitelisted chat IDs can control the bot
- Commands execute with same permissions as dashboard users
- Bot token stored securely (never logged or displayed)

---

### Security & Privacy Features

MESH MASTER 2.0 includes comprehensive security enhancements to protect sensitive data:

#### Message Content Redaction
All message content is automatically redacted in logs to protect privacy:
- **Debug/info logs** show `[X chars]` instead of full message text
- **File logs** (`mesh-master.log`) never contain message content
- **Dashboard activity feed** shows icons and metadata, not content
- **Console output** protects user privacy while maintaining debugging capabilities

Example log output:
```
🤖 [AsyncAI] Queueing response for Node_abc: [47 chars]
📡 Relay to snmo: [23 chars]
```

#### PIN Protection & Encryption
Mesh Mail system includes robust PIN security:
- **Hashed PINs** — Stored as bcrypt hashes, never plain text
- **Brute-force throttling** — Exponential backoff after failed attempts
- **Encryption keys** — Auto-generated per mailbox for content encryption
- **Owner verification** — Only mailbox owners can change PINs
- **Secure storage** — `data/mail_security.json` is gitignored and local-only

#### Chat Context Encryption
Saved conversation contexts (`/save` and `/recall`) are encrypted per radio ID:
- **Radio ID as key** — Each user's contexts encrypted with key derived from their radio ID (SHA256)
- **Fernet encryption** — Industry-standard symmetric encryption for all conversation data
- **Encrypted fields** — context, summary, and search_blob are all encrypted
- **Isolation** — Different radio IDs cannot decrypt each other's contexts
- **Transparent migration** — Existing plaintext contexts automatically encrypted on startup
- **File access insufficient** — Reading `data/saved_contexts.json` shows only ciphertext

Security model:
```
Radio ID (!12345678) → SHA256 hash → Fernet key → Encrypt/decrypt contexts
```

Only the correct radio ID can decrypt its own conversation history. This protects privacy in multi-user mesh networks and prevents filesystem-level snooping.

#### URL Content Filtering
Web search and crawl commands block inappropriate content:
- **Adult content filter** — Blocks adult/NSFW sites from `/web` results
- **Warez filter** — Prevents piracy/illegal download sites
- **Humorous error messages** — User-friendly blocked content notifications
- **Whitelist override** — Admins can configure exceptions if needed

#### Data Gitignoring
All sensitive user data is automatically excluded from git:
- `data/mail_security.json` — Mailbox PINs and encryption keys
- `data/saved_contexts.json` — Encrypted conversation contexts
- `data/logs/` — Private user log entries
- `data/relay_optout.json` — User privacy preferences
- `data/onboarding_state.json` — User onboarding progress
- `*.log` files — All runtime logs
- `messages_archive.json` — Message history
- `mesh_mail.db` — Mail database

This ensures:
- ✅ Safe git updates without losing user data
- ✅ No accidental commits of sensitive information
- ✅ Privacy preservation across code changes
- ✅ Secure multi-user deployments

---

## For Developers & AI Assistants

### 🚨 Security-First Development

**STOP!** Before making any code changes, read these critical documents:

1. **[SECURITY_INSTRUCTIONS.md](SECURITY_INSTRUCTIONS.md)** — Complete security guidelines
2. **[CLAUDE.md](CLAUDE.md)** — Full project context and architecture

#### Security Incident History

**October 19, 2025** — Credential exposure incident where `config.json` (containing dashboard password and Tailscale auth key) was accidentally committed to GitHub.

**Resolution:**
- Used `git filter-repo` to purge entire history
- Removed all personal data files (logs, mail, conversations, wiki cache)
- Created comprehensive security documentation
- Established strict gitignore policies
- Force-pushed clean history to GitHub

**Lesson:** Even one accidental commit can expose credentials in git history forever. Prevention is critical.

#### Protected Files (NEVER COMMIT)

These files contain sensitive data and **must never** be committed:

**Credentials:**
- `config.json` — Admin password, API keys, Tailscale auth tokens
- `*.pem`, `*.key`, `*_rsa`, `*_ed25519` — SSH keys, deploy keys

**User Data:**
- `data/logs/` — Private user logs
- `data/mail_security.json` — Mailbox PINs, encryption keys
- `data/saved_contexts.json` — Encrypted conversations
- `data/user_ai_settings.json` — User preferences
- `data/offline_wiki/`, `data/offline_crawl/` — Search/browsing history

**System Files:**
- `*.log`, `*.db`, `*.backup` — Runtime data

#### If You Accidentally Commit Credentials

1. **STOP** — Don't commit anything else
2. **READ** — Open SECURITY_INSTRUCTIONS.md
3. **ROTATE** — Change all exposed credentials immediately
4. **PURGE** — Use git filter-repo to remove from history
5. **FORCE PUSH** — Update GitHub with clean history
6. **NOTIFY** — Alert users if credentials were public

### 🤖 AI Assistant Starter Prompt

<details>
<summary><b>Click to expand starter prompt for Claude/ChatGPT/other AI assistants</b></summary>

```
I'm working on Mesh Master, an off-grid AI operations suite for Meshtastic LoRa mesh networks.

CRITICAL SECURITY INSTRUCTIONS:

Before making ANY changes to this codebase, you MUST:
1. Read SECURITY_INSTRUCTIONS.md completely
2. Review CLAUDE.md for project architecture
3. NEVER commit these files to git:
   - config.json (contains passwords, API keys)
   - data/ directory (user data, logs, mail)
   - *.log, *.db, *.backup files
   - SSH keys (*.pem, *.key, *_rsa, *_ed25519)

SECURITY INCIDENT HISTORY:
- October 19, 2025: config.json with credentials accidentally committed
- Resolution: git filter-repo history purge, force push to GitHub
- Lesson: Even one accidental commit exposes credentials forever

PROTECTED DEVELOPMENT RULES:
1. Always check git status before committing
2. Run security audit commands from SECURITY_INSTRUCTIONS.md
3. config.json.example is the template (safe to commit)
4. config.json is the live file (NEVER commit)
5. setup.sh automatically copies .example to live on first run

PROJECT CONTEXT:
- Main file: mesh-master.py (~27,000+ lines)
- Language: Python 3.11+
- Framework: Flask (dashboard), Meshtastic (mesh communication)
- AI: Ollama (local LLMs like llama3.2:1b, wizard-math:7b)
- Database: SQLite (mesh_mail.db)
- Platform: Cross-platform (Pi, macOS, Windows, Docker)

KEY FEATURES:
- Network bridge relay with ACK tracking
- PIN-protected mesh mail system
- Offline knowledge (Wikipedia, web crawl cache)
- 20+ multiplayer games
- Interactive onboarding
- Auto-update system
- Desktop shortcuts (cross-platform)
- Telegram bot integration
- Real-time dashboard with metrics

QUICK REFERENCE:
- Dashboard: http://localhost:5001/dashboard
- Logs: tail -f mesh-master.log
- Service: sudo systemctl status mesh-ai
- Git repo: https://github.com/Snail3D/Mesh-Master

Now, please confirm you've read SECURITY_INSTRUCTIONS.md and CLAUDE.md before we begin.
```

</details>

### Development Workflow

**Initial setup:**
```bash
git clone https://github.com/Snail3D/Mesh-Master.git
cd Mesh-Master
./setup.sh  # Creates config.json from template
nano config.json  # CHANGE admin_password and add your credentials
```

**Before committing:**
```bash
git status  # Check for sensitive files
git diff    # Review all changes
# Verify no config.json, data/, or *.log files staged
```

**Security audit commands** (from SECURITY_INSTRUCTIONS.md):
```bash
# Check for exposed credentials in staged files
git diff --cached | grep -i "password\|token\|key\|secret"

# Check for data files about to be committed
git status | grep -E "(config\.json|data/|\.log|\.db|\.pem|\.key)"

# List all gitignored files (should include data/, *.log, etc.)
git status --ignored
```

---

### Relay System (Network Bridge)

The relay system enables cross-network message delivery using shortnames.

#### How It Works

**Basic Usage:**
```
snmo hello there
/snmo hello there
```
Both send "hello there" to the node with shortname "snmo"

**Architecture:**
- **Shortname Cache** — Thread-safe lookup table (shortname → node_id)
- **Queue-Based Processing** — 3 worker threads, 100-item queue capacity
- **Multi-Chunk Support** — Long messages automatically split (160 chars/chunk)
- **ACK Tracking** — 20-second timeout per chunk, real-time confirmation
- **Cross-Network Bridge** — If Mesh Master sees networks A & B, users on A can relay to users on B

**ACK Confirmation:**
```
✅ ACK by NodeName — Message delivered successfully
❌ No ACK from NodeName — Delivery failed (node offline or out of range)
```

**Offline Message Queue:**
When a relay fails (recipient offline), messages are automatically queued:
- **Storage:** Up to 10 messages per user
- **Expiry:** 24 hours from queue time
- **Retry:** 3 delivery attempts when recipient comes online (listens for heartbeats)
- **Notification:** Recipient gets all queued messages when they reconnect

**Privacy Controls:**
```
/optout  — Disable receiving relays (others can't relay to the user)
/optin   — Re-enable receiving relays
```
Preferences persist in `data/relay_optout.json` across reboots.

**Use Cases:**
- Send messages to specific nodes across different channels
- Bridge isolated mesh networks (e.g., hikers on trail + base camp)
- Coordinate team communications without channel flooding
- Store-and-forward for intermittent nodes

**Technical Details:**
- Relay requests processed asynchronously (non-blocking)
- Concurrent relay handling with thread-safe state management
- Per-chunk ACK tracking for reliable multi-chunk delivery
- Automatic shortname cache updates from node database
- Graceful degradation when recipient node is unreachable

---

### Mesh Mail System

Mesh Mail is an async messaging system (like email) built for mesh networks.

#### Core Features

**PIN-Protected Mailboxes:**
- Create mailboxes with optional 4+ digit PINs
- Owner-only mailbox management
- Encrypted content storage
- Brute-force attack protection

**Multi-User Collaboration:**
- Subscribers automatically notified of new mail
- Unread message counts tracked per user
- Quiet hours support (configurable)
- Reminder notifications (hourly, configurable frequency)

**Search Functionality:**
- `/c mailbox search_term` — Search mailbox for specific keywords
- Keyword matching across message content and sender names
- Shows up to 5 most recent matches
- Searches recent messages (configurable `mail_search_max_messages`)

#### Commands

**Sending Mail:**
```bash
/m mailbox message          # Send to mailbox
/mail recipient message     # Direct mail command
```

**Reading Mail:**
```bash
/c                          # Check all subscribed mailboxes
                            # Response: "You have 3 messages in 'ops' mailbox. (1 unread)"

/c supplies                 # Check specific mailbox
                            # Response: "You have 5 messages in 'supplies' mailbox. (3 unread)"

/c ops briefing             # Search for "briefing" in ops mailbox
                            # Shows up to 5 matching messages
```

**Management:**
```bash
/emailhelp                  # Show mail system help
/wipe mailbox name          # Delete a mailbox (owner only)
/wipe chathistory           # Clear AI chat history
/wipe personality           # Reset AI personality
/wipe all mailbox           # Wipe mailbox and all data
```

#### Mailbox Creation Flow

1. User sends `/m newbox first message`
2. System detects new mailbox, prompts for owner confirmation
3. User confirms, optionally sets PIN
4. Mailbox created with encryption
5. Subscribers auto-added (sender = first subscriber)

#### Notification System

**Heartbeat-Driven:**
- Checks for unread mail every ~30 seconds (heartbeat interval)
- Sends notifications to subscribers with unread counts
- Respects quiet hours and reminder frequency settings

**Configuration:**
```json
{
  "mail_notify_enabled": true,
  "mail_notify_reminders_enabled": true,
  "mail_notify_reminder_hours": 1.0,
  "mail_notify_max_reminders": 3,
  "mail_notify_quiet_hours_enabled": true,
  "mail_quiet_start_hour": 20,
  "mail_quiet_end_hour": 8,
  "mail_notify_include_self": false,
  "mail_notify_heartbeat_only": true
}
```

**Reminder Logic:**
- First notification: Immediate when mail arrives
- Reminders: Every N hours (default: 1 hour) up to max reminders (default: 3)
- Quiet hours: No notifications between 20:00-08:00 (configurable)
- Include self: Whether sender gets their own mail notifications

#### Security Features

**PIN Protection:**
- PINs hashed with bcrypt (never stored plain text)
- Exponential backoff on failed attempts: 1s → 2s → 4s → 8s...
- Max attempts tracked per user
- Lockout after too many failed attempts

**Encryption:**
- Auto-generated encryption keys per mailbox
- Content encrypted at rest
- Keys stored in `data/mail_security.json` (gitignored)

**Access Control:**
- Owner verification for destructive operations
- Subscriber management (owner can add/remove)
- PIN required for viewing protected mailboxes

#### Storage

**Database:** `mesh_mail.db` (SQLite)
- Messages table with timestamps, sender, content
- Efficient querying for recent messages
- Automatic cleanup of old messages (configurable)

**Security File:** `data/mail_security.json`
```json
{
  "mailbox_name": {
    "owner": "node_id",
    "pin_hash": "bcrypt_hash",
    "encryption_key": "base64_key",
    "subscribers": {
      "node_id": {
        "last_read_ts": 1234567890,
        "unread_count": 3,
        "last_notification_ts": 1234567800,
        "notification_count": 1
      }
    }
  }
}
```

#### Use Cases

**Team Coordination:**
```
/m ops Mission briefing at 0600 tomorrow
/m ops Updated weather forecast: rain expected
/c ops briefing
  → Shows messages containing "briefing" in ops mailbox
```

**Information Sharing:**
```
/m intel Saw 3 hikers at waypoint B, heading north
/m supplies Need more batteries, low on channel 2
/c supplies batteries
  → Shows messages containing "batteries" in supplies mailbox
```

**Long-Form Messages:**
```
/m journal Today we reached the summit after 6 hours...
/m notes Remember to check radio settings before departure
/c notes
  → Shows all messages in notes mailbox
```

**Collaborative Planning:**
```
/m planning Route A blocked, suggest Route B via creek
/c planning route
  → Shows messages containing "route" in planning mailbox
```

#### Search Example

```
User: /c ops
Bot: You have 5 messages in 'ops' mailbox. (3 unread)

User: /c ops briefing
Bot: 🔍 Matches in 'ops' (newest first)
     1) 2025-10-09 14:30 Alice: Mission briefing at 0600 tomorrow
     2) 2025-10-08 09:15 Bob: Updated briefing materials attached

User: /c ops weather
Bot: 🔍 Matches in 'ops' (newest first)
     1) 2025-10-09 15:00 Alice: Updated weather forecast: rain expected
```

The search performs keyword matching across message content and sender names (configurable `mail_search_max_messages`).

---

### Integrations & Extensibility
- Native Ollama support tuned for low-bandwidth meshes (`llama3.2:1b` by default) with adjustable context size, chunk delays, and timeout controls.
- Home Assistant relay can forward a dedicated channel (with optional PIN requirement) to the Conversation API.
- Feature flags (`feature_flags.json`) let operators disable specific commands or restrict replies to DMs/broadcasts.

---

## Installation

> **⚡ One-Command Install** — See the [Quick Install](#-quick-install-one-command) at the top of this page for the easiest installation method.

The one-command installer automatically:
- Downloads Mesh Master if not already installed
- Removes old service installations
- Installs system service with auto-start and auto-restart
- Creates desktop shortcuts (Start/Stop icons)
- Starts the service immediately

**Next steps after installation:**
1. Dashboard opens automatically at `http://localhost:5001/dashboard`
2. Configure your radio connection (serial or WiFi)
3. Set your admin password
4. Start meshing!

**Manual Installation:**
If you prefer manual setup or need advanced customization, see [INSTALL.md](INSTALL.md) for detailed platform-specific instructions.

---

## Everyday Commands

- **Getting started** — `/onboard`, `/onboarding`, or `/onboardme` for an interactive tour (DM only).
- **AI conversations** — `/ai`, `/bot`, `/query`, or `/data` (DM or configured channels).
- **Network & Relay** — `<shortname> <message>` to relay messages across networks. `/nodes` lists all reachable nodes, `/node <shortname>` shows signal details, `/networks` lists connected channels. `/optout` to disable receiving relays, `/optin` to re-enable.
- **Mesh mail** — `/m <mailbox> <message>` or `/mail <recipient> <message>`, `/c [mailbox]` or `/checkmail`, `/emailhelp`, `/wipe ...`.
- **Quick knowledge** — `/bible [topic]`, `/chucknorris`, `/elpaso`, `/meshtastic`, `/offline wiki`, `/web <query>`, `/wiki <topic>`, `/find <query>`, `/drudge`, `/weather`.
- **Field notes** — `/log <title>` for private notes (visible only to the author), `/checklog [title]` or `/readlog [title]` to view logs; `/report <title>` for public reports (searchable by all), `/checkreport [title]` or `/readreport [title]` to view reports. Both are DM-only. Use `/find <query>` to search with fuzzy matching.
- **Personality & context** — `/aipersonality [persona]` (list/set/prompt/reset), `/vibe [tone]`, `/save [name]`, `/recall [name]`, `/reset`, `/chathistory`.
- **Games** — `/games`, `/hangman start`, `/wordle start`, `/wordladder start cold warm`, `/adventure start`, `/cipher start`, `/quizbattle start`, `/morse start`, `/rps`, `/coinflip`, `/yahtzee`, `/blackjack`.
- **Location & status** — `/test`, `/motd`, `/menu`, Meshtastic "Request Position".
- **Version & updates** — `/about` shows current version, credits, links, and checks for updates available on GitHub.
- **Admin (DM-only)** — `/admin` (console), `/status`, `/whatsoff`, `/allcommands`, `/ai on/off`, `/channels+dm on`, `/channels on`, `/dm on`, `/autoping on/off`, `/<command> on/off`, `/changemotd`, `/changeprompt`, `/showprompt`, `/showmodel`, `/selectmodel`, `/hops <0-7>`, `/stop`, `/reboot`, `/update` (pulls latest from GitHub and restarts). See [COMMANDS.md](COMMANDS.md) for whitelist configuration.

**Note:** `/about` and `/donate` are always enabled and cannot be disabled by admins.

All commands are case-insensitive. Special commands buffer ~3 seconds before responding to reduce radio congestion.

---

## Dashboard & Monitoring

Access the dashboard at `http://localhost:5001/dashboard` or `http://<your-ip>:5001/dashboard` (mobile-accessible on same network) for:

- **Real-time Activity Feed** — Icon-based log stream with emoji categorization (📨 incoming, 📖 Bible, 🎮 Game, 🤖 AI, 🔐 Admin, etc.). Toggle between summary and verbose modes. **NEW:** Optimized 20-line view for mobile devices with auto-scroll detection.
- **Radio Configuration** — Set node names (long/short), device role (CLIENT, ROUTER, REPEATER), modem preset (spreading factor), and frequency slot—all dynamically pulled from current Meshtastic firmware.
- **Ollama Model Management** — View installed models, switch active model, download new models with progress tracking.
- **Onboarding Customization** — Enable/disable auto-onboarding for new users and customize the welcome message.
- **Operations Center** — Browse all available commands organized by category (Admin, AI Settings, Email, Games, Fun, Web & Search, etc.). Categories default to collapsed for a cleaner view.
- **GitHub Version Control & Updates** — View current branch and available versions, switch branches directly from the dashboard. **Check for updates** and apply them with automatic restart (systemd service on Linux). **Note:** On macOS or non-systemd systems, the update will pull code but you'll need to manually restart the Python process.
- **Configuration Editor** — Edit settings by category (Serial Connection, AI, Messaging, etc.) with inline help tooltips.

---

## Onboarding System

New users receive an interactive 9-step guided tour when they send `/onboard`, `/onboarding`, or `/onboardme` via DM:

1. **Welcome** — Introduction to MESH-MASTER capabilities
2. **Main Menu** — How to access `/menu` for all features
3. **Mesh Mail** — Sending and receiving messages with `/mail` and `/checkmail`
4. **Logs & Reports** — Private logs (visible only to the author) vs. public reports (searchable by all)
5. **Games** — Overview of available games and the `/games` command
6. **AI Assistance** — How to ask questions and interact with the AI
7. **Helpful Tools** — Weather, alarms, timers, Bible verses, web search, Wikipedia
8. **Getting Help** — Where to find help with `/help` and `/menu`
9. **Ready to Go** — Summary and encouragement to start using the system

**Customization:**
- Dashboard → Onboarding panel allows you to enable/disable auto-onboarding for first-time users
- Customize the welcome message that greets new users
- Onboarding state persists across restarts in `data/onboarding_state.json`

---

## Documentation & Support

- Mesh Mail internals: `docs/mail_readme.md`  
- Command map: `docs/mesh_master_command_tree.pdf`  
- Service management: `README_SERVICE.md`  
- Security practices: `SECURITY.md`

Issue reports and contributions are welcome via GitHub pull requests.

---

## Support This Project ☕

If you find Mesh Master useful, consider supporting its development!

**💙 Buy Me a Coffee:** [buymeacoffee.com/Snail3D](https://buymeacoffee.com/Snail3D)

**⭐ Star on GitHub:** [github.com/Snail3D/Mesh-Master](https://github.com/Snail3D/Mesh-Master)

Your contributions help fund:
- Feature development & bug fixes
- Documentation & tutorials
- Server costs for testing
- Hardware for mesh field testing

You can also use the `/donate` command in Mesh Master to see this info over the mesh!

---

## Acknowledgements

- Original Mesh Master project by [MR_TBOT](https://github.com/mr-tbot/mesh-master); this fork builds on that foundation with a focus on fully offline resilience.
- Thanks to the Meshtastic community researchers, testers, and field operators who supplied feedback, hardware profiles, and localization tweaks.

---

## License

MESH MASTER is distributed under the terms of the [MIT License](LICENSE).

The Meshtastic name and logo remain trademarks of Meshtastic LLC.
