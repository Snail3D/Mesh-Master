#!/bin/bash
# Mesh Master Bot v2.0 - One-Shot Training Script
# Optimized for Llama-3.2-1B with anti-overfitting measures
#
# Usage: bash train_mesh_master.sh
#
# Requirements:
# - GPU with 16GB+ VRAM (or 24GB for safe margin)
# - CUDA 11.8+
# - Python 3.10+
# - HuggingFace token with Llama-3.2 access

set -e  # Exit on error

echo "🤖 Mesh Master Bot v2.0 Training Script"
echo "========================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================
# Configuration
# ============================================
TRAINING_DIR="$(pwd)/training_run"
DATA_FILE="${1:-mesh_conversations.jsonl}"
HF_TOKEN="${HF_TOKEN:-}"
WANDB_PROJECT="mesh-master-bot-v2"

echo "📁 Working directory: $TRAINING_DIR"
echo "📊 Training data: $DATA_FILE"
echo ""

# ============================================
# Step 1: Check Prerequisites
# ============================================
echo "🔍 Checking prerequisites..."

# Check GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}❌ NVIDIA GPU not found! This script requires CUDA.${NC}"
    exit 1
fi

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)
echo -e "${GREEN}✅ GPU: $GPU_NAME ($GPU_MEM)${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

# Check training data
if [ ! -f "$DATA_FILE" ]; then
    echo -e "${RED}❌ Training data not found: $DATA_FILE${NC}"
    echo ""
    echo "Create a ShareGPT format JSONL file with your training data:"
    echo '{"conversations": [{"from": "human", "value": "question"}, {"from": "gpt", "value": "answer"}]}'
    echo ""
    exit 1
fi

LINE_COUNT=$(wc -l < "$DATA_FILE")
echo -e "${GREEN}✅ Training data: $LINE_COUNT examples${NC}"

# Check HuggingFace token
if [ -z "$HF_TOKEN" ]; then
    echo ""
    echo -e "${YELLOW}🔑 HuggingFace token required${NC}"
    echo "Get one at: https://huggingface.co/settings/tokens"
    echo "(Must have access to meta-llama/Llama-3.2-1B-Instruct)"
    echo ""
    read -sp "Enter HuggingFace token: " HF_TOKEN
    echo ""
fi

echo ""

# ============================================
# Step 2: Setup Environment
# ============================================
echo "📦 Setting up environment..."

mkdir -p "$TRAINING_DIR"
cd "$TRAINING_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies (this may take 5-10 minutes)..."
pip install -q --upgrade pip

pip install -q \
    torch==2.5.1 \
    transformers==4.46.2 \
    datasets==3.0.2 \
    accelerate==1.1.1 \
    peft==0.13.2 \
    bitsandbytes==0.44.1 \
    wandb \
    huggingface_hub

# Install axolotl
pip install -q git+https://github.com/axolotl-ai-cloud/axolotl.git@main

# Try flash-attention (may fail on some systems)
pip install -q flash-attn==2.7.0.post2 2>/dev/null || echo "⚠️ Flash attention not available (CPU fallback)"

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# ============================================
# Step 3: Login to HuggingFace
# ============================================
echo "🔐 Authenticating with HuggingFace..."

python3 << EOF
from huggingface_hub import login
login(token="$HF_TOKEN")
print("✅ Logged in!")
EOF

echo ""

# ============================================
# Step 4: Create Training Config
# ============================================
echo "⚙️ Creating training configuration..."

cat > training_config.yaml << 'YAML'
# Mesh Master Bot v2.0 - Optimized Training Config
# Base: Llama-3.2-1B-Instruct
# Key fixes: 1 epoch, 10x lower LR, proper regularization

base_model: meta-llama/Llama-3.2-1B-Instruct
model_type: LlamaForCausalLM
tokenizer_type: AutoTokenizer
trust_remote_code: true

# QLoRA - Memory Efficient Fine-Tuning
load_in_4bit: true
adapter: qlora
lora_r: 8
lora_alpha: 16
lora_dropout: 0.15
lora_target_linear: true
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj

# Sequence & Batching
sequence_len: 2048
sample_packing: true
pad_to_sequence_len: true
micro_batch_size: 2
gradient_accumulation_steps: 16
eval_batch_size: 2
num_epochs: 1

# Learning Rate (CRITICAL - 10x lower than v1!)
optimizer: adamw_8bit
lr_scheduler: cosine
learning_rate: 0.00002
warmup_steps: 50
warmup_ratio: 0.05
weight_decay: 0.01

# Precision
bf16: auto
fp16: false
tf32: true
flash_attention: true
gradient_checkpointing: true

# Dataset
datasets:
  - path: TRAINING_DATA_PATH
    type: sharegpt
    conversation: conversations

val_set_size: 0.15

# Evaluation & Checkpointing
evaluation_strategy: steps
eval_steps: 50
save_steps: 100
logging_steps: 5
output_dir: ./outputs
save_strategy: steps
save_total_limit: 3

# Early Stopping (Prevent Overfitting!)
early_stopping_patience: 3
load_best_model_at_end: true
metric_for_best_model: eval_loss
greater_is_better: false

# Tokens
special_tokens:
  bos_token: "<|begin_of_text|>"
  eos_token: "<|end_of_text|>"
  unk_token: "<|unk|>"

chat_template: llama3
seed: 42

# Logging
wandb_project: WANDB_PROJECT_NAME
wandb_name: mesh-1b-bash-run
YAML

# Replace placeholders
sed -i "s|TRAINING_DATA_PATH|$(realpath $DATA_FILE)|g" training_config.yaml
sed -i "s|WANDB_PROJECT_NAME|$WANDB_PROJECT|g" training_config.yaml

echo -e "${GREEN}✅ Config created: training_config.yaml${NC}"
echo ""

# ============================================
# Step 5: Start Training
# ============================================
echo "🚀 Starting training..."
echo "This will take 2-4 hours depending on your GPU and dataset size."
echo ""

START_TIME=$(date +%s)

accelerate launch -m axolotl.cli.train training_config.yaml

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))

echo ""
echo -e "${GREEN}✅ Training completed in ${HOURS}h ${MINUTES}m${NC}"
echo ""

# ============================================
# Step 6: Merge LoRA Adapters
# ============================================
echo "🔀 Merging LoRA adapters into base model..."

python3 -m axolotl.cli.merge_lora \
  training_config.yaml \
  --lora_model_dir=./outputs \
  --load_in_4bit=False \
  --load_in_8bit=False

echo -e "${GREEN}✅ Model merged${NC}"
echo ""

# ============================================
# Step 7: Convert to GGUF for Ollama
# ============================================
echo "📦 Converting to GGUF format for Ollama..."

pip install -q llama-cpp-python gguf

# Find the conversion script
CONVERT_SCRIPT=$(python3 -c "import llama_cpp; import os; print(os.path.join(os.path.dirname(llama_cpp.__file__), 'llama_cpp/convert-hf-to-gguf.py'))")

if [ ! -f "$CONVERT_SCRIPT" ]; then
    echo -e "${RED}❌ Conversion script not found!${NC}"
    echo "Manual conversion required - see outputs/merged directory"
    exit 1
fi

python3 "$CONVERT_SCRIPT" \
  ./outputs/merged \
  --outfile mesh-master-bot-v2.gguf \
  --outtype q8_0

GGUF_SIZE=$(du -h mesh-master-bot-v2.gguf | cut -f1)
echo -e "${GREEN}✅ GGUF created: mesh-master-bot-v2.gguf ($GGUF_SIZE)${NC}"
echo ""

# ============================================
# Step 8: Create Modelfile
# ============================================
echo "📝 Creating Ollama Modelfile..."

cat > Modelfile << 'MODELFILE'
FROM ./mesh-master-bot-v2.gguf

# Anti-repetition parameters (CRITICAL!)
PARAMETER temperature 0.5
PARAMETER repeat_penalty 1.15
PARAMETER num_predict 200
PARAMETER top_p 0.85
PARAMETER top_k 30

# Stop tokens
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"

# Context window
PARAMETER num_ctx 2048

# System prompt optimized for mesh networks
SYSTEM You are Mesh Master, an AI assistant for Meshtastic mesh networks. Keep responses concise (ideally under 160 characters) for LoRa bandwidth efficiency. Be accurate, helpful, and direct. Never repeat yourself.
MODELFILE

echo -e "${GREEN}✅ Modelfile created${NC}"
echo ""

# ============================================
# Step 9: Test the Model (Optional)
# ============================================
echo "🧪 Testing model..."

python3 << 'TESTPY'
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print("Loading model...")
model_path = "./outputs/merged"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

def test(question):
    messages = [{"role": "user", "content": question}]
    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        input_ids,
        max_new_tokens=150,
        temperature=0.5,
        repetition_penalty=1.15,
        do_sample=True
    )

    response = tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
    print(f"\nQ: {question}")
    print(f"A: {response}")
    print(f"Length: {len(response)} chars")

print("\n" + "="*60)
print("Test Questions:")
print("="*60)

test("How do I relay to alice?")
test("What's a meshtastic router?")
test("Hey are you there?")

print("\n" + "="*60)
print("✅ Testing complete!")
print("="*60)
TESTPY

echo ""

# ============================================
# Step 10: Summary & Next Steps
# ============================================
echo "🎉 Training Complete!"
echo "===================="
echo ""
echo "📂 Output files:"
echo "  - mesh-master-bot-v2.gguf  (Ollama model, $GGUF_SIZE)"
echo "  - Modelfile                 (Import config)"
echo "  - outputs/merged/           (Full model)"
echo ""
echo "📥 To use on your Raspberry Pi:"
echo ""
echo "  1. Copy files:"
echo "     scp mesh-master-bot-v2.gguf Modelfile pi@raspberrypi:/home/pi/"
echo ""
echo "  2. Import to Ollama:"
echo "     ssh pi@raspberrypi"
echo "     ollama create mesh-master-bot-v2 -f Modelfile"
echo ""
echo "  3. Test it:"
echo "     ollama run mesh-master-bot-v2 \"How do I relay to alice?\""
echo ""
echo "  4. Update Mesh Master config:"
echo "     nano /home/pi/Programs/mesh-ai/config.json"
echo "     Change: \"ollama_model\": \"mesh-master-bot-v2\""
echo ""
echo "  5. Restart service:"
echo "     sudo systemctl restart mesh-ai"
echo ""
echo -e "${GREEN}✅ All done! Good luck with your model!${NC}"
echo ""
