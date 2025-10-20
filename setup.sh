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
    echo -e "${YELLOW}⚠️  Python 3 not found${NC}"
    echo ""
    echo "Would you like to install Python 3 automatically?"
    read -p "Install Python? (Y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "Installing Python 3..."
        if [[ "$OS" == "macOS" ]]; then
            if command -v brew &> /dev/null; then
                brew install python3
            else
                echo -e "${RED}❌ Homebrew not found${NC}"
                echo "Please install Homebrew first: https://brew.sh"
                echo "Or download Python from: https://www.python.org/downloads/"
                exit 1
            fi
        elif [[ "$OS" == "Raspberry Pi" || "$OS" == "Linux" ]]; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        elif [[ "$OS" == "Windows (Git Bash)" ]]; then
            echo -e "${RED}❌ Cannot auto-install on Windows${NC}"
            echo "Please download Python from: https://www.python.org/downloads/"
            echo "IMPORTANT: Check 'Add Python to PATH' during installation"
            exit 1
        fi

        # Re-check for Python
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
            echo -e "${GREEN}✓${NC} Python 3 installed successfully"
        else
            echo -e "${RED}❌ Python installation failed${NC}"
            exit 1
        fi
    else
        echo "Python 3 is required. Exiting."
        exit 1
    fi
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

# On Raspberry Pi, install system packages to avoid slow builds
if [[ "$OS" == "Raspberry Pi" ]]; then
    echo "Installing system packages for faster Pi installation..."
    echo "(This provides pre-compiled binaries instead of building from source)"

    # Try to update apt, but continue if it fails
    if sudo apt-get update -qq 2>/dev/null; then
        sudo apt-get install -y python3-pip python3-cryptography python3-bcrypt libatlas-base-dev 2>&1 | grep -v "already"
        echo -e "${GREEN}✓${NC} System packages installed"
    else
        echo -e "${YELLOW}⚠️${NC}  apt-get update failed (possibly malformed sources list)"
        echo "Continuing with pip installation (may be slower)..."
    fi
    echo ""
fi

# Upgrade pip (skip on Pi to avoid hangs)
if [[ "$OS" == "Raspberry Pi" ]]; then
    echo "Skipping pip upgrade on Raspberry Pi (using existing pip to avoid hangs)..."
    echo -e "${GREEN}✓${NC} pip ready (using existing version)"
else
    echo "Upgrading pip..."
    pip install --upgrade pip --no-cache-dir
    echo -e "${GREEN}✓${NC} pip upgraded"
fi
echo ""

# Install dependencies
echo "Installing Python dependencies..."
if [[ "$OS" == "Raspberry Pi" ]]; then
    echo "(This may take 5-10 minutes on Raspberry Pi - please be patient)"
else
    echo "(This may take a few minutes...)"
fi
echo ""

# Install base requirements
if [[ -f "requirements.txt" ]]; then
    echo "Installing from requirements.txt..."

    # On Raspberry Pi, use mostly system packages to avoid compilation
    if [[ "$OS" == "Raspberry Pi" ]]; then
        echo "Using Raspberry Pi optimized installation..."
        echo "(Installing from system packages when available to avoid compilation)"
        echo ""

        # Install common Python packages from apt to avoid pip compilation issues
        echo "Installing system packages..."

        # Try to install each package individually in case some are already installed
        for pkg in python3-protobuf python3-tornado python3-requests python3-flask python3-pil python3-numpy; do
            if dpkg -l | grep -q "^ii.*$pkg"; then
                echo "  $pkg already installed"
            else
                echo "  Installing $pkg..."
                sudo apt-get install -y $pkg 2>&1 | tail -1
            fi
        done

        echo -e "${GREEN}✓${NC} System packages ready"
        echo ""

        # Only install meshtastic and packages not available via apt
        echo "Installing remaining packages via pip (using piwheels for pre-built binaries)..."

        # Simple pure-Python packages (should be fast)
        echo "Installing pubsub..."
        pip install pubsub --no-cache-dir --prefer-binary && echo -e "  ${GREEN}✓${NC} pubsub" || echo -e "  ${YELLOW}⚠️${NC} pubsub failed"

        echo "Installing unidecode..."
        pip install unidecode --no-cache-dir --prefer-binary && echo -e "  ${GREEN}✓${NC} unidecode" || echo -e "  ${YELLOW}⚠️${NC} unidecode failed"

        echo "Installing python-chess..."
        pip install python-chess --no-cache-dir --prefer-binary && echo -e "  ${GREEN}✓${NC} python-chess" || echo -e "  ${YELLOW}⚠️${NC} python-chess failed"

        echo "Installing pytest..."
        pip install pytest --no-cache-dir --prefer-binary && echo -e "  ${GREEN}✓${NC} pytest" || echo -e "  ${YELLOW}⚠️${NC} pytest failed"

        # Meshtastic (may have dependencies, use piwheels)
        echo "Installing meshtastic (this may take 1-2 minutes on Pi)..."
        pip install meshtastic --no-cache-dir --prefer-binary --index-url https://www.piwheels.org/simple --extra-index-url https://pypi.org/simple && echo -e "  ${GREEN}✓${NC} meshtastic" || echo -e "  ${YELLOW}⚠️${NC} meshtastic failed"

        # Reportlab (may take longer, has native code)
        echo "Installing reportlab..."
        pip install reportlab --no-cache-dir --prefer-binary --index-url https://www.piwheels.org/simple --extra-index-url https://pypi.org/simple && echo -e "  ${GREEN}✓${NC} reportlab" || echo -e "  ${YELLOW}⚠️${NC} reportlab failed"

        echo ""
        echo -e "${GREEN}✓${NC} Finished installing requirements"
    else
        pip install -r requirements.txt --no-cache-dir
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✓${NC} Installed requirements.txt"
        else
            echo -e "${YELLOW}⚠️${NC}  Some packages may have failed"
        fi
    fi
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Install additional required packages not in requirements.txt
echo ""
echo "Installing additional dependencies..."
if [[ "$OS" == "Raspberry Pi" ]]; then
    # Try to install, but use --prefer-binary to avoid compilation
    echo "(Attempting to use binary wheels to avoid compilation)"
    pip install cryptography python-telegram-bot bcrypt --no-cache-dir --prefer-binary --verbose 2>&1 | grep -E "Collecting|Installing|Successfully|ERROR" | tee /tmp/pip-install.log

    echo ""
    echo -e "${GREEN}✓${NC} Additional dependencies installed"
else
    pip install cryptography python-telegram-bot bcrypt --no-cache-dir
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓${NC} Installed additional dependencies"
    else
        echo -e "${YELLOW}⚠️${NC}  Some additional packages may have failed"
    fi
fi
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
    if ollama list 2>/dev/null | grep -q "llama3.2:1b"; then
        echo -e "${GREEN}✓${NC} llama3.2:1b model already installed"
    else
        echo -e "${YELLOW}⚠️  llama3.2:1b model not found${NC}"
        echo ""
        echo "Would you like to download llama3.2:1b? (Recommended for Mesh Master)"
        echo "Size: ~1.3GB download"
        read -p "Download model? (Y/n) " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo "Downloading llama3.2:1b model (this may take a few minutes)..."
            ollama pull llama3.2:1b
            if [[ $? -eq 0 ]]; then
                echo -e "${GREEN}✓${NC} Model downloaded successfully"
            else
                echo -e "${YELLOW}⚠️${NC}  Model download failed (you can try again later with: ollama pull llama3.2:1b)"
            fi
        else
            echo "Skipping model download (you can install later with: ollama pull llama3.2:1b)"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Ollama not found${NC}"
    echo ""
    echo "Ollama is required for AI features. Would you like to install it?"
    read -p "Install Ollama? (Y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "Installing Ollama..."
        if [[ "$OS" == "macOS" ]]; then
            if command -v brew &> /dev/null; then
                brew install ollama
                brew services start ollama
                sleep 3  # Wait for Ollama to start
            else
                echo -e "${YELLOW}⚠️${NC}  Homebrew not found, using direct install..."
                curl -fsSL https://ollama.com/install.sh | sh
            fi
        elif [[ "$OS" == "Raspberry Pi" || "$OS" == "Linux" ]]; then
            curl -fsSL https://ollama.com/install.sh | sh
        elif [[ "$OS" == "Windows (Git Bash)" ]]; then
            echo -e "${RED}❌ Cannot auto-install on Windows${NC}"
            echo "Please download from: https://ollama.com/download/windows"
            echo "After installing, re-run this setup script"
            echo ""
        fi

        # Re-check for Ollama
        if command -v ollama &> /dev/null; then
            echo -e "${GREEN}✓${NC} Ollama installed successfully"

            # Auto-download llama3.2:1b after installing Ollama
            echo ""
            echo "Downloading llama3.2:1b model (recommended for Mesh Master)..."
            echo "Size: ~1.3GB download (this may take a few minutes)"
            ollama pull llama3.2:1b
            if [[ $? -eq 0 ]]; then
                echo -e "${GREEN}✓${NC} Model downloaded successfully"
            else
                echo -e "${YELLOW}⚠️${NC}  Model download failed (you can try again later with: ollama pull llama3.2:1b)"
            fi
        else
            echo -e "${YELLOW}⚠️${NC}  Ollama installation may require manual steps"
            echo "Visit: https://ollama.com for installation instructions"
        fi
    else
        echo -e "${YELLOW}⚠️${NC}  Skipping Ollama installation"
        echo "AI features will not work without Ollama"
        echo "Install later from: https://ollama.com"
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
