#!/usr/bin/env bash

# Mesh Master Linux/Debian Systemd Service Installation Script
# This sets up Mesh Master to run automatically and restart on crashes

set -e

# Verify we're NOT on macOS (this is for Linux/Debian)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "❌ This script is for Linux/Debian only"
    echo "For macOS, use: ./scripts/macos/install_service.sh"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  Mesh Master Linux Service Installer"
echo "=========================================="
echo ""

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
    for dir in "$HOME/Mesh-Master" "$HOME/Programs/mesh-ai" "/opt/Mesh-Master" "/usr/local/Mesh-Master"; do
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
            echo -e "${YELLOW}sudo apt-get install git${NC}"
            echo "or"
            echo -e "${YELLOW}sudo yum install git${NC}"
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
        echo -e "${YELLOW}sudo bash scripts/linux/install_service.sh${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Found Mesh Master at: $PROJECT_DIR"
echo ""

# Run setup.sh if config.json doesn't exist
if [[ ! -f "$PROJECT_DIR/config.json" ]]; then
    echo "Running initial setup..."
    cd "$PROJECT_DIR"
    if [[ -f "./setup.sh" ]]; then
        bash ./setup.sh
        echo -e "${GREEN}✓${NC} Setup complete"
    fi
fi

# Install Python dependencies if requirements.txt exists
if [[ -f "$PROJECT_DIR/requirements.txt" ]]; then
    echo "Checking Python dependencies..."

    # Find Python
    PYTHON_CMD=$(which python3)

    # Check if we should use venv
    if [[ -f "$PROJECT_DIR/.venv/bin/pip" ]]; then
        echo "Installing dependencies in virtual environment..."
        "$PROJECT_DIR/.venv/bin/pip" install -q -r "$PROJECT_DIR/requirements.txt"
    else
        echo "Installing dependencies with system Python..."
        "$PYTHON_CMD" -m pip install -q -r "$PROJECT_DIR/requirements.txt" --user 2>/dev/null || \
        "$PYTHON_CMD" -m pip install -q -r "$PROJECT_DIR/requirements.txt"
    fi
    echo -e "${GREEN}✓${NC} Dependencies installed"
fi

echo ""

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}❌ Error: systemd not found${NC}"
    echo ""
    echo "This script requires systemd (systemctl command)."
    echo "Your system might use a different init system."
    exit 1
fi

# Check if running with sudo/root for systemd operations
if [[ $EUID -ne 0 ]]; then
    echo -e "${YELLOW}⚠️  This script needs sudo privileges to install the systemd service${NC}"
    echo ""
    echo "Please run with sudo:"
    echo -e "${YELLOW}sudo ./scripts/linux/install_service.sh${NC}"
    echo ""
    echo "Or run the commands manually:"
    echo "  sudo cp mesh-ai.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable mesh-ai"
    echo "  sudo systemctl start mesh-ai"
    exit 1
fi

# Check if mesh-ai.service file exists
if [[ ! -f "$PROJECT_DIR/mesh-ai.service" ]]; then
    echo -e "${RED}❌ Error: mesh-ai.service file not found${NC}"
    echo ""
    echo "Expected to find mesh-ai.service in: $PROJECT_DIR"
    echo ""
    echo "This file should contain your systemd service configuration."
    exit 1
fi

echo "Installing systemd service..."
echo ""

# Stop and disable old service if it exists
if systemctl is-active --quiet mesh-ai; then
    echo -e "${YELLOW}⚠️  Stopping existing Mesh Master service...${NC}"
    systemctl stop mesh-ai
fi
if systemctl is-enabled --quiet mesh-ai 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Disabling old service...${NC}"
    systemctl disable mesh-ai
fi

# Copy service file to systemd directory
echo "Copying service file to /etc/systemd/system/..."
cp "$PROJECT_DIR/mesh-ai.service" /etc/systemd/system/

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable service (start on boot)
echo "Enabling service to start on boot..."
systemctl enable mesh-ai

# Start the service
echo "Starting mesh-ai service..."
systemctl start mesh-ai

# Create desktop shortcuts (run as the original user, not root)
echo "Creating desktop shortcuts..."
if [[ -f "$PROJECT_DIR/scripts/desktop/create_shortcuts.py" ]]; then
    # Find the original user (before sudo)
    ORIGINAL_USER="${SUDO_USER:-$USER}"

    # Find Python
    SHORTCUT_PYTHON=$(which python3)
    if [[ -f "$PROJECT_DIR/.venv/bin/python" ]]; then
        SHORTCUT_PYTHON="$PROJECT_DIR/.venv/bin/python"
    fi

    # Run as original user (not root)
    if [[ -n "$SUDO_USER" ]]; then
        sudo -u "$SUDO_USER" "$SHORTCUT_PYTHON" "$PROJECT_DIR/scripts/desktop/create_shortcuts.py" 2>/dev/null
    else
        "$SHORTCUT_PYTHON" "$PROJECT_DIR/scripts/desktop/create_shortcuts.py" 2>/dev/null
    fi

    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓${NC} Desktop shortcuts created"
    else
        echo -e "${YELLOW}⚠️${NC} Desktop shortcuts skipped (optional)"
    fi
else
    echo -e "${YELLOW}⚠️${NC} Desktop shortcut script not found (optional)"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Mesh Master Service Installed!"
echo "==========================================${NC}"
echo ""
echo "The service is now running and will:"
echo "  • Start automatically on boot"
echo "  • Restart automatically if it crashes"
echo "  • Restart automatically after /update command"
echo ""
echo "Desktop shortcuts created:"
echo "  • Start Mesh Master (launches dashboard)"
echo "  • Stop Mesh Master (stops service)"
echo ""
echo "Useful commands:"
echo ""
echo "  Check status:"
echo "    sudo systemctl status mesh-ai"
echo ""
echo "  View logs:"
echo "    sudo journalctl -u mesh-ai -f"
echo ""
echo "  Restart service:"
echo "    sudo systemctl restart mesh-ai"
echo ""
echo "  Stop service:"
echo "    sudo systemctl stop mesh-ai"
echo ""
echo "  Disable auto-start:"
echo "    sudo systemctl disable mesh-ai"
echo ""
echo "  Uninstall service:"
echo "    ./scripts/linux/uninstall_service.sh"
echo ""
echo "Dashboard: http://localhost:5001/dashboard"
echo ""
