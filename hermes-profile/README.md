# Mesh Master Hermes Profile

This directory contains the complete Hermes agent profile for the Mesh Master bot.

## Structure

```
hermes-profile/
├── SOUL.md                 # Agent identity & behavior rules
├── config.yaml.template    # Sanitized config (no secrets)
├── install-profile.sh      # One-command installer
└── skills/
    └── mesh-master/
        ├── SKILL.md        # Mesh Master domain knowledge
        └── references/
            ├── architecture.md
            └── commands.md
```

## Quick Start

```bash
# From the Mesh-Master repo root:
./hermes-profile/install-profile.sh
```

This copies everything to `~/.hermes-supabot/profiles/meshmaster/`. Then:

1. Edit `~/.hermes-supabot/profiles/meshmaster/config.yaml` — add your Telegram bot token
2. Edit `~/.hermes-supabot/profiles/meshmaster/.env` — add API keys if needed
3. Start the gateway: `hermes --profile meshmaster gateway run`

## What's Included

- **SOUL.md** — Agent identity as "Mesh Master", English-only enforcement, two-tier AI system docs
- **mesh-master skill** — Full reference for all Mesh Master commands, architecture, and subsystems
- **Config template** — Pre-configured for Qwen3.6 via MLX, auto-approve (yolo mode), port 8650

## Security

- `config.yaml.template` contains **no secrets** — safe for public repo
- Real `config.yaml` is created locally by the installer and should **never** be committed
- API keys go in `.env` (also never committed)
- The `.gitignore` in the repo root excludes `config.yaml` and `.env` files
