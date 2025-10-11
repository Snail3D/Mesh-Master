#!/bin/bash
# Mesh Master Bot v2.0 - MLX Training for Apple Silicon (M4 Mac Mini)
# Optimized for Metal GPU acceleration with unified memory

set -e

echo "🍎 Mesh Master Bot v2.0 - MLX Training for Apple Silicon"
echo "========================================================="
echo ""

# Configuration
MODEL_NAME="meta-llama/Llama-3.2-1B-Instruct"
OUTPUT_DIR="./training/outputs/mesh-master-mlx-v2"
DATA_PATH="./training/data/mesh_conversations.jsonl"
ADAPTER_PATH="${OUTPUT_DIR}/adapters"
MERGED_PATH="${OUTPUT_DIR}/merged"
GGUF_PATH="${OUTPUT_DIR}/mesh-master-bot-v2.gguf"

# MLX Training Parameters (optimized for M4)
LEARNING_RATE=0.00002      # Conservative to prevent overfitting
EPOCHS=1                    # Single pass only!
BATCH_SIZE=4                # M4 can handle this with unified memory
LORA_RANK=8                 # Small adapter
LORA_ALPHA=16
LORA_DROPOUT=0.15
MAX_SEQ_LENGTH=2048

# Check dependencies
echo "📦 Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+."
    exit 1
fi

# Check if running on Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo "⚠️  Warning: Not running on Apple Silicon. MLX is optimized for M-series chips."
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv-mlx" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv .venv-mlx
fi

echo "🔧 Activating virtual environment..."
source .venv-mlx/bin/activate

# Install MLX and dependencies
echo "📥 Installing MLX and dependencies..."
pip install --upgrade pip
pip install mlx-lm mlx transformers datasets huggingface_hub

# Check for training data
if [ ! -f "$DATA_PATH" ]; then
    echo "❌ Training data not found at: $DATA_PATH"
    echo "Please create mesh_conversations.jsonl with your training data."
    echo ""
    echo "Example format (ShareGPT):"
    echo '{"conversations": [{"from": "human", "value": "How do I relay?"}, {"from": "gpt", "value": "Use: alice <message>"}]}'
    exit 1
fi

# Count training examples
NUM_EXAMPLES=$(wc -l < "$DATA_PATH")
echo "✅ Found $NUM_EXAMPLES training examples"

# Authenticate with HuggingFace (for Llama-3.2 access)
echo ""
echo "🔑 HuggingFace Authentication Required"
echo "You need access to meta-llama/Llama-3.2-1B-Instruct"
echo "Get your token from: https://huggingface.co/settings/tokens"
echo ""
read -p "Enter your HuggingFace token (or press Enter to skip if already logged in): " HF_TOKEN

if [ ! -z "$HF_TOKEN" ]; then
    export HUGGING_FACE_HUB_TOKEN=$HF_TOKEN
    huggingface-cli login --token $HF_TOKEN
fi

# Create output directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$ADAPTER_PATH"
mkdir -p "$MERGED_PATH"

# Convert JSONL to MLX format
echo ""
echo "🔄 Converting training data to MLX format..."
python3 << 'PYTHON_SCRIPT'
import json
import sys

# Read ShareGPT JSONL
input_path = "./training/data/mesh_conversations.jsonl"
output_path = "./training/data/mesh_conversations_mlx.jsonl"

print(f"Reading from: {input_path}")
with open(input_path, 'r') as f_in:
    lines = f_in.readlines()

# Convert to MLX format (text completion style)
mlx_data = []
for line in lines:
    data = json.loads(line)
    convs = data.get('conversations', [])

    # Build conversation string
    text = ""
    for turn in convs:
        role = turn['from']
        content = turn['value']

        if role == 'human':
            text += f"<|begin_of_text|>user\n{content}\n\n"
        elif role == 'gpt':
            text += f"assistant\n{content}<|end_of_text|>\n"

    mlx_data.append({"text": text.strip()})

# Write MLX format
with open(output_path, 'w') as f_out:
    for item in mlx_data:
        f_out.write(json.dumps(item) + '\n')

print(f"✅ Converted {len(mlx_data)} examples to: {output_path}")
PYTHON_SCRIPT

# Start training
echo ""
echo "🚀 Starting LoRA fine-tuning with MLX..."
echo ""
echo "Configuration:"
echo "  Model: $MODEL_NAME"
echo "  Learning Rate: $LEARNING_RATE"
echo "  Epochs: $EPOCHS"
echo "  Batch Size: $BATCH_SIZE"
echo "  LoRA Rank: $LORA_RANK"
echo "  Max Sequence Length: $MAX_SEQ_LENGTH"
echo ""

# MLX LoRA fine-tuning
mlx_lm.lora \
    --model "$MODEL_NAME" \
    --train \
    --data "./training/data/mesh_conversations_mlx.jsonl" \
    --adapter-file "$ADAPTER_PATH" \
    --iters 1000 \
    --steps-per-eval 50 \
    --steps-per-report 10 \
    --save-every 100 \
    --learning-rate $LEARNING_RATE \
    --batch-size $BATCH_SIZE \
    --lora-layers 8 \
    --test-batches 5

echo ""
echo "✅ Training complete!"
echo ""

# Merge adapters with base model
echo "🔀 Merging LoRA adapters with base model..."
mlx_lm.fuse \
    --model "$MODEL_NAME" \
    --adapter-file "$ADAPTER_PATH" \
    --save-path "$MERGED_PATH" \
    --de-quantize

echo "✅ Model merged successfully!"
echo ""

# Convert to GGUF for Ollama
echo "🔄 Converting to GGUF format (Q8_0 quantization)..."
python3 << 'PYTHON_CONVERT'
import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

merged_path = "./training/outputs/mesh-master-mlx-v2/merged"
gguf_path = "./training/outputs/mesh-master-mlx-v2/mesh-master-bot-v2.gguf"

print(f"Loading merged model from: {merged_path}")
model = AutoModelForCausalLM.from_pretrained(merged_path)
tokenizer = AutoTokenizer.from_pretrained(merged_path)

# Save in GGUF format (requires llama.cpp)
print("Note: GGUF conversion requires llama.cpp")
print("You can convert manually using:")
print(f"  python llama.cpp/convert.py {merged_path} --outtype q8_0 --outfile {gguf_path}")
PYTHON_CONVERT

echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Convert to GGUF using llama.cpp (if not done):"
echo "   git clone https://github.com/ggerganov/llama.cpp"
echo "   cd llama.cpp && make"
echo "   python convert.py $MERGED_PATH --outtype q8_0 --outfile $GGUF_PATH"
echo ""
echo "2. Copy files to your Raspberry Pi:"
echo "   scp $GGUF_PATH snailpi@raspberrypi:/home/snailpi/"
echo "   scp training/models/Modelfile.mesh-master-v2 snailpi@raspberrypi:/home/snailpi/Modelfile"
echo ""
echo "3. Create Ollama model on Pi:"
echo "   ollama create mesh-master-bot-v2 -f /home/snailpi/Modelfile"
echo ""
echo "4. Test the model:"
echo "   ollama run mesh-master-bot-v2 'How do I relay to alice?'"
echo ""
echo "5. Update Mesh Master config:"
echo "   Edit config.json: \"ollama_model\": \"mesh-master-bot-v2\""
echo "   sudo systemctl restart mesh-ai"
echo ""
echo "✅ Training complete! Model files in: $OUTPUT_DIR"
