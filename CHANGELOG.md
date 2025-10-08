# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-10-07

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
