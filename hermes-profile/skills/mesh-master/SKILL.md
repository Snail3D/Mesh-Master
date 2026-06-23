---
name: mesh-master
description: "Mesh Master v2.5 — off-grid AI operations suite for Meshtastic and MeshCore LoRa mesh networks. Architecture, commands, Docker/OrbStack setup, device management, two-tier agentic AI, and integration points."
version: 1.0.0
category: software-development
---

# Mesh Master

## Quick Reference

- **Repo:** `~/clawd/Mesh-Master/` (GitHub: Snail3D/Mesh-Master)
- **Version:** v2.5 — Off-Grid AI Operations Suite
- **Language:** Python 3.11+ (main file ~35K lines)
- **Docker:** OrbStack, container `mesh-master`, port 5000
- **Config:** `~/clawd/Mesh-Master/config.json`
- **Dashboard:** http://localhost:5000
- **Model:** Qwen3.6-35B-A3B via MLX strip proxy at `http://127.0.0.1:8087/v1`

## Architecture

```
mesh-master.py (35K lines, entry point)
├── Flask web server (port 5000) — dashboard + API
├── Meshtastic interface (serial/WiFi)
├── MeshCore interface (BLE/serial/TCP) — meshcore_manager.py
├── Message routing & command dispatch
├── AI provider system (ollama/groq/openai/home_assistant)
├── Async response queue
└── mesh_master/ (package)
    ├── meshcore_manager.py — MeshCore BLE/serial/TCP integration
    ├── mail_manager.py — PIN-protected mailboxes (SQLite)
    ├── relay_manager.py — cross-network bridge with ACK tracking
    ├── onboarding_manager.py — 9-step guided tour
    ├── system_context.py — 50K token context-aware help
    ├── user_entries.py — private logs + public reports
    ├── alarm_timer_manager.py — scheduling/reminders
    ├── offline_wiki.py — cached Wikipedia
    ├── offline_crawl.py — web archival
    ├── offline_ddg.py — DuckDuckGo search cache
    ├── help_database.py — command docs
    └── games/game_manager.py — 20+ games (126K lines)
```

## Docker / OrbStack

### Build & Run

```bash
cd ~/clawd/Mesh-Master

# Build image
docker build -t mesh-master .

# Run with docker compose
docker compose up -d

# Or run directly with serial passthrough + host network access
docker run -d \
  --name mesh-master \
  --privileged \
  -p 5000:5000 \
  -v /dev/cu.usbmodem1101:/dev/cu.usbmodem1101 \
  -v ./config.json:/app/config.json \
  -v ./data:/app/data \
  --add-host=host.docker.internal:host-gateway \
  mesh-master

# Container lifecycle
docker start mesh-master
docker stop mesh-master
docker restart mesh-master
docker logs -f mesh-master
docker exec -it mesh-master bash
```

### Serial Passthrough for Docker

The Heltec V3 is at `/dev/cu.usbmodem1101`. For Docker access:
```yaml
privileged: true
devices:
  - /dev/cu.usbmodem1101:/dev/cu.usbmodem1101
environment:
  - MESH_INTERFACE=/dev/cu.usbmodem1101
```

### MLX Model Endpoint from Docker

The container reaches the MLX strip proxy on the host:
```yaml
environment:
  - OPENAI_BASE_URL=http://host.docker.internal:8087/v1
  - OPENAI_API_KEY=***  - OPENAI_MODEL=qwen3.6-35b-a3b
```

## Two-Tier Agentic AI System

### Vision

Replace the current "dumb" AI (single prompt → single response) with an agentic system where the AI can call tools to actually DO things for users.

### Tier 1: Regular Users (Agentic Personal Assistant)

Curated tool set — the AI can take actions on behalf of the user:

| Tool | What it does | Mesh Master source |
|------|-------------|-------------------|
| `check_mail` | Check user's mailbox for unread messages | mail_manager.py |
| `send_mail` | Send mail to another user | mail_manager.py |
| `check_mesh_presence` | List who's on the mesh, last check-in times | meshtastic interface |
| `search_knowledge` | Search wiki, web archive, DDG cache, reports | offline_*.py, user_entries.py |
| `read_wiki` | Look up a Wikipedia article (offline cache first) | offline_wiki.py |
| `web_search` | Search DuckDuckGo (cached) | offline_ddg.py |
| `create_log` | Create a private log entry | user_entries.py |
| `read_logs` | Read user's private logs | user_entries.py |
| `create_report` | Create a public report | user_entries.py |
| `search_reports` | Search all public reports | user_entries.py |
| `set_reminder` | Set an alarm/reminder | alarm_timer_manager.py |
| `list_reminders` | List user's reminders | alarm_timer_manager.py |
| `get_weather` | Fetch weather for a location | mesh-master.py weather cmd |
| `get_node_info` | Get info about a specific node | meshtastic interface |
| `list_channels` | List available channels | mesh-master.py |
| `get_help` | Get help with a command | help_database.py |

### Tier 2: Admin Users (Full Hermes Agent)

Admins get escalated to the Hermes meshmaster profile — real computer control:
- Terminal (shell commands, Docker, esptool)
- File system (read/edit code, configs, data)
- Browser automation (dashboard testing, web research)
- Computer use (macOS desktop control)
- Full Mesh Master management (config, restart, firmware)

### Implementation Plan

1. Add `"openai"` to `_VALID_PROVIDERS` in mesh-master.py (line ~6387)
2. Wire up OpenAI-compatible endpoint (MLX proxy at localhost:8087)
3. Build tool-calling loop: prompt → model → tool_calls → execute → response
4. Define user tools as Python functions with JSON schemas
5. Add admin detection → escalate to Hermes API
6. Config keys:
   - `ai_provider: "openai"`
   - `openai_base_url: "http://host.docker.internal:8087/v1"`
   - `openai_model: "qwen3.6-35b-a3b"`
   - `openai_api_key: "sk-none"`

## Device Management

### Heltec V3 (ESP32-S3)

- **Port:** `/dev/cu.usbmodem1101`
- **MAC:** `90:70:69:85:06:b8`
- **Current firmware:** MeshCore Companion BLE v1.16.0
- **Bootloader mode:** Hold BOOT button, press RST, release BOOT

### Flashing Firmware

```bash
# Erase flash
esptool --port /dev/cu.usbmodem1101 --baud 460800 erase-flash

# Flash MeshCore (download pre-built from GitHub releases)
gh release download companion-v1.16.0 --repo meshcore-dev/MeshCore \
  --pattern "Heltec_v3_companion_radio_ble-v1.16.0-*-merged.bin" \
  --dir /tmp/meshcore-flash

esptool --port /dev/cu.usbmodem1101 --baud 460800 \
  write-flash 0x0 /tmp/meshcore-flash/Heltec_v3_companion_radio_ble-*.bin
```

### MeshCore CLI

```bash
# Python package (installed in ~/clawd/Mesh-Master/.venv)
.venv/bin/python -c "from meshcore import MeshCore, BLEConnection"

# Connect via BLE (requires Bluetooth on)
# Phone app: MeshCore (iOS/Android)
# Web client: https://app.meshcore.nz
# Config tool: https://config.meshcore.io
```

## Key Config (config.json)

```json
{
  "ai_provider": "openai",
  "openai_base_url": "http://host.docker.internal:8087/v1",
  "openai_model": "qwen3.6-35b-a3b",
  "openai_api_key": "sk-none",
  "openai_timeout": 120,
  "serial_port": "/dev/cu.usbmodem1101",
  "serial_baud": 38400,
  "use_meshcore": true,
  "meshcore_connection_type": "ble",
  "meshcore_auto_reconnect": true,
  "radio_protocol": "auto",
  "ai_node_name": "Mesh Master"
}
```

## MeshCore vs Meshtastic

| | Meshtastic | MeshCore |
|--|-----------|----------|
| Maturity | Established, large community | Newer, lightweight |
| Focus | Casual LoRa comms | Embedded multi-hop routing |
| Firmware | meshtastic-firmware | MeshCore (C++ library) |
| Python pkg | `meshtastic` | `meshcore` |
| Protocol | protobufs | custom lightweight |
| Clients | many apps | web/Android/iOS/CLI |

Mesh Master supports BOTH via `radio_protocol: "auto"`.

## Monitoring Commands

```bash
# Container status
docker ps | grep mesh-master
docker logs --tail 50 mesh-master

# Dashboard
open http://localhost:5000

# Check MLX proxy health
curl -s http://localhost:8087/v1/models | python3 -m json.tool
```

## Pitfalls

- **Docker can't reach localhost:8087** — use `host.docker.internal:8087` from inside the container
- **Serial device changes** — Heltec V3 may show on different `/dev/cu.usbmodem*` after replug
- **Bluetooth off on Mac** — BLE MeshCore connection fails silently
- **MLX proxy down** — `com.snailmac.qwen-strip-proxy` launchd service must be running (port 8087)
- **Python 3.9 too old** — `meshcore` package needs Python 3.10+, use `.venv` with Python 3.12
- **OrbStack vs Docker Desktop** — OrbStack already installed (v2.1.2), use `docker` command directly

## Reference Files

- `references/commands.md` — Complete Mesh Master command reference (all commands, aliases, examples)
- `references/architecture.md` — Full CLAUDE.md with architecture details, config schema, all subsystems

**Load these when the user asks about specific commands, how something works, or needs to configure a feature.**

## Operational Quick Start

When Eric asks you to "start everything up" or "get Mesh Master running":

```bash
# 1. Check MLX proxy is running (Qwen3.6 model)
curl -s http://localhost:8087/v1/models | python3 -m json.tool

# 2. Start Hermes bridge (connects Mesh Master → Hermes agent)
cd ~/clawd/Mesh-Master && HERMES_PROFILE=meshmaster python3.12 hermes_bridge.py &

# 3. Start Mesh Master in Docker
cd ~/clawd/Mesh-Master && docker compose -f docker-compose.meshmaster.yml up -d

# 4. Check status
docker logs --tail 20 mesh-master
curl -s http://localhost:5000 | head -5
curl -s http://localhost:9097/health
```

When Eric asks to "shut it down":
```bash
docker compose -f docker-compose.meshmaster.yml down
kill $(pgrep -f hermes_bridge.py)
```

## Service Management

### Restart Mesh Master (Docker)
```bash
# Restart the container
docker restart mesh-master

# Or via compose
cd ~/clawd/Mesh-Master && docker compose -f docker-compose.meshmaster.yml restart

# Check logs after restart
docker logs --tail 30 mesh-master
```

### Restart Hermes Bridge
```bash
# Kill existing
kill $(pgrep -f hermes_bridge.py)
# Start fresh
cd ~/clawd/Mesh-Master && HERMES_PROFILE=meshmaster python3.12 hermes_bridge.py &
# Verify
curl -s http://localhost:9097/health | python3 -m json.tool
```

### Restart MLX / Qwen3.6 Model
```bash
# Check if proxy is running
curl -s http://localhost:8087/v1/models | python3 -m json.tool

# If not, restart the launchd services
launchctl kickstart -k gui/501/com.snailmac.qwen-mlxlm
launchctl kickstart -k gui/501/com.snailmac.qwen-strip-proxy
sleep 5
curl -s http://localhost:8087/v1/models | python3 -m json.tool
```

### Restart Hermes Gateway (meshmaster profile)
```bash
# Can't restart from inside gateway — run from a separate terminal
meshmaster gateway restart
# Or via launchctl
launchctl kickstart -k gui/501/ai.hermes.gateway-meshmaster
```

### Full Stack Restart (everything)
```bash
# 1. MLX proxy
launchctl kickstart -k gui/501/com.snailmac.qwen-mlxlm
launchctl kickstart -k gui/501/com.snailmac.qwen-strip-proxy
sleep 5

# 2. Hermes bridge
kill $(pgrep -f hermes_bridge.py) 2>/dev/null
cd ~/clawd/Mesh-Master && HERMES_PROFILE=meshmaster python3.12 hermes_bridge.py &
sleep 2

# 3. Mesh Master Docker
cd ~/clawd/Mesh-Master && docker compose -f docker-compose.meshmaster.yml down
docker compose -f docker-compose.meshmaster.yml up -d
sleep 3

# 4. Verify everything
echo "MLX: $(curl -s http://localhost:8087/v1/models | python3 -c 'import sys,json; print(json.load(sys.stdin)["data"][0]["id"])' 2>/dev/null || echo 'DOWN')"
echo "Bridge: $(curl -s http://localhost:9097/health | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])' 2>/dev/null || echo 'DOWN')"
echo "Mesh Master: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:5000 2>/dev/null || echo 'DOWN')"
echo "Docker: $(docker ps --filter name=mesh-master --format '{{.Status}}' 2>/dev/null || echo 'DOWN')"
```
