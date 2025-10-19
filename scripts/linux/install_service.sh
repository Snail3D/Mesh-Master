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

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "Project directory: $PROJECT_DIR"
echo ""

# Verify we're in the Mesh Master project directory
if [[ ! -f "$PROJECT_DIR/mesh-master.py" ]]; then
    echo -e "${RED}❌ Error: mesh-master.py not found!${NC}"
    echo ""
    echo "This script must be run from the Mesh Master project directory."
    echo ""
    echo "Please navigate to your Mesh-Master folder and try again:"
    echo -e "${YELLOW}cd ~/Mesh-Master${NC}"
    echo -e "${YELLOW}./scripts/linux/install_service.sh${NC}"
    echo ""
    echo "Or run with bash:"
    echo -e "${YELLOW}bash scripts/linux/install_service.sh${NC}"
    exit 1
fi

# Additional verification - check for key files
if [[ ! -f "$PROJECT_DIR/config.json" ]] && [[ ! -f "$PROJECT_DIR/config.json.example" ]]; then
    echo -e "${RED}❌ Error: This doesn't look like a Mesh Master directory${NC}"
    echo ""
    echo "Expected to find config.json or config.json.example"
    echo "Current directory: $PROJECT_DIR"
    echo ""
    echo "Please make sure you're in the Mesh-Master project folder."
    exit 1
fi

echo -e "${GREEN}✓${NC} Found Mesh Master installation"
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

echo ""
echo -e "${GREEN}✅ Success! Mesh Master service installed${NC}"
echo ""
echo "Service is now running and will start automatically on boot."
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
