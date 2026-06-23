#!/usr/bin/env bash
# ============================================================
# Hermes Bootstrap Installer v0.1
# One-click AI-guided installation of a local Hermes Agent
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/bootstrap/install.sh | bash
#
# What it does:
#   Phase 1 (this script): Detect OS, install deps, download model, start inference
#   Phase 2 (AI agent):    Install Hermes, create profile, configure Telegram, start gateway
#
# The agent runs on a LOCAL uncensored model — no cloud API needed.
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

BANNER="
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🐌  HERMES BOOTSTRAP INSTALLER  🐌                      ║
║                                                           ║
║   One-click AI-guided local agent installation            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"

echo -e "${CYAN}${BANNER}${NC}"

# --- Detect OS ---
OS="unknown"
ARCH=$(uname -m)

if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
fi

echo -e "${BLUE}📋 System Detection:${NC}"
echo -e "  OS: ${OS}"
echo -e "  Arch: ${ARCH}"

if [[ "$OS" == "unknown" ]]; then
    echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

if [[ "$OS" == "windows" ]]; then
    echo -e "${YELLOW}⚠️  Windows support coming soon. Use WSL2 for now.${NC}"
    exit 1
fi

# --- Install directory ---
INSTALL_DIR="${HOME}/.hermes-bootstrap"
mkdir -p "$INSTALL_DIR"

echo -e "  Install dir: $INSTALL_DIR"
echo ""

# --- Check for Python ---
echo -e "${BLUE}🐍 Checking Python...${NC}"
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "  ${GREEN}✓${NC} Python $PYVER"
    
    # Check version >= 3.10
    PYMAJOR=$(echo $PYVER | cut -d. -f1)
    PYMINOR=$(echo $PYVER | cut -d. -f2)
    if [[ "$PYMAJOR" -lt 3 ]] || ([[ "$PYMAJOR" -eq 3 ]] && [[ "$PYMINOR" -lt 10 ]]); then
        echo -e "  ${YELLOW}⚠️  Python 3.10+ required, found $PYVER${NC}"
        echo -e "  ${BLUE}Attempting to install Python 3.12...${NC}"
        if [[ "$OS" == "macos" ]]; then
            if command -v brew &>/dev/null; then
                brew install python@3.12
                python3.12 -m ensurepip
            else
                echo -e "${RED}❌ Homebrew not found. Install from https://brew.sh${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}Please install Python 3.10+ manually.${NC}"
            exit 1
        fi
    fi
else
    echo -e "  ${YELLOW}Python not found. Installing...${NC}"
    if [[ "$OS" == "macos" ]]; then
        if command -v brew &>/dev/null; then
            brew install python@3.12
        else
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install python@3.12
        fi
    else
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    fi
fi

# --- Check for git ---
echo -e "${BLUE}📦 Checking git...${NC}"
if ! command -v git &>/dev/null; then
    echo -e "  ${YELLOW}Installing git...${NC}"
    if [[ "$OS" == "macos" ]]; then
        brew install git
    else
        sudo apt-get install -y git
    fi
fi
echo -e "  ${GREEN}✓${NC} git $(git --version)"

# --- Create virtual environment ---
echo ""
echo -e "${BLUE}🔧 Creating virtual environment...${NC}"
cd "$INSTALL_DIR"
if [[ ! -d ".venv" ]]; then
    if [[ "$OS" == "macos" ]] && command -v python3.12 &>/dev/null; then
        python3.12 -m venv .venv
    else
        python3 -m venv .venv
    fi
fi
source .venv/bin/activate
pip install --upgrade pip -q
echo -e "  ${GREEN}✓${NC} Virtual environment ready"

# --- Install inference server ---
echo ""
echo -e "${BLUE}🧠 Setting up local AI model...${NC}"

if [[ "$OS" == "macos" ]] && [[ "$ARCH" == "arm64" ]]; then
    # macOS Apple Silicon — use MLX
    echo -e "  ${CYAN}Platform: Apple Silicon — using MLX${NC}"
    pip install mlx-lm -q
    
    # Model selection — smallest uncensored Qwen3 that fits
    MODEL_ID="mlx-community/Qwen2.5-7B-Instruct-4bit"
    
    echo -e "  ${BLUE}Downloading model: $MODEL_ID${NC}"
    echo -e "  ${YELLOW}(This may take a few minutes depending on your internet)...${NC}"
    
    # Download model
    pip install huggingface_hub -q
    python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('$MODEL_ID', local_dir='$INSTALL_DIR/model')
print('Model downloaded successfully')
" 2>/dev/null || {
        echo -e "${RED}❌ Failed to download model. Check your internet connection.${NC}"
        exit 1
    }
    
    # Start MLX server in background
    echo -e "  ${BLUE}Starting MLX inference server on port 8087...${NC}"
    nohup python3 -m mlx_lm.server \
        --model "$INSTALL_DIR/model" \
        --port 8087 \
        --host 0.0.0.0 \
        > "$INSTALL_DIR/mlx-server.log" 2>&1 &
    MLX_PID=$!
    echo $MLX_PID > "$INSTALL_DIR/mlx.pid"
    echo -e "  ${GREEN}✓${NC} MLX server started (PID $MLX_PID)"
    
else
    # Linux or Intel Mac — use llama.cpp
    echo -e "  ${CYAN}Platform: Linux/Intel — using llama.cpp${NC}"
    
    # Install llama.cpp
    if [[ ! -d "$INSTALL_DIR/llama.cpp" ]]; then
        echo -e "  ${BLUE}Building llama.cpp...${NC}"
        git clone https://github.com/ggml-org/llama.cpp.git "$INSTALL_DIR/llama.cpp"
        cd "$INSTALL_DIR/llama.cpp"
        cmake -B build -DGGML_NATIVE=ON
        cmake --build build --config Release -j$(nproc 2>/dev/null || echo 4)
        cd "$INSTALL_DIR"
    fi
    
    LLLAMA_BIN="$INSTALL_DIR/llama.cpp/build/bin/llama-server"
    if [[ ! -f "$LLLAMA_BIN" ]]; then
        LLLAMA_BIN="$INSTALL_DIR/llama.cpp/build/bin/llama-server"
    fi
    
    # Download model (GGUF format)
    MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
    MODEL_FILE="$INSTALL_DIR/model.gguf"
    
    if [[ ! -f "$MODEL_FILE" ]]; then
        echo -e "  ${BLUE}Downloading model...${NC}"
        echo -e "  ${YELLOW}(This may take a few minutes)...${NC}"
        curl -L -o "$MODEL_FILE" "$MODEL_URL" || {
            echo -e "${RED}❌ Failed to download model.${NC}"
            exit 1
        }
    fi
    
    # Start llama.cpp server
    echo -e "  ${BLUE}Starting llama.cpp server on port 8087...${NC}"
    nohup "$LLLAMA_BIN" \
        -m "$MODEL_FILE" \
        --port 8087 \
        --host 0.0.0.0 \
        -c 4096 \
        -np 2 \
        > "$INSTALL_DIR/llama-server.log" 2>&1 &
    LLAMA_PID=$!
    echo $LLAMA_PID > "$INSTALL_DIR/llama.pid"
    echo -e "  ${GREEN}✓${NC} llama.cpp server started (PID $LLAMA_PID)"
fi

# --- Wait for inference server to be ready ---
echo ""
echo -e "${BLUE}⏳ Waiting for AI model to warm up...${NC}"
MAX_WAIT=60
WAITED=0
while ! curl -s http://localhost:8087/v1/models | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; do
    sleep 2
    WAITED=$((WAITED + 2))
    if [[ $WAITED -ge $MAX_WAIT ]]; then
        echo -e "${RED}❌ Model server didn't start within ${MAX_WAIT}s${NC}"
        echo -e "Check logs: $INSTALL_DIR/mlx-server.log or $INSTALL_DIR/llama-server.log"
        exit 1
    fi
    echo -ne "  Waiting... ${WAITED}s\r"
done
echo -e "  ${GREEN}✓${NC} AI model is ready on port 8087"

# --- Download the bootstrap agent ---
echo ""
echo -e "${BLUE}🤖 Downloading bootstrap agent...${NC}"

# Download the agent script from the Mesh Master repo
AGENT_URL="https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/bootstrap/bootstrap_agent.py"
curl -fsSL "$AGENT_URL" -o "$INSTALL_DIR/bootstrap_agent.py" || {
    echo -e "${RED}❌ Failed to download bootstrap agent.${NC}"
    echo -e "You can find it at: $AGENT_URL"
    exit 1
}
echo -e "  ${GREEN}✓${NC} Bootstrap agent downloaded"

# --- Install agent dependencies ---
pip install requests -q

# --- Launch the AI agent ---
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                           ║${NC}"
echo -e "${CYAN}║   🚀 LAUNCHING AI BOOTSTRAP AGENT                         ║${NC}"
echo -e "${CYAN}║                                                           ║${NC}"
echo -e "${CYAN}║   The agent will now guide you through the rest of        ║${NC}"
echo -e "${CYAN}║   the installation. It has terminal access and can        ║${NC}"
echo -e "${CYAN}║   install software, create configs, and set up your       ║${NC}"
echo -e "${CYAN}║   Telegram bot.                                           ║${NC}"
echo -e "${CYAN}║                                                           ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Run the agent
python3 "$INSTALL_DIR/bootstrap_agent.py" \
    --install-dir "$INSTALL_DIR" \
    --model-endpoint "http://localhost:8087/v1" \
    --os "$OS" \
    --arch "$ARCH"

echo ""
echo -e "${GREEN}✅ Bootstrap complete!${NC}"
echo -e "Your Hermes agent should now be running."
