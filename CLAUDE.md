# CLAUDE.md - Mesh Master Project Context

> **Project Context Document for AI Assistants**
> This document provides essential context for Claude and other AI assistants working on the Mesh Master project.

---

## Project Overview

**MESH MASTER v2.5** is an off-grid AI operations suite for Meshtastic LoRa mesh networks. It functions as a resilient AI copilot that remembers conversations, coordinates teams, and maintains network operations even when internet connectivity is unavailable.

**Repository:** https://github.com/Snail3D/Mesh-Master
**Fork of:** Original Mesh Master by MR_TBOT
**License:** MIT
**Primary Language:** Python 3.11+

---

## Architecture Overview

### Core Components

1. **Main Application** ([mesh-master.py](mesh-master.py)) - ~28,000 lines
   - Entry point and orchestration
   - Flask web server (port 5000)
   - Meshtastic interface management (serial/WiFi)
   - Message routing and processing
   - Command parsing and dispatch
   - Async response queue management

2. **Mesh Master Package** ([mesh_master/](mesh_master/))
   - `mail_manager.py` - PIN-protected mailbox system with notifications
   - `relay_manager.py` - Network bridge relay with ACK tracking and offline queue
   - `onboarding_manager.py` - Interactive 9-step user onboarding
   - `system_context.py` - Context-aware AI help system (~50k token context)
   - `user_entries.py` - Private logs and public reports with fuzzy search
   - `alarm_timer_manager.py` - Scheduling and reminder system
   - `offline_wiki.py` - Local Wikipedia mirror with caching
   - `offline_crawl.py` - Web content archival
   - `offline_ddg.py` - DuckDuckGo search caching
   - `help_database.py` - Command documentation database
   - `games/game_manager.py` - 20+ multiplayer games (~126k lines)

3. **Data Storage** ([data/](data/))
   - `logs/` - Private user logs (DM-only access)
   - `reports/` - Public searchable reports
   - `offline_wiki/` - Cached Wikipedia articles with index
   - `offline_crawl/` - Archived web pages
   - `offline_ddg/` - Saved search results
   - `bible_progress.json` - Bible reading tracker
   - `relay_optout.json` - User relay privacy preferences
   - `onboarding_state.json` - User onboarding progress
   - `user_ai_settings.json` - Per-user AI personality settings

4. **Static Assets** ([static/](static/))
   - Dashboard HTML/CSS/JS
   - Twemoji library for emoji rendering
   - Real-time log streaming interface

5. **Configuration Files**
   - `config.json` - Main configuration (connection, AI, channels)
   - `commands_config.json` - Command behavior and feature flags
   - `motd.json` - Message of the day
   - `feature_flags.json` - Feature toggles

---

## Key Features & Subsystems

### 1. Network Bridge Relay System
**Files:** `mesh_master/relay_manager.py`, relay logic in main file

**Purpose:** Forward messages across mesh networks by shortname

**How it works:**
- Command: `<shortname> <message>` or `/<shortname> <message>`
- Real-time ACK tracking (20-second timeout)
- Multi-chunk support for long messages
- Queue-based architecture (3 workers, 100-item queue)
- **Offline queue:** Failed relays stored and auto-delivered when recipient comes online
  - Max 10 messages per user
  - 24-hour expiry
  - 3 delivery attempts
- **Privacy controls:** `/optout` and `/optin` commands

**Cross-network bridging:**
If Mesh Master sees multiple networks (e.g., SnailNet + LongFast), it bridges them seamlessly.

### 2. Context-Aware AI Help System
**Files:** `mesh_master/system_context.py`

**Purpose:** Provide AI responses with full system awareness

**How it works:**
- `/system <question>` - Get help with ~50k token context
- Auto-activates after `/help` or `/menu`
- Context includes: all commands, architecture, settings, network state
- Single-use mode vs persistent mode (during onboarding)
- Frustration detection suggests `/reset` when user seems stuck

### 3. Interactive Onboarding
**Files:** `mesh_master/onboarding_manager.py`

**9-step guided tour:**
1. Welcome & capabilities
2. Main menu navigation
3. Mesh mail system
4. Logs (private) vs Reports (public)
5. Games overview
6. AI assistance
7. Helpful tools (weather, Bible, wiki, search)
8. Getting help
9. Ready to go

**Features:**
- DM-only commands: `/onboard`, `/onboarding`, `/onboardme`
- Customizable welcome message via dashboard
- State persistence across restarts
- Context-aware help available at any step

### 4. Mesh Mail System
**Files:** `mesh_master/mail_manager.py`, `mesh_mail.db` (SQLite)

**Purpose:** PIN-protected mailboxes for async messaging

**Commands:**
- `/m <mailbox> <message>` or `/mail <recipient> <message>` - Send mail
- `/c [mailbox]` or `/checkmail` - Check mail
- `/emailhelp` - Mail system help
- `/wipe mailbox`, `/wipe chathistory`, `/wipe personality`, `/wipe all <mailbox>`

**Features:**
- PIN protection with brute-force throttling
- Multi-user notifications
- Llama-powered summaries (`llama3.2:1b`)
- Owner metadata tracking
- Heartbeat-driven notification engine

### 5. Private Logs & Public Reports
**Files:** `mesh_master/user_entries.py`, `data/logs/`, `data/reports/`

**Logs (Private):**
- `/log <title>` - Create private entry
- `/checklog [title]`, `/readlog [title]`, `/checklogs [title]` - View your logs
- **Only visible to creator** - DM-only commands
- Stored in `data/logs/<user_shortname>_<title>.json`

**Reports (Public):**
- `/report <title>` - Create public entry
- `/checkreport [title]`, `/readreport [title]`, `/checkreports [title]` - View reports
- **Searchable by everyone** via `/find`
- Stored in `data/reports/<title>.json`

**Features:**
- Fuzzy matching with "Did you mean?" suggestions
- `/find <query>` searches logs (your own) + reports (all) + wiki + crawl data
- Configurable max entries: `logs_max_entries`, `reports_max_entries`

### 6. Game Hub
**Files:** `mesh_master/games/game_manager.py` (~126k lines)

**20+ games including:**
- Chess & Checkers (multiplayer duels)
- Blackjack, Yahtzee, Tic-Tac-Toe, Bingo
- Hangman, Wordle, Word Ladder
- Adventure stories (branching narratives)
- Cipher drills, Morse code practice
- Rock-Paper-Scissors, Coinflip
- Quiz Battle
- **Mesh Master Quiz** (`/masterquiz`) - 50 questions about Mesh Master
- **Meshtastic Quiz** (`/meshtasticquiz`) - 50 questions about Meshtastic

**All games:**
- DM-friendly
- Multilingual support
- State persistence

### 7. Offline Knowledge
**Files:** `mesh_master/offline_wiki.py`, `offline_crawl.py`, `offline_ddg.py`

**Commands:**
- `/offline wiki <topic>` - Local Wikipedia lookup
- `/web <query>` - Web search with URL content filtering
- `/wiki <topic>` - Online Wikipedia
- `/meshtastic <question>` - Curated field guide (~25k tokens)
- `/find <query>` - Search across all offline data

**Features:**
- Cached articles with TTL (10-minute default)
- Background prefetching
- Daily download cap (1000 articles)
- URL content filter blocks adult/warez sites
- Auto-save from online wiki lookups

### 8. AI Personality System
**Files:** `data/user_ai_settings.json`

**Commands:**
- `/aipersonality [persona]` - List/set/prompt/reset
- `/vibe [tone]` - Adjust conversation tone
- `/save [name]` - Capture conversation context
- `/recall [name]` - Restore saved context
- `/reset` - Clear conversation memory
- `/chathistory` - View conversation log

**Per-user settings:**
- Active personality ID
- Custom prompt additions
- Saved context capsules
- Message history

---

## Configuration

### Main Config ([config.json](config.json))

**Connection:**
- `serial_port` - USB serial path (e.g., `/dev/serial/by-id/usb-RAKwireless_...`)
- `serial_baud` - Baud rate (38400)
- `use_wifi` - WiFi mode toggle
- `wifi_host`, `wifi_port` - Network connection

**AI Provider:**
- `ai_provider` - "ollama" (default)
- `ollama_url` - Local Ollama endpoint
- `ollama_model` - Model name (e.g., "wizard-math:7b", "llama3.2:1b")
- `ollama_timeout` - Generation timeout (120s)
- `ollama_context_chars` - Context window (1600)
- `ollama_num_ctx` - Ollama num_ctx parameter (1024)
- `system_prompt` - Core system prompt

**Mesh Settings:**
- `channel_names` - Channel name mapping (0-9)
- `chunk_size` - Max message chunk size (160)
- `chunk_buffer_seconds` - Delay between chunks (5)
- `max_ai_chunks` - Max AI response chunks (2)
- `reply_in_channels` - Allow channel replies
- `reply_in_directs` - Allow DM replies

**Mail System:**
- `mail_notify_enabled` - Enable notifications
- `mail_notify_reminder_hours` - Reminder frequency (1.0)
- `mail_notify_max_reminders` - Max reminders (3)
- `mail_notify_quiet_hours_enabled` - Quiet hours toggle
- `mail_quiet_start_hour`, `mail_quiet_end_hour` - Quiet hours (20:00-08:00)
- `mail_search_timeout` - Llama search timeout (120s)

**Offline Knowledge:**
- `offline_wiki_enabled` - Enable offline wiki
- `offline_wiki_dir` - Storage directory
- `offline_wiki_max_articles` - Storage limit (500)
- `offline_wiki_daily_cap` - Download limit (1000/day)
- `offline_wiki_context_chars` - Context size (40000)
- `offline_wiki_autosave_from_wiki` - Auto-save from `/wiki` commands

**Logs & Reports:**
- `logs_dir` - Private logs directory (data/logs)
- `reports_dir` - Public reports directory (data/reports)
- `logs_max_entries` - Max log entries per user
- `reports_max_entries` - Max report entries

### Feature Flags ([feature_flags.json](feature_flags.json))
- Command enable/disable toggles
- Message mode: `broadcast`, `dm`, or `both`

---

## Message Flow

### Inbound Messages
1. **Meshtastic RX** → `on_meshtastic_message()`
2. **Parse** → Extract sender, content, channel, is_dm
3. **Filter** → Antispam, cooldown, self-message detection
4. **Command Detection** → Check for `/` prefix or shortname relay
5. **Dispatch** → Route to appropriate handler
6. **Response** → Queue async response or immediate reply

### Outbound Messages
1. **Message Queue** → `async_response_queue` (25-item limit)
2. **Worker Threads** → Process queue items
3. **Chunking** → Split long messages (160 char chunks, 5s delay)
4. **ACK Tracking** → Wait for acknowledgment (relay system)
5. **Retry Logic** → Offline queue for failed relays

### Relay Flow
1. **Parse** → `<shortname> <message>`
2. **Lookup** → Find node by shortname in network
3. **Privacy Check** → Verify recipient not opted out
4. **Send** → Forward message with ACK tracking
5. **Confirm** → "✅ ACK by NodeName" or "❌ No ACK"
6. **Offline Queue** → Store if failed, retry when online

---

## Web Dashboard

**URL:** `http://localhost:5000/dashboard` (or `http://<ip>:5000/dashboard`)

**Panels:**
1. **Activity Feed** - Real-time log stream with emoji categories
   - 📨 Incoming messages
   - 🤖 AI responses
   - 📖 Bible lookups
   - 🎮 Game activity
   - 🔐 Admin actions
   - ⚠️ Warnings
   - Mobile-optimized (20-line view)

2. **Radio Configuration**
   - Node names (long/short)
   - Device role (CLIENT, ROUTER, REPEATER)
   - Modem preset (spreading factor)
   - Frequency slot
   - Dynamically pulled from firmware

3. **Ollama Model Management**
   - View installed models
   - Switch active model
   - Download new models with progress

4. **Onboarding Customization**
   - Enable/disable auto-onboarding
   - Customize welcome message

5. **Operations Center**
   - All commands by category
   - Collapsible sections
   - Command descriptions

6. **GitHub Version Control**
   - Current branch/version
   - Switch branches
   - Update from remote

7. **Configuration Editor**
   - Edit settings by category
   - Inline help tooltips

**Health Endpoints:**
- `GET /ready` - Radio link status (200 = up, 503 = down)
- `GET /live` - Process liveness
- `GET /healthz` - Full JSON health snapshot
- `GET /heartbeat` - Last heartbeat timestamp
- `POST /send` - Automated message sending
- `POST /ui_send` - UI message form

---

## Development Workflow

### Running Locally
```bash
cd /home/snailpi/Programs/mesh-ai
source .venv/bin/activate
NO_BROWSER=1 python mesh-master.py
```

### Key Files to Edit
- **Add commands:** Search for command handlers in `mesh-master.py` (search for `def handle_`)
- **Modify AI behavior:** Edit `system_prompt` in `config.json`
- **Add games:** Edit `mesh_master/games/game_manager.py`
- **Tweak relay:** Edit `mesh_master/relay_manager.py`
- **Update dashboard:** Edit templates in `static/`

### Testing
```bash
pytest tests/
```

### Systemd Service
Service file: `/etc/systemd/system/mesh-ai.service`

```bash
sudo systemctl status mesh-ai
sudo systemctl restart mesh-ai
sudo systemctl stop mesh-ai
sudo journalctl -u mesh-ai -f
```

### Logs
- `mesh-master.log` - Main application log
- `messages.log` - Message history
- `messages_archive.json` - Persistent message archive
- `script.log` - Script execution log
- Dashboard: `http://localhost:5000/logs`

---

## Common Tasks

### Add a New Command
1. Search for command patterns in `mesh-master.py`
2. Add command string to detection logic
3. Create handler function: `def handle_mycommand(...)`
4. Add to `/menu` output
5. Update `help_database.py` with documentation

### Change AI Model
```bash
# Via dashboard
http://localhost:5000/dashboard → Ollama Model Management

# Via config.json
"ollama_model": "llama3.2:1b"  # or wizard-math:7b, etc.

# Restart service
sudo systemctl restart mesh-ai
```

### Add Offline Wiki Articles
```bash
# Auto-download via /wiki command
/wiki <topic>  # (with offline_wiki_autosave_from_wiki: true)

# Manual download
python -c "from mesh_master.offline_wiki import OfflineWiki; ow = OfflineWiki(...); ow.save_article('Topic Name', 'content...')"
```

### Clear User Data
```bash
# Via DM commands
/wipe chathistory
/wipe personality
/wipe mailbox <name>
/wipe all <mailbox>

# Manual cleanup
rm data/logs/<user>_*.json
rm data/reports/*.json
rm data/user_ai_settings.json
```

---

## Security & Privacy

### Message Content Redaction
All debug/info logs redact message content (show `[X chars]` instead of full text).

### PIN Protection
- Mesh Mail: Optional PIN for mailboxes
- Brute-force throttling (exponential backoff)
- Stored in `data/mail_security.json`

### URL Content Filter
- Blocks adult and warez sites from `/web` crawling and search results
- Humorous error message for blocked sites

### Relay Privacy
- `/optout` - Disable receiving relays
- `/optin` - Re-enable relays
- Preferences persist in `data/relay_optout.json`

### Git Ignore
All sensitive data gitignored:
- `data/` (logs, reports, settings)
- `*.log`
- `*.db`
- `config.json` (if contains secrets)

---

## Troubleshooting

### No Response from AI
1. Check Ollama is running: `curl http://localhost:11434/api/generate`
2. Check model loaded: `ollama list`
3. Check timeout: Increase `ollama_timeout` in config
4. Check logs: `grep -i ollama mesh-master.log`

### Serial Connection Issues
1. Check device path: `ls -la /dev/serial/by-id/`
2. Check permissions: `sudo usermod -a -G dialout $USER`
3. Check baud rate: `serial_baud` should match device (38400)
4. Apply RAK4631 profile: `./scripts/apply_rak4631_profile.py`

### Relay Not Working
1. Check shortname: `/nodes` to see all reachable nodes
2. Check privacy: Verify recipient hasn't `/optout`
3. Check ACK timeout: Default 20s, may need adjustment for long-range
4. Check logs: Search for "relay" in `mesh-master.log`

### Dashboard Not Loading
1. Check Flask port: `netstat -tulpn | grep 5000`
2. Check firewall: `sudo ufw allow 5000`
3. Check logs: `tail -f mesh-master.log | grep -i flask`
4. Try raw logs: `http://localhost:5000/logs/raw`

### High Memory Usage
1. Check message archive size: `ls -lh messages_archive.json`
2. Enable rotation: `message_archive_rotation_enabled: true`
3. Reduce archive days: `message_archive_max_days: 30`
4. Reduce async queue: `async_response_queue_max: 10`

---

## Architecture Decisions

### Why Async Response Queue?
- **Problem:** Ollama generation blocks message receive loop
- **Solution:** Queue responses, process in background threads
- **Benefit:** RX remains responsive, AI replies don't block network

### Why Offline Knowledge?
- **Problem:** Internet unavailable in off-grid scenarios
- **Solution:** Cache Wikipedia, web crawls, search results locally
- **Benefit:** Knowledge available without connectivity

### Why Network Bridge Relay?
- **Problem:** Meshtastic nodes only see their direct mesh
- **Solution:** Mesh Master bridges multiple networks it can see
- **Benefit:** Cross-network communication without manual routing

### Why Private Logs vs Public Reports?
- **Problem:** Users need both personal notes and team visibility
- **Solution:** `/log` for private (DM-only), `/report` for public (searchable)
- **Benefit:** Privacy + collaboration

### Why PIN-Protected Mail?
- **Problem:** Sensitive messages on open mesh network
- **Solution:** Mailboxes with optional PIN protection
- **Benefit:** Async secure messaging without encryption overhead

---

## Performance Considerations

### Message Chunking
- Default: 160 chars/chunk, 5s delay
- Reduces radio congestion
- Allows other nodes to transmit
- Configurable: `chunk_size`, `chunk_buffer_seconds`

### Context Window Limits
- Ollama context: 1600 chars (low-bandwidth optimization)
- System context: ~50k tokens (for `/system` help)
- Meshtastic KB: 3200 chars (trimmed field guide)
- Offline wiki: 40k chars (cached articles)

### Queue Limits
- Async response queue: 25 items (prevents memory overflow)
- Relay queue: 100 items (burst handling)
- Offline queue: 10 messages/user (storage limit)

### Cache TTLs
- Meshtastic KB: 600s (10 minutes)
- Offline wiki: Persistent until eviction
- DuckDuckGo: Persistent until manual clear

---

## Future Development Ideas

- [ ] Multi-language UI (dashboard i18n)
- [ ] Message encryption (E2E for mail)
- [ ] Voice message transcription (Whisper)
- [ ] Image analysis (vision models)
- [ ] Mesh network topology visualization
- [ ] Advanced routing (multi-hop relay optimization)
- [ ] Plugin system (custom commands without core edits)
- [ ] Mobile app (native Android/iOS client)
- [ ] Distributed consensus (multi-master coordination)
- [ ] Emergency broadcast system (priority alerting)

---

## Important Notes for Claude

### When Working on This Project:

1. **Always check if Mesh Master is running** before making changes:
   ```bash
   sudo systemctl status mesh-ai
   ```

2. **Stop the service before editing critical files:**
   ```bash
   sudo systemctl stop mesh-ai
   # Make edits
   sudo systemctl start mesh-ai
   ```

3. **Test changes locally first:**
   ```bash
   cd /home/snailpi/Programs/mesh-ai
   source .venv/bin/activate
   NO_BROWSER=1 python mesh-master.py
   ```

4. **Check logs after changes:**
   ```bash
   sudo journalctl -u mesh-ai -f
   tail -f /home/snailpi/Programs/mesh-ai/mesh-master.log
   ```

5. **Backup config before major changes:**
   ```bash
   cp config.json config.json.backup
   ```

6. **Use git for version control:**
   ```bash
   git status
   git diff
   git add .
   git commit -m "Description of changes"
   ```

7. **Key locations:**
   - Project root: `/home/snailpi/Programs/mesh-ai/`
   - Main script: `mesh-master.py`
   - Config: `config.json`
   - Data: `data/`
   - Logs: `mesh-master.log`, `messages.log`
   - Service: `/etc/systemd/system/mesh-ai.service`

8. **Remember:**
   - This is a production system running 24/7
   - Changes affect real users on the mesh network
   - Test thoroughly before deploying
   - Always have rollback plan

---

## Quick Reference

### Most Common Commands
- `/menu` - Main menu
- `/help` - Help system
- `/ai <question>` - Ask AI
- `/system <question>` - System-aware AI help
- `<shortname> <message>` - Relay message
- `/nodes` - List all nodes
- `/mail <user> <msg>` - Send mail
- `/checkmail` - Check mail
- `/log <title>` - Private log entry
- `/report <title>` - Public report entry
- `/find <query>` - Search everything
- `/games` - List games
- `/onboard` - Start onboarding

### Most Edited Files
- `mesh-master.py` - Main logic
- `config.json` - Settings
- `mesh_master/relay_manager.py` - Relay system
- `mesh_master/system_context.py` - Help system
- `mesh_master/mail_manager.py` - Mail system
- `mesh_master/games/game_manager.py` - Games

### Most Important Logs
- `mesh-master.log` - Everything
- `messages.log` - Message history
- `sudo journalctl -u mesh-ai` - Systemd service logs

---

**Last Updated:** 2025-10-10
**Version:** 2.5
**Maintainer:** snailpi (Snail3D fork)
