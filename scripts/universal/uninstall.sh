#!/usr/bin/env bash

# Mesh Master Universal Uninstallation Script
# Auto-detects platform and calls the appropriate uninstaller

set -e

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
    # macOS - run directly
    bash "$SCRIPT_PATH"
elif [[ "$PLATFORM" == "Linux" ]]; then
    # Linux - check for sudo
    if [[ $EUID -ne 0 ]]; then
        echo -e "${YELLOW}⚠️  This script requires sudo for Linux${NC}"
        echo ""
        echo "Please run with sudo:"
        echo -e "${YELLOW}sudo bash $SCRIPT_PATH${NC}"
        exit 1
    fi
    bash "$SCRIPT_PATH"
elif [[ "$PLATFORM" == "Windows" ]]; then
    # Windows - run batch file (requires Git Bash or similar)
    echo -e "${YELLOW}Note: Run this in PowerShell as Administrator for Windows${NC}"
    echo ""
    echo "Windows uninstall script:"
    echo -e "${BLUE}$SCRIPT_PATH${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Uninstallation complete!${NC}"
echo ""
