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
    echo -e "${YELLOW}⚠️  Mesh Master systemd service is not installed${NC}"
    echo ""
    echo "Will still clean up desktop shortcuts and processes..."
    echo ""
else
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

    echo -e "${GREEN}✓${NC} Service removed"
    echo ""
fi

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

# Get the Mesh-Master directory (try multiple methods)
# Method 0: Use hint from parent script if available
if [[ -n "$MESH_DIR_HINT" ]] && [[ -d "$MESH_DIR_HINT" ]] && [[ -f "$MESH_DIR_HINT/mesh-master.py" ]]; then
    MESH_DIR="$MESH_DIR_HINT"
else
    # Method 1: From script location
    MESH_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)

    # Method 2: If that failed, try from current directory
    if [[ -z "$MESH_DIR" ]] || [[ ! -d "$MESH_DIR" ]]; then
        # Check if we're already in Mesh-Master directory
        if [[ -f "mesh-master.py" ]] && [[ -d "scripts" ]]; then
            MESH_DIR=$(pwd)
        # Check if we're in scripts/ subdirectory
        elif [[ -f "../mesh-master.py" ]]; then
            MESH_DIR=$(cd .. && pwd)
        # Check if we're in scripts/linux/ subdirectory
        elif [[ -f "../../mesh-master.py" ]]; then
            MESH_DIR=$(cd ../.. && pwd)
        fi
    fi
fi

# CRITICAL SAFETY CHECK: Ensure MESH_DIR is valid and not a system directory
if [[ -z "$MESH_DIR" ]] || [[ "$MESH_DIR" == "/" ]] || [[ "$MESH_DIR" == "/usr" ]] || [[ "$MESH_DIR" == "/etc" ]] || [[ "$MESH_DIR" == "/var" ]] || [[ "$MESH_DIR" == "/home" ]] || [[ "$MESH_DIR" == "/root" ]]; then
    echo -e "${RED}❌ ERROR: Could not safely detect Mesh Master directory${NC}"
    echo "Detected path: $MESH_DIR"
    echo ""
    echo "To manually remove Mesh Master, run from inside the Mesh-Master directory:"
    echo -e "  ${YELLOW}cd /path/to/Mesh-Master && rm -rf \"\$(pwd)\"${NC}"
    echo ""
    exit 1
fi

# Additional safety: Check if directory name contains "Mesh-Master" or "mesh-master"
if [[ ! "$MESH_DIR" =~ [Mm]esh-[Mm]aster ]]; then
    echo -e "${RED}❌ ERROR: Directory path doesn't look like Mesh Master${NC}"
    echo "Detected path: $MESH_DIR"
    echo ""
    echo "For safety, refusing to delete. To manually remove:"
    echo -e "  ${YELLOW}rm -rf \"$MESH_DIR\"${NC}"
    echo ""
    exit 1
fi

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
