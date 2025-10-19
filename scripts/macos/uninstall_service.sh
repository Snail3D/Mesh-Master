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

# Remove desktop shortcuts
echo "Removing desktop shortcuts..."
DESKTOP="$HOME/Desktop"
removed_count=0

if [[ -d "$DESKTOP/Start Mesh Master.app" ]]; then
    rm -rf "$DESKTOP/Start Mesh Master.app"
    ((removed_count++))
fi

if [[ -d "$DESKTOP/Stop Mesh Master.app" ]]; then
    rm -rf "$DESKTOP/Stop Mesh Master.app"
    ((removed_count++))
fi

if [[ $removed_count -gt 0 ]]; then
    echo -e "${GREEN}✓${NC} Removed $removed_count desktop shortcut(s)"
else
    echo -e "${YELLOW}⚠️${NC} No desktop shortcuts found"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Mesh Master Service Uninstalled"
echo "==========================================${NC}"
echo ""
echo "The service has been removed:"
echo "  • Service stopped and disabled"
echo "  • Auto-start on boot disabled"
echo "  • Desktop shortcuts removed"
echo ""
echo "Your data and config files are preserved."
echo ""
echo "To run manually:"
echo "  cd /path/to/Mesh-Master"
echo "  python3 mesh-master.py"
echo ""
