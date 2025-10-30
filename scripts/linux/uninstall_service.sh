#!/usr/bin/env bash

# Mesh Master Linux/Debian Systemd Service Uninstallation Script

set -e

# Verify we're NOT on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "❌ This script is for Linux/Debian only"
    echo "For macOS, use: ./scripts/macos/uninstall_service.sh"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  Mesh Master Linux Service Uninstaller"
echo "=========================================="
echo ""

# Check if running with sudo/root
if [[ $EUID -ne 0 ]]; then
    echo -e "${YELLOW}⚠️  This script needs sudo privileges${NC}"
    echo ""
    echo "Please run with sudo:"
    echo -e "${YELLOW}sudo ./scripts/linux/uninstall_service.sh${NC}"
    exit 1
fi

SERVICE_FILE="/etc/systemd/system/mesh-ai.service"

# Check if service is installed
if [[ ! -f "$SERVICE_FILE" ]]; then
    echo -e "${YELLOW}⚠️  Mesh Master service is not installed${NC}"
    echo ""
    echo "Service file not found: $SERVICE_FILE"
    exit 0
fi

echo "Found service file: $SERVICE_FILE"
echo ""

# Stop the service if running
echo "Stopping mesh-ai service..."
systemctl stop mesh-ai 2>/dev/null || true

# Disable the service
echo "Disabling mesh-ai service..."
systemctl disable mesh-ai 2>/dev/null || true

# Remove service file
echo "Removing service file..."
rm -f "$SERVICE_FILE"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Remove desktop shortcuts (run as original user, not root)
echo "Removing desktop shortcuts..."
ORIGINAL_USER="${SUDO_USER:-$USER}"
USER_HOME=$(eval echo ~$ORIGINAL_USER)
DESKTOP="$USER_HOME/Desktop"
removed_count=0

if [[ -f "$DESKTOP/start-mesh-master.desktop" ]]; then
    rm -f "$DESKTOP/start-mesh-master.desktop"
    ((removed_count++))
fi

if [[ -f "$DESKTOP/stop-mesh-master.desktop" ]]; then
    rm -f "$DESKTOP/stop-mesh-master.desktop"
    ((removed_count++))
fi

# Also remove the launcher shortcut created by setup.sh
if [[ -f "$DESKTOP/Mesh Master.desktop" ]]; then
    rm -f "$DESKTOP/Mesh Master.desktop"
    ((removed_count++))
fi

if [[ $removed_count -gt 0 ]]; then
    echo -e "${GREEN}✓${NC} Removed $removed_count desktop shortcut(s)"
else
    echo -e "${YELLOW}⚠️${NC} No desktop shortcuts found"
fi

# Kill any running Mesh Master processes
echo "Stopping any running Mesh Master processes..."
pkill -f "python.*mesh-master.py" 2>/dev/null || true
pkill -f "mesh-master.py" 2>/dev/null || true
ps aux | grep "[m]esh-master.py" | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 1
echo -e "${GREEN}✓${NC} Processes stopped"

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
echo "Your data and config files are preserved."
echo ""
echo "To completely remove Mesh Master (including all data):"
echo -e "  ${YELLOW}cd .. && rm -rf Mesh-Master${NC}"
echo ""
echo "To reinstall the service, run:"
echo "  sudo ./scripts/linux/install_service.sh"
echo ""
