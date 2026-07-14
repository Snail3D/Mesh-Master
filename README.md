<div align="center">

<img src="static/mesh-master-banner.png" alt="Mesh Master" width="600">

<a href="https://www.youtube.com/watch?v=X034-Q5VDd8" target="_blank">
  <img src="https://ytcards.demolab.com/?id=X034-Q5VDd8&title=&lang=en&timestamp=&background_color=%230d1117&title_color=%23ffffff&stats_color=%23dedede&max_title_lines=1&width=480&border_radius=5&duration=" alt="Watch the video">
</a>

### v2.6 — Off-Grid AI Operations Suite

**MESH MASTER** is a resilient copilot for Meshtastic and MeshCore LoRa mesh networks. It remembers conversations, relays messages across networks, handles async messaging, runs games, and maintains operations even when internet is unavailable.

> **Disclaimer:** This is a community project, not affiliated with the official Meshtastic or MeshCore projects. Always maintain backup communication paths for emergencies.

</div>

---

## 🆕 What's New in v2.6

- **MeshCore Protocol Support** — Dual-protocol mesh networking (Meshtastic + MeshCore) with automatic protocol detection
- **OpenAI-Compatible AI Provider** — Connect any OpenAI-compatible endpoint (MLX, LM Studio, vLLM, Ollama OpenAI mode) with automatic Ollama fallback
- **Hermes Agent Integration** — Admins can escalate to a full Hermes agent with computer control via `/hermes` or `@hermes`
- **Two-Tier Agentic AI** — Regular users get an agentic personal assistant; admins get full system control
- **OrbStack/Docker Support** — Run Mesh Master in Docker with serial passthrough and host MLX endpoint access
- **Hermes Bridge v2** — Direct synchronous bridge replacing the old file-queue approach

---

## 🚀 Quick Start

#### Installation

**macOS / Linux / Raspberry Pi:**
```bash
rm -rf ~/Mesh-Master && git clone https://github.com/Snail3D/Mesh-Master.git ~/Mesh-Master && cd ~/Mesh-Master && bash setup.sh
```

**Docker / OrbStack (macOS recommended):**
```bash
git clone https://github.com/Snail3D/Mesh-Master.git
cd Mesh-Master
cp config.json.example config.json
# Edit config.json with your settings
docker compose -f docker-compose.meshmaster.yml up -d
```

**Windows (Automatic - Recommended):**
> 🎯 **One-Click Install** - Automatically downloads Git, Python, and Mesh Master

1. Right-click PowerShell → **Run as Administrator**
2. Copy and paste this command:

```powershell
irm https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/windows/install.ps1 | iex
```

### After Installation
1. Double-click the **Mesh Master** desktop icon (or service starts automatically if installed)
2. Open the dashboard at **http://localhost:5000**

---

## 🧠 AI Provider Configuration

Mesh Master supports multiple AI providers. Set `ai_provider` in `config.json`:

| Provider | Config Key | Use Case |
|----------|-----------|----------|
| **openai** | `openai_base_url`, `openai_model` | Any OpenAI-compatible endpoint (MLX, LM Studio, vLLM) |
| **ollama** | `ollama_url`, `ollama_model` | Local Ollama instance (default) |
| **groq** | `groq_api_key`, `groq_model` | Groq cloud (fast inference) |
| **home_assistant** | — | Home Assistant integration |

### OpenAI-Compatible Endpoint (MLX / LM Studio / vLLM)

```json
{
  "ai_provider": "openai",
  "openai_base_url": "http://localhost:8087/v1",
  "openai_model": "qwen3.6-35b-a3b",
  "openai_api_key": "sk-none",
  "openai_timeout": 120
}
```

Works with any OpenAI-compatible API:
- **MLX** (Apple Silicon): `http://localhost:8087/v1`
- **LM Studio**: `http://localhost:1234/v1`
- **vLLM**: `http://localhost:8000/v1`
- From Docker: use `http://host.docker.internal:8087/v1`

---

## 📡 MeshCore Support

Mesh Master v2.6 supports both Meshtastic and MeshCore protocols:

```json
{
  "use_meshcore": true,
  "meshcore_connection_type": "serial",
  "meshcore_serial_port": "/dev/cu.usbmodem1101",
  "meshcore_auto_reconnect": true,
  "radio_protocol": "auto"
}
```

| Setting | Options | Description |
|---------|---------|-------------|
| `radio_protocol` | `auto`, `meshtastic`, `meshcore` | Protocol selection. `auto` probes at startup |
| `use_meshcore` | `true`/`false` | Enable MeshCore alongside Meshtastic |
| `meshcore_connection_type` | `serial`, `ble`, `tcp` | How to connect to the MeshCore device |

### macOS BLE Connection (LaunchAgent required)

On macOS 15+, running Mesh Master with `meshcore_connection_type: "ble"` from an SSH session or `osascript`-launched Terminal will fail with:

```
ERROR:meshcore_manager:MeshCore _create_connection failed: BLE is not authorized - check macOS privacy settings
```

macOS TCC denies CoreBluetooth access to processes launched without a GUI context, and the permission prompt never appears. Even after `tccutil reset All`, SSH-launched Python cannot trigger the dialog.

**Fix:** run Mesh Master as a user LaunchAgent so launchd provides the proper CoreBluetooth context:

```bash
# 1. Create the plist
cat > ~/Library/LaunchAgents/com.snail.mesh-master.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.snail.mesh-master</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USER/Mesh-Master/.venv/bin/python</string>
        <string>/Users/YOUR_USER/Mesh-Master/mesh-master.py</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/YOUR_USER/Mesh-Master</string>
    <key>StandardOutPath</key><string>/Users/YOUR_USER/Mesh-Master/mesh-master.log</string>
    <key>StandardErrorPath</key><string>/Users/YOUR_USER/Mesh-Master/mesh-master.log</string>
</dict>
</plist>
EOF

# 2. Load and start
launchctl load ~/Library/LaunchAgents/com.snail.mesh-master.plist
launchctl start com.snail.mesh-master

# 3. Verify
lsof -i :5001 | grep LISTEN
tail -f ~/Mesh-Master/mesh-master.log | grep -iE 'meshcore|ble|connect'
```

Only one BLE client can hold the radio at a time — disconnect any MeshCore companion app or iPhone app before starting.


### MeshCore vs Meshtastic

| | Meshtastic | MeshCore |
|--|-----------|----------|
| Focus | Casual LoRa comms | Lightweight multi-hop routing |
| Maturity | Established community | Newer, focused on embedded |
| Firmware | meshtastic-firmware | MeshCore C++ library |
| Python pkg | `meshtastic` | `meshcore` |
| Clients | Many apps | Web/Android/iOS/CLI |

---

## 🤖 Hermes Agent Integration

Admins can escalate requests to a full Hermes agent with computer control, terminal access, and Mesh Master management capabilities.

### Usage

```
/hermes <your request>       — Admin command
@hermes <your request>       — Mention in any message
/agent <your request>        — Alias (legacy)
```

### Setup

1. Install [Hermes Agent](https://github.com/NousResearch/hermes-agent) on the host
2. Create a `meshmaster` profile: `hermes profile create meshmaster --description "Mesh Master agent"`
3. Start the Hermes Bridge: `python3 hermes_bridge.py` (listens on port 9097)
4. Configure in `config.json`:
   ```json
   {
     "agent_webhook_url": "http://localhost:9097/meshmaster/agent"
   }
   ```

### How It Works

```
Mesh Master (Docker) → HTTP POST → Hermes Bridge → hermes chat -q → Response
```

The bridge calls `hermes --profile meshmaster chat -q "<query>"` synchronously and returns the response. The Hermes agent has full computer control — terminal, file system, browser, Docker management.

---

## 🏗 Docker / OrbStack

### docker-compose.meshmaster.yml

Pre-configured for OrbStack with serial passthrough and MLX endpoint access:

```bash
docker compose -f docker-compose.meshmaster.yml up -d
```

Features:
- Serial device passthrough (`/dev/cu.usbmodem1101`)
- Host MLX endpoint access (`host.docker.internal:8087`)
- Live config and data volume mounts
- Auto-restart on failure

---

## Key Features

### Network Relay
Send messages to any node by shortname:
```
snmo how's the weather?
/snmo how's the weather?
```
- Real-time ACK tracking with 20-second timeout
- Multi-chunk support for long messages
- Auto-delivery queue when recipient is offline
- Privacy controls: `/optout` and `/optin`

### Mesh Mail
Async messaging system (like email on the mesh) with PIN-protected mailboxes

### 20+ Games
Chess, Blackjack, Hangman, Wordle, Morse code, Quizzes, and more. All DM-friendly.

### AI Assistant
Ask questions, get help, adjust personality. Supports Ollama, OpenAI-compatible endpoints, and Groq.

### Offline Knowledge
Cached Wikipedia, web archive, DuckDuckGo search — works without internet.

### Logs & Reports
Private logs and public searchable reports with fuzzy matching.

### Dashboard
Real-time web interface for monitoring and control at **http://localhost:5000**

### Telegram Bot
Control your mesh from Telegram with remote commands and notifications.

### Security & Privacy
- Message content redacted from logs
- PIN-protected mailboxes with bcrypt hashing
- Self-service blocking and data deletion
- All user data excluded from git

---

## Commands (Quick Reference)
[COMMANDS.md](COMMANDS.md) (all commands)

**Network & Relay**
- `<shortname> <msg>` — Relay message to shortname
- `/nodes` — List all reachable nodes
- `/node <shortname>` — Show signal details
- `/optout`, `/optin` — Control relay receipt

**Mesh Mail**
- `/m <box> <msg>` — Send to mailbox
- `/c <box> PIN` — Check mail
- `/emailhelp` — Mail system help

**AI & Personality**
- `/ai <question>` — Ask AI (no /ai prefix needed in DM mode)
- `/hermes <request>` — Escalate to full Hermes agent (admin only)
- `/vibe [tone]` — Adjust conversation tone
- `/save [name]` — Capture context
- `/recall [name]` — Restore context

**Games & Fun**
- `/games` — List all games
- `/hangman start`, `/wordle start`
- `/masterquiz`, `/meshtasticquiz`
- `/rps`, `/coinflip`, `/yahtzee`, `/blackjack`

**Knowledge**
- `/offline wiki <topic>` — Local Wikipedia mirror
- `/wiki <topic>` — Fetch from online Wikipedia
- `/web <query>` — DuckDuckGo search
- `/find <query>` — Search logs, reports, wiki, and crawl cache
- `/bible [topic]` — Bible verses
- `/weather` — Weather forecast

**Admin (DM-only)**
- `/hermes <request>` — Full Hermes agent with computer control
- `/menu` — Main menu
- `/about` — Version info
- `/status` — System status
- `/update` — Pull latest from GitHub
- `/reboot` — Restart server
- `/ban <shortname>` — Permanently ban a user
- `/timeout <shortname>` — Timeout a user for 24 hours

---

## Security Notes

**Before making code changes, read:**
1. [SECURITY_INSTRUCTIONS.md](SECURITY_INSTRUCTIONS.md) — Security guidelines
2. [CLAUDE.md](CLAUDE.md) — Full project context

**Never commit:**
- `config.json` — Contains passwords and API keys
- `data/` — User logs, mail, conversations
- `*.log`, `*.db` files — Runtime data

---

## Support

- 📖 **Docs:** [COMMANDS.md](COMMANDS.md), [README_SERVICE.md](README_SERVICE.md), [CLAUDE.md](CLAUDE.md)
- 🐛 **Issues:** Report on GitHub
- ⭐ **Star the Project:** [github.com/Snail3D/Mesh-Master](https://github.com/Snail3D/Mesh-Master)

---

## License

MIT License — See [LICENSE](LICENSE)

Meshtastic is a trademark of Meshtastic LLC. MeshCore is a project by meshcore-dev.

---

- Original Mesh-AI by [MR_TBOT](https://github.com/mr-tbot/mesh-ai)
- Enhanced by [Snail3D](https://github.com/Snail3D)
- Meshtastic & MeshCore communities for hardware, testing, and feedback
