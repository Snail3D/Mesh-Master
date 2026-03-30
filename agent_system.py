#!/usr/bin/env python3
"""
Integrated Agent System - Receives requests and sends responses DIRECTLY
No polling, no separate files - everything in one process
"""

import json
import http.server
import socketserver
import threading
import requests
import os
import time

# Load Telegram config once at startup
TG_CONFIG = {}
try:
    with open('data/telegram_config.json', 'r') as f:
        TG_CONFIG = json.load(f)
    print(f"✅ Loaded Telegram config: {len(TG_CONFIG.get('authorized_chat_ids', []))} chats")
except Exception as e:
    print(f"❌ Failed to load Telegram config: {e}")

REQUESTS_FILE = "data/hermes_requests.json"
RESPONSES_FILE = "data/hermes_responses.json"

def send_telegram_message(chat_id, message):
    """Send message directly via Telegram API"""
    token = TG_CONFIG.get('token', '')
    if not token:
        print("❌ No token available")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": chat_id, "text": message[:4000]},
            timeout=10
        )
        r.raise_for_status()
        print(f"✅ Telegram message sent to {chat_id}")
        return True
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")
        return False

def process_request(req):
    """Process a request and send response immediately"""
    sender_key = req.get('sender_key', '')
    query = req.get('query', '')
    source = req.get('source', 'telegram')
    
    print(f"\n📝 Processing request from {sender_key}: {query[:50]}")
    
    # Generate response
    response_text = f"🐌 Received: '{query}'. Agent is working automatically!"
    
    # Send immediately based on source
    if source == 'telegram' and sender_key.startswith('telegram_'):
        chat_id = sender_key.replace('telegram_', '')
        success = send_telegram_message(chat_id, response_text)
    else:
        # For mesh, write to responses file for Meshmaster to pick up
        success = write_response(req, response_text)
    
    return success

def write_response(req, response_text):
    """Write response to file for Meshmaster"""
    try:
        responses = []
        if os.path.exists(RESPONSES_FILE):
            with open(RESPONSES_FILE, 'r') as f:
                responses = json.load(f)
        
        responses.append({
            "id": f"resp_{req['id']}",
            "sender_key": req['sender_key'],
            "message": response_text,
            "source": req.get('source', 'telegram'),
            "channel_idx": req.get('channel_idx'),
            "is_direct": req.get('is_direct', True),
            "timestamp": time.time(),
            "status": "pending_delivery"
        })
        
        with open(RESPONSES_FILE, 'w') as f:
            json.dump(responses, f, indent=2)
        
        return True
    except Exception as e:
        print(f"❌ Failed to write response: {e}")
        return False

class AgentHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs
    
    def do_POST(self):
        if self.path != "/meshmaster/agent":
            self.send_error(404)
            return
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            sender_key = data.get('sender_key', 'unknown')
            query = data.get('query', '')
            
            print(f"\n🔔 New request from {sender_key}: {query[:60]}")
            
            # Save request
            req_entry = {
                'id': str(int(time.time() * 1000000)),
                'sender_key': sender_key,
                'sender_id': data.get('sender_id'),
                'query': query,
                'source': data.get('source', 'telegram'),
                'channel_idx': data.get('channel_idx'),
                'is_direct': data.get('is_direct', True),
                'conversation_history': data.get('conversation_history', []),
                'timestamp': data.get('timestamp'),
                'status': 'pending',
                'received_at': time.time()
            }
            
            # Save to file
            requests = []
            if os.path.exists(REQUESTS_FILE):
                with open(REQUESTS_FILE, 'r') as f:
                    requests = json.load(f)
            requests.append(req_entry)
            with open(REQUESTS_FILE, 'w') as f:
                json.dump(requests, f, indent=2)
            
            # Process immediately in background thread
            def process_and_respond():
                time.sleep(0.5)  # Small delay
                process_request(req_entry)
                # Mark as completed
                try:
                    with open(REQUESTS_FILE, 'r') as f:
                        reqs = json.load(f)
                    for r in reqs:
                        if r['id'] == req_entry['id']:
                            r['status'] = 'completed'
                    with open(REQUESTS_FILE, 'w') as f:
                        json.dump(reqs, f, indent=2)
                except:
                    pass
            
            threading.Thread(target=process_and_respond, daemon=True).start()
            
            # Return immediate acknowledgment
            response = {
                'response': "🐌 Message received by agent.",
                'request_id': req_entry['id'],
                'status': 'accepted'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error: {e}")
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
        else:
            self.send_error(404)

def run_server(port=9090):
    with socketserver.TCPServer(("", port), AgentHandler) as httpd:
        print(f"🚀 Agent system running on port {port}")
        print("Waiting for requests...")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
