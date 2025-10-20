#!/bin/bash
# Mesh Master Launcher - Unix/macOS

echo "========================================"
echo "  Starting Mesh Master"
echo "========================================"
echo ""

# Kill any existing instances
echo "Checking for old instances..."
pkill -f "python.*mesh-master.py" 2>/dev/null || true
pkill -f "mesh-master.py" 2>/dev/null || true

# Kill zombies
ps aux | grep "[m]esh-master.py" | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Set PYTHONPATH for utilities
export PYTHONPATH="$SCRIPT_DIR/scripts/utilities:$PYTHONPATH"

# Determine which Python to use (prefer venv)
PYTHON_EXEC="python3"
if [ -f .venv/bin/python3 ]; then
    PYTHON_EXEC=".venv/bin/python3"
fi

# Start Mesh Master in background
echo "Starting Mesh Master..."
nohup $PYTHON_EXEC mesh-master.py > mesh-master.log 2>&1 &

# Wait for server to start
sleep 5

# Open browser (platform-specific)
echo "Opening dashboard..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:5001/dashboard
else
    # Linux
    xdg-open http://localhost:5001/dashboard 2>/dev/null ||     sensible-browser http://localhost:5001/dashboard 2>/dev/null ||     x-www-browser http://localhost:5001/dashboard 2>/dev/null ||     echo "Please open http://localhost:5001/dashboard in your browser"
fi

echo ""
echo "========================================"
echo "  Mesh Master Started!"
echo "  Dashboard: http://localhost:5001"
echo "========================================"
