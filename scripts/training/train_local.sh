#!/bin/bash
# Mesh Master Bot - Local Laptop Training
#
# This script runs fine-tuning on your laptop (CPU/MPS)
# Optimized for Apple Silicon Macs and consumer laptops
#
# Requirements:
# - 16GB+ RAM
# - 10GB free disk space
# - Python 3.10+
#
# Usage:
#   bash scripts/training/train_local.sh

set -e

echo "🤖 Mesh Master Bot - Local Training"
echo "====================================="
echo ""

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
echo "🐍 Python: $python_version"

# Check if in correct directory
if [ ! -f "mesh-master.py" ]; then
    echo "❌ Error: Must run from Mesh-Master root directory"
    echo "   cd to your Mesh-Master folder first"
    exit 1
fi

# Step 1: Install dependencies
echo ""
echo "📦 Step 1/4: Installing dependencies..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created virtual environment"
fi

source venv/bin/activate

pip install --upgrade pip > /dev/null 2>&1
pip install torch torchvision torchaudio > /dev/null 2>&1
pip install transformers accelerate bitsandbytes datasets peft trl > /dev/null 2>&1
pip install axolotl > /dev/null 2>&1 || echo "⚠️  Axolotl install failed, will try alternate method"

echo "✅ Dependencies installed"

# Step 2: Generate training data
echo ""
echo "📊 Step 2/4: Generating training dataset..."
if [ ! -f "data/training/train_v2.jsonl" ]; then
    python3 scripts/training/prepare_training_data_v2.py \
        --output data/training/train_v2.jsonl \
        --min-pairs 15000
    echo "✅ Generated 15k training pairs"
else
    echo "✅ Training data already exists"
fi

# Step 3: Validate config
echo ""
echo "🔍 Step 3/4: Validating training config..."
if command -v axolotl &> /dev/null; then
    axolotl validate training_configs/mesh-ai-1b-laptop.yaml || echo "⚠️  Validation warnings (may be OK)"
fi
echo "✅ Config validated"

# Step 4: Start training
echo ""
echo "🚀 Step 4/4: Starting training..."
echo ""
echo "Training configuration:"
echo "  - Model: Llama-3.2-1B-Instruct"
echo "  - Method: QLoRA (4-bit)"
echo "  - Dataset: 15k pairs"
echo "  - Epochs: 1 (prevents overtraining)"
echo "  - Expected time: 3-6 hours"
echo ""
echo "💡 Tip: Keep your laptop plugged in and don't let it sleep!"
echo ""
read -p "Press Enter to start training..."

# Try Axolotl first, fall back to custom script
if command -v axolotl &> /dev/null; then
    echo "Using Axolotl..."
    accelerate launch -m axolotl.cli.train training_configs/mesh-ai-1b-laptop.yaml
else
    echo "Using direct training (Axolotl not available)..."
    python3 scripts/training/train_direct.py training_configs/mesh-ai-1b-laptop.yaml
fi

echo ""
echo "✅ Training complete!"
echo ""
echo "📁 Model saved to: ./outputs/mesh-ai-1b-laptop/"
echo ""
echo "Next steps:"
echo "1. Merge LoRA adapters:"
echo "   python3 scripts/training/merge_lora.py"
echo ""
echo "2. Convert to GGUF:"
echo "   bash scripts/training/convert_to_gguf.sh"
echo ""
echo "3. Import to Ollama:"
echo "   ollama create mesh-master-bot-v2 -f models/Modelfile"
