#!/bin/bash
# Quick model switcher for Mesh Master
# Usage: ./switch_model.sh <model_name>

if [ -z "$1" ]; then
    echo "Usage: ./switch_model.sh <model_name>"
    echo ""
    echo "Available models:"
    ollama list
    echo ""
    echo "Current model:"
    grep "ollama_model" config.json
    exit 1
fi

MODEL="$1"

# Update config.json
echo "Switching to model: $MODEL"
sed -i "s/\"ollama_model\": \".*\"/\"ollama_model\": \"$MODEL\"/" config.json

# Show what we changed to
echo "Updated config:"
grep "ollama_model" config.json

# Restart service
echo "Restarting mesh-ai service..."
sudo systemctl restart mesh-ai

echo "Done! Model switched to $MODEL"
echo "Check status: sudo systemctl status mesh-ai"
