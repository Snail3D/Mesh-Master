#!/bin/bash
# Mesh Master Bot v2.0 - Google Colab Training Script
#
# To use in Colab:
# 1. Upload this script and your mesh_conversations.jsonl
# 2. Run: !bash colab_train.sh
#
# Or paste this entire script into a code cell and run it

set -e

echo "🤖 Mesh Master Bot v2.0 - Colab Training"
echo "========================================"
echo ""

# ============================================
# Check GPU
# ============================================
echo "🔍 Checking GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv
echo ""

# ============================================
# Install Dependencies
# ============================================
echo "📦 Installing dependencies (~5 minutes)..."

pip install -q -U \
  git+https://github.com/axolotl-ai-cloud/axolotl.git@main \
  transformers==4.46.2 \
  datasets==3.0.2 \
  accelerate==1.1.1 \
  peft==0.13.2 \
  bitsandbytes==0.44.1 \
  flash-attn==2.7.0.post2 \
  wandb \
  huggingface_hub

echo "✅ Dependencies installed"
echo ""

# ============================================
# Login to HuggingFace
# ============================================
echo "🔐 HuggingFace Login"
echo "Get your token at: https://huggingface.co/settings/tokens"
echo ""

python3 << 'EOF'
from huggingface_hub import login
import getpass

token = getpass.getpass("Enter HuggingFace token: ")
login(token=token)
print("✅ Logged in!")
EOF

echo ""

# ============================================
# Check Training Data
# ============================================
DATA_FILE="${1:-/content/mesh_conversations.jsonl}"

if [ ! -f "$DATA_FILE" ]; then
    echo "❌ Training data not found: $DATA_FILE"
    echo ""
    echo "Upload mesh_conversations.jsonl to /content/"
    echo "Format: {\"conversations\": [{\"from\": \"human\", \"value\": \"Q\"}, {\"from\": \"gpt\", \"value\": \"A\"}]}"
    exit 1
fi

LINE_COUNT=$(wc -l < "$DATA_FILE")
echo "✅ Training data: $LINE_COUNT examples"
echo ""

# Show sample
echo "📝 Sample conversation:"
python3 << EOF
import json
with open("$DATA_FILE") as f:
    ex = json.loads(f.readline())
    for turn in ex['conversations']:
        role = "User" if turn['from'] == 'human' else "Assistant"
        print(f"{role}: {turn['value']}")
EOF

echo ""

# ============================================
# Create Training Config
# ============================================
echo "⚙️ Creating training config..."

cat > /content/training_config.yaml << 'YAML'
base_model: meta-llama/Llama-3.2-1B-Instruct
model_type: LlamaForCausalLM
tokenizer_type: AutoTokenizer
trust_remote_code: true

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

sequence_len: 2048
sample_packing: true
pad_to_sequence_len: true
micro_batch_size: 2
gradient_accumulation_steps: 16
eval_batch_size: 2
num_epochs: 1

optimizer: adamw_8bit
lr_scheduler: cosine
learning_rate: 0.00002
warmup_steps: 50
warmup_ratio: 0.05
weight_decay: 0.01

bf16: auto
fp16: false
tf32: true
flash_attention: true
gradient_checkpointing: true

datasets:
  - path: DATA_PATH_PLACEHOLDER
    type: sharegpt
    conversation: conversations

val_set_size: 0.15

evaluation_strategy: steps
eval_steps: 50
save_steps: 100
logging_steps: 5
output_dir: /content/outputs
save_strategy: steps
save_total_limit: 3

early_stopping_patience: 3
load_best_model_at_end: true
metric_for_best_model: eval_loss
greater_is_better: false

special_tokens:
  bos_token: "<|begin_of_text|>"
  eos_token: "<|end_of_text|>"
  unk_token: "<|unk|>"

chat_template: llama3
seed: 42

wandb_project: mesh-master-bot-v2
wandb_name: mesh-1b-colab
YAML

# Replace data path
sed -i "s|DATA_PATH_PLACEHOLDER|$DATA_FILE|g" /content/training_config.yaml

echo "✅ Config created"
echo ""

# ============================================
# Start Training
# ============================================
echo "🚀 Starting training..."
echo "⏱️ Estimated time: 2-3 hours on T4, 45-60min on A100"
echo ""

START=$(date +%s)

accelerate launch -m axolotl.cli.train /content/training_config.yaml

END=$(date +%s)
DURATION=$((END - START))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))

echo ""
echo "✅ Training completed in ${HOURS}h ${MINUTES}m"
echo ""

# ============================================
# Merge LoRA
# ============================================
echo "🔀 Merging LoRA adapters..."

python3 -m axolotl.cli.merge_lora \
  /content/training_config.yaml \
  --lora_model_dir=/content/outputs \
  --load_in_4bit=False \
  --load_in_8bit=False

echo "✅ Model merged"
echo ""

# ============================================
# Convert to GGUF
# ============================================
echo "📦 Converting to GGUF..."

pip install -q llama-cpp-python gguf

python3 -c "
from llama_cpp import llama_cpp
import sys
sys.argv = [
    'convert',
    '/content/outputs/merged',
    '--outfile', '/content/mesh-master-bot-v2.gguf',
    '--outtype', 'q8_0'
]
exec(open('/usr/local/lib/python3.10/dist-packages/llama_cpp/llama_cpp/convert-hf-to-gguf.py').read())
" 2>&1 | grep -v "Warning"

GGUF_SIZE=$(du -h /content/mesh-master-bot-v2.gguf | cut -f1)
echo "✅ GGUF created: $GGUF_SIZE"
echo ""

# ============================================
# Create Modelfile
# ============================================
echo "📝 Creating Modelfile..."

cat > /content/Modelfile << 'MODELFILE'
FROM ./mesh-master-bot-v2.gguf

PARAMETER temperature 0.5
PARAMETER repeat_penalty 1.15
PARAMETER num_predict 200
PARAMETER top_p 0.85
PARAMETER top_k 30

PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"

PARAMETER num_ctx 2048

SYSTEM You are Mesh Master, an AI assistant for Meshtastic mesh networks. Keep responses concise (ideally under 160 characters) for LoRa bandwidth efficiency. Be accurate, helpful, and direct. Never repeat yourself.
MODELFILE

echo "✅ Modelfile created"
echo ""

# ============================================
# Test Model
# ============================================
echo "🧪 Testing model..."
echo ""

python3 << 'TESTPY'
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained("/content/outputs/merged")
model = AutoModelForCausalLM.from_pretrained(
    "/content/outputs/merged",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

def test(q):
    msgs = [{"role": "user", "content": q}]
    ids = tokenizer.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
    out = model.generate(ids, max_new_tokens=150, temperature=0.5, repetition_penalty=1.15, do_sample=True)
    resp = tokenizer.decode(out[0][ids.shape[-1]:], skip_special_tokens=True)
    print(f"\nQ: {q}")
    print(f"A: {resp}")
    print(f"Length: {len(resp)} chars")

print("\n" + "="*60)
test("How do I relay to alice?")
test("What's a meshtastic router?")
test("Hey are you there?")
print("="*60)
print("\n✅ Testing complete!")
TESTPY

echo ""

# ============================================
# Download Files
# ============================================
echo "📥 Preparing downloads..."

python3 << 'DLPY'
from google.colab import files
import os

print("\nDownloading files to your computer...")
print("This may take a few minutes for the GGUF file (~450MB)")
print("")

if os.path.exists('/content/mesh-master-bot-v2.gguf'):
    files.download('/content/mesh-master-bot-v2.gguf')
    print("✅ Downloaded: mesh-master-bot-v2.gguf")

if os.path.exists('/content/Modelfile'):
    files.download('/content/Modelfile')
    print("✅ Downloaded: Modelfile")

print("\n" + "="*60)
print("🎉 ALL DONE!")
print("="*60)
DLPY

echo ""
echo "📦 Next Steps:"
echo ""
echo "1. Import to Ollama on your Pi:"
echo "   scp mesh-master-bot-v2.gguf Modelfile pi@raspberrypi:/home/pi/"
echo "   ssh pi@raspberrypi"
echo "   ollama create mesh-master-bot-v2 -f Modelfile"
echo ""
echo "2. Test it:"
echo "   ollama run mesh-master-bot-v2 \"How do I relay to alice?\""
echo ""
echo "3. Update Mesh Master:"
echo "   nano /home/pi/Programs/mesh-ai/config.json"
echo "   Change: \"ollama_model\": \"mesh-master-bot-v2\""
echo "   sudo systemctl restart mesh-ai"
echo ""
echo "✅ Training complete!"
