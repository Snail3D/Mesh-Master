# Mesh Master Bot - Fine-Tuned AI Model

## Overview
**Mesh Master Bot** is a specialized 1B-parameter AI model fine-tuned for Meshtastic mesh networking operations. Based on Llama-3.2-1B-Instruct, it understands mesh commands, networking concepts, and provides concise responses optimized for LoRa bandwidth constraints.

## Model Details
- **Base Model:** meta-llama/Llama-3.2-1B-Instruct
- **Fine-Tuning Method:** QLoRA (4-bit quantization)
- **Training Data:** 50k+ mesh networking conversation pairs
- **Quantization:** Q8_0 GGUF (448MB)
- **Optimized For:**
  - Mesh networking commands
  - Concise responses (<320 chars)
  - Offline operation
  - Low-latency inference (<500ms)

## Files in This Directory

### mesh-ai-1b-Q8_0.gguf (448MB)
Quantized model ready for Ollama deployment. Q8_0 provides excellent quality with manageable file size.

### Modelfile
Ollama configuration file with:
- Mesh Master Bot identity
- Optimized parameters (temp=0.7, top_p=0.9)
- System prompt for mesh networking context
- Chat template for Llama-3.2 format

## Quick Start

### 1. Install Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or visit: https://ollama.com/download
```

### 2. Import Mesh Master Bot
```bash
cd models/
ollama create mesh-master-bot -f Modelfile
```

### 3. Test the Model
```bash
ollama run mesh-master-bot "How do I relay a message to alice?"
```

Expected response:
```
alice your message OR /alice your message
System tracks ACKs automatically. If no ACK in 20s, message likely lost.
```

### 4. Integrate with Mesh-Master
Update `config.json`:
```json
{
  "ai_provider": "ollama",
  "ollama_model": "mesh-master-bot",
  "ollama_url": "http://localhost:11434",
  "ollama_num_ctx": 2048
}
```

## What the Model Knows

### Commands
- `/nodes` - List mesh nodes
- `/relay` - Message routing
- `/mail` - Mailbox system
- `/weather` - Weather reports
- `/optout` - Privacy controls
- 40+ additional commands

### Networking Concepts
- SNR (Signal-to-Noise Ratio)
- ACK/NACK acknowledgments
- Hop counts and routing
- LoRa airtime limits
- Mesh topology

### Troubleshooting
- Signal quality issues
- Message delivery failures
- Configuration problems
- Hardware diagnostics

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Command Accuracy | 92% |
| Response Latency | <500ms (CPU) |
| Brevity (<320 chars) | 83% |
| Model Size | 448MB |
| VRAM Usage | ~1.5GB |

## Training Details

The model was fine-tuned on:
- **Real conversations:** Anonymized mesh-master logs
- **Mail threads:** Q&A patterns from mailbox interactions
- **Synthetic examples:** 43k command/response templates
- **Total dataset:** 50,000+ training pairs

Training configuration:
- LoRA rank: 16
- Learning rate: 0.0002
- Epochs: 3
- Sequence length: 4096 tokens
- Training time: ~10 hours (RTX 3090)

## Model Capabilities

✅ **Can Do:**
- Explain mesh commands and usage
- Troubleshoot networking issues
- Suggest optimal configurations
- Answer technical questions
- Provide concise, bandwidth-efficient responses

❌ **Cannot Do:**
- Access live mesh state (unless integrated)
- Execute commands autonomously (without integration)
- Browse the internet
- Access files or databases

## Integration Example

```python
import requests

def ask_mesh_master_bot(question):
    """Query the local Ollama model"""
    response = requests.post('http://localhost:11434/api/generate',
        json={
            'model': 'mesh-master-bot',
            'prompt': question,
            'stream': False
        }
    )
    return response.json()['response']

# Example
answer = ask_mesh_master_bot("What's a good SNR value?")
print(answer)
# Output: "SNR >5 dB is good, 0-5 fair, <0 poor. For reliable links, aim for 7+ dB."
```

## Customization

### Adjust Response Length
Edit `Modelfile` and change:
```
PARAMETER num_predict 128  # Shorter responses
```

### Change Temperature
```
PARAMETER temperature 0.5  # More deterministic
PARAMETER temperature 1.0  # More creative
```

### Update System Prompt
Modify the `SYSTEM` section in `Modelfile` to customize behavior.

## Upgrading

To update the model with new training data:

1. Prepare new conversation pairs (see `scripts/training/prepare_training_data.py`)
2. Fine-tune with Axolotl (see `training_configs/mesh-ai-1b.yaml`)
3. Convert to GGUF and quantize
4. Update with: `ollama create mesh-master-bot -f Modelfile`

## License
Same as Mesh-Master project (check main LICENSE file)

## Credits
- Base model: Meta (Llama 3.2)
- Fine-tuning: Mesh-Master community
- Training framework: Axolotl + Ollama

## Support
For issues or questions:
- GitHub Issues: [Your repo URL]
- Documentation: `docs/TRAINING_GUIDE.md`
- Mesh-Master Discord: [If applicable]

---

**Mesh Master Bot** - Your AI expert for mesh networking! 🤖📡
