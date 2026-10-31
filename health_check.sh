#!/usr/bin/env bash
# MESH-MASTER Health Check Script
# This script checks if MESH-MASTER is running properly

set -euo pipefail

echo "🔍 MESH-MASTER Health Check $(date)"
echo "=================================="

# Check if service is enabled
if systemctl is-enabled mesh-ai.service &>/dev/null; then
    echo "✅ Service enabled for auto-start"
else
    echo "❌ Service NOT enabled for auto-start"
    exit 1
fi

# Check if service is active
if systemctl is-active mesh-ai.service &>/dev/null; then
    echo "✅ Service is running"
else
    echo "❌ Service is NOT running"
    exit 1
fi

# Check if web interface is responding
PORT="${MESH_MASTER_PORT:-5001}"
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/dashboard" | grep -q "200"; then
    echo "✅ Web interface responding on port ${PORT}"
else
    echo "❌ Web interface NOT responding"
    exit 1
fi

# Check if RAK device is connected
if ls /dev/serial/by-id/usb-RAKwireless* &>/dev/null; then
    echo "✅ RAK device detected"
    
    # Check autosuspend status
    for dev in /sys/bus/usb/devices/*; do 
        if [ -f "$dev/idVendor" ] && grep -q "239a" "$dev/idVendor" 2>/dev/null; then
            control_status=$(cat "$dev/power/control" 2>/dev/null || echo "unknown")
            if [ "$control_status" = "on" ]; then
                echo "✅ USB autosuspend disabled (control: $control_status)"
            else
                echo "⚠️  USB autosuspend status: $control_status"
            fi
            break
        fi
    done
else
    echo "❌ RAK device NOT detected"
fi

# Check service logs for recent errors
if journalctl -u mesh-ai.service --since "5 minutes ago" --no-pager -q | grep -i error; then
    echo "⚠️  Recent errors found in service logs"
else
    echo "✅ No recent errors in service logs"
fi

echo "=================================="
echo "🎯 MESH-MASTER appears to be healthy!"