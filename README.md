# MESH MASTER v2.5 — Off-Grid AI Operations Suite

**MESH MASTER 2.5** is the next evolution of the Mesh-AI project: a resilient AI copilot for Meshtastic LoRa meshes that remembers conversations, coordinates teams, and keeps the network moving even when the wider internet is gone. Version 2.5 introduces context-aware AI help, offline relay queuing, enhanced privacy controls, URL content filtering, and fuzzy search—all while maintaining the Mesh Mail hub, network bridge relay system, llama-powered games for morale and training, rich offline knowledge, and a comprehensive web command center.

> **Disclaimer**  
> This project is an independent community effort and is **not associated** with the official Meshtastic project. Always maintain backup communication paths for real emergencies.

![Mesh Master 2.0 hero](docs/mesh-master-2.0-hero.svg)

---

## 2.5 Headline Upgrades
- **Network Bridge Relay with ACK Tracking** — Forward messages to any node by shortname: `snmo hello there` or `/snmo hello there`. Real-time ACK confirmation shows which node acknowledged. Multi-chunk support for long messages. Acts as a bridge across multiple mesh networks—if this node sees networks A and B, users on network A can relay to users on network B seamlessly. **NEW:** Offline message queue stores failed relays and automatically delivers when recipient comes online (up to 3 attempts, 24-hour expiry).
- **Relay Privacy Controls** — `/optout` disables receiving relays (others can't relay to you), `/optin` re-enables. Privacy preferences persist across reboots and updates in `data/relay_optout.json`.
- **Cross-Network Node Discovery** — `/nodes` lists all nodes seen in the last 24 hours across all channels/networks (sorted newest first). `/node <shortname>` shows detailed signal info (SNR, signal strength, last heard, hops, battery level, power status) with modem-aware thresholds. `/networks` lists all connected channels.
- **Context-Aware AI Help** — `/system <question>` provides AI responses with full system awareness (~50k token context including all commands, architecture, your settings, network state). Auto-activates during onboarding and after `/help` or `/menu` for seamless learning.
- **Interactive Onboarding** — New users receive a guided 9-step tour via `/onboard` (or `/onboarding`, `/onboardme`) covering the main menu, mesh mail, logs & reports, games, AI assistance, and helpful tools. Fully customizable welcome messages through the dashboard. Context-aware help available at any step.
- **Private Logs & Public Reports** — `/log` creates private entries visible only to you; `/report` creates public entries searchable by everyone via `/find`. **NEW:** Fuzzy matching with "Did you mean" suggestions for misspelled names. Command aliases: `/readlog`, `/readlogs`, `/checklog`, `/checklogs` (logs) and `/readreport`, `/readreports`, `/checkreport`, `/checkreports` (reports).
- **Enhanced Privacy & Security** — Message content redacted in all debug/info logs (shows `[X chars]` instead of full text). URL filter blocks adult and warez sites from crawling and search results with humorous error message. All sensitive user data gitignored.
- **Enhanced Dashboard** — Real-time activity feed (20-line mobile-optimized view), radio configuration controls (node names, roles, modem presets, frequency slots), Ollama model management, collapsible command categories, and GitHub version selector. Accessible on mobile devices via `http://<your-ip>:5000/dashboard`.
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
MESH MASTER 2.5 can act as a relay bridge between multiple mesh networks, enabling communication across network boundaries.

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

### Context-Aware AI Help System
MESH MASTER 2.5 includes an intelligent help system that provides AI responses with full awareness of your system configuration, available commands, and network state.

**Features:**
- **`/system <question>`** — Ask questions with ~50k token context including all commands, architecture details, your current settings, and network status
- **Auto-activation:** System context automatically activates during onboarding and after `/help` or `/menu` commands
- **Single-use mode:** After help commands, the next AI question gets full system context, then clears to avoid overhead
- **Persistent mode:** During onboarding, context remains active for the entire session (30-minute timeout)
- **Frustration detection:** AI can gently suggest `/reset` to clear conversation memory when you seem stuck

**Example queries:**
- `/system how does the relay work?` — Get detailed explanation of relay system with ACK tracking
- `/system what LLM am I using?` — See your current model and provider configuration
- `/system how do I search my logs?` — Learn about `/checklog`, `/readlog`, and `/find` commands

### Persistent Mesh Intelligence
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

### Integrations & Extensibility
- Native Ollama support tuned for low-bandwidth meshes (`llama3.2:1b` by default) with adjustable context size, chunk delays, and timeout controls.  
- Home Assistant relay can forward a dedicated channel (with optional PIN requirement) to the Conversation API.  
- Feature flags (`feature_flags.json`) let operators disable specific commands or restrict replies to DMs/broadcasts.

---

## Quick Start (Python)

1. **Clone & enter the repository**
   ```bash
   git clone https://github.com/Snail3D/Mesh-Master.git
   cd Mesh-Master
   ```
2. **Create a virtual environment and install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Configure your node**
   - Edit `config.json` and update connection details (`serial_port` or `wifi_host`), `ai_provider` settings, and channel preferences.  
   - Adjust `commands_config.json`, `motd.json`, and any feature flags as desired.
4. **Launch Mesh Master**
   ```bash
   NO_BROWSER=1 python mesh-master.py
   ```
5. **Open the dashboard**
   - Visit `http://localhost:5000/dashboard` for live logs and controls.

---

## Container Workflow

Build the 2.5 image locally so you run the exact code in this repository:

```bash
docker build -t mesh-master:2.5 .
```

Minimal compose example:

```yaml
services:
  mesh-master:
    image: mesh-master:2.5
    container_name: mesh-master
    privileged: true
    ports:
      - "5000:5000"
    volumes:
      - ./config.json:/app/config.json:ro
      - ./commands_config.json:/app/commands_config.json:ro
      - ./motd.json:/app/motd.json:ro
      - ./data:/app/data
      - ./state/mesh-master.log:/app/mesh-master.log
      - ./state/messages.log:/app/messages.log
      - ./state/messages_archive.json:/app/messages_archive.json
      - ./state/script.log:/app/script.log
      - ./state/mesh_mailboxes.json:/app/mesh_mailboxes.json
      - ./state/mesh_mail.db:/app/mesh_mail.db
    restart: unless-stopped
```

If you rely on USB serial, also bind `/dev/serial/by-id` (read-only) and `/dev` as needed, and set `MESH_INTERFACE`/`serial_port` accordingly.

Create the `state` directory (and `touch` the files listed above) before the first run so Docker can mount them successfully.

---

## Everyday Commands

- **Getting started** — `/onboard`, `/onboarding`, or `/onboardme` for an interactive tour with context-aware help (DM only).
- **AI conversations** — `/ai`, `/bot`, `/query`, or `/data` (DM or configured channels). `/system <question>` for context-aware help with full system knowledge.
- **Network & Relay** — `<shortname> <message>` to relay messages across networks. `/nodes` lists all reachable nodes, `/node <shortname>` shows signal details, `/networks` lists connected channels. `/optout` to disable receiving relays, `/optin` to re-enable.
- **Mesh mail** — `/m <mailbox> <message>` or `/mail <recipient> <message>`, `/c [mailbox]` or `/checkmail`, `/emailhelp`, `/wipe ...`.
- **Quick knowledge** — `/bible [topic]`, `/chucknorris`, `/elpaso`, `/meshtastic`, `/offline wiki`, `/web <query>`, `/wiki <topic>`, `/find <query>`, `/drudge`, `/weather`.
- **Field notes** — `/log <title>` for private notes (only you can see), `/checklog [title]` or `/readlog [title]` to view your logs; `/report <title>` for public reports (searchable by all), `/checkreport [title]` or `/readreport [title]` to view reports. Both are DM-only. Use `/find <query>` to search with fuzzy matching.
- **Personality & context** — `/aipersonality [persona]` (list/set/prompt/reset), `/vibe [tone]`, `/save [name]`, `/recall [name]`, `/reset`, `/chathistory`.
- **Games** — `/games`, `/hangman start`, `/wordle start`, `/wordladder start cold warm`, `/adventure start`, `/cipher start`, `/quizbattle start`, `/morse start`, `/rps`, `/coinflip`, `/yahtzee`, `/blackjack`.
- **Location & status** — `/test`, `/motd`, `/menu`, Meshtastic "Request Position," `/about`.
- **Admin (DM-only)** — `/changemotd <message>`, `/changeprompt <text>`, `/showprompt`, `/printprompt`, `/showmodel`, `/selectmodel`, `/hops <0-7>`, `/stop`, `/exit`, `/reboot`.

All commands are case-insensitive. Special commands buffer ~3 seconds before responding to reduce radio congestion.

---

## Dashboard & Monitoring

Access the dashboard at `http://localhost:5000/dashboard` or `http://<your-ip>:5000/dashboard` (mobile-accessible on same network) for:

- **Real-time Activity Feed** — Icon-based log stream with emoji categorization (📨 incoming, 📖 Bible, 🎮 Game, 🤖 AI, 🔐 Admin, etc.). Toggle between summary and verbose modes. **NEW:** Optimized 20-line view for mobile devices with auto-scroll detection.
- **Radio Configuration** — Set node names (long/short), device role (CLIENT, ROUTER, REPEATER), modem preset (spreading factor), and frequency slot—all dynamically pulled from current Meshtastic firmware.
- **Ollama Model Management** — View installed models, switch active model, download new models with progress tracking.
- **Onboarding Customization** — Enable/disable auto-onboarding for new users and customize the welcome message.
- **Operations Center** — Browse all available commands organized by category (Admin, AI Settings, Email, Games, Fun, Web & Search, etc.). Categories default to collapsed for a cleaner view.
- **GitHub Version Control** — View current branch and available versions, switch branches directly from the dashboard.
- **Configuration Editor** — Edit settings by category (Serial Connection, AI, Messaging, etc.) with inline help tooltips.

**Health Monitoring:**
- **Logs:** `/logs` (HTML) and `/logs/raw` (plain text); streaming SSE feed powers the dashboard in real time.
- **Health probes:**
  - `GET /ready` → HTTP 200 only when the radio link is up (503 otherwise).
  - `GET /live` → process liveness.
  - `GET /healthz` → full JSON snapshot (connection, queue depth, worker status, AI timing, last error).
- **Heartbeat:** Watch `mesh-master.log` for the `💓 HB` line every ~30 seconds summarizing RX/TX/AI ages.
- **REST hooks:** `POST /send` and `POST /ui_send` accept JSON payloads for automations; `/discord_webhook` bridges Discord events into the mesh when enabled.

## Onboarding System

New users receive an interactive 9-step guided tour when they send `/onboard`, `/onboarding`, or `/onboardme` via DM:

1. **Welcome** — Introduction to MESH-MASTER capabilities
2. **Main Menu** — How to access `/menu` for all features
3. **Mesh Mail** — Sending and receiving messages with `/mail` and `/checkmail`
4. **Logs & Reports** — Private logs (visible only to you) vs. public reports (searchable by all)
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

## Configuration Essentials

Key fields from `config.json` (trimmed for brevity):

```json
{
  "serial_port": "/dev/serial/by-id/usb-RAKwireless_WisCore_RAK4631_Board_XXXX",
  "serial_baud": 38400,
  "ai_provider": "ollama",
  "system_prompt": "You are an offline chatbot serving a local mesh network...",
  "ollama_model": "llama3.2:1b",
  "ollama_timeout": 120,
  "ollama_context_chars": 4000,
  "async_response_queue_max": 25,
  "meshtastic_kb_max_context_chars": 3200,
  "meshtastic_kb_cache_ttl": 600,
  "default_personality_id": "trail_scout",
  "mail_search_timeout": 120,
  "reply_in_channels": true,
  "reply_in_directs": true,
  "chunk_size": 200,
  "chunk_buffer_seconds": 1,
  "home_assistant_enabled": false,
  "home_assistant_channel_index": 1
}
```

Additional knobs:
- **Mesh Mail:** `mailbox_max_messages`, `mail_follow_up_delay`, `mail_notify_enabled`, `mail_notify_reminders_enabled`, `mail_notify_quiet_hours_enabled`, `mail_notify_reminder_hours`, `mail_notify_expiry_hours`, `mail_notify_max_reminders`, `mail_notify_include_self`, `mail_notify_heartbeat_only`, `mail_search_model`, `mail_search_max_messages`, `mail_search_num_ctx`, `mail_search_timeout`, `notify_active_start_hour`, `notify_active_end_hour`, and `mail_security_file`.
- **Saved context:** `saved_context_max_chars`, `saved_context_summary_chars`, `context_session_timeout_seconds`.
- **Feature toggles:** `feature_flags.json` can disable commands or switch `message_mode` to `broadcast`, `dm`, or `both`.
- **Logs & Reports:** `logs_dir` (default: `data/logs`) stores private user logs; `reports_dir` (default: `data/reports`) stores public reports. Configure `logs_max_entries` and `reports_max_entries` to limit storage.
- **Offline knowledge:** configure `offline_wiki_dir`, `offline_crawl_dir`, `offline_ddg_dir` plus the `*_summary_chars` / `*_context_chars` settings to control local article size. Use `/find <query>` in a DM to search wiki snapshots, crawls, DDG saves, reports (public), and logs (your private entries only)—reply with the number to open or return the entry.

Remember to restart the service after editing configs that lack runtime setters.

---

## Hardware Tips

- **RAK4631 Always-On Profile:**
  1. Copy `99-rak-no-autosuspend.rules` into `/etc/udev/rules.d/`, reload udev, and replug the device.  
  2. Apply `hardware_profiles/rak4631_always_on.yaml` with `./scripts/apply_rak4631_profile.py` (add `--dry-run` to preview).  
  3. Confirm `role: ROUTER_CLIENT` and `is_power_saving: false` with `meshtastic --info`.
- **Log Hygiene:** `CLEAN_LOGGING.md` outlines how to rotate logs safely when running unattended.  
- **Back up frequently:** snapshot `config.json`, `commands_config.json`, `motd.json`, `messages.log`, `messages_archive.json`, `mesh_mailboxes.json`, and `data/mail_security.json` together.

---

## Upgrade Notes from 1.x

- Single-instance PID locks prevent accidental double starts. Stop older services before launching 2.0.  
- Mesh Mail subsystems replace ad-hoc DM forwarding—migrate workflows to `/m`/`/c` commands.  
- New async response queue defaults to 25 messages; adjust `async_response_queue_max` if running on limited hardware.  
- Knowledge base trimmed and cached; tune `meshtastic_kb_max_context_chars` when using larger models.  
- Dashboard styling and APIs remain compatible, but cached assets moved to `static/`.

---

## Documentation & Support

- Mesh Mail internals: `docs/mail_readme.md`  
- Command map: `docs/mesh_master_command_tree.pdf`  
- Service management: `README_SERVICE.md`  
- Security practices: `SECURITY.md`

Issue reports and contributions are welcome via GitHub pull requests.

---

## Acknowledgements

- Original Mesh Master project by [MR_TBOT](https://github.com/mr-tbot/mesh-master); this fork builds on that foundation with a focus on fully offline resilience.  
- Thanks to the Meshtastic community researchers, testers, and field operators who supplied feedback, hardware profiles, and localization tweaks.

---

## License

MESH MASTER is distributed under the terms of the [MIT License](LICENSE).

The Meshtastic name and logo remain trademarks of Meshtastic LLC.
