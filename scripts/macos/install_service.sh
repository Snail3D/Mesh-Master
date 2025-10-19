#!/usr/bin/env bash

# Mesh Master macOS LaunchAgent Installation Script
# This sets up Mesh Master to run automatically and restart on crashes

set -e

# Verify we're actually on macOS before proceeding
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    echo "For Linux/Pi, use: sudo systemctl enable mesh-ai"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  Mesh Master macOS Service Installer"
echo "=========================================="
echo ""

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script is for macOS only${NC}"
    echo "For Linux, run: curl -sSL https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/linux/install_service.sh | sudo bash"
    exit 1
fi

# Try to find Mesh-Master directory automatically
PROJECT_DIR=""

# Method 1: Check if script is inside Mesh-Master directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" 2>/dev/null && pwd )"
if [[ -n "$SCRIPT_DIR" ]]; then
    POTENTIAL_DIR="$( cd "$SCRIPT_DIR/../.." 2>/dev/null && pwd )"
    if [[ -f "$POTENTIAL_DIR/mesh-master.py" ]]; then
        PROJECT_DIR="$POTENTIAL_DIR"
    fi
fi

# Method 2: Check current directory
if [[ -z "$PROJECT_DIR" ]] && [[ -f "$PWD/mesh-master.py" ]]; then
    PROJECT_DIR="$PWD"
fi

# Method 3: Search common locations
if [[ -z "$PROJECT_DIR" ]]; then
    for dir in "$HOME/Mesh-Master" "$HOME/Documents/Mesh-Master" "$HOME/Desktop/Mesh-Master" "$HOME/Downloads/Mesh-Master"; do
        if [[ -f "$dir/mesh-master.py" ]]; then
            PROJECT_DIR="$dir"
            break
        fi
    done
fi

# Method 4: Try to find anywhere in home directory (may take a moment)
if [[ -z "$PROJECT_DIR" ]]; then
    echo "Searching for Mesh-Master installation..."
    FOUND_DIR=$(find "$HOME" -name "mesh-master.py" -type f 2>/dev/null | head -1)
    if [[ -n "$FOUND_DIR" ]]; then
        PROJECT_DIR="$(dirname "$FOUND_DIR")"
    fi
fi

# If still not found, offer to clone it automatically
if [[ -z "$PROJECT_DIR" ]] || [[ ! -f "$PROJECT_DIR/mesh-master.py" ]]; then
    echo -e "${YELLOW}⚠️  Mesh-Master not found on this system${NC}"
    echo ""
    echo "Would you like to download Mesh-Master automatically?"
    echo ""
    read -p "Download to ~/Mesh-Master? (Y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # User wants to download
        CLONE_DIR="$HOME/Mesh-Master"

        # Check if git is installed
        if ! command -v git &> /dev/null; then
            echo -e "${RED}❌ git is not installed${NC}"
            echo "Please install git first:"
            echo -e "${YELLOW}brew install git${NC}"
            exit 1
        fi

        # Check if directory already exists
        if [[ -d "$CLONE_DIR" ]]; then
            echo -e "${RED}❌ Directory already exists: $CLONE_DIR${NC}"
            echo "Please remove it first or clone manually to a different location"
            exit 1
        fi

        echo "Cloning Mesh-Master repository..."
        if git clone https://github.com/Snail3D/Mesh-Master.git "$CLONE_DIR"; then
            PROJECT_DIR="$CLONE_DIR"
            echo -e "${GREEN}✓${NC} Downloaded Mesh-Master to: $PROJECT_DIR"
            echo ""
        else
            echo -e "${RED}❌ Failed to clone repository${NC}"
            exit 1
        fi
    else
        # User declined download
        echo ""
        echo "Please clone Mesh-Master manually:"
        echo -e "${YELLOW}git clone https://github.com/Snail3D/Mesh-Master.git${NC}"
        echo -e "${YELLOW}cd Mesh-Master${NC}"
        echo -e "${YELLOW}bash scripts/macos/install_service.sh${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Found Mesh Master at: $PROJECT_DIR"
echo ""

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# LaunchAgent directory
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.meshmaster.plist"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Check if service is already installed
if [[ -f "$PLIST_PATH" ]]; then
    echo -e "${YELLOW}⚠️  Mesh Master service is already installed${NC}"
    echo ""
    read -p "Do you want to reinstall? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi

    # Unload existing service
    echo "Unloading existing service..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm "$PLIST_PATH"
fi

# Find Python 3 path
PYTHON_PATH=$(which python3)
if [[ -z "$PYTHON_PATH" ]]; then
    echo -e "${RED}❌ Error: python3 not found in PATH${NC}"
    echo "Please install Python 3 first."
    exit 1
fi

echo "Using Python: $PYTHON_PATH"
echo ""

# Check if virtual environment exists
if [[ -f "$PROJECT_DIR/.venv/bin/python" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment detected${NC}"
    echo "Using virtual environment Python: $PROJECT_DIR/.venv/bin/python"
    PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
fi

# Create the plist file from template
echo "Creating LaunchAgent plist..."
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.meshmaster</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$PROJECT_DIR/mesh-master.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>

    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/mesh-master-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/mesh-master-stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin</string>
    </dict>

    <key>ProcessType</key>
    <string>Background</string>

    <key>Nice</key>
    <integer>0</integer>
</dict>
</plist>
EOF

echo -e "${GREEN}✓${NC} Plist file created: $PLIST_PATH"
echo ""

# Load the service
echo "Loading Mesh Master service..."
launchctl load "$PLIST_PATH"

# Give it a moment to start
sleep 2

# Check if it's running
if launchctl list | grep -q "com.meshmaster"; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  ✅ Mesh Master Service Installed!"
    echo "==========================================${NC}"
    echo ""
    echo "The service is now running and will:"
    echo "  • Start automatically on login"
    echo "  • Restart automatically if it crashes"
    echo "  • Restart automatically after /update command"
    echo ""
    echo "Useful commands:"
    echo "  • Check status:  launchctl list | grep meshmaster"
    echo "  • View logs:     tail -f $PROJECT_DIR/logs/mesh-master-stdout.log"
    echo "  • Stop service:  launchctl unload $PLIST_PATH"
    echo "  • Start service: launchctl load $PLIST_PATH"
    echo "  • Restart:       launchctl kickstart -k gui/\$(id -u)/com.meshmaster"
    echo ""
    echo "Dashboard: http://localhost:5001/dashboard"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Service failed to start${NC}"
    echo "Check logs at: $PROJECT_DIR/logs/mesh-master-stderr.log"
    exit 1
fi
