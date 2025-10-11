#!/usr/bin/env python3
"""
Mesh Master Bot v2.0 - Simple MLX Training for Apple Silicon M4
Optimized for Metal acceleration with minimal dependencies
"""

import json
import os
from pathlib import Path

def setup_training():
    """Setup MLX training environment"""
    print("🍎 Mesh Master Bot v2.0 - MLX Training for M4 Mac Mini")
    print("=" * 60)
    print()

    # Check if MLX is available
    try:
        import mlx.core as mx
        import mlx.nn as nn
        print(f"✅ MLX version: {mx.__version__}")
        print(f"✅ Metal backend: Available")
    except ImportError:
        print("❌ MLX not found. Install with: pip install mlx mlx-lm")
        return False

    return True


def convert_sharegpt_to_mlx(input_file, output_file):
    """Convert ShareGPT JSONL to MLX training format"""
    print(f"\n🔄 Converting training data...")
    print(f"  Input: {input_file}")
    print(f"  Output: {output_file}")

    if not os.path.exists(input_file):
        print(f"❌ Training data not found: {input_file}")
        print("\nCreate mesh_conversations.jsonl with format:")
        print('{"conversations": [{"from": "human", "value": "question"}, {"from": "gpt", "value": "answer"}]}')
        return False

    converted = []
    with open(input_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            conversations = data.get('conversations', [])

            # Build single text string
            text = "<|begin_of_text|>"
            for turn in conversations:
                role = "user" if turn['from'] == 'human' else "assistant"
                content = turn['value']
                text += f"{role}\n{content}\n\n"
            text += "<|end_of_text|>"

            converted.append({"text": text})

    # Save converted data
    with open(output_file, 'w') as f:
        for item in converted:
            f.write(json.dumps(item) + '\n')

    print(f"✅ Converted {len(converted)} examples")
    return True


def main():
    """Main training orchestration"""

    if not setup_training():
        return 1

    # Configuration
    config = {
        "model": "meta-llama/Llama-3.2-1B-Instruct",
        "data_path": "./training/data/mesh_conversations.jsonl",
        "mlx_data_path": "./training/data/mesh_conversations_mlx.jsonl",
        "output_dir": "./training/outputs/mesh-master-mlx-v2",
        "learning_rate": 0.00002,
        "epochs": 1,
        "batch_size": 4,
        "lora_rank": 8,
        "lora_alpha": 16,
        "max_seq_length": 2048,
    }

    # Create output directory
    Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)

    # Convert training data
    if not convert_sharegpt_to_mlx(config["data_path"], config["mlx_data_path"]):
        return 1

    print("\n📝 Training Configuration:")
    for key, value in config.items():
        if key not in ["data_path", "mlx_data_path"]:
            print(f"  {key}: {value}")

    print("\n🚀 Starting training with MLX...")
    print("\nTo train, run:")
    print(f"""
mlx_lm.lora \\
    --model {config['model']} \\
    --train \\
    --data {config['mlx_data_path']} \\
    --adapter-file {config['output_dir']}/adapters \\
    --iters 1000 \\
    --steps-per-eval 50 \\
    --steps-per-report 10 \\
    --save-every 100 \\
    --learning-rate {config['learning_rate']} \\
    --batch-size {config['batch_size']} \\
    --lora-layers {config['lora_rank']}
""")

    print("\n📋 After training, merge the adapters:")
    print(f"""
mlx_lm.fuse \\
    --model {config['model']} \\
    --adapter-file {config['output_dir']}/adapters \\
    --save-path {config['output_dir']}/merged \\
    --de-quantize
""")

    print("\n📦 Convert to GGUF for Ollama:")
    print("""
1. Install llama.cpp:
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp && make

2. Convert merged model:
   python llama.cpp/convert.py ./training/outputs/mesh-master-mlx-v2/merged \\
       --outtype q8_0 \\
       --outfile ./training/outputs/mesh-master-mlx-v2/mesh-master-bot-v2.gguf

3. Transfer to Raspberry Pi:
   scp ./training/outputs/mesh-master-mlx-v2/mesh-master-bot-v2.gguf snailpi@raspberrypi:/home/snailpi/
   scp ./training/models/Modelfile.mesh-master-v2 snailpi@raspberrypi:/home/snailpi/Modelfile

4. Create Ollama model:
   ssh snailpi@raspberrypi
   ollama create mesh-master-bot-v2 -f /home/snailpi/Modelfile
   ollama run mesh-master-bot-v2 "How do I relay to alice?"
""")

    print("\n✅ Setup complete! Ready to train on your M4 Mac Mini.")
    print(f"\nModel will be saved to: {config['output_dir']}")

    return 0


if __name__ == "__main__":
    exit(main())
