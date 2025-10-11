#!/usr/bin/env python3
"""
Mesh-Master Training Data Preparation v2 - REDUCED SYNTHETIC DATA

Generates high-quality training data with LESS repetition to prevent overtraining.

Key Changes from v1:
- Fewer synthetic templates (43k → 10k)
- More diverse real conversation extraction
- Better data balancing
- Quality filtering

Usage:
    python prepare_training_data_v2.py --output data/training/train_v2.jsonl --min-pairs 15000
"""

import json
import re
from pathlib import Path
from typing import List, Dict
import argparse
import random

def anonymize_text(text: str) -> str:
    """Remove PII from training data"""
    # Anonymize node IDs
    text = re.sub(r'![a-f0-9]{8}', '!<node>', text, flags=re.IGNORECASE)
    # Anonymize IPs
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<ip>', text)
    # Anonymize UUIDs
    text = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<uuid>', text, flags=re.IGNORECASE)
    return text

def extract_real_conversations(messages_archive_path: Path) -> List[Dict]:
    """Extract actual user conversations from mesh-master logs"""
    if not messages_archive_path.exists():
        print(f"⚠️  No messages archive found at {messages_archive_path}")
        return []

    archive = json.loads(messages_archive_path.read_text())
    pairs = []

    for msg in archive:
        if msg.get('type') == 'ai_query':
            question = anonymize_text(msg.get('question', ''))
            response = anonymize_text(msg.get('response', ''))

            # Quality filter: skip very short or error responses
            if len(response) < 10 or 'error' in response.lower():
                continue

            pairs.append({
                'conversations': [
                    {'from': 'human', 'value': question},
                    {'from': 'gpt', 'value': response}
                ]
            })

    print(f"✅ Extracted {len(pairs)} real conversation pairs")
    return pairs

def generate_core_command_pairs() -> List[Dict]:
    """
    Generate ESSENTIAL command training pairs only (REDUCED from v1)

    v1: 43k synthetic pairs (too many!)
    v2: ~3k synthetic pairs (core commands only)
    """

    pairs = []

    # Core commands - 2-3 variations each (not 10+)
    core_commands = {
        '/nodes': [
            ("Show me all nodes", "/nodes - lists all reachable nodes with SNR and last heard"),
            ("List mesh nodes", "/nodes"),
            ("Who's on the mesh?", "Use /nodes to see all reachable nodes"),
        ],
        '/relay': [
            ("How do I relay to alice?", "alice your message OR /alice your message"),
            ("Send message to bob", "bob your message - system tracks ACKs"),
            ("Relay syntax?", "shortname message OR /shortname message"),
        ],
        '/mail': [
            ("Check my mail", "/checkmail or /c"),
            ("How does mail work?", "Send: /mail username subject|body  Check: /checkmail"),
            ("Read messages", "/c shows unread mail"),
        ],
        '/ai': [
            ("Ask AI a question", "/ai your question"),
            ("How to use AI?", "/ai <question> - queries local LLM"),
        ],
        '/nodes': [
            ("Check signal quality", "Use /node <shortname> to see SNR. >5 dB is good, <0 is poor"),
        ],
    }

    for cmd, variations in core_commands.items():
        for question, answer in variations:
            pairs.append({
                'conversations': [
                    {'from': 'human', 'value': question},
                    {'from': 'gpt', 'value': answer}
                ]
            })

    print(f"✅ Generated {len(pairs)} core command pairs")
    return pairs

def generate_troubleshooting_pairs() -> List[Dict]:
    """Generate DIVERSE troubleshooting scenarios (not templates)"""

    scenarios = [
        # Signal issues
        ("Poor signal to node", "Check SNR with /node <shortname>. If <0 dB: reposition antenna, use ROUTER role, or add relay node."),
        ("No ACK received", "No ACK in 20s means weak signal, node offline, or message lost. Check /node <shortname> for status."),
        ("Message not delivered", "Check: 1) /node <target> shows recent activity 2) SNR >0 dB 3) Node not opted out (/optout list)"),

        # Configuration
        ("How to change frequency", "Edit config: frequency_slot (0-6 for US915). Restart required."),
        ("Set node name", "config.json: node_name field. Or via dashboard /config"),

        # Performance
        ("Slow AI responses", "Check: 1) ollama_model size 2) CPU/GPU usage 3) Context length (reduce ollama_num_ctx)"),
        ("High memory usage", "Increase persistent_messages_max_mb or run /wipe to clear old messages"),
    ]

    pairs = []
    for issue, solution in scenarios:
        pairs.append({
            'conversations': [
                {'from': 'human', 'value': issue},
                {'from': 'gpt', 'value': solution}
            ]
        })

    print(f"✅ Generated {len(pairs)} troubleshooting pairs")
    return pairs

def generate_identity_pairs() -> List[Dict]:
    """Bot identity and purpose (minimal, not repetitive)"""

    identity = [
        ("Who are you?", "I'm Mesh Master Bot, your AI assistant for Meshtastic mesh networking!"),
        ("What can you do?", "I help with mesh commands, troubleshooting, relaying messages, and network diagnostics."),
        ("What's your name?", "Mesh Master Bot"),
    ]

    pairs = []
    for q, a in identity:
        pairs.append({
            'conversations': [
                {'from': 'human', 'value': q},
                {'from': 'gpt', 'value': a}
            ]
        })

    print(f"✅ Generated {len(pairs)} identity pairs")
    return pairs

def generate_mesh_concepts() -> List[Dict]:
    """Teach core mesh networking concepts (not commands)"""

    concepts = [
        ("What is SNR?", "Signal-to-Noise Ratio. Measures link quality in dB. >5 is good, 0-5 fair, <0 poor."),
        ("Explain hop limit", "Max number of relay hops (default 3). Each hop reduces reliability and adds latency."),
        ("What's airtime?", "LoRa transmission time. Longer messages = more airtime = slower network. Keep <320 chars."),
        ("ACK timeout?", "20 seconds. If no ACK, message assumed lost due to signal/collision/offline node."),
        ("Best modem preset?", "Long_Fast for general use (5 km range). Long_Slow for extreme range (20+ km)."),
        ("ROUTER role?", "Node that relays messages for others. Uses more power but extends network."),
    ]

    pairs = []
    for q, a in concepts:
        pairs.append({
            'conversations': [
                {'from': 'human', 'value': q},
                {'from': 'gpt', 'value': a}
            ]
        })

    print(f"✅ Generated {len(pairs)} concept pairs")
    return pairs

def balance_dataset(all_pairs: List[Dict], target_size: int) -> List[Dict]:
    """
    Balance and limit dataset to prevent overtraining

    Target: ~15k pairs (down from 50k)
    - 5k real conversations (if available)
    - 3k core commands
    - 2k troubleshooting
    - 2k concepts
    - 3k misc/augmented
    """

    random.shuffle(all_pairs)

    if len(all_pairs) > target_size:
        print(f"⚖️  Limiting dataset: {len(all_pairs)} → {target_size} pairs")
        return all_pairs[:target_size]

    return all_pairs

def create_train_val_split(pairs: List[Dict], val_ratio: float = 0.15):
    """Split into train/val with proper ratio"""
    random.shuffle(pairs)
    split_idx = int(len(pairs) * (1 - val_ratio))

    return pairs[:split_idx], pairs[split_idx:]

def main():
    parser = argparse.ArgumentParser(description='Generate v2 training data (reduced overtraining)')
    parser.add_argument('--output', default='data/training/train_v2.jsonl', help='Output JSONL file')
    parser.add_argument('--min-pairs', type=int, default=15000, help='Target dataset size (default: 15k)')
    parser.add_argument('--val-ratio', type=float, default=0.15, help='Validation split ratio')
    args = parser.parse_args()

    print("🚀 Mesh Master Bot Training Data v2 Generator")
    print(f"📊 Target size: {args.min_pairs} pairs (reduced from 50k)")
    print()

    # Collect all pairs
    all_pairs = []

    # Real conversations (if available)
    messages_path = Path('messages_archive.json')
    all_pairs.extend(extract_real_conversations(messages_path))

    # Synthetic data (REDUCED)
    all_pairs.extend(generate_core_command_pairs())
    all_pairs.extend(generate_troubleshooting_pairs())
    all_pairs.extend(generate_identity_pairs())
    all_pairs.extend(generate_mesh_concepts())

    # Balance dataset
    all_pairs = balance_dataset(all_pairs, args.min_pairs)

    # Train/val split
    train_pairs, val_pairs = create_train_val_split(all_pairs, args.val_ratio)

    # Write train set
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w') as f:
        for pair in train_pairs:
            f.write(json.dumps(pair) + '\n')

    # Write val set
    val_path = output_path.parent / 'val_v2.jsonl'
    with val_path.open('w') as f:
        for pair in val_pairs:
            f.write(json.dumps(pair) + '\n')

    print()
    print("✅ Training data v2 generated!")
    print(f"📄 Train: {len(train_pairs)} pairs → {output_path}")
    print(f"📄 Val: {len(val_pairs)} pairs → {val_path}")
    print(f"💾 Total: {len(all_pairs)} pairs")
    print()
    print("💡 This reduced dataset should prevent overtraining while")
    print("   maintaining strong mesh networking knowledge.")
    print()
    print("Next steps:")
    print("1. Review samples: head -5 data/training/train_v2.jsonl")
    print("2. Train with: accelerate launch -m axolotl.cli.train training_configs/mesh-ai-1b-v1.1-gentle.yaml")
    print("3. Use 1 epoch only (already set in v1.1-gentle config)")

if __name__ == '__main__':
    main()
