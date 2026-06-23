#!/usr/bin/env bash
# install-profile.sh — Install the Mesh Master Hermes profile
#
# Usage: ./hermes-profile/install-profile.sh
#
# Copies SOUL.md, skills, and config template to the Hermes profile directory.
# Does NOT overwrite existing config.yaml — only creates it from template if missing.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes-supabot}"
PROFILE_DIR="$HERMES_HOME/profiles/meshmaster"

echo "🐌 Installing Mesh Master Hermes profile..."
echo "   Source: $SCRIPT_DIR"
echo "   Target: $PROFILE_DIR"
echo ""

# Create profile directory structure
mkdir -p "$PROFILE_DIR/skills"

# Copy SOUL.md (always overwrite — this is the identity file)
cp "$SCRIPT_DIR/SOUL.md" "$PROFILE_DIR/SOUL.md"
echo "  ✅ SOUL.md copied"

# Copy skills
if [ -d "$SCRIPT_DIR/skills" ]; then
  cp -r "$SCRIPT_DIR/skills/"* "$PROFILE_DIR/skills/" 2>/dev/null || true
  echo "  ✅ Skills copied"
fi

# Copy config from template only if it doesn't exist (preserve existing secrets)
if [ ! -f "$PROFILE_DIR/config.yaml" ]; then
  cp "$SCRIPT_DIR/config.yaml.template" "$PROFILE_DIR/config.yaml"
  echo "  ✅ config.yaml created from template"
  echo ""
  echo "  ⚠️  EDIT $PROFILE_DIR/config.yaml to add:"
  echo "     - Telegram bot token (from @BotFather)"
  echo "     - Model path (if different from default Qwen3.6)"
  echo "     - MLX endpoint (if not localhost:8087)"
else
  echo "  ⏭️  config.yaml already exists — skipping (preserving existing config)"
fi

# Create .env if it doesn't exist
if [ ! -f "$PROFILE_DIR/.env" ]; then
  touch "$PROFILE_DIR/.env"
  echo "  ✅ .env created (add API keys here)"
else
  echo "  ⏭️  .env already exists — skipping"
fi

echo ""
echo "🎉 Profile installed!"
echo ""
echo "Next steps:"
echo "  1. Edit $PROFILE_DIR/config.yaml — add your Telegram bot token"
echo "  2. Edit $PROFILE_DIR/.env — add any API keys"
echo "  3. Start the gateway:"
echo "     hermes --profile meshmaster gateway run"
echo "  4. Or set up as a launchd service (see docs/DEPLOYMENT.md)"
