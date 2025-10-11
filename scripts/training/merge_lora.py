#!/usr/bin/env python3
"""
Merge LoRA adapters back into base model

After training, this combines the base Llama-3.2-1B model with
the trained LoRA adapters to create a standalone merged model.

Usage:
    python merge_lora.py --adapter ./outputs/mesh-ai-1b-laptop --output ./mesh-master-bot-merged
"""

import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def merge_lora(adapter_path: str, output_path: str, base_model: str = "meta-llama/Llama-3.2-1B-Instruct"):
    """Merge LoRA adapters with base model"""

    print("🔧 Merging LoRA adapters...")
    print(f"   Base: {base_model}")
    print(f"   Adapter: {adapter_path}")
    print(f"   Output: {output_path}")
    print()

    # Load base model
    print("📥 Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True
    )

    # Load LoRA adapters
    print("📥 Loading LoRA adapters...")
    model = PeftModel.from_pretrained(model, adapter_path)

    # Merge adapters into model
    print("🔀 Merging adapters...")
    model = model.merge_and_unload()

    # Save merged model
    print(f"💾 Saving merged model to {output_path}...")
    model.save_pretrained(output_path)

    # Copy tokenizer
    print("📝 Copying tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    tokenizer.save_pretrained(output_path)

    print()
    print("✅ Merge complete!")
    print(f"📁 Merged model saved to: {output_path}")
    print()
    print("Next: Convert to GGUF for Ollama:")
    print(f"   python llama.cpp/convert.py {output_path} --outtype f16 --outfile mesh-ai-v2.gguf")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA adapters with base model")
    parser.add_argument("--adapter", default="./outputs/mesh-ai-1b-laptop", help="Path to trained adapter")
    parser.add_argument("--output", default="./mesh-master-bot-v2-merged", help="Output path for merged model")
    parser.add_argument("--base", default="meta-llama/Llama-3.2-1B-Instruct", help="Base model name")

    args = parser.parse_args()

    merge_lora(args.adapter, args.output, args.base)
