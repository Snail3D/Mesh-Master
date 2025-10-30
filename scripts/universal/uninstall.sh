#!/usr/bin/env bash

# Mesh Master Universal Uninstallation Script
# Can be run standalone (curl | bash) or from within the repo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  Mesh Master Universal Uninstaller"
echo "=========================================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux"* ]]; then
    PLATFORM="Linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="Windows"
else
    echo -e "${RED}❌ Unknown platform: $OSTYPE${NC}"
    exit 1
fi

echo -e "Detected platform: ${BLUE}$PLATFORM${NC}"
echo ""

# Try to find the script path (if running from repo)
if [[ -n "${BASH_SOURCE[0]}" ]] && [[ -f "${BASH_SOURCE[0]}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    if [[ "$PLATFORM" == "macOS" ]]; then
        SCRIPT_PATH="$SCRIPT_DIR/macos/uninstall_service.sh"
    elif [[ "$PLATFORM" == "Linux" ]]; then
        SCRIPT_PATH="$SCRIPT_DIR/linux/uninstall_service.sh"
    elif [[ "$PLATFORM" == "Windows" ]]; then
        SCRIPT_PATH="$SCRIPT_DIR/windows/uninstall_service.bat"
    fi
fi

# If script exists, use it
if [[ -n "$SCRIPT_PATH" ]] && [[ -f "$SCRIPT_PATH" ]]; then
    echo -e "Using uninstaller: ${BLUE}$SCRIPT_PATH${NC}"
    echo ""

    if [[ "$PLATFORM" == "macOS" ]]; then
        bash "$SCRIPT_PATH"
    elif [[ "$PLATFORM" == "Linux" ]]; then
        if [[ $EUID -ne 0 ]]; then
            echo -e "${YELLOW}Elevating to root with sudo...${NC}"
            echo ""
            sudo bash "$SCRIPT_PATH"
        else
            bash "$SCRIPT_PATH"
        fi
    elif [[ "$PLATFORM" == "Windows" ]]; then
        echo -e "${YELLOW}⚠️  Windows Setup${NC}"
        echo ""
        echo "Please run as Administrator:"
        echo -e "${BLUE}powershell -ExecutionPolicy Bypass -Command \"& '$SCRIPT_PATH'\"${NC}"
        echo ""
    fi
else
    # Standalone mode - do the uninstall inline
    echo -e "${YELLOW}Running standalone uninstaller...${NC}"
    echo ""

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

    if [[ "$PLATFORM" == "Linux" ]]; then
        # Linux .desktop files
        for shortcut in "Mesh Master.desktop" "Start Mesh Master.desktop" "Stop Mesh Master.desktop"; do
            if [[ -f "$DESKTOP/$shortcut" ]]; then
                rm -f "$DESKTOP/$shortcut"
                ((removed_count++))
            fi
        done
    elif [[ "$PLATFORM" == "macOS" ]]; then
        # macOS .app bundles
        for shortcut in "Mesh Master.app" "Start Mesh Master.app" "Stop Mesh Master.app"; do
            if [[ -d "$DESKTOP/$shortcut" ]]; then
                rm -rf "$DESKTOP/$shortcut"
                ((removed_count++))
            fi
        done
    fi

    if [[ $removed_count -gt 0 ]]; then
        echo -e "${GREEN}✓${NC} Removed $removed_count desktop shortcut(s)"
    else
        echo -e "${YELLOW}⚠️${NC} No desktop shortcuts found"
    fi

    # Handle systemd service (Linux)
    if [[ "$PLATFORM" == "Linux" ]] && [[ -f "/etc/systemd/system/mesh-ai.service" ]]; then
        echo ""
        echo "Found systemd service. Removing..."

        if [[ $EUID -ne 0 ]]; then
            echo -e "${YELLOW}⚠️  Need sudo to remove systemd service${NC}"
            sudo systemctl stop mesh-ai 2>/dev/null || true
            sudo systemctl disable mesh-ai 2>/dev/null || true
            sudo rm -f /etc/systemd/system/mesh-ai.service
            sudo systemctl daemon-reload
        else
            systemctl stop mesh-ai 2>/dev/null || true
            systemctl disable mesh-ai 2>/dev/null || true
            rm -f /etc/systemd/system/mesh-ai.service
            systemctl daemon-reload
        fi

        echo -e "${GREEN}✓${NC} Systemd service removed"
    fi

    # Handle LaunchAgent (macOS)
    if [[ "$PLATFORM" == "macOS" ]] && [[ -f "$HOME/Library/LaunchAgents/com.meshmaster.plist" ]]; then
        echo ""
        echo "Found LaunchAgent service. Removing..."
        launchctl unload "$HOME/Library/LaunchAgents/com.meshmaster.plist" 2>/dev/null || true
        rm "$HOME/Library/LaunchAgents/com.meshmaster.plist"
        echo -e "${GREEN}✓${NC} LaunchAgent removed"
    fi

    echo ""
    echo -e "${GREEN}=========================================="
    echo "  ✅ Mesh Master Uninstalled"
    echo "==========================================${NC}"
    echo ""
    echo "Removed:"
    echo "  • All desktop shortcuts"
    echo "  • All running processes"
    if [[ "$PLATFORM" == "Linux" ]] && [[ -f "/etc/systemd/system/mesh-ai.service" ]]; then
        echo "  • Systemd service"
    elif [[ "$PLATFORM" == "macOS" ]] && [[ -f "$HOME/Library/LaunchAgents/com.meshmaster.plist" ]]; then
        echo "  • LaunchAgent service"
    fi
    echo ""

    # Auto-delete directory if AUTO_DELETE env var is set (used by dashboard)
    if [[ "$AUTO_DELETE" == "true" ]]; then
        echo "Auto-deleting Mesh Master directory..."
        # Get the script directory (Mesh-Master folder)
        MESH_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)

        if [[ -n "$MESH_DIR" ]] && [[ -d "$MESH_DIR" ]]; then
            # Move up one level and delete
            cd "$HOME" 2>/dev/null || cd /tmp
            sleep 2  # Give processes time to terminate
            rm -rf "$MESH_DIR" 2>/dev/null
            echo -e "${GREEN}✓${NC} Mesh Master directory deleted: $MESH_DIR"
            echo ""
            echo "Mesh Master has been completely removed!"
        else
            echo -e "${YELLOW}⚠️${NC} Could not auto-delete directory (path not found)"
            echo "Please manually delete: cd ~ && rm -rf Mesh-Master"
        fi
    else
        echo "To completely remove Mesh Master directory:"
        echo -e "  ${YELLOW}cd ~ && rm -rf Mesh-Master${NC}"
        echo ""
    fi
fi
