#!/usr/bin/env python3
"""
Hermes Bridge - HTTP endpoint for Meshmaster /agent command
Receives requests from Meshmaster and forwards to Hermes agent
"""

import json
import http.server
import socketserver
import threading
import os
import sys
from datetime import datetime

REQUESTS_FILE = "/home/snailpi/Mesh-Master/data/hermes_requests.json"
RESPONSES_FILE = "/home/snailpi/Mesh-Master/data/hermes_responses.json"
AGENT_WEBHOOK_URL = "http://localhost:8000/hermes/webhook"  # Hermes notification endpoint

class HermesHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def do_POST(self):
        if self.path != "/meshmaster/agent":
            self.send_error(404, "Not found")
            return
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            sender_key = data.get('sender_key', 'unknown')
            query = data.get('query', '')
            source = data.get('source', 'unknown')
            
            print(f"[{datetime.now().isoformat()}] Agent request from {sender_key}: {query[:60]}...")
            
            # Save request to file for Hermes to process
            request_entry = {
                'id': datetime.now().strftime('%Y%m%d%H%M%S%f'),
                'sender_key': sender_key,
                'sender_id': data.get('sender_id'),
                'query': query,
                'source': source,
                'channel_idx': data.get('channel_idx'),
                'is_direct': data.get('is_direct'),
                'conversation_history': data.get('conversation_history', []),
                'timestamp': data.get('timestamp'),
                'status': 'pending',
                'received_at': datetime.now().isoformat()
            }
            
            # Append to requests file
            try:
                if os.path.exists(REQUESTS_FILE):
                    with open(REQUESTS_FILE, 'r') as f:
                        requests = json.load(f)
                else:
                    requests = []
                requests.append(request_entry)
                with open(REQUESTS_FILE, 'w') as f:
                    json.dump(requests, f, indent=2)
            except Exception as e:
                print(f"Error saving request: {e}")
            
            # Return immediate acknowledgment
            response = {
                'response': f"🐌 Agent request received! Query: '{query[:50]}{'...' if len(query) > 50 else ''}'\n\nProcessing... Check Telegram for full response.",
                'request_id': request_entry['id'],
                'status': 'accepted'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"Error processing request: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
        elif self.path == "/requests":
            # Return pending requests (for Hermes to poll)
            try:
                if os.path.exists(REQUESTS_FILE):
                    with open(REQUESTS_FILE, 'r') as f:
                        requests = json.load(f)
                    pending = [r for r in requests if r.get('status') == 'pending']
                else:
                    pending = []
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'pending': pending}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404, "Not found")


def run_server(port=8080):
    with socketserver.TCPServer(("", port), HermesHandler) as httpd:
        print(f"Hermes Bridge listening on port {port}")
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get('HERMES_BRIDGE_PORT', 8080))
    run_server(port)
