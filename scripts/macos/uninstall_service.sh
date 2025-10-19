#!/usr/bin/env bash

# Mesh Master macOS LaunchAgent Uninstallation Script

set -e

# Verify we're actually on macOS before proceeding
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  Mesh Master macOS Service Uninstaller"
echo "=========================================="
echo ""

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script is for macOS only${NC}"
    exit 1
fi

PLIST_PATH="$HOME/Library/LaunchAgents/com.meshmaster.plist"

# Check if service is installed
if [[ ! -f "$PLIST_PATH" ]]; then
    echo -e "${YELLOW}⚠️  Mesh Master service is not installed${NC}"
    exit 0
fi

echo "Found service at: $PLIST_PATH"
echo ""

# Confirm uninstallation
read -p "Are you sure you want to uninstall the Mesh Master service? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Unload the service
echo "Stopping and unloading service..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true

# Remove the plist file
echo "Removing plist file..."
rm "$PLIST_PATH"

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Mesh Master Service Uninstalled"
echo "==========================================${NC}"
echo ""
echo "The service has been removed."
echo "Mesh Master will no longer start automatically."
echo ""
echo "To run manually:"
echo "  cd /path/to/mesh-ai"
echo "  python3 mesh-master.py"
echo ""
