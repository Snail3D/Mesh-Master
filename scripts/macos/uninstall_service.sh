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

# Kill any running Mesh Master processes
echo "Stopping any running Mesh Master processes..."
pkill -f "python.*mesh-master.py" 2>/dev/null || true
pkill -f "mesh-master.py" 2>/dev/null || true
ps aux | grep "[m]esh-master.py" | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 1
echo -e "${GREEN}✓${NC} Processes stopped"

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

# Also remove the launcher shortcut created by setup.sh
if [[ -d "$DESKTOP/Mesh Master.app" ]]; then
    rm -rf "$DESKTOP/Mesh Master.app"
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
echo "  • All processes stopped"
echo ""

# Get the Mesh-Master directory (two levels up from scripts/macos)
MESH_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)

# Check for AUTO_DELETE env var (set by dashboard)
if [[ "$AUTO_DELETE" == "true" ]]; then
    echo "Auto-deleting Mesh Master directory..."
    cd "$HOME" 2>/dev/null || cd /tmp
    sleep 2
    rm -rf "$MESH_DIR" 2>/dev/null
    echo -e "${GREEN}✓${NC} Mesh Master directory deleted: $MESH_DIR"
    echo ""
    echo "Mesh Master has been completely removed!"
else
    # Interactive mode - delete with countdown
    echo ""
    echo -e "${YELLOW}⚠️  DIRECTORY DELETION IN PROGRESS${NC}"
    echo ""
    echo "The Mesh Master directory will be DELETED:"
    echo -e "  ${BLUE}$MESH_DIR${NC}"
    echo ""
    echo "This includes:"
    echo "  • config.json (your settings and passwords)"
    echo "  • data/ (logs, reports, mail, saved contexts)"
    echo "  • All source code"
    echo ""
    echo -e "${RED}Deleting in 5 seconds... Press Ctrl+C to cancel!${NC}"
    echo ""

    # Countdown
    for i in 5 4 3 2 1; do
        echo -ne "  ${i}... \r"
        sleep 1
    done
    echo ""

    echo "Deleting Mesh Master directory..."
    cd "$HOME" 2>/dev/null || cd /tmp
    sleep 1
    rm -rf "$MESH_DIR" 2>/dev/null

    if [[ ! -d "$MESH_DIR" ]]; then
        echo -e "${GREEN}✓${NC} Mesh Master directory deleted: $MESH_DIR"
        echo ""
        echo "Mesh Master has been completely removed!"
    else
        echo -e "${RED}❌${NC} Failed to delete directory. Please run manually:"
        echo -e "  ${YELLOW}rm -rf \"$MESH_DIR\"${NC}"
    fi
fi
echo ""
