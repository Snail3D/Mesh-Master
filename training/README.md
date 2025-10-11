# 🤖 Mesh Master Bot v2.0 Training Guide

**Fine-tuning Llama-3.2-1B-Instruct for Meshtastic Mesh Networks**

---

## 🚨 What Went Wrong in v1.0

The original mesh-master-bot had catastrophic issues:

### ❌ Problems:
1. **Wrong base model** - Used `gemma3:270m` (too small!) instead of Llama-3.2-1B
2. **Learning rate too high** - 0.0002 overwrote base knowledge
3. **Too many epochs** - 3 passes caused severe overfitting
4. **No regularization** - Zero weight decay, low dropout
5. **Missing repeat penalty** - Caused infinite loops (`/optout prevents others from relaying...`)

### 🐛 Symptoms:
- Repetitive looping text
- Regurgitating commands instead of answering questions
- Long, unfocused responses (250-300+ chars)
- Hallucinating mesh commands

---

## ✅ What's Fixed in v2.0

| Setting | v1.0 (BAD) | v2.0 (FIXED) | Why It Matters |
|---------|-----------|--------------|----------------|
| **Base Model** | gemma3:270m | Llama-3.2-1B | 4x more parameters, better reasoning |
| **Learning Rate** | 0.0002 | 0.00002 | 10x lower = less catastrophic forgetting |
| **Epochs** | 3 | 1 | Prevents overfitting/memorization |
| **LoRA Rank** | 16 | 8 | Smaller adapter = less memorization |
| **Dropout** | 0.05 | 0.15 | 3x more regularization |
| **Weight Decay** | 0.0 | 0.01 | Added to prevent overfitting |
| **Repeat Penalty** | None | 1.15 | Stops infinite loops! |
| **Temperature** | 0.7 | 0.5 | More focused responses |
| **Early Stopping** | None | Patience 3 | Stops training before overfitting |

---

## 📁 Training Files

```
training/
├── configs/
│   └── mesh-master-1b-v2.yaml        # Optimized training config
├── data/
│   ├── mesh_conversations_sample.jsonl  # Example training data
│   └── mesh_conversations.jsonl      # YOUR training data (create this!)
├── models/
│   └── Modelfile.mesh-master-v2      # Ollama modelfile with proper parameters
├── scripts/
│   └── colab_train_mesh_master.ipynb # Google Colab training notebook
└── README.md                          # This file
```

---

## 🚀 Quick Start (Google Colab)

### Step 1: Prepare Training Data

Create `mesh_conversations.jsonl` in ShareGPT format:

```jsonl
{"conversations": [{"from": "human", "value": "How do I relay to alice?"}, {"from": "gpt", "value": "Just type: alice <your message>"}]}
{"conversations": [{"from": "human", "value": "What's a meshtastic router?"}, {"from": "gpt", "value": "A router node that ONLY relays messages—doesn't send/receive its own."}]}
```

**Tips for good training data:**
- ✅ Short, concise responses (under 200 chars ideal)
- ✅ Mix of technical and casual questions
- ✅ Show personality (friendly, helpful, not robotic)
- ✅ Include variations of same question
- ✅ Cover edge cases and troubleshooting
- ❌ Don't just list commands - explain them conversationally
- ❌ Don't repeat same patterns too much

**Recommended dataset size:** 500-2000 examples (quality > quantity!)

### Step 2: Upload to Google Colab

1. Open `scripts/colab_train_mesh_master.ipynb` in Colab
2. Select GPU runtime (T4 or better): Runtime → Change runtime type → GPU
3. Upload your `mesh_conversations.jsonl` file
4. Run cells in order

### Step 3: Authenticate

You'll need:
- **HuggingFace token** with Llama-3.2 access ([get here](https://huggingface.co/settings/tokens))
- **Weights & Biases account** (optional, for tracking)

### Step 4: Train

Training takes:
- **T4 GPU (free):** ~2-3 hours
- **A100 GPU (paid):** ~45-60 minutes

### Step 5: Download Model

The notebook will produce:
- `mesh-master-bot-v2.gguf` - The trained model (Q8 quantized, ~450MB)
- `Modelfile` - Ollama import config

### Step 6: Import to Ollama

On your Raspberry Pi:

```bash
# Copy files to Pi
scp mesh-master-bot-v2.gguf snailpi@raspberrypi:/home/snailpi/
scp Modelfile snailpi@raspberrypi:/home/snailpi/

# SSH to Pi
ssh snailpi@raspberrypi

# Create Ollama model
cd /home/snailpi
ollama create mesh-master-bot-v2 -f Modelfile

# Test it
ollama run mesh-master-bot-v2 "How do I relay to alice?"

# If good, update Mesh Master config
nano /home/snailpi/Programs/mesh-ai/config.json
# Change: "ollama_model": "mesh-master-bot-v2"

# Restart service
sudo systemctl restart mesh-ai
```

---

## 🧪 Testing Your Model

### Quick Tests (before deploying):

```bash
# Test 1: Simple question
ollama run mesh-master-bot-v2 "How do I relay to alice?"
# Expected: Short answer like "alice <message>" (NOT a loop!)

# Test 2: Casual greeting
ollama run mesh-master-bot-v2 "Hey are you there?"
# Expected: Friendly response like "Yep, still here! What can I help with?"

# Test 3: Technical question
ollama run mesh-master-bot-v2 "What's a good SNR?"
# Expected: Concise technical answer (not repeating itself)

# Test 4: Edge case
ollama run mesh-master-bot-v2 "Tell me a joke"
# Expected: Stays on topic or politely declines
```

### Red Flags (signs of overfitting):

❌ **Repeating the same phrase over and over** (like v1.0 did)
❌ **Just listing commands instead of explaining**
❌ **Responses longer than 300 chars consistently**
❌ **Hallucinating mesh commands that don't exist**
❌ **Ignoring the question and giving a canned response**

If you see these, the model is still overfit! Try:
- Lower learning rate even more (0.00001)
- Add more diverse training data
- Reduce LoRA rank to 4

---

## 📊 Understanding Training Metrics

Watch these during training:

### Loss (Lower = Better)
- **Train loss decreasing:** Good! Model is learning
- **Eval loss increasing while train loss decreases:** BAD! Overfitting!
- **Both decreasing together:** Perfect!

### Early Stopping
If eval loss doesn't improve for 3 checkpoints, training stops automatically. This is GOOD - prevents overfitting!

### Ideal Training Curve:
```
Step    Train Loss    Eval Loss
0       2.5          2.5
100     1.8          1.7
200     1.2          1.1
300     0.9          0.95   ← Both still decreasing = good!
400     0.7          0.8    ← Eval going up = stop here!
```

---

## 🔧 Advanced Tuning

### If model is too creative/random:
```yaml
learning_rate: 0.00001  # Even lower
temperature: 0.3        # In Modelfile
```

### If model is too robotic/boring:
```yaml
temperature: 0.6        # In Modelfile
lora_dropout: 0.1       # Less regularization
```

### If model outputs are too long:
```yaml
# In Modelfile:
PARAMETER num_predict 150   # Stricter limit
```

### If model still loops:
```yaml
# In Modelfile:
PARAMETER repeat_penalty 1.25  # Higher penalty
PARAMETER frequency_penalty 0.5
```

---

## 💾 File Sizes

- **Base Llama-3.2-1B:** ~1.3GB (FP16)
- **LoRA adapters:** ~30MB
- **Merged model:** ~1.3GB
- **GGUF Q8_0:** ~450MB ← What you'll use
- **Training checkpoints:** ~1.5GB each (delete after merging!)

---

## ⚠️ Common Issues

### "CUDA out of memory"
- Reduce `micro_batch_size` to 1
- Increase `gradient_accumulation_steps` to 32
- Use free T4 instead of CPU

### "Llama-3.2 not accessible"
- Get access at https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
- Update your HF token in Colab

### "Model still repeating text"
- Check you're using **1 epoch** not 3
- Verify `repeat_penalty: 1.15` in Modelfile
- May need to retrain with even lower learning rate

### "Responses are still too long"
- Add more short examples to training data
- Lower `num_predict` in Modelfile
- Add explicit "keep it short" examples

---

## 📚 Resources

- **Axolotl docs:** https://github.com/axolotl-ai-cloud/axolotl
- **Llama-3.2 model card:** https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
- **LoRA paper:** https://arxiv.org/abs/2106.09685
- **Ollama docs:** https://github.com/ollama/ollama/blob/main/docs/modelfile.md

---

## 🎯 Success Criteria

Your model is ready when:

✅ Responses are concise (80-150 chars typical)
✅ No repetitive loops
✅ Answers questions accurately
✅ Friendly but professional tone
✅ Doesn't hallucinate commands
✅ Adapts to casual and technical questions

---

## 🙏 Credits

- **Base model:** Meta (Llama-3.2-1B-Instruct)
- **Training framework:** Axolotl
- **Mesh Master project:** Snail3D
- **Original Mesh Master:** MR_TBOT

---

**Good luck with training! 🚀**

Questions? Check the issues at https://github.com/Snail3D/Mesh-Master
