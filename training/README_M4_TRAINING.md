# 🍎 Training Mesh Master Bot on Mac Mini M4

**MLX-optimized training for Apple Silicon with Metal acceleration**

---

## Why Train on Mac M4?

The Mac Mini M4 is actually **excellent** for fine-tuning small LLMs:

✅ **Unified memory** - No GPU/CPU data transfer bottleneck
✅ **Neural Engine** - Hardware acceleration for ML operations
✅ **Metal backend** - Native GPU acceleration via MLX
✅ **Energy efficient** - Lower power than cloud GPUs
✅ **No cloud costs** - Train locally for free
✅ **Fast** - M4 can train 1B models in 1-2 hours

### Expected Performance:
- **Llama-3.2-1B with LoRA:** ~1-2 hours (with 1000-2000 examples)
- **Memory usage:** ~4-6GB (easily fits in base 16GB model)
- **Cost:** $0 (vs $5-20 for cloud GPUs)

---

## Prerequisites

### 1. Install Python 3.10+

macOS Sonoma/Sequoia usually has Python 3.9, so install a newer version:

```bash
# Using Homebrew
brew install python@3.11

# Verify version
python3 --version  # Should show 3.10 or higher
```

### 2. Install MLX and Dependencies

```bash
# Create project directory
mkdir -p ~/mesh-master-training
cd ~/mesh-master-training

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install MLX (Apple Silicon optimized)
pip install --upgrade pip
pip install mlx mlx-lm transformers datasets huggingface_hub
```

### 3. Get HuggingFace Access

You need access to Llama-3.2-1B-Instruct:

1. Go to: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
2. Click "Request Access" (usually approved instantly)
3. Get your token: https://huggingface.co/settings/tokens
4. Login: `huggingface-cli login`

---

## Quick Start

### Method 1: Simple Python Script (Recommended)

```bash
# Download the training files from GitHub
git clone https://github.com/Snail3D/Mesh-Master.git
cd Mesh-Master/training

# Activate virtual environment
source ~/.venv/bin/activate  # Or wherever you created it

# Prepare your training data (see format below)
# Create: training/data/mesh_conversations.jsonl

# Run training setup
python3 scripts/train_mlx_simple.py
```

This will:
1. Convert your training data to MLX format
2. Show you the exact commands to run
3. Guide you through the full process

### Method 2: All-in-One Bash Script

```bash
cd Mesh-Master/training
chmod +x scripts/train_mlx_m4.sh
./scripts/train_mlx_m4.sh
```

---

## Training Data Format

Create `training/data/mesh_conversations.jsonl` in ShareGPT format:

```jsonl
{"conversations": [{"from": "human", "value": "How do I relay to alice?"}, {"from": "gpt", "value": "Just type: alice <your message>"}]}
{"conversations": [{"from": "human", "value": "What's a meshtastic router?"}, {"from": "gpt", "value": "A router node that ONLY relays messages—doesn't send/receive its own."}]}
{"conversations": [{"from": "human", "value": "Hey are you still there?"}, {"from": "gpt", "value": "Yep, still here! What can I help with?"}]}
```

### Tips for Good Training Data:

✅ **500-2000 examples** - Quality over quantity
✅ **Short responses** - Under 160 chars ideal (LoRa bandwidth limit)
✅ **Mix technical + casual** - Show personality
✅ **Conversational** - Not just command lists
✅ **Varied phrasing** - Same question asked different ways

❌ **Don't repeat patterns** - Causes overfitting
❌ **Don't use jargon without context** - Model needs to learn meanings
❌ **Don't make responses too long** - Mesh bandwidth is limited

---

## Training Process

### Step 1: Convert Data

```bash
python3 scripts/train_mlx_simple.py
```

This converts your ShareGPT JSONL to MLX format.

### Step 2: Start Training

```bash
mlx_lm.lora \
    --model meta-llama/Llama-3.2-1B-Instruct \
    --train \
    --data training/data/mesh_conversations_mlx.jsonl \
    --adapter-file training/outputs/mesh-master-mlx-v2/adapters \
    --iters 1000 \
    --steps-per-eval 50 \
    --steps-per-report 10 \
    --save-every 100 \
    --learning-rate 0.00002 \
    --batch-size 4 \
    --lora-layers 8
```

**What you'll see:**
```
Loading model meta-llama/Llama-3.2-1B-Instruct...
Model loaded (1.2GB)
Starting training...

Iter 10: Train loss 2.342, Val loss 2.318, Time 0.8s
Iter 20: Train loss 1.834, Val loss 1.821, Time 0.7s
Iter 50: Train loss 1.245, Val loss 1.267, Time 0.8s
...
Iter 1000: Train loss 0.823, Val loss 0.845, Time 0.7s

Training complete! Saved to: training/outputs/mesh-master-mlx-v2/adapters
```

**Training time:** ~1-2 hours on M4 (depends on dataset size)

**Watch for:**
- ✅ Both train and val loss decreasing = Good!
- ❌ Val loss increasing while train decreases = Overfitting! (stop early)

### Step 3: Merge Adapters

```bash
mlx_lm.fuse \
    --model meta-llama/Llama-3.2-1B-Instruct \
    --adapter-file training/outputs/mesh-master-mlx-v2/adapters \
    --save-path training/outputs/mesh-master-mlx-v2/merged \
    --de-quantize
```

This merges the LoRA adapters into the base model.

### Step 4: Test Locally (Before Converting)

```bash
mlx_lm.generate \
    --model training/outputs/mesh-master-mlx-v2/merged \
    --prompt "How do I relay to alice?" \
    --max-tokens 100
```

**Expected output:**
```
Just type: alice <your message>
```

**Red flags:**
- Repeating text infinitely
- Long rambling responses
- Hallucinating commands
- Generic/robotic answers

If you see these, retrain with:
- Lower learning rate (0.00001)
- More diverse training data
- Fewer iterations

### Step 5: Convert to GGUF

You need `llama.cpp` for this:

```bash
# Clone llama.cpp (one-time setup)
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Convert model to GGUF Q8_0 (high quality, ~450MB)
python convert.py ../Mesh-Master/training/outputs/mesh-master-mlx-v2/merged \
    --outtype q8_0 \
    --outfile ../Mesh-Master/training/outputs/mesh-master-mlx-v2/mesh-master-bot-v2.gguf
```

**File sizes:**
- MLX merged model: ~1.3GB
- GGUF Q8_0: ~450MB (this is what you'll use)

---

## Deploy to Raspberry Pi

### Step 1: Transfer Files

```bash
# From your Mac
cd ~/Mesh-Master/training

# Copy GGUF model
scp outputs/mesh-master-mlx-v2/mesh-master-bot-v2.gguf snailpi@<pi-ip>:/home/snailpi/

# Copy Modelfile
scp models/Modelfile.mesh-master-v2 snailpi@<pi-ip>:/home/snailpi/Modelfile
```

### Step 2: Create Ollama Model

```bash
# SSH to Pi
ssh snailpi@<pi-ip>

# Create Ollama model
cd /home/snailpi
ollama create mesh-master-bot-v2 -f Modelfile

# Test it
ollama run mesh-master-bot-v2 "How do I relay to alice?"
```

**Expected:** Short, helpful answer (not looping!)

### Step 3: Update Mesh Master Config

```bash
# Edit config
nano /home/snailpi/Programs/mesh-ai/config.json

# Change line:
"ollama_model": "mesh-master-bot-v2"

# Restart service
sudo systemctl restart mesh-ai

# Check logs
sudo journalctl -u mesh-ai -f
```

### Step 4: Test on Mesh Network

Send a DM to Mesh Master:
```
/ai How do I relay to alice?
```

Should respond concisely without looping!

---

## Troubleshooting

### "MLX not found"

```bash
# Reinstall MLX
pip uninstall mlx mlx-lm
pip install --upgrade mlx mlx-lm
```

### "Model download failed"

- Check internet connection
- Verify HuggingFace access to Llama-3.2
- Try: `huggingface-cli login` again

### "Out of memory"

- Close other apps
- Reduce batch size to 2:
  ```bash
  --batch-size 2
  ```

### "Training too slow"

- Normal for M4: ~1-2 hours for 1000 iterations
- Speed up by reducing iterations:
  ```bash
  --iters 500  # Faster but may underfit
  ```

### "Model still repeating text"

Check Modelfile has:
```
PARAMETER repeat_penalty 1.15
```

If issue persists:
1. Retrain with lower learning rate (0.00001)
2. Add more diverse examples
3. Reduce LoRA rank to 4

### "Responses too long"

In Modelfile:
```
PARAMETER num_predict 150  # Stricter limit
```

Also add more short-response examples to training data.

---

## Advantages of M4 Training

| Feature | Mac M4 | Google Colab Free | Cloud GPU |
|---------|--------|-------------------|-----------|
| **Cost** | $0 | $0 | $5-20/hour |
| **Speed** | 1-2 hours | 2-3 hours | 45-60 min |
| **Memory** | 16GB+ unified | 12GB limited | Varies |
| **Stability** | No timeouts | 12hr limit | Stable |
| **Privacy** | 100% local | Google sees data | Provider sees data |
| **Convenience** | Works offline | Needs internet | Needs internet |

**Verdict:** M4 is perfect for this task! Local, fast, private, and cost-free.

---

## Advanced Tuning

### If Model is Too Random/Creative:

```bash
# Lower learning rate
--learning-rate 0.00001

# In Modelfile
PARAMETER temperature 0.3
```

### If Model is Too Robotic:

```bash
# In Modelfile
PARAMETER temperature 0.6

# Add more personality examples to training data
```

### If You Want Faster Training:

```bash
# Increase batch size (if memory allows)
--batch-size 8

# Reduce iterations
--iters 500
```

### If You Want Higher Quality:

```bash
# More iterations
--iters 2000

# Higher quantization (larger file)
--outtype q8_0  # Best quality
--outtype f16   # Even better, but 2x size
```

---

## File Locations

After training, you'll have:

```
training/
├── outputs/
│   └── mesh-master-mlx-v2/
│       ├── adapters/                    # LoRA weights (~30MB)
│       ├── merged/                      # Full merged model (~1.3GB)
│       └── mesh-master-bot-v2.gguf     # GGUF for Ollama (~450MB)
└── data/
    ├── mesh_conversations.jsonl         # Your training data
    └── mesh_conversations_mlx.jsonl     # MLX-converted format
```

**Keep:** `mesh-master-bot-v2.gguf` (this goes to Pi)
**Optional:** `adapters/` (for future fine-tuning)
**Delete:** `merged/` (large, not needed after GGUF conversion)

---

## Resources

- **MLX Documentation:** https://ml-explore.github.io/mlx/
- **MLX LM GitHub:** https://github.com/ml-explore/mlx-lm
- **Llama.cpp:** https://github.com/ggerganov/llama.cpp
- **Llama-3.2 Model Card:** https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct

---

## Success Checklist

Before deploying to your mesh network:

- [ ] Training completed without errors
- [ ] Validation loss decreased (not increased)
- [ ] Test prompt gives sensible answer
- [ ] No repetitive loops in test output
- [ ] Response length under 200 chars
- [ ] GGUF file size ~450MB
- [ ] Ollama `run` test works on Pi
- [ ] Modelfile has `repeat_penalty 1.15`

---

**Happy training on your M4! 🍎🚀**

Questions? Open an issue: https://github.com/Snail3D/Mesh-Master/issues
