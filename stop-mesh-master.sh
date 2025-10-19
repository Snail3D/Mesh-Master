#!/bin/bash
# Mesh Master Stop Script - Unix/macOS

echo "========================================"
echo "  Stopping Mesh Master"
echo "========================================"
echo ""

# Kill all instances
pkill -f "python.*mesh-master.py"
pkill -f "mesh-master.py"

# Kill zombies forcefully
ps aux | grep "[m]esh-master.py" | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Also kill any Flask processes on port 5001
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

echo ""
echo "========================================"
echo "  Mesh Master Stopped"
echo "========================================"
