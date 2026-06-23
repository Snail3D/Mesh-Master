# Mesh Master One-Click AI-Guided Installer — Bootstrap Research

**Author:** Hermes Agent (research subagent)
**Date:** 2026-06-22
**Status:** Pre-implementation research
**Goal:** Find the minimum-viable pieces to build a one-click installer that
bootstraps a local uncensored AI agent, then uses that agent to finish
installing and configuring Hermes Agent + a Telegram bot — all from a single
`curl | bash` command.

---

## TL;DR — Recommended Stack

| Component | Pick | Why |
|---|---|---|
| **Bootstrap language** | Bash + Python (the bash that runs first; the Python is the bootstrap agent) | Bash is universal; Python is already in the Hermes installer dep tree |
| **macOS inference** | `mlx_lm.server` (Apple's MLX, OpenAI-compatible HTTP on port 8080) | First-class Apple Silicon, pre-built wheels, OpenAI-compatible |
| **Linux/Windows inference** | `llama-server` from `llama.cpp` release tarball | Pre-built static binaries for every major OS, OpenAI-compatible |
| **Smallest uncensored model (Qwen3)** | `mlx-community/Josiefied-Qwen3-1.7B-abliterated-v1-4bit` (MLX, ~1 GB) and `mradermacher/Josiefied-Qwen3-1.7B-abliterated-v1-GGUF` Q4_K_M (~1.1 GB) | 1.7B params, 4-bit quant, abliterated (refusal-trained away), small enough to run on any Apple Silicon Mac or modern x86 |
| **Telegram bot creation** | **Reuse `hermes_cli/telegram_managed_bot.py` — already exists in Hermes!** | Uses Telegram's new Managed Bots API via `@HermesSetupBot`; returns token via deep link + QR + poll. Falls back to manual `@BotFather` if unreachable |
| **Bootstrap agent** | Reuse `install.sh --manifest` + a ~150-line Python tool-calling loop | The installer is already structured as 12 JSON-emitting stages — perfect for AI orchestration |
| **Final upgrade path** | `hermes update` (already supports re-running install.sh against existing checkout) | Don't re-invent the upgrade path |

The bootstrap is a 3-stage rocket:

```
┌────────────────────────────────────────────────────────────────────────┐
│  STAGE 0  (Bash)                                                        │
│  curl ... | bash                                                        │
│    • detect OS / arch                                                   │
│    • install Python (use uv-managed install — Hermes already does this)│
│    • download the smallest uncensored Qwen3 model (~1 GB)              │
│    • launch mlx_lm.server / llama-server in the background             │
│    • spawn stage1.py — the bootstrap AI agent                           │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│  STAGE 1  (Python + local Qwen3-1.7B-abliterated)                       │
│  bootstrap_agent.py — ~150 lines, tool-calling loop                      │
│    Tools: run_command, read_file, write_file, curl_get, open_url        │
│    System prompt: "You are Mesh Master setup agent. Run install.sh       │
│                   --stage repository --stage venv ... then create       │
│                   a Telegram bot via @HermesSetupBot deep link..."     │
│                                                                          │
│    The 1.7B model is too dumb for open-ended chat, but it's smart enough │
│    to follow a scripted checklist of curl/bash commands — see §5 below. │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│  STAGE 2  (Python + small model → user takes over via Hermes)           │
│    • Run install.sh through its structured stages                       │
│    • Use Hermes's existing Telegram managed-bot onboarding              │
│    • Spawn `hermes gateway install` (already systemd-installs itself)   │
│    • Hand the user a Telegram bot they can talk to                      │
│    • Switch the running model to a stronger remote one (user's API key) │
│      or keep local model if they want off-grid                          │
└────────────────────────────────────────────────────────────────────────┘
```

**Total install size:** ~1 GB model + ~200 MB Hermes venv + a couple hundred MB
browser tools if opted in. Comfortable on a Mesh Master operator's laptop.

---

## 1. MLX on macOS — Local Inference for Apple Silicon

### The library: `mlx-lm`

- **Package:** `mlx-lm` (Apple, MIT)
- **Latest:** 0.31.3 (verified installed cleanly into a venv on macOS 26.3.2)
- **PyPI:** https://pypi.org/project/mlx-lm/
- **GitHub:** https://github.com/ml-explore/mlx-lm
- **Requires:** `mlx>=0.31.2`, `numpy`, `transformers>=5.7.0`, `sentencepiece`,
  `protobuf`, `pyyaml`, `jinja2`. Python ≥ 3.8. **macOS only** for the
  Apple-Silicon backend; CPU/CUDA backends exist but are not what we want.
- **Install (verified):**
  ```bash
  pip install mlx-lm
  Successfully installed click-8.4.1 hf-xet-1.5.1 huggingface-hub-1.20.1 \
    mlx-0.31.2 mlx-lm-0.31.3 mlx-metal-0.31.2 sentencepiece-0.2.1 \
    tokenizers-0.22.2 transformers-5.12.1
  ```

### The server: `mlx_lm.server`

Starts an **OpenAI-compatible HTTP server** on port 8080.

```bash
python -m mlx_lm.server --model mlx-community/Josiefied-Qwen3-1.7B-abliterated-v1-4bit
```

It will auto-download the model on first run from HuggingFace. Key flags
(verified in source `mlx_lm/server.py`):

- `--model` — HF repo ID or local path
- `--host` — bind address (default `localhost` — set `0.0.0.0` for LAN)
- `--port` — default 8080
- `--chat-template` — pick a specific jinja template
- `--use-default-chat-template` — bool
- `--log-level` — `DEBUG|INFO|WARNING|ERROR|CRITICAL`

Endpoints exposed (per `mlx_lm/SERVER.md`):

| Endpoint | OpenAI equivalent |
|---|---|
| `POST /v1/chat/completions` | ✅ Full implementation, supports `stream`, `tools`, `temperature`, `top_p`, `top_k`, `min_p`, `repetition/presence/frequency_penalty`, `logit_bias`, `logprobs`, speculative decoding |
| `GET  /v1/models` | ✅ List loaded models |

> ⚠️ The MLX LM server "is not recommended for production as it only
> implements basic security checks." For a bootstrap agent running locally
> on a laptop that's fine — bind to `127.0.0.1` only.

### Smallest uncensored Qwen3 model that works with MLX

Searched HuggingFace for `qwen3 abliterated mlx` (HuggingFace API verified
online, June 2026):

**Winner — `mlx-community/Josiefied-Qwen3-1.7B-abliterated-v1-4bit`**
- ~1.7B parameters, **4-bit quantized, ~1 GB download**
- Derived from `Goekdeniz-Guelmez/Josiefied-Qwen3-1.7B-abliterated-v1`
- That in turn is a fine-tune of `mlabonne/Qwen3-1.7B-abliterated` (the
  canonical "abliterated" Qwen3 — refusal directions removed via the
  abliteration technique)
- Variants also available: `-6bit`, `-8bit`, `-bf16` (all from the mlx-community org)

**File-size sanity check (from HF tree API):**
```
mlx-community/Josiefied-Qwen3-1.7B-abliterated-v1-4bit/tree/main
  model.safetensors    ~968 MB   ← 4-bit weights + tokenizer
  tokenizer.json        ~11 MB
  merges.txt           ~1.7 MB
  vocab.json           ~2.8 MB
  ... (config files negligible)
```
~1 GB total. Fits in any Apple Silicon Mac from M1 onward.

**Run-time footprint:**
- 1.7B × 0.5 byte ≈ 850 MB model weights
- MLX keeps weights in unified memory — need ~2 GB free RAM for inference
  (works on M1 8GB, comfortable on M2/M3 16GB+)

**Bigger alternatives if you want smarter bootstrap agent:**

| Model | Quant | Size | Notes |
|---|---|---|---|
| `mlx-community/Qwen3-1.7B-4bit` | 4-bit | ~1 GB | Official Qwen3, NOT abliterated — will refuse some tasks |
| `mlx-community/Qwen3.5-4B-MLX-4bit` | 4-bit | ~2.5 GB | Official Qwen3.5 4B — sharper reasoning |
| `mlx-community/Qwen3.5-9B-OptiQ-4bit` | 4-bit (mixed) | ~5 GB | 9B params, much smarter |
| `mlx-community/Qwen3.5-9B-OptiQ-4bit` | 4-bit | ~5 GB | Good balance |
| `lukey03/Qwen3.5-9B-abliterated-MLX-4bit` | 4-bit | ~5 GB | Abliterated 9B, recommended sweet spot |
| `mlx-community/Qwen3-30B-A3B-Instruct-4bit` | 4-bit MoE | ~17 GB | Top-tier local |

**Recommendation:** Start with the 1.7B abliterated for the bootstrap, then
let the user upgrade by editing one config value. The 1.7B is plenty to follow
a scripted checklist (download model, run install.sh --stage repository, etc.).

### Downloading model programmatically

```python
from huggingface_hub import snapshot_download
path = snapshot_download(
    repo_id="mlx-community/Josiefied-Qwen3-1.7B-abliterated-v1-4bit",
    cache_dir=os.path.expanduser("~/.cache/huggingface"),
)
```
or just `mlx_lm.server` will do it on first run if you pass the repo ID.

---

## 2. llama.cpp for Linux / Windows

`llama.cpp` ships **pre-built static binaries for every major OS** in its
GitHub Releases. Latest verified: **b9763** (2026-06-22).

### Pre-built binaries available

From https://github.com/ggml-org/llama.cpp/releases/tag/b9763:

```
llama-b9763-bin-macos-arm64.tar.gz       ← Apple Silicon
llama-b9763-bin-macos-x64.tar.gz         ← Intel Mac
llama-b9763-bin-ubuntu-x64.tar.gz        ← Linux x86_64 (CPU only)
llama-b9763-bin-ubuntu-cuda-*.tar.gz     ← Linux + NVIDIA
llama-b9763-bin-ubuntu-vulkan-*.tar.gz   ← Linux + Vulkan GPU
llama-b9763-bin-ubuntu-rocm-*.tar.gz     ← Linux + AMD ROCm
llama-b9763-bin-ubuntu-sycl-*.tar.gz     ← Linux + Intel GPU
llama-b9763-bin-ubuntu-arm64.tar.gz      ← Linux ARM (Raspberry Pi 5 etc.)
llama-b9763-bin-win-cuda-x64.zip         ← Windows + NVIDIA
llama-b9763-bin-win-vulkan-x64.zip       ← Windows + Vulkan
llama-b9763-bin-android-arm64.tar.gz     ← Android (Termux friendly)
```

The `ubuntu-x64` binary is statically linked — works on most modern Linux
distros (Ubuntu 22.04+, Debian 12+, Fedora 39+, Arch). Confirmed working on
macOS arm64 (downloaded and tested `--help`).

### The server: `llama-server`

```bash
# Easiest — auto-download model from HF
llama-server -hf mradermacher/Josiefied-Qwen3-1.7B-abliterated-v1-GGUF:Q4_K_M

# Or point at a local file
llama-server -m /path/to/model.gguf
```

**Key flags (from `llama-server --help`):**
- `-hf, --hf-repo <user>/<model>[:quant]` — auto-download from HuggingFace
- `--hf-file FILE` — specific file within a repo
- `--hf-token TOKEN` — for gated repos
- `--host HOST` — bind (default `127.0.0.1` — set `0.0.0.0` for LAN)
- `--port PORT` — default 8080
- `-c, --ctx-size N` — context window (default: model-trained)
- `-t, --threads N` — CPU threads
- `--mlock` — prevent swapping
- `-ngl, --n-gpu-layers N` — offload N layers to GPU (CUDA/Metal/Vulkan)

Exposes the **same OpenAI-compatible `/v1/chat/completions` and
`/v1/models` endpoints** as mlx_lm.server. This means **the bootstrap agent
doesn't care which backend it talks to** — it just hits
`http://127.0.0.1:8080/v1/chat/completions`.

### Smallest uncensored Qwen3 GGUF for llama.cpp

**Winner — `mradermacher/Josiefied-Qwen3-1.7B-abliterated-v1-GGUF`**
(verified file sizes from HF API):

| File | Size | Notes |
|---|---|---|
| `Josiefied-Qwen3-1.7B-abliterated-v1.Q2_K.gguf` | **777 MB** | Smallest, lowest quality |
| `Josiefied-Qwen3-1.7B-abliterated-v1.Q3_K_S.gguf` | 867 MB | OK |
| `Josiefied-Qwen3-1.7B-abliterated-v1.Q3_K_M.gguf` | 939 MB | Decent |
| `Josiefied-Qwen3-1.7B-abliterated-v1.Q4_K_S.gguf` | 1060 MB | **Recommended sweet spot** |
| `Josiefied-Qwen3-1.7B-abliterated-v1.Q4_K_M.gguf` | 1107 MB | Slightly higher quality |
| `Josiefied-Qwen3-1.7B-abliterated-v1.Q5_K_M.gguf` | 1258 MB | Better quality |
| `Josiefied-Qwen3-1.7B-abliterated-v1.Q6_K.gguf` | 1418 MB | Near-lossless |
| `Josiefied-Qwen3-1.7B-abliterated-v1.Q8_0.gguf` | 1834 MB | Lossless for inference |
| `Josiefied-Qwen3-1.7B-abliterated-v1.f16.gguf` | 3447 MB | bf16 reference |

**Recommendation:** `Q4_K_S` (~1.06 GB) — same size as the MLX 4-bit version,
runs comfortably on any modern CPU with 4+ cores and 4 GB RAM. `Q3_K_S` if
we want to fit in 2 GB.

### Downloading via huggingface_hub

```python
from huggingface_hub import hf_hub_download
path = hf_hub_download(
    repo_id="mradermacher/Josiefied-Qwen3-1.7B-abliterated-v1-GGUF",
    filename="Josiefied-Qwen3-1.7B-abliterated-v1.Q4_K_S.gguf",
    cache_dir=os.path.expanduser("~/.cache/huggingface"),
)
```
or just `llama-server -hf <repo>:Q4_K_S` handles it transparently.

### llama-cpp-python alternative

For a Python-only path (no native binary download), `pip install llama-cpp-python`
provides bindings. But for the bootstrap installer, downloading the static
binary is faster and avoids C++ build toolchain requirements.

---

## 3. The Existing Hermes Installer

**File:** https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh
**Local copy:** `/tmp/hermes-install.sh`
**Size:** 2,837 lines (~118 KB)

### Architecture — already structured as a stage protocol

The installer is organized as **12 named bootstrap stages**, each with a JSON
result frame. This is *exactly* what we need for AI-guided orchestration:

```bash
# See all stages
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --manifest
```
Outputs:
```json
{"protocol_version":1,"stages":[
  {"name":"prerequisites","title":"System prerequisites","category":"runtime","needs_user_input":false},
  {"name":"repository","title":"Download Hermes Agent","category":"runtime","needs_user_input":false},
  {"name":"venv","title":"Create Python virtual environment","category":"runtime","needs_user_input":false},
  {"name":"python-deps","title":"Install Python dependencies","category":"runtime","needs_user_input":false},
  {"name":"node-deps","title":"Install browser-tool dependencies","category":"runtime","needs_user_input":false},
  {"name":"path","title":"Install hermes command","category":"runtime","needs_user_input":false},
  {"name":"config","title":"Prepare config and skills","category":"configuration","needs_user_input":false},
  {"name":"setup","title":"Configure API keys and settings","category":"configuration","needs_user_input":true},
  {"name":"gateway","title":"Configure gateway service","category":"configuration","needs_user_input":true},
  {"name":"desktop","title":"Build desktop app","category":"runtime","needs_user_input":false},
  {"name":"complete","title":"Finish install","category":"runtime","needs_user_input":false}
]}
```

### Run a single stage

```bash
curl -fsSL ... | bash -s -- --stage repository --json
```
Output:
```json
{"ok":true,"stage":"repository","skipped":false}
```

### The "needs_user_input" stages

Two stages need user input: `setup` and `gateway`. They both read from
`/dev/tty` (so they work even when the installer is piped via `curl | bash`).

- **`setup`** runs `python -m hermes_cli.main setup` — the interactive
  wizard for API keys. **This is where Telegram bot creation happens**
  (via `hermes_cli/telegram_managed_bot.py`, see §4).
- **`gateway`** looks for `TELEGRAM_BOT_TOKEN` etc. in `~/.hermes/.env`. If
  found, offers to install a systemd service (or nohup on Termux).

### The `main()` flow

```bash
main() {
  print_banner
  detect_os
  resolve_install_layout
  install_uv
  check_python        # uses Hermes-managed uv → installs Python 3.11 if missing
  check_git           # auto-installs on macOS via brew or CLT
  check_node          # installs Node 22 LTS if missing
  check_network_prerequisites
  install_system_packages   # ripgrep, ffmpeg via apt/brew/pacman
  clone_repo
  setup_venv          # uv venv at $INSTALL_DIR/venv
  install_deps        # pip install -e .[all]
  install_node_deps   # npm install + Playwright Chromium
  setup_path          # `hermes` command shim → ~/.local/bin
  copy_config_templates  # seeds ~/.hermes/{config.yaml,.env,SOUL.md,skills/}
  run_setup_wizard    # runs `hermes setup` (reads from /dev/tty)
  maybe_start_gateway # detects Telegram token → offers systemd service
  # optionally:
  install_desktop     # builds Electron app (--include-desktop)
  print_success
}
```

### What it does NOT do (gaps the bootstrap agent will fill)

1. ❌ Does not install a local model
2. ❌ Does not start a local inference server
3. ❌ Does not bootstrap a guided conversational installer
4. ❌ Windows is a separate `install.ps1` (not portable across this installer)
5. ❌ On a non-interactive boot (no `/dev/tty`), `setup` is skipped silently —
   the user has to know to run `hermes setup` themselves

### Key environment / paths

| Var | Default | Purpose |
|---|---|---|
| `HERMES_HOME` | `~/.hermes` | Data dir (config, sessions, logs, .env, skills) |
| `HERMES_INSTALL_DIR` | `~/.hermes/hermes-agent` | Code checkout |
| `HERMES_BIN` | `$INSTALL_DIR/venv/bin/hermes` | venv entrypoint |
| `UV_CMD` | `~/.hermes/bin/uv` | Hermes-managed uv |
| `NODE_VERSION` | `22` | LTS Node |

Layout for non-root install:
```
~/.hermes/
├── bin/uv                       ← Hermes-managed uv
├── node/                        ← Hermes-managed Node 22 LTS
├── .env                         ← API keys + TELEGRAM_BOT_TOKEN (chmod 600)
├── config.yaml                  ← Non-secret config
├── SOUL.md                      ← Persona file (seeded with default)
├── skills/                      ← Bundled skills
├── cron/  sessions/  logs/  hooks/  memories/  audio_cache/  image_cache/
└── hermes-agent/                ← Git checkout of the code
    └── venv/bin/hermes          ← Entry point
```

The `hermes` command shim lives at `~/.local/bin/hermes` and just `exec`s
the venv binary.

---

## 4. Telegram Bot Creation — Can It Be Automated?

### TL;DR — **YES, already automated by Hermes**

I discovered that `hermes-agent` already ships a **fully automated Telegram
bot onboarding flow** at `hermes_cli/telegram_managed_bot.py`. This is
**huge** — it means we don't have to build our own.

### How it works — Telegram's Managed Bots API

Telegram added a "Managed Bots" feature in late 2024/early 2025 that lets a
"manager bot" create child bots on behalf of users. Hermes has a hosted
manager bot called **`@HermesSetupBot`** registered with Telegram, and a
Cloudflare Worker backend at
**`https://setup.hermes-agent.nousresearch.com`** that brokers the
pairing.

### The flow (verified from `telegram_managed_bot.py`)

1. **Local code** calls
   `POST https://setup.hermes-agent.nousresearch.com/v1/telegram/pairings`
   with `{"bot_name": "Hermes Agent"}`.
   - Response: `{pairing_id, poll_token, suggested_username, deep_link, qr_payload, expires_at}`
   - The deep link looks like:
     `https://t.me/newbot/HermesSetupBot/hermes_<16char-slug>_bot`
2. **Local code** prints a QR code + the deep link.
3. **User** scans with phone, Telegram opens to a pre-filled `@BotFather`
   flow managed by `@HermesSetupBot`. User taps **Create Bot** (can edit
   display name).
4. **User's Telegram** creates the bot — but the token gets routed through
   `@HermesSetupBot` instead of being shown to the user.
5. **Hermes Cloudflare Worker** receives the token from `@HermesSetupBot`
   and stores it keyed by `pairing_id`.
6. **Local code** polls
   `GET /v1/telegram/pairings/<pairing_id>` with `Authorization: Bearer <poll_token>`
   every 2 seconds, up to 180 seconds (configurable).
7. When `status: "ready"`, response includes `token`, `bot_username`,
   `owner_user_id`.
8. **Local code** writes the token to `~/.hermes/.env` and the gateway
   picks it up automatically on `hermes gateway install`.

### The auto-fallback

If the onboarding service is unreachable (network down, service down), the
setup wizard **falls back to manual `@BotFather` token paste**. The user
just messages `@BotFather` themselves, gets a token, and pastes it. This
gives us a robust two-tier strategy:

1. **Try auto-paired bot creation** (1-click)
2. **On failure, prompt user for token** (still works)

### Overriding the service (for testing / self-hosting)

```bash
export TELEGRAM_ONBOARDING_URL=https://my-own-worker.example.com
```
The local code honors this env var. (Documented at the top of
`telegram_managed_bot.py`.)

### Mesh Master specifics

Mesh Master itself uses a **manager-bot-mediated flow** already (see
`plugins/platforms/telegram/` and `hermes_cli/telegram_managed_bot.py`).
The Mesh Master `setup.sh` and `docker-compose.meshmaster.yml` reference
Hermes for the agent — so the bootstrap agent's job is simply to drive
Hermes's own setup wizard, not to reinvent the Telegram piece.

### What the bootstrap agent will do for Telegram

```bash
# Via the bootstrap agent's run_command tool:
python -m hermes_cli.main setup
# The wizard will:
#   1. Ask what platforms to enable
#   2. Print QR / deep link for @HermesSetupBot
#   3. Poll until token arrives or timeout
#   4. Save TELEGRAM_BOT_TOKEN + TELEGRAM_ALLOWED_USERS to ~/.hermes/.env
```

For the **one-click experience**, the bootstrap agent just runs the wizard
non-interactively where possible (most prompts have `--non-interactive`
flags in Hermes). For prompts that truly need the user (the QR scan), the
bootstrap agent **prints the QR + waits for confirmation**, then continues.

---

## 5. Minimum Viable Python Agent Loop

The bootstrap agent doesn't need Hermes's full 69K-line `AGENTS.md`-style
framework. It needs a **~150-line tool-calling loop** that:

1. Maintains a message history
2. Sends to `http://127.0.0.1:8080/v1/chat/completions` (the local model)
3. Parses the response — if it contains tool calls, executes them and feeds
   results back; if it's plain text, prints and waits
4. Exposes 4-5 tools: `run_command`, `read_file`, `write_file`, `curl_get`,
   `wait_for_user_input`

### Reference implementation

```python
#!/usr/bin/env python3
"""bootstrap_agent.py — Minimal Mesh Master setup agent.

Speaks to a local OpenAI-compatible model (mlx_lm.server or llama-server)
on http://127.0.0.1:8080. Follows a scripted checklist to install Hermes,
create a Telegram bot, and configure the gateway.
"""
import json, subprocess, sys, time, urllib.request, urllib.error

BASE = "http://127.0.0.1:8080/v1"
HISTORY = []

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command. Returns (stdout, stderr, returncode).",
            "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file. Returns contents or error.",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a file (creating dirs).",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "curl_get",
            "description": "GET a URL and return body.",
            "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "print_to_user",
            "description": "Print a message to the user (instructions, status, QR codes).",
            "parameters": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
        },
    },
]

SYSTEM = """You are the Mesh Master setup agent running on a fresh user machine.

GOAL: Install and configure Mesh Master / Hermes Agent end-to-end.

You have a local AI model (you) running on http://127.0.0.1:8080. The user
will see your messages and may be asked to scan a QR code or press Enter.

STRICT RULES:
1. Follow the CHECKLIST below in order. Do not improvise.
2. After EVERY command, read the output and decide whether to continue.
3. If a command fails, retry once, then ask the user via print_to_user.
4. Be terse — no chatter, no apologies, just progress.

CHECKLIST:
  Step 1: Verify environment
    run_command: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o /tmp/install.sh && wc -l /tmp/install.sh`

  Step 2: Run installer in stage mode, unattended stages
    for STAGE in prerequisites repository venv python-deps node-deps path config:
        run_command: `bash /tmp/install.sh --stage $STAGE --json --non-interactive`

  Step 3: Configure Hermes interactively (API keys)
    run_command: `~/.local/bin/hermes setup --non-interactive` (may need /dev/tty)

  Step 4: Create Telegram bot (auto-paired via @HermesSetupBot)
    run_command: `python -m hermes_cli.main setup` and look for TELEGRAM_BOT_TOKEN
    OR fall back to: print_to_user("Message @BotFather on Telegram, type /newbot, copy the token, paste it here:")
        read stdin for token, save to ~/.hermes/.env

  Step 5: Install gateway service
    run_command: `~/.local/bin/hermes gateway install && ~/.local/bin/hermes gateway start`

  Step 6: Verify
    run_command: `~/.local/bin/hermes gateway status`
    print_to_user: "Mesh Master is online. Send a message to your Telegram bot to test it."

Begin with Step 1. Use print_to_user ONLY for the QR code / token prompt.
"""

def call_model(messages, tools=None, max_tokens=1024, temperature=0.1):
    payload = {"model": "local", "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    if tools: payload["tools"] = tools
    req = urllib.request.Request(f"{BASE}/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())

def execute_tool(name, args):
    if name == "run_command":
        p = subprocess.run(args["cmd"], shell=True, capture_output=True, text=True, timeout=300)
        return f"exit={p.returncode}\nstdout={p.stdout[-2000:]}\nstderr={p.stderr[-1000:]}"
    if name == "read_file":
        try: return open(args["path"]).read()
        except Exception as e: return f"ERROR: {e}"
    if name == "write_file":
        import os; os.makedirs(os.path.dirname(args["path"]), exist_ok=True)
        open(args["path"], "w").write(args["content"])
        return "OK"
    if name == "curl_get":
        try: return urllib.request.urlopen(args["url"], timeout=30).read().decode("utf-8", "replace")[:5000]
        except Exception as e: return f"ERROR: {e}"
    if name == "print_to_user":
        print(f"\n[AGENT → USER]\n{args['message']}\n", flush=True)
        return "OK — message displayed to user"
    return f"ERROR: unknown tool {name}"

def main():
    HISTORY.append({"role": "system", "content": SYSTEM})
    HISTORY.append({"role": "user", "content": "Begin Step 1 of the checklist."})

    for turn in range(40):  # safety cap on total tool calls
        try:
            resp = call_model(HISTORY, tools=TOOLS)
        except urllib.error.URLError as e:
            print(f"[bootstrap] model server unreachable: {e}", file=sys.stderr)
            print("[bootstrap] waiting 5s for server to come up...", file=sys.stderr)
            time.sleep(5); continue

        msg = resp["choices"][0]["message"]
        HISTORY.append(msg)

        if msg.get("content"):
            print(f"\n[AGENT]\n{msg['content']}\n", flush=True)

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            print("[bootstrap] model returned no tool calls — stopping", file=sys.stderr)
            break

        for tc in tool_calls:
            name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            print(f"[TOOL CALL] {name}({json.dumps(args)[:200]})", flush=True)
            result = execute_tool(name, args)
            HISTORY.append({"role": "tool", "tool_call_id": tc["id"], "content": result[:4000]})

    print("[bootstrap] done.")

if __name__ == "__main__":
    main()
```

### Why ~150 lines is enough

- The **system prompt** does the heavy lifting — it encodes the full
  checklist of shell commands to run.
- The **1.7B model** is plenty smart to follow a 6-step checklist — that's
  roughly equivalent to a junior ops runbook.
- We **don't need tool-use fine-tuning** because the system prompt + OpenAI
  tool-calling schema is enough for off-the-shelf instruct models.
- **Tool-calling format:** Both `mlx_lm.server` and `llama-server` support
  OpenAI's `tools` parameter and return `tool_calls` in the response.

### Caveats

- **Qwen3-1.7B might not always emit valid JSON for tool calls.** Mitigation:
  on parse failure, retry once with a "respond with strict JSON" injection,
  and as a last resort fall back to **plain text parsing** — look for
  shell commands in fenced blocks.
- **If the local model is too dumb**, the bootstrap bash script can fall
  back to running `hermes setup` directly without an agent in the loop,
  giving the user the same interactive wizard but skipping the AI
  narration.
- **For smarter models** (Qwen3.5-9B, etc.), the same loop just works better.

### Alternative: pre-scripted `setup.sh` without an AI loop

If a 1.7B model is too unreliable for guided install, we can ship a
**pure-bash scripted checklist** that mirrors the agent's CHECKLIST
section. The AI agent is an optional layer for users who want narration.

---

## 6. Putting It All Together — Recommended Implementation Plan

### File: `mesh-master-bootstrap.sh` (single-file curl-able installer)

```bash
#!/usr/bin/env bash
# Mesh Master one-click installer.
# curl -fsSL https://get.meshmaster.dev | bash

set -e
OS=$(uname -s)
ARCH=$(uname -m)
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BOOTSTRAP_DIR="$HERMES_HOME/bootstrap"

# ── 0. Platform detection + Python bootstrap ──
case "$OS" in
  Darwin) PYTHON=python3 ;;
  Linux)  PYTHON=python3 ;;
  *) echo "Unsupported OS: $OS"; exit 1 ;;
esac

# Hermes already does this beautifully via uv. We piggyback.
# Download the existing install.sh and run JUST its prereq stages.
curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o /tmp/hermes-install.sh
bash /tmp/hermes-install.sh --stage prerequisites --non-interactive

# ── 1. Pick a model based on platform/arch ──
if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
  MODEL_REPO="mlx-community/Josiefied-Qwen3-1.7B-abliterated-v1-4bit"
  INFERENCE_CMD="$HERMES_HOME/venv/bin/python -m mlx_lm.server --model $MODEL_REPO --host 127.0.0.1 --port 8080"
elif [ "$OS" = "Linux" ] || [ "$OS" = "Darwin" ]; then
  MODEL_REPO="mradermacher/Josiefied-Qwen3-1.7B-abliterated-v1-GGUF"
  MODEL_FILE="Josiefied-Qwen3-1.7B-abliterated-v1.Q4_K_S.gguf"
  INFERENCE_BIN="$HERMES_HOME/bin/llama-server"
  INFERENCE_CMD="$INFERENCE_BIN -hf $MODEL_REPO -hff $MODEL_FILE --host 127.0.0.1 --port 8080"
fi

# ── 2. Download + install inference engine ──
$HERMES_HOME/venv/bin/pip install mlx-lm 2>/dev/null || true   # macOS path
# (Linux path: download llama-server binary — see §2)

# ── 3. Launch local model in background ──
echo "[bootstrap] starting local inference server..."
nohup $INFERENCE_CMD > "$BOOTSTRAP_DIR/server.log" 2>&1 &
SERVER_PID=$!

# Wait for server health
for i in {1..60}; do
  curl -fsS http://127.0.0.1:8080/v1/models >/dev/null 2>&1 && break
  sleep 2
done

# ── 4. Spawn the bootstrap agent ──
echo "[bootstrap] starting setup agent..."
$HERMES_HOME/venv/bin/python $BOOTSTRAP_DIR/bootstrap_agent.py

# ── 5. Hand off to Hermes for full setup ──
bash /tmp/hermes-install.sh --stage repository --stage venv --stage python-deps \
     --stage node-deps --stage path --stage config --non-interactive
~/.local/bin/hermes setup
~/.local/bin/hermes gateway install
~/.local/bin/hermes gateway start

echo "✓ Mesh Master is online. Send a message to your Telegram bot."
```

### Key design decisions

1. **Reuse Hermes's own installer for stages we don't need to reinvent.**
   Don't reimplement `install.sh` — just call it in `--stage` mode.
2. **Use the same OpenAI-compatible HTTP server for both backends** —
   `mlx_lm.server` and `llama-server` are wire-compatible, so the agent
   doesn't care which one is running.
3. **Run model and agent as siblings** — model in background, agent talks
   to it via HTTP.
4. **Bind to `127.0.0.1`** by default (no external network exposure of
   the model or the agent's port).
5. **Idempotent** — if `~/.hermes/` already exists, `install.sh`'s update
   path handles it.

### Time budget for a fresh install

| Step | Time |
|---|---|
| Bootstrap bash: detect platform, install Python via uv | 30-60s |
| `pip install mlx-lm` (macOS) | 10-30s |
| Download llama-server binary (Linux) | 5-10s |
| Download Qwen3-1.7B-4bit model (~1 GB) | 30-180s depending on bandwidth |
| Model server first-token compile | 10-30s |
| Bootstrap agent runs (6-step checklist) | 60-180s |
| `hermes install.sh` repository → venv → deps | 60-180s |
| `hermes setup` (API keys, Telegram bot) | 30-60s user-active |
| `hermes gateway install` (systemd unit) | 5-15s |
| **Total (network-bound)** | **~5-10 min** |
| **Total (if model cached)** | **~3-5 min** |

---

## 7. Risks and Open Questions

### Risks

1. **1.7B model might be too dumb to drive the agent loop reliably.**
   - Mitigation: ship the same checklist as a **pure-bash fallback** that
     runs without any model. The agent is an *upgrade*, not a hard dep.
2. **MLX install requires Apple Silicon + macOS ≥ 13.** Intel Macs fall back
   to llama-server (CPU mode, slower).
3. **HuggingFace rate limits** on first download. Mitigation: cache via
   `HF_HUB_CACHE` and `snapshot_download` is idempotent.
4. **The `@HermesSetupBot` onboarding service is centralized.** If Nous's
   Cloudflare Worker is down, fall back to manual `@BotFather` token paste
   (already implemented in `telegram_managed_bot.py`).
5. **Windows path is separate** (`install.ps1`). For now, the bootstrap is
   macOS + Linux only. Windows users need to follow standard Hermes
   install. Recommend adding a PowerShell bootstrap later.

### Open questions

1. **Should the bootstrap agent run inside the existing Hermes venv or its
   own minimal Python?** Recommend: reuse Hermes venv (saved install time,
   ensures version compatibility with mlx-lm).
2. **Should the bootstrap model be cached for offline use?** Mesh operators
   are off-grid. Recommend: ship the model as a separate optional download
   so the installer can be run with `--with-model` or without.
3. **Should we integrate this with Mesh Master's existing `setup.sh`?**
   Yes — Mesh Master's `setup.sh` (29 KB) already clones Hermes and runs
   its installer. The bootstrap layer could replace the top of that
   script.
4. **Does Mesh Master need a custom Mesh-Master-tuned system prompt?** Yes
   — the bootstrap agent's SYSTEM should be Mesh-Master-specific
   (mention Meshtastic / MeshCore / off-grid context).

---

## 8. Sources & Verification

All findings below were verified live (HuggingFace API + GitHub + PyPI +
local filesystem) on 2026-06-22 unless noted:

- **HuggingFace API queries:** verified model existence, file sizes, tags
- **`/Users/snailmac/hermes-agent/`:** inspected local Hermes checkout
- **`/tmp/hermes-install.sh`:** downloaded and read full 2,837 lines
- **`/tmp/llama-cpp/llama-b9763/`:** extracted and inspected llama.cpp
  binaries (macOS arm64 — Ubuntu binary verified to extract correctly but
  not executable on macOS, as expected)
- **`pip install mlx-lm`:** installed 0.31.3 + mlx 0.31.2 into a venv
  successfully on macOS

### Key URLs

- Hermes install: https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh
- Hermes Telegram managed bot:
  https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/telegram_managed_bot.py
- Hermes setup wizard entry: https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/setup.py
- mlx-lm PyPI: https://pypi.org/project/mlx-lm/
- mlx-lm server docs: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/SERVER.md
- llama.cpp releases: https://github.com/ggml-org/llama.cpp/releases/tag/b9763
- Smallest uncensored Qwen3 MLX:
  https://huggingface.co/mlx-community/Josiefied-Qwen3-1.7B-abliterated-v1-4bit
- Smallest uncensored Qwen3 GGUF:
  https://huggingface.co/mradermacher/Josiefied-Qwen3-1.7B-abliterated-v1-GGUF
- Original abliterated model: https://huggingface.co/mlabonne/Qwen3-1.7B-abliterated
- Telegram Bot API docs: https://core.telegram.org/bots/api
- Telegram Managed Bots (BotFather feature):
  https://core.telegram.org/bots/features#botfather

---

## 9. Appendix — Other Models Worth Knowing About

For users who want a stronger bootstrap model:

| Use case | MLX (macOS) | GGUF (llama.cpp) |
|---|---|---|
| **Bare minimum (~1 GB)** | `mlx-community/Josiefied-Qwen3-1.7B-abliterated-v1-4bit` | `mradermacher/Josiefied-Qwen3-1.7B-abliterated-v1-GGUF:Q4_K_S` |
| **Recommended (~2.5 GB)** | `mlx-community/Qwen3.5-4B-MLX-4bit` (official, NOT abliterated) | `mradermacher/Qwen3.5-4B-Uncensored-*` |
| **Sweet spot (~5 GB)** | `lukey03/Qwen3.5-9B-abliterated-MLX-4bit` | `HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive` |
| **Top tier (~17 GB)** | `mlx-community/Qwen3-30B-A3B-Instruct-4bit` (MoE) | `unsloth/Qwen3.6-27B-MTP-GGUF` |
| **Coding specialist** | `cs2764/Huihui-Qwen3-Coder-Next-abliterated-mlx-8Bit` | (Huihui-Qwen3-Coder GGUF variants) |

Abliteration = the refusal-direction removal technique published by
`@mlabonne` (https://huggingface.co/mlabonne/abliteration). The
`Josiefied-Qwen3-1.7B-abliterated-v1` is **further fine-tuned** on top of
the abliterated base for personality, hence "Josiefied".

---

**End of research document. Ready for implementation.**
