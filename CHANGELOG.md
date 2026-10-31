# Changelog

All notable changes to this project will be documented in this file.

## [2.6.9] - 2026-10-31

### Security
- **Unauthenticated secrets disclosure.** `GET /dashboard/metrics` returned the
  plaintext `admin_password`, the admin passphrase, the Home Assistant token and
  the Tailscale key to any caller; `GET /dashboard/telegram/config` returned the
  Telegram bot token; `GET /logs/verbose` returned the log ring buffer, which
  contains the generated password. All three now require a logged-in session,
  and the config overview masks secret values in its `raw` field.
- **Telegram chat allow-list was not enforced inbound.** `authorized_chat_ids`
  only gated outbound sends, so any Telegram user who found the bot could
  transmit on the mesh and spend AI credits. Unauthorized chats are now ignored.
- **Hermes bridge had no authentication.** It runs `hermes` in yolo mode
  (terminal + computer_use), so a POST to `127.0.0.1:9097` was arbitrary command
  execution — reachable from any web page via a `no-cors` request. It now binds
  loopback, honours an optional `HERMES_BRIDGE_TOKEN` (`X-Bridge-Token`) and
  rejects foreign `Origin`s. Also threaded, so `/health` no longer queues behind
  a running chat.
- **Command injection in `/dashboard/update/apply`**: the `version` field was
  interpolated into a generated bash script. It is now validated. The script is
  also written with `mkstemp` instead of a predictable `/tmp/mesh_update.sh`
  (symlink overwrite).
- Installers no longer ship `admin_password: "password"`; a fresh install
  generates one on first run.

- **Startup crash on non-UTF-8 stdout** (Windows Git Bash, `LANG=C` on a Pi):
  `mesh-master.py` died at import with `UnicodeEncodeError` on the first emoji in
  a log line, because the module emits emoji throughout (286 ⚠ / 191 ❌ / 88 ✅).
  `sys.stdout` / `sys.stderr` are now reconfigured to UTF-8 with
  `errors="replace"` before any output. Thanks @kolotush-commits (#3).
- **Telegram bot silently missing on Docker and Windows installs**:
  `python-telegram-bot` was never in `requirements.txt`, only in a separate
  `setup.sh` line. `Dockerfile` and `scripts/windows/install.ps1` install only
  `requirements.txt`, so both shipped with `TELEGRAM_AVAILABLE = False` and the
  bot never started. Now declared as `python-telegram-bot>=21.11.1,<22`.
  Thanks @kolotush-commits (#4).

- **MeshCore auto-detect never worked**: `MeshCore` was not imported in
  `mesh-master.py`, so the probe raised `NameError` and `radio_protocol: "auto"`
  always reported Meshtastic. The probe also no longer leaves the `meshcore`
  logger pinned to ERROR, and the relay strips the `mc_` destination prefix.
- **MeshCore → Telegram forwarding skipped channel traffic**: the forward ran
  after the "no AI reply" early return, so ordinary channel messages never
  reached Telegram.
- **DM history leaked between senders**: `build_ollama_history` included every
  DM's AI replies, so one user's conversation appeared in another's context.
- **`/hermes` was not a registered command** (and `@hermes` did nothing): both
  are documented but only `/agent` resolved. `/hermes` is now an alias and
  `@hermes` / `@agent` are rewritten to the command.
- **Onboarding swallowed control words**: a new user's first `stop`, `resume`,
  `blacklistme` or yes/no confirmation was eaten by the tour.
- **Telegram config save leaked pollers**: the stop event was never read and
  `run_polling` was never stopped, so each save added another poller and each
  DM was answered once per poller. Saves now stop and join the old thread.
- **`/agent` blocked the radio receive thread** for up to the full bridge
  timeout; it now runs on the async worker.
- **meshtastic 2.7 raised its command/ACK timeout from 20s to 300s**, which
  would stall a chunk send for five minutes. All interfaces now get an explicit
  `radio_op_timeout` (default 30s).
- **Radio node lookups always missed**: `interface.nodes` is keyed `"!xxxxxxxx"`,
  but the dashboard indexed it with an int, so radio name / battery / info fell
  back to defaults. Added a tolerant `lookup_node()`.
- **`node.writeConfig()` raised `TypeError`** (needs a config name) on every
  rename, and dead proto3 `ch.settings = ChannelSettings()` assignments always
  raised. The serial baud switch targeted a non-existent `_serial` attribute.
- `pubsub==0.1.2` was the wrong distribution (it shadows pypubsub's `pubsub`
  package and has no `pub`); `psutil` / `nvidia-ml-py` were imported but never
  declared; `bleak` floor raised to match meshtastic.
- Docker/compose published port 5000 while the app listens on 5001; config
  files were mounted at `/app/…` but read from `/app/data/…`; the Dockerfile
  installed meshtastic twice. `health_check.sh` used the wrong unit name and
  port. `setup.sh` now `cd`s to the project root and the Pi branch installs
  `requirements.txt` (it previously omitted meshcore and Telegram entirely).

### Removed
- Eight orphaned agent scripts that nothing imported or launched
  (`hermes_poller.py`, `agent_responder.py`, `auto_agent.py`, `agent_system.py`,
  `simple_agent.py`, `intelligent_agent.py`, `agent_9095.py`, `agent_9096.py`)
  and the dead `data/hermes_responses.json` polling loop in `mesh-master.py`
  (nothing wrote that file).

## [2.6.8] - 2026-09-20

### Fixed
- **Linux serial connections** (Kali/Debian/Ubuntu): a scanned radio now actually connects.
  - The dashboard "Save Serial Settings" and "Save WiFi Settings" buttons had no
    click handlers and never persisted a port. They now save atomically and
    reconnect live (no process restart).
  - New `/dashboard/serial/diagnose` + a per-port **🩺 Diagnose** button detects
    permissions, port holders, brltty, and ModemManager, and returns the exact
    copy-paste fix.
  - Auto-detect now genuinely probes Meshtastic/MeshCore instead of always
    reporting 38400 (it used `ser.isOpen()`, which is always true).
  - Serial failures now surface actionable hints (dialout group, brltty,
    ModemManager, changing `/dev/ttyUSB*` paths, holder process names).
- MeshCore propagates the real connection error instead of a generic
  "Failed to connect via serial".
- Bluetooth connect/forget write config atomically under lock and reconnect in
  place instead of spawning a second process.

### Changed
- Public default serial baud is now **115200** (native Meshtastic USB); 38400
  remains available for legacy/long-cable UART runs.
- Added `scripts/linux/fix-serial.sh` and Linux serial notes to README/setup.sh.
- Added `pyserial` and `pyserial-asyncio-fast` to requirements and removed the
  duplicate `meshcore` pin.
- Untracked `config.json.bak` and ignored config backups (may hold secrets).

## [2.6.0] - 2026-06-22

### Added
- **OpenAI-compatible AI provider**: New `openai` provider option for any OpenAI-compatible API endpoint (MLX, LM Studio, vLLM, etc.)
  - Config keys: `openai_base_url`, `openai_model`, `openai_api_key`, `openai_timeout`
  - Works with local MLX strip proxy (localhost:8087) for Qwen3.6-35B-A3B
  - Automatic fallback to Ollama if the OpenAI endpoint fails
- **MeshCore protocol support**: Dual-protocol mesh networking (Meshtastic + MeshCore)
  - `radio_protocol: "auto"` probes at startup and uses whichever is detected
  - `use_meshcore: true` enables MeshCore alongside Meshtastic
  - Connection types: serial, BLE, TCP
  - Config keys: `meshcore_connection_type`, `meshcore_serial_port`, `meshcore_ble_address`, etc.
- **meshcore Python package** added to requirements.txt and Dockerfile
- **OrbStack/Docker support** with serial device passthrough and host MLX endpoint access
- Config descriptions for all new MeshCore and OpenAI settings
- New `docker-compose.meshmaster.yml` for OrbStack with serial passthrough + MLX endpoint

### Changed
- Version bumped to 2.6
- `_VALID_PROVIDERS` now includes `"openai"`
- CLAUDE.md updated to reflect MeshCore support and v2.6

## [2.1.0] - 2025-10-07

Highlights
- **Interactive Onboarding**: New 9-step guided tour via `/onboard`, `/onboarding`, or `/onboardme` (DM only)
  - Customizable welcome messages through dashboard
  - Auto-onboarding toggle for first-time users
  - Persistent state across restarts
- **Private Logs & Public Reports**: Enhanced privacy model
  - `/log <title>` creates private entries visible only to creator
  - `/report <title>` creates public entries searchable by everyone
  - `/find` respects privacy: shows only your logs, but all reports
  - Author-based filtering in UserEntryStore
- **Enhanced Dashboard Controls**
  - Real-time activity feed with icon-based categorization
  - Radio configuration: node names, device role, modem preset, frequency slot
  - Ollama model management with download progress
  - GitHub version selector
  - Operations Center with collapsible command categories (default collapsed)
  - Configuration editor by category with inline help
- **Data Persistence**: Protected all user data via .gitignore
  - logs/, reports/, mail, settings, game states persist across updates
  - Git pulls won't overwrite user data
- **Simplified Activity Logs**: Icon-based notifications for privacy
  - 📨 Incoming messages, 📖 Bible, 🎮 Games, 🤖 AI, 🔐 Admin, etc.
  - No message content or node names in logs
  - Toggle between summary and verbose modes
- **Process Management**: Automatic cleanup of orphaned processes
  - Startup script kills stale mesh-master.py processes
  - Systemd ExecStopPost ensures clean shutdown
  - Prevents "Resource temporarily unavailable" serial port locks
- **Command Improvements**
  - Added usage examples to all command descriptions
  - Command aliases: `/onboard`, `/onboarding`, `/onboardme` all work
  - Updated help text to clarify privacy and functionality

Notes
- All onboarding steps use 5th grade reading level for accessibility
- Dashboard "Activity" panel removes "Snapshot" branding
- Command categories organized: Admin, AI Settings, Email, Reports & Logs, Games, Fun, Web & Search, Books & Reference, Files & Data, Information

## [1.9.0] - 2025-09-29

Highlights
- Resend (No Ack): per‑chunk DM retries with configurable interval/attempts, “(Nth try)” suffix toggle, and network‑usage gating.
- User controls: `/stop` mutes, `resume|/start|/continue` unmutes, `blacklistme` (with Y/N) blocks, and `unblock` restores.
- Dynamic admin aliases: admins can link commands via `/new=/existing`; persisted in `commands_config.json`, reflected in menu.
- Dashboard: Ack Telemetry snapshot (DM first/resend rates), “Reset All Defaults” button with confirmation + activity log.
- Radio panel: clean stacked “Channels” layout, only active channels render, “Generate” PSK shows a reset warning, add‑channel cancel clears status.

Notes
- Broadcast resends remain optional and off by default; DMs honor per‑chunk ACKs and stop on success.
- Telemetry is anonymous and stored in memory; can be expanded in UI later.

## [1.1.0] - 2025-09-27

Highlights
- Retired the `/weather` command and all external location datasets to keep Mesh Master fully offline.
- Trimmed the bundled MeshTastic knowledge base to a focused core (~25k tokens) for faster responses.
- Added a warm cache for `/meshtastic` lookups (configurable via `meshtastic_kb_cache_ttl`) so follow-up questions reuse the loaded context.

Notes
- The knowledge base still reloads when the source file changes or cache TTL expires.
- Set `meshtastic_kb_max_context_chars` in `config.json` (defaults to 3200) to cap the prompt size if needed.

## [1.0.0] - 2025-09-25

Highlights
- DM-only admin commands
  - `/changeprompt <text>`: Update AI system prompt (persists to `config.json`).
  - `/changemotd <text>`: Update MOTD (persists to `motd.json`).
  - `/showprompt` and `/printprompt`: Display current system prompt.
- Health and heartbeat
  - Endpoints: `/healthz` (detailed), `/live` (liveness), `/ready` (readiness).
  - Heartbeat log line every ~30s summarizing status and activity ages.
- Stability and robustness
  - Atomic writes for config/MOTD to avoid partial files.
  - App-level PID lock to prevent multiple instances.

Notes
- Admin commands are DM-only to avoid channel misuse.
- Health reports degraded states (disconnected radio, stalled queue, recent AI error).
