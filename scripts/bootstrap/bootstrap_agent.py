#!/usr/bin/env python3
"""
Bootstrap Agent — A minimal AI agent that installs Hermes from scratch.

Runs on a LOCAL model (no cloud API needed). Has terminal + file access.
Guides the user through installing Hermes Agent, creating a Telegram bot,
configuring everything, and starting the gateway.

This is a self-contained agent loop — no Hermes framework required.
It uses the OpenAI-compatible API of the local model server.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# --- Configuration ---
MODEL_ENDPOINT = "http://localhost:8087/v1"
MODEL_NAME = ""  # Auto-detected from the server
MAX_TURNS = 50
MAX_TOKENS = 4096

SYSTEM_PROMPT = """You are the Hermes Bootstrap Agent — a self-installing AI agent that sets up a complete Hermes Agent installation on this machine.

You have TWO tools available:
1. run_command(command) — Run a shell command and get its output
2. ask_user(question) — Ask the user a question and get their response

YOUR MISSION: Install and configure a complete Hermes Agent setup:

1. Install Hermes Agent (curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash)
2. Verify Hermes is installed (hermes --version)
3. Create a new Hermes profile called "meshmaster" if it doesn't exist
4. Configure the profile to use THIS local model endpoint (http://localhost:8087/v1)
5. Set up the model config: provider=custom, base_url=http://localhost:8087/v1, api_key=sk-none
6. Set up Telegram bot — Hermes has AUTOMATED bot creation via @HermesSetupBot:
   - Run: hermes gateway setup (or hermes setup gateway)
   - This will create a bot automatically — the user just taps "Create Bot" in Telegram
   - If the automated flow fails, fall back to asking the user for a manual @BotFather token
7. Configure the Telegram bot token in the profile's .env file
8. Enable useful toolsets (terminal, web, file, skills, vision)
9. Start the Telegram gateway (hermes gateway install && hermes gateway start)
10. Test that everything works

RULES:
- Be autonomous — run commands, don't just suggest them
- If something fails, try a different approach
- Keep the user informed of progress
- Ask the user only when you genuinely need their input (e.g., tap "Create Bot" in Telegram)
- Be concise in your status updates
- When you're done, confirm the agent is live and tell them how to test it

To call a tool, respond with JSON in this exact format:
{"tool": "run_command", "command": "your shell command here"}
or
{"tool": "ask_user", "question": "your question here"}

When you want to give a status update WITHOUT calling a tool, just respond with text.
When the installation is complete, respond with: INSTALLATION_COMPLETE
"""


def get_model_name():
    """Auto-detect the model name from the server."""
    try:
        r = requests.get(f"{MODEL_ENDPOINT}/models", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("data"):
                return data["data"][0]["id"]
    except Exception:
        pass
    return "default"


def call_model(messages, model_name):
    """Call the local model with the conversation history."""
    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3,
        "stream": False,
    }
    try:
        r = requests.post(
            f"{MODEL_ENDPOINT}/chat/completions",
            json=payload,
            timeout=120,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            return f"[ERROR] Model returned status {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"[ERROR] Model call failed: {e}"


def run_command(command):
    """Run a shell command and return its output."""
    print(f"  🔧 $ {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        output = ""
        if stdout:
            output += stdout
        if stderr:
            output += f"\n[stderr] {stderr}" if stdout else stderr
        if not output:
            output = "(no output)"
        # Truncate very long output
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
        print(f"  📤 {output[:200]}{'...' if len(output) > 200 else ''}")
        return output
    except subprocess.TimeoutExpired:
        return "[ERROR] Command timed out after 300s"
    except Exception as e:
        return f"[ERROR] {e}"


def ask_user(question):
    """Ask the user a question."""
    print(f"\n🤖 {question}")
    print("\n> ", end="", flush=True)
    response = input()
    return response.strip()


def parse_tool_call(text):
    """Try to parse a JSON tool call from the model's response."""
    # Try to find JSON in the response
    json_match = re.search(r'\{[^{}]*"tool"[^{}]*\}', text, re.DOTALL)
    if not json_match:
        # Try larger JSON blocks
        json_match = re.search(r'\{.*"tool".*:".*".*\}', text, re.DOTALL)
    if not json_match:
        return None

    try:
        data = json.loads(json_match.group())
        if "tool" in data:
            return data
    except json.JSONDecodeError:
        pass
    return None


def main():
    global MODEL_ENDPOINT, MODEL_NAME

    parser = argparse.ArgumentParser(description="Hermes Bootstrap Agent")
    parser.add_argument("--install-dir", required=True, help="Installation directory")
    parser.add_argument("--model-endpoint", default=MODEL_ENDPOINT, help="Model API endpoint")
    parser.add_argument("--os", default="linux", help="Operating system")
    parser.add_argument("--arch", default="x86_64", help="Architecture")
    args = parser.parse_args()

    MODEL_ENDPOINT = args.model_endpoint.rstrip("/")
    MODEL_NAME = get_model_name()

    print(f"\n🧠 Model: {MODEL_NAME}")
    print(f"📡 Endpoint: {MODEL_ENDPOINT}")
    print(f"💻 OS: {args.os} ({args.arch})")
    print(f"📁 Install dir: {args.install_dir}")
    print(f"\n{'='*60}\n")

    # Build the conversation
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Start the installation. OS={args.os}, Arch={args.arch}, InstallDir={args.install_dir}. The local model is already running at {MODEL_ENDPOINT}. Go!"},
    ]

    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        print(f"\n--- Turn {turn} ---")

        # Call the model
        response = call_model(messages, MODEL_NAME)

        if not response or response.startswith("[ERROR]"):
            print(f"❌ Model error: {response}")
            break

        # Check for completion
        if "INSTALLATION_COMPLETE" in response:
            # Print any text before the marker
            text_before = response.split("INSTALLATION_COMPLETE")[0].strip()
            if text_before:
                print(f"\n🤖 {text_before}")
            print("\n✅ Installation complete!")
            break

        # Try to parse a tool call
        tool_call = parse_tool_call(response)

        if tool_call:
            # Add the model's response to history
            messages.append({"role": "assistant", "content": response})

            tool_name = tool_call.get("tool", "")
            tool_result = ""

            if tool_name == "run_command":
                command = tool_call.get("command", "")
                if command:
                    tool_result = run_command(command)
                else:
                    tool_result = "[ERROR] Empty command"
            elif tool_name == "ask_user":
                question = tool_call.get("question", "What would you like me to do?")
                tool_result = ask_user(question)
            else:
                tool_result = f"[ERROR] Unknown tool: {tool_name}"

            # Add the tool result to the conversation
            messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
        else:
            # No tool call — just text response
            print(f"\n🤖 {response}")
            messages.append({"role": "assistant", "content": response})

            # If the model isn't calling tools, prompt it to continue
            if turn < MAX_TURNS:
                messages.append({"role": "user", "content": "Continue with the installation. Call a tool or respond with INSTALLATION_COMPLETE when done."})

    if turn >= MAX_TURNS:
        print("\n⚠️ Reached maximum turns. Installation may be incomplete.")
        print("You can continue manually with: hermes setup")

    print(f"\n{'='*60}")
    print(f"Bootstrap agent finished after {turn} turns.")


if __name__ == "__main__":
    main()
