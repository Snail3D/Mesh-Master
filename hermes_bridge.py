#!/usr/bin/env python3
"""
Hermes Bridge v2 — Direct synchronous bridge for Mesh Master → Hermes agent.

Replaces the old file-queue + poller approach with a direct call:
  Mesh Master (Docker) → HTTP POST → this bridge → hermes chat -q → response

Listens on port 9097. Mesh Master calls POST /meshmaster/agent with JSON:
  {sender_id, sender_key, query, source, channel_idx, is_direct, conversation_history}

Returns the Hermes agent's response synchronously.

Config:
  HERMES_PROFILE (env) — which Hermes profile to use (default: meshmaster)
  HERMES_BRIDGE_PORT (env) — port to listen on (default: 9097)
  HERMES_TIMEOUT (env) — max seconds for Hermes to respond (default: 120)
"""

import json
import http.server
import socketserver
import subprocess
import os
import sys
import shlex
from datetime import datetime

HERMES_PROFILE = os.environ.get("HERMES_PROFILE", "meshmaster")
PORT = int(os.environ.get("HERMES_BRIDGE_PORT", "9097"))
HERMES_TIMEOUT = int(os.environ.get("HERMES_TIMEOUT", "120"))


class HermesBridgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {args[0]}", flush=True)

    def do_POST(self):
        if self.path != "/meshmaster/agent":
            self.send_error(404, "Not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            sender_key = data.get("sender_key", "unknown")
            query = data.get("query", "")
            source = data.get("source", "unknown")
            history = data.get("conversation_history", [])

            if not query.strip():
                self._json_response(400, {"error": "Empty query"})
                return

            print(f"  From: {sender_key} ({source})")
            print(f"  Query: {query[:80]}{'...' if len(query) > 80 else ''}")

            # Build the prompt for Hermes with context
            prompt_parts = []

            # Add conversation history for context
            if history:
                prompt_parts.append("Previous conversation context:")
                for msg in history[-5:]:  # Last 5 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if content:
                        prompt_parts.append(f"  [{role}]: {content[:200]}")
                prompt_parts.append("")

            prompt_parts.append(f"Request from mesh user '{sender_key}':")
            prompt_parts.append(query)
            prompt_parts.append("")
            prompt_parts.append(
                "Respond concisely — this will be sent over a LoRa mesh radio. "
                "Keep it under 200 characters if possible. No markdown formatting."
            )

            full_prompt = "\n".join(prompt_parts)

            # Call Hermes CLI directly
            cmd = [
                "hermes",
                "--profile", HERMES_PROFILE,
                "chat",
                "-q", full_prompt,
                "--quiet",
            ]

            print(f"  Calling: hermes --profile {HERMES_PROFILE} chat -q ...")

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=HERMES_TIMEOUT,
                )

                if result.returncode == 0:
                    response_text = result.stdout.strip()
                    if not response_text:
                        response_text = "🐌 Agent processed the request but returned no output."
                    print(f"  Response ({len(response_text)} chars): {response_text[:60]}...")
                else:
                    error_msg = result.stderr.strip()[:200] if result.stderr else "Unknown error"
                    print(f"  Hermes error (exit {result.returncode}): {error_msg}")
                    response_text = f"⚠️ Agent error: {error_msg}"

            except subprocess.TimeoutExpired:
                print(f"  Hermes timeout after {HERMES_TIMEOUT}s")
                response_text = f"⏱️ Agent timeout ({HERMES_TIMEOUT}s) — request may be too complex for synchronous mode."
            except FileNotFoundError:
                print("  Hermes CLI not found — is hermes installed?")
                response_text = "🔌 Agent offline — Hermes CLI not found on host."
            except Exception as e:
                print(f"  Unexpected error: {e}")
                response_text = f"❌ Agent error: {str(e)[:100]}"

            self._json_response(200, {"response": response_text, "status": "completed"})

        except json.JSONDecodeError:
            self._json_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            print(f"  Bridge error: {e}")
            self._json_response(500, {"error": str(e)})

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {
                "status": "ok",
                "profile": HERMES_PROFILE,
                "port": PORT,
                "timestamp": datetime.now().isoformat(),
            })
        else:
            self.send_error(404, "Not found")

    def _json_response(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    print(f"🐌 Hermes Bridge v2", flush=True)
    print(f"  Profile: {HERMES_PROFILE}", flush=True)
    print(f"  Port: {PORT}", flush=True)
    print(f"  Timeout: {HERMES_TIMEOUT}s", flush=True)
    print(f"  Endpoint: POST http://localhost:{PORT}/meshmaster/agent", flush=True)
    print(flush=True)

    # Verify hermes is available
    try:
        result = subprocess.run(["hermes", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  Hermes version: {result.stdout.strip()}", flush=True)
        else:
            print("  ⚠️  Hermes CLI found but returned error on --version", flush=True)
    except FileNotFoundError:
        print("  ⚠️  Hermes CLI not found in PATH!", flush=True)
        print("  Install: curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash", flush=True)
    except Exception:
        pass

    print(flush=True)
    print("Listening...", flush=True)

    with socketserver.TCPServer(("0.0.0.0", PORT), HermesBridgeHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutting down...", flush=True)
        sys.exit(0)
