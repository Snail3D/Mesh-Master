#!/bin/bash
# Mesh Master Start Script - Unix/macOS

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

# Change to project directory
cd "/home/snailpi/Programs/mesh-ai"

# Activate virtual environment if it exists
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

# Start Mesh Master in background
echo "Starting Mesh Master..."
nohup python3 mesh-master.py > /dev/null 2>&1 &

# Wait for server to start
sleep 5

# Open browser (platform-specific)
echo "Opening dashboard..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:5000/dashboard
else
    # Linux
    xdg-open http://localhost:5000/dashboard 2>/dev/null ||     sensible-browser http://localhost:5000/dashboard 2>/dev/null ||     x-www-browser http://localhost:5000/dashboard 2>/dev/null ||     echo "Please open http://localhost:5000/dashboard in your browser"
fi

echo ""
echo "========================================"
echo "  Mesh Master Started!"
echo "  Dashboard: http://localhost:5000"
echo "========================================"
