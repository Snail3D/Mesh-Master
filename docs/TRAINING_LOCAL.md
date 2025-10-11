# Training Mesh Master Bot on Your Laptop

Quick guide for training the Mesh Master Bot v2 locally on your laptop (no cloud GPU needed).

## Requirements

- **RAM:** 16GB minimum (32GB recommended)
- **Storage:** 10GB free space
- **Time:** 3-6 hours (depends on CPU/GPU)
- **OS:** macOS (Apple Silicon preferred), Linux, or Windows WSL

## Quick Start

### 1. Install Dependencies

```bash
cd /path/to/Mesh-Master

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install --upgrade pip
pip install torch transformers accelerate bitsandbytes datasets peft trl
pip install "axolotl[flash-attn] @ git+https://github.com/OpenAccess-AI-Collective/axolotl.git"
```

### 2. Generate Training Data

```bash
# Generate 15k high-quality training pairs (reduced from 50k to prevent overtraining)
python3 scripts/training/prepare_training_data_v2.py \
    --output data/training/train_v2.jsonl \
    --min-pairs 15000
```

**Output:**
```
✅ Generated 3k core command pairs
✅ Generated 8 troubleshooting pairs
✅ Generated 3 identity pairs
✅ Generated 6 concept pairs
📄 Train: 12750 pairs → data/training/train_v2.jsonl
📄 Val: 2250 pairs → data/training/val_v2.jsonl
```

### 3. Review Training Config

The laptop-optimized config (`training_configs/mesh-ai-1b-laptop.yaml`) uses:

- **1 epoch** (prevents overtraining - was 3 in v1.0)
- **Lower learning rate** (0.00005 vs 0.0002)
- **Smaller LoRA rank** (8 vs 16)
- **Higher dropout** (0.1 vs 0.05)
- **Reduced sequence length** (1024 vs 4096)
- **Only attention layers** (q/k/v/o, not MLP)

### 4. Start Training

```bash
# Option A: Automated script
bash scripts/training/train_local.sh

# Option B: Manual
accelerate launch -m axolotl.cli.train training_configs/mesh-ai-1b-laptop.yaml
```

**Training Progress:**
```
Epoch 1/1  [████████████----] 75%  ETA: 45min
Step 500/667 | Loss: 0.823 | LR: 0.00003
```

### 5. Monitor Training

Watch for these good signs:
- ✅ Loss decreasing (1.5 → 0.8)
- ✅ Validation loss similar to train loss
- ✅ No "CUDA out of memory" errors

Bad signs (overtraining):
- ❌ Val loss increasing while train loss decreases
- ❌ Loss drops below 0.3 (memorizing data)

**If training is too slow:**
- Reduce `micro_batch_size` to 1
- Increase `gradient_accumulation_steps` to 8
- Reduce `sequence_len` to 512

### 6. Merge LoRA Adapters

After training completes:

```bash
python3 scripts/training/merge_lora.py \
    --adapter ./outputs/mesh-ai-1b-laptop \
    --output ./mesh-master-bot-v2-merged
```

### 7. Convert to GGUF (for Ollama)

```bash
# Clone llama.cpp if needed
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp && make
    cd ..
fi

# Convert to GGUF
python3 llama.cpp/convert.py ./mesh-master-bot-v2-merged \
    --outtype f16 \
    --outfile mesh-ai-1b-v2.gguf

# Quantize to Q4_K_M (recommended for speed)
./llama.cpp/quantize mesh-ai-1b-v2.gguf mesh-ai-1b-v2-Q4_K_M.gguf Q4_K_M
```

### 8. Import to Ollama

```bash
# Update Modelfile with new model path
cat > Modelfile.v2 <<EOF
FROM ./mesh-ai-1b-v2-Q4_K_M.gguf

TEMPLATE """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
<|assistant|>
{{ end }}"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

SYSTEM """You are Mesh Master Bot, an AI assistant for Meshtastic mesh networks. Provide concise, helpful responses about mesh commands, networking, and troubleshooting."""
EOF

# Create model
ollama create mesh-master-bot-v2 -f Modelfile.v2

# Test it
ollama run mesh-master-bot-v2 "How do I relay to alice?"
```

## Testing the Model

### Quick Test

```bash
ollama run mesh-master-bot-v2 "What is SNR?"
```

**Expected (good):**
```
Signal-to-Noise Ratio. Measures link quality in dB. >5 is good, 0-5 fair, <0 poor.
```

**Overtraining symptoms:**
- Robotic/templated responses
- Repeating exact training examples
- Can't generalize to new questions
- Loses base model capabilities

### Full Evaluation

```bash
python3 scripts/training/eval_model.py \
    --model mesh-master-bot-v2 \
    --test-file data/training/val_v2.jsonl
```

## Troubleshooting

### Out of Memory

**Symptoms:** `RuntimeError: CUDA out of memory` or system freeze

**Fixes:**
1. Reduce `micro_batch_size` to 1
2. Enable more aggressive gradient checkpointing
3. Reduce `sequence_len` to 512
4. Close other apps

### Training Too Slow

**Symptoms:** <10 steps/hour

**Fixes:**
1. Use smaller `sequence_len` (512 instead of 1024)
2. Disable `sample_packing`
3. Consider cloud GPU (Google Colab, Runpod, Vast.ai)

### Model Not Learning

**Symptoms:** Loss stays high (>1.5)

**Fixes:**
1. Increase `learning_rate` to 0.0001
2. Check training data quality
3. Increase to 2 epochs (but watch for overtraining!)

### Overtraining (Model Too Specialized)

**Symptoms:**
- Can't answer general questions
- Robotic responses
- Repeating training data verbatim

**Fixes:**
1. ✅ Use v1.1 config (1 epoch, lower LR)
2. ✅ Use v2 dataset (15k pairs, not 50k)
3. Stop training early (use best checkpoint, not final)
4. Add more diverse training data

## Comparison: v1.0 vs v1.1 vs v2.0

| Aspect | v1.0 (Overtrained) | v1.1 (Gentler) | v2.0 (Balanced) |
|--------|-------------------|----------------|-----------------|
| **Epochs** | 3 | 1 | 1 |
| **Learning Rate** | 0.0002 | 0.00005 | 0.00005 |
| **LoRA Rank** | 16 | 8 | 8 |
| **Dataset Size** | 50k | 50k | 15k |
| **Target Modules** | 7 (attn+MLP) | 4 (attn only) | 4 (attn only) |
| **Dropout** | 0.05 | 0.1 | 0.1 |
| **Result** | ❌ Too robotic | ⚠️ Better but still repetitive | ✅ Natural + accurate |

## Advanced: Fine-Tuning the Fine-Tune

If v2.0 is still too strong or too weak:

**Too specialized?** (Can't chat naturally)
- Reduce to 10k training pairs
- Add more general conversation data
- Use only 0.5 epochs (early stopping)

**Too weak?** (Doesn't know mesh commands)
- Increase to 20k pairs
- Add 1.5 epochs
- Slightly higher LR (0.0001)

## Next Steps

1. Test model in real mesh conversations
2. Collect user feedback
3. Iteratively improve training data
4. Consider continued pretraining on mesh docs (advanced)

## Resources

- [Axolotl Docs](https://github.com/OpenAccess-AI-Collective/axolotl)
- [Llama 3.2 Model Card](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Mesh-Master GitHub](https://github.com/Snail3D/Mesh-Master)
