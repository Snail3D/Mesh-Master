#!/bin/bash

# Mesh Master Setup Script
# Automatically sets up config.json from template

echo "========================================"
echo "  Mesh Master Setup"
echo "========================================"
echo ""

# Check if config.json already exists
if [ -f "config.json" ]; then
    echo "✅ config.json already exists"
    echo "   No changes made to preserve your settings"
else
    echo "📝 config.json not found"

    if [ -f "config.json.example" ]; then
        echo "   Copying config.json.example to config.json..."
        cp config.json.example config.json
        echo "✅ Created config.json from template"
        echo ""
        echo "⚠️  IMPORTANT: Edit config.json and change these settings:"
        echo "   - admin_password: Change from 'CHANGE_ME' to a secure password"
        echo "   - admin_password_hint: Add a helpful password hint"
        echo "   - serial_port: Set your Meshtastic device path (if using serial)"
        echo "   - auto_update_enabled: Set to true if you want automatic updates"
        echo ""
    else
        echo "❌ config.json.example not found!"
        echo "   Please create config.json manually"
        exit 1
    fi
fi

echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your settings"
echo "2. Run: python3 mesh-master.py"
echo "3. Access dashboard: http://localhost:5000/dashboard"
echo ""
