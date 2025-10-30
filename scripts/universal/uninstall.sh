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

    # Get the Mesh-Master directory before calling platform-specific script
    if [[ -n "${BASH_SOURCE[0]}" ]] && [[ -f "${BASH_SOURCE[0]}" ]]; then
        MESH_DIR_EXPORT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)
    else
        # Try from current directory
        if [[ -f "mesh-master.py" ]]; then
            MESH_DIR_EXPORT=$(pwd)
        elif [[ -f "../mesh-master.py" ]]; then
            MESH_DIR_EXPORT=$(cd .. && pwd)
        elif [[ -f "../../mesh-master.py" ]]; then
            MESH_DIR_EXPORT=$(cd ../.. && pwd)
        fi
    fi

    if [[ "$PLATFORM" == "macOS" ]]; then
        bash "$SCRIPT_PATH" "$MESH_DIR_EXPORT"
    elif [[ "$PLATFORM" == "Linux" ]]; then
        if [[ $EUID -ne 0 ]]; then
            echo -e "${YELLOW}Elevating to root with sudo...${NC}"
            echo ""
            # Pass MESH_DIR as argument instead of environment variable (sudo blocks env vars)
            sudo bash "$SCRIPT_PATH" "$MESH_DIR_EXPORT"
        else
            bash "$SCRIPT_PATH" "$MESH_DIR_EXPORT"
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

    # Handle directory deletion
    # Get the Mesh-Master directory (try multiple methods)
    # Method 0: Use argument from caller if provided (dashboard passes this)
    if [[ -n "$1" ]] && [[ -d "$1" ]] && [[ -f "$1/mesh-master.py" ]]; then
        MESH_DIR="$1"
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
            # Check if we're in scripts/universal/ subdirectory
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

    # Auto-delete if AUTO_DELETE env var is set (used by dashboard)
    if [[ "$AUTO_DELETE" == "true" ]]; then
        echo "Auto-deleting Mesh Master directory..."
        cd "$HOME" 2>/dev/null || cd /tmp
        sleep 2  # Give processes time to terminate
        rm -rf "$MESH_DIR" 2>/dev/null
        echo -e "${GREEN}✓${NC} Mesh Master directory deleted: $MESH_DIR"
        echo ""
        echo "Mesh Master has been completely removed!"
    else
        # Interactive mode - delete directory with countdown
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
fi
