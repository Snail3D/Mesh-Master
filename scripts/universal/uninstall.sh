#!/usr/bin/env bash

# Mesh Master Universal Uninstallation Script
# Auto-detects platform and calls the appropriate uninstaller
# Automatically handles platform-specific requirements (sudo, PowerShell, etc.)

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
    SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/macos/uninstall_service.sh"
elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux"* ]]; then
    PLATFORM="Linux"
    SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/linux/uninstall_service.sh"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="Windows"
    SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/windows/uninstall_service.bat"
else
    echo -e "${RED}❌ Unknown platform: $OSTYPE${NC}"
    exit 1
fi

echo -e "Detected platform: ${BLUE}$PLATFORM${NC}"
echo ""

# Check if script exists
if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo -e "${RED}❌ Uninstall script not found: $SCRIPT_PATH${NC}"
    exit 1
fi

echo -e "Using uninstaller: ${BLUE}$SCRIPT_PATH${NC}"
echo ""

# Execute the appropriate uninstaller
if [[ "$PLATFORM" == "macOS" ]]; then
    # macOS - run directly (no sudo needed)
    bash "$SCRIPT_PATH"

elif [[ "$PLATFORM" == "Linux" ]]; then
    # Linux - auto-elevate with sudo if needed
    if [[ $EUID -ne 0 ]]; then
        echo -e "${YELLOW}Elevating to root with sudo...${NC}"
        echo ""
        sudo bash "$SCRIPT_PATH"
    else
        bash "$SCRIPT_PATH"
    fi

elif [[ "$PLATFORM" == "Windows" ]]; then
    # Windows - provide helpful instructions
    echo -e "${YELLOW}⚠️  Windows Setup${NC}"
    echo ""
    echo "The next step requires PowerShell with Administrator privileges."
    echo ""
    echo "Follow these steps:"
    echo "  1. Press ${BLUE}Win+X${NC} and select ${BLUE}Terminal (Admin)${NC}"
    echo "  2. Copy and paste this command:"
    echo ""
    echo -e "${BLUE}powershell -ExecutionPolicy Bypass -Command \"& '$SCRIPT_PATH'\"${NC}"
    echo ""
    echo "Then press Enter."
    echo ""
fi

echo ""
echo -e "${GREEN}✅ Uninstallation complete!${NC}"
echo ""
