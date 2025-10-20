#!/bin/bash
# Mesh Master Universal Setup Script
# Installs dependencies and prepares environment for first run
# Works on macOS, Linux, Raspberry Pi, and Windows (via Git Bash)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  Mesh Master Universal Setup"
echo "=========================================="
echo ""

# Detect OS
OS="Unknown"
ARCH="Unknown"

if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    ARCH=$(uname -m)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Check if it's Raspberry Pi
    if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model; then
        OS="Raspberry Pi"
        ARCH=$(uname -m)
    else
        OS="Linux"
        ARCH=$(uname -m)
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS="Windows (Git Bash)"
    ARCH=$(uname -m)
fi

echo -e "${BLUE}Detected OS: $OS ($ARCH)${NC}"
echo ""

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${GREEN}✓${NC} Project directory: $PROJECT_DIR"
echo ""

# Check for Python 3
echo "Checking for Python 3..."
PYTHON_CMD="python3"

# On Windows, try 'python' first (Python 3 is often just 'python')
if [[ "$OS" == "Windows (Git Bash)" ]]; then
    if command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1)
        if [[ "$PYTHON_VERSION" == *"Python 3"* ]]; then
            PYTHON_CMD="python"
        fi
    fi
fi

if command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_VERSION=$($PYTHON_CMD --version)
    echo -e "${GREEN}✓${NC} Found: $PYTHON_VERSION"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo ""
    echo "Please install Python 3.9 or later:"
    if [[ "$OS" == "macOS" ]]; then
        echo "  Download from: https://www.python.org/downloads/"
        echo "  Or via Homebrew: brew install python"
    elif [[ "$OS" == "Raspberry Pi" || "$OS" == "Linux" ]]; then
        echo "  sudo apt-get update"
        echo "  sudo apt-get install python3 python3-pip python3-venv"
    elif [[ "$OS" == "Windows (Git Bash)" ]]; then
        echo "  Download from: https://www.python.org/downloads/"
        echo "  IMPORTANT: Check 'Add Python to PATH' during installation"
    fi
    exit 1
fi
echo ""

# Create virtual environment
echo "Setting up virtual environment..."
if [[ -d ".venv" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
    read -p "Recreate it? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old virtual environment..."
        rm -rf .venv
    else
        echo "Keeping existing virtual environment"
    fi
fi

if [[ ! -d ".venv" ]]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OS" == "Windows (Git Bash)" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi
echo -e "${GREEN}✓${NC} Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q
echo -e "${GREEN}✓${NC} pip upgraded"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
echo "(This may take a few minutes...)"
echo ""

# Install base requirements
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓${NC} Installed requirements.txt"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Install additional required packages not in requirements.txt
echo "Installing additional dependencies..."
pip install cryptography python-telegram-bot bcrypt -q
echo -e "${GREEN}✓${NC} Installed cryptography, telegram, bcrypt"
echo ""

# Create config.json from example if it doesn't exist
if [[ ! -f "config.json" ]]; then
    if [[ -f "config.json.example" ]]; then
        echo "Creating config.json from example..."
        cp config.json.example config.json

        # Set web_port to 5001 to avoid macOS AirPlay conflict
        if command -v $PYTHON_CMD &> /dev/null; then
            $PYTHON_CMD << 'EOF'
import json

try:
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Set port 5001 for universal compatibility
    config['web_port'] = 5001

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print("✓ config.json created and configured for port 5001")
except Exception as e:
    print(f"⚠️  Created config.json but couldn't set port: {e}")
EOF
        fi

        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit config.json before running${NC}"
        echo ""
        echo "You need to configure:"
        echo "  1. admin_password (change from default!)"
        echo "  2. Serial connection (serial_port) OR WiFi (wifi_host)"
        echo "  3. Any other settings for your setup"
        echo ""
    else
        echo -e "${RED}❌ config.json.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} config.json already exists"
    echo ""
fi

# Create data directory if it doesn't exist
if [[ ! -d "data" ]]; then
    mkdir -p data
    echo -e "${GREEN}✓${NC} Created data directory"
fi

# Check for Ollama (AI engine)
echo "Checking for Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama is installed"

    # Check if a model is pulled
    if ollama list 2>/dev/null | grep -q "llama3.2"; then
        echo -e "${GREEN}✓${NC} Ollama model found"
    else
        echo -e "${YELLOW}⚠️  No Ollama models found${NC}"
        echo ""
        echo "Recommended: Pull a model for AI functionality"
        echo "  ollama pull llama3.2:1b    (Lightweight, good for Pi)"
        echo "  ollama pull llama3.2:3b    (Better quality, needs more RAM)"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  Ollama not found${NC}"
    echo ""
    echo "Ollama is required for AI features."
    echo ""
    if [[ "$OS" == "macOS" ]]; then
        echo "  Install from: https://ollama.com"
        echo "  Or via Homebrew: brew install ollama"
    elif [[ "$OS" == "Raspberry Pi" || "$OS" == "Linux" ]]; then
        echo "  curl -fsSL https://ollama.com/install.sh | sh"
    elif [[ "$OS" == "Windows (Git Bash)" ]]; then
        echo "  Download from: https://ollama.com/download/windows"
    fi
    echo ""
fi

# Create desktop shortcut with icon
echo "Creating desktop shortcut..."
if [[ -f "scripts/desktop/create_shortcuts.py" ]]; then
    $PYTHON_CMD scripts/desktop/create_shortcuts.py 2>/dev/null
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓${NC} Desktop shortcut created with MM icon"
    else
        echo -e "${YELLOW}⚠️${NC}  Desktop shortcut creation failed (optional)"
    fi
else
    echo -e "${YELLOW}⚠️${NC}  Desktop shortcut script not found (optional)"
fi
echo ""

echo ""
echo "=========================================="
echo -e "  ${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "✨ Desktop shortcut created! Look for:"
echo "   📱 Mesh Master (with blue MM icon)"
echo ""
echo "What the shortcut does:"
echo "  • Kills any old/zombie instances"
echo "  • Starts fresh Mesh Master"
echo "  • Opens dashboard automatically"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit your configuration:"
if [[ "$OS" == "Windows (Git Bash)" ]]; then
    echo "   notepad config.json"
else
    echo "   nano config.json"
fi
echo ""
echo "   IMPORTANT: Change admin_password from default!"
echo ""
echo "2. Start Mesh Master:"
echo "   Double-click the Mesh Master icon on your desktop"
echo "   OR run: ./mesh-master.sh"
echo ""
echo "3. Access dashboard:"
echo "   http://localhost:5001/dashboard"
echo ""
echo "Platform-specific notes:"
if [[ "$OS" == "macOS" ]]; then
    echo "  • Port 5001 is used to avoid macOS AirPlay conflict"
    echo "  • Desktop shortcut is a .app bundle"
    echo "  • Add Meshtastic device to dialout group if needed"
elif [[ "$OS" == "Raspberry Pi" ]]; then
    echo "  • Add user to dialout group: sudo usermod -a -G dialout \$USER"
    echo "  • Reboot after adding to group"
    echo "  • Recommended model: llama3.2:1b (lightweight)"
    echo "  • Desktop shortcut is a .desktop file"
elif [[ "$OS" == "Linux" ]]; then
    echo "  • Desktop shortcut is a .desktop file"
    echo "  • May need to mark as trusted/executable"
elif [[ "$OS" == "Windows (Git Bash)" ]]; then
    echo "  • Python must be in PATH"
    echo "  • Use COM ports for serial (e.g., COM3)"
    echo "  • Check Device Manager for Meshtastic port"
    echo "  • Desktop shortcut is a .lnk file"
fi
echo ""
echo "For help, see: README.md"
echo ""
