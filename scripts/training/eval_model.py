#!/usr/bin/env python3
"""
Model Evaluation Suite for Mesh-AI

Tests fine-tuned model against baseline on:
- Command accuracy (does it suggest correct commands?)
- Brevity (does it fit in chunk budget?)
- Hallucination rate (does it invent fake commands?)
- Latency (response time comparison)

Usage:
    python eval_model.py --model mesh-ai-1b --baseline llama3.2:1b --threshold 85
"""

import argparse
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


# Ollama API endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"


def query_ollama(model: str, prompt: str, timeout: int = 30) -> Tuple[str, float]:
    """
    Query Ollama model and measure latency.

    Args:
        model: Model name (e.g., 'mesh-ai-1b')
        prompt: User prompt
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response_text, latency_seconds)
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 256
        }
    }

    start = time.time()
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()
        response = result.get('response', '').strip()
        latency = time.time() - start
        return response, latency
    except Exception as e:
        print(f"  ⚠️  Error querying {model}: {e}")
        return "", -1


# Test cases for command accuracy
COMMAND_ACCURACY_TESTS = [
    {
        'question': 'How do I see all nodes?',
        'expected_commands': ['/nodes'],
        'expected_concepts': ['nodes', 'list', 'mesh']
    },
    {
        'question': 'relay message to bob',
        'expected_commands': ['/bob', 'bob'],
        'expected_concepts': ['relay', 'shortname', 'bob']
    },
    {
        'question': 'check my mail',
        'expected_commands': ['/c', '/checkmail'],
        'expected_concepts': ['mail', 'checkmail', 'mailbox']
    },
    {
        'question': 'send mail to admin',
        'expected_commands': ['/m', '/mail'],
        'expected_concepts': ['mail', 'mailbox', 'send']
    },
    {
        'question': 'stop receiving relays',
        'expected_commands': ['/optout'],
        'expected_concepts': ['optout', 'relay', 'disable']
    },
    {
        'question': 'search my logs',
        'expected_commands': ['/find'],
        'expected_concepts': ['find', 'search', 'logs']
    },
    {
        'question': 'create private note',
        'expected_commands': ['/log'],
        'expected_concepts': ['log', 'private', 'note']
    },
    {
        'question': 'public report',
        'expected_commands': ['/report'],
        'expected_concepts': ['report', 'public']
    },
    {
        'question': 'play a game',
        'expected_commands': ['/games'],
        'expected_concepts': ['games', 'play', 'wordle', 'chess']
    },
    {
        'question': 'new user help',
        'expected_commands': ['/onboard', '/onboarding'],
        'expected_concepts': ['onboard', 'help', 'tutorial']
    },
    {
        'question': 'node signal strength',
        'expected_commands': ['/node'],
        'expected_concepts': ['snr', 'rssi', 'signal', 'node']
    },
    {
        'question': 'list commands',
        'expected_commands': ['/help', '/menu'],
        'expected_concepts': ['help', 'commands', 'menu']
    },
]


# Technical knowledge tests
TECHNICAL_TESTS = [
    {
        'question': 'What is SNR?',
        'expected_concepts': ['signal', 'noise', 'ratio', 'quality', 'db']
    },
    {
        'question': 'ACK timeout',
        'expected_concepts': ['20', 'seconds', 'acknowledgment', 'ack']
    },
    {
        'question': 'chunk size',
        'expected_concepts': ['160', 'char', 'limit', 'message']
    },
    {
        'question': 'node roles',
        'expected_concepts': ['client', 'router', 'repeater']
    },
    {
        'question': 'poor signal troubleshooting',
        'expected_concepts': ['snr', 'antenna', 'position', 'signal']
    },
]


# Hallucination detection - questions with NO valid answer
HALLUCINATION_TESTS = [
    {
        'question': '/deletemesh command',
        'should_not_contain': ['use /deletemesh', 'deletemesh command'],
        'should_contain': ['no command', "doesn't exist", 'not available', 'try /help']
    },
    {
        'question': '/superrelay command',
        'should_not_contain': ['use /superrelay', 'superrelay command'],
        'should_contain': ['no command', "doesn't exist", 'try /relay', 'not available']
    },
]


def test_command_accuracy(model: str) -> Dict:
    """Test if model suggests correct commands"""
    print(f"\n{'='*60}")
    print(f"Command Accuracy Test: {model}")
    print('='*60)

    correct = 0
    partial = 0
    wrong = 0
    latencies = []

    for test in COMMAND_ACCURACY_TESTS:
        question = test['question']
        response, latency = query_ollama(model, question)
        latencies.append(latency)

        if not response:
            wrong += 1
            continue

        response_lower = response.lower()

        # Check if any expected command is mentioned
        found_command = any(cmd.lower() in response_lower for cmd in test['expected_commands'])

        # Check if expected concepts are present
        found_concepts = sum(1 for concept in test['expected_concepts']
                             if concept.lower() in response_lower)
        concept_ratio = found_concepts / len(test['expected_concepts'])

        if found_command and concept_ratio >= 0.5:
            correct += 1
            status = "✓"
        elif found_command or concept_ratio >= 0.3:
            partial += 1
            status = "~"
        else:
            wrong += 1
            status = "✗"

        print(f"  {status} {question[:40]:40} ({len(response):3} chars, {latency:.2f}s)")

    total = len(COMMAND_ACCURACY_TESTS)
    accuracy = (correct / total * 100) if total > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    return {
        'correct': correct,
        'partial': partial,
        'wrong': wrong,
        'total': total,
        'accuracy': accuracy,
        'avg_latency': avg_latency
    }


def test_brevity(model: str, chunk_size: int = 160, max_chunks: int = 2) -> Dict:
    """Test if responses fit within chunk budget"""
    print(f"\n{'='*60}")
    print(f"Brevity Test: {model} (budget: {chunk_size * max_chunks} chars)")
    print('='*60)

    budget = chunk_size * max_chunks
    within_budget = 0
    over_budget = 0
    lengths = []

    questions = [test['question'] for test in COMMAND_ACCURACY_TESTS]

    for question in questions:
        response, latency = query_ollama(model, question)
        length = len(response)
        lengths.append(length)

        if length <= budget:
            within_budget += 1
            status = "✓"
        else:
            over_budget += 1
            status = "✗"

        chunks_needed = (length + chunk_size - 1) // chunk_size
        print(f"  {status} {question[:40]:40} {length:3} chars ({chunks_needed} chunks)")

    total = len(questions)
    compliance_rate = (within_budget / total * 100) if total > 0 else 0
    avg_length = sum(lengths) / len(lengths) if lengths else 0

    return {
        'within_budget': within_budget,
        'over_budget': over_budget,
        'total': total,
        'compliance_rate': compliance_rate,
        'avg_length': avg_length,
        'max_length': max(lengths) if lengths else 0
    }


def test_hallucinations(model: str) -> Dict:
    """Test if model hallucinates fake commands"""
    print(f"\n{'='*60}")
    print(f"Hallucination Test: {model}")
    print('='*60)

    no_hallucinations = 0
    hallucinations = 0

    for test in HALLUCINATION_TESTS:
        question = test['question']
        response, _ = query_ollama(model, question)

        if not response:
            continue

        response_lower = response.lower()

        # Check for hallucinated content
        found_bad = any(phrase.lower() in response_lower
                        for phrase in test['should_not_contain'])

        # Check for appropriate "don't know" responses
        found_good = any(phrase.lower() in response_lower
                         for phrase in test['should_contain'])

        if not found_bad and found_good:
            no_hallucinations += 1
            status = "✓"
        else:
            hallucinations += 1
            status = "✗"

        print(f"  {status} {question[:40]:40}")
        if found_bad:
            print(f"      ⚠️  Hallucinated fake command/feature")

    total = len(HALLUCINATION_TESTS)
    accuracy = (no_hallucinations / total * 100) if total > 0 else 0

    return {
        'no_hallucinations': no_hallucinations,
        'hallucinations': hallucinations,
        'total': total,
        'accuracy': accuracy
    }


def test_technical_knowledge(model: str) -> Dict:
    """Test technical mesh networking knowledge"""
    print(f"\n{'='*60}")
    print(f"Technical Knowledge Test: {model}")
    print('='*60)

    correct = 0
    wrong = 0

    for test in TECHNICAL_TESTS:
        question = test['question']
        response, _ = query_ollama(model, question)

        if not response:
            wrong += 1
            continue

        response_lower = response.lower()

        # Check if expected concepts are present
        found_concepts = sum(1 for concept in test['expected_concepts']
                             if concept.lower() in response_lower)
        concept_ratio = found_concepts / len(test['expected_concepts'])

        if concept_ratio >= 0.5:
            correct += 1
            status = "✓"
        else:
            wrong += 1
            status = "✗"

        print(f"  {status} {question[:40]:40} ({found_concepts}/{len(test['expected_concepts'])} concepts)")

    total = len(TECHNICAL_TESTS)
    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        'correct': correct,
        'wrong': wrong,
        'total': total,
        'accuracy': accuracy
    }


def compare_models(model_a: str, model_b: str) -> Dict:
    """Compare two models side-by-side"""
    print(f"\n{'='*60}")
    print(f"Model Comparison: {model_a} vs {model_b}")
    print('='*60)

    results_a = {
        'command_accuracy': test_command_accuracy(model_a),
        'brevity': test_brevity(model_a),
        'hallucinations': test_hallucinations(model_a),
        'technical': test_technical_knowledge(model_a)
    }

    results_b = {
        'command_accuracy': test_command_accuracy(model_b),
        'brevity': test_brevity(model_b),
        'hallucinations': test_hallucinations(model_b),
        'technical': test_technical_knowledge(model_b)
    }

    return {
        'model_a': model_a,
        'model_b': model_b,
        'results_a': results_a,
        'results_b': results_b
    }


def print_summary(results: Dict):
    """Print summary of evaluation results"""
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print('='*60)

    cmd_acc = results['command_accuracy']
    print(f"\nCommand Accuracy:")
    print(f"  Correct: {cmd_acc['correct']}/{cmd_acc['total']} ({cmd_acc['accuracy']:.1f}%)")
    print(f"  Avg Latency: {cmd_acc['avg_latency']:.2f}s")

    brev = results['brevity']
    print(f"\nBrevity (Chunk Budget):")
    print(f"  Within Budget: {brev['within_budget']}/{brev['total']} ({brev['compliance_rate']:.1f}%)")
    print(f"  Avg Length: {brev['avg_length']:.0f} chars")
    print(f"  Max Length: {brev['max_length']} chars")

    hall = results['hallucinations']
    print(f"\nHallucination Rate:")
    print(f"  No Hallucinations: {hall['no_hallucinations']}/{hall['total']} ({hall['accuracy']:.1f}%)")

    tech = results['technical']
    print(f"\nTechnical Knowledge:")
    print(f"  Correct: {tech['correct']}/{tech['total']} ({tech['accuracy']:.1f}%)")

    # Overall score
    overall = (cmd_acc['accuracy'] + brev['compliance_rate'] +
               hall['accuracy'] + tech['accuracy']) / 4
    print(f"\nOverall Score: {overall:.1f}%")

    return overall


def main():
    parser = argparse.ArgumentParser(description='Evaluate Mesh-AI model')
    parser.add_argument('--model', type=str, default='mesh-ai-1b',
                        help='Model to evaluate')
    parser.add_argument('--baseline', type=str,
                        help='Baseline model for comparison')
    parser.add_argument('--threshold', type=float, default=85.0,
                        help='Minimum passing score (%%)')
    parser.add_argument('--output', type=Path,
                        help='Output JSON file for results')

    args = parser.parse_args()

    print(f"\n{'#'*60}")
    print(f"# Mesh-AI Model Evaluation Suite")
    print(f"{'#'*60}")

    # Run evaluation
    results = {
        'command_accuracy': test_command_accuracy(args.model),
        'brevity': test_brevity(args.model),
        'hallucinations': test_hallucinations(args.model),
        'technical': test_technical_knowledge(args.model)
    }

    overall_score = print_summary(results)

    # Compare with baseline if provided
    if args.baseline:
        comparison = compare_models(args.model, args.baseline)
        print(f"\n{'='*60}")
        print(f"Comparison: {args.model} vs {args.baseline}")
        print('='*60)

        # Print delta
        for metric in ['command_accuracy', 'brevity', 'hallucinations', 'technical']:
            a_score = comparison['results_a'][metric].get('accuracy', 0)
            b_score = comparison['results_b'][metric].get('accuracy', 0)
            delta = a_score - b_score
            symbol = "+" if delta > 0 else ""
            print(f"  {metric:20} {symbol}{delta:+.1f}% ({a_score:.1f}% vs {b_score:.1f}%)")

    # Save results
    if args.output:
        output_data = {
            'model': args.model,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results,
            'overall_score': overall_score
        }

        if args.baseline:
            output_data['comparison'] = comparison

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✓ Results saved to {args.output}")

    # Pass/fail check
    print(f"\n{'='*60}")
    if overall_score >= args.threshold:
        print(f"✓ PASS: Score {overall_score:.1f}% >= {args.threshold}%")
        return 0
    else:
        print(f"✗ FAIL: Score {overall_score:.1f}% < {args.threshold}%")
        return 1


if __name__ == '__main__':
    exit(main())
