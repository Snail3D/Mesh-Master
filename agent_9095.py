#!/usr/bin/env python3
"""
Debug agent - with full logging to see what's failing
"""
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

# Load config
with open('data/telegram_config.json') as f:
    TG = json.load(f)

LOG_FILE = "/tmp/agent_debug.log"

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    
    def do_POST(self):
        log(f"=== NEW REQUEST to {self.path} ===")
        
        if self.path != "/meshmaster/agent":
            log(f"ERROR: Wrong path: {self.path}")
            self.send_error(404)
            return
        
        # Read request
        try:
            length = int(self.headers.get('Content-Length', 0))
            log(f"Content-Length: {length}")
            
            data = json.loads(self.rfile.read(length).decode())
            log(f"Data received: {json.dumps(data)[:200]}")
            
            sender = data.get('sender_key', '')
            query = data.get('query', '')
            source = data.get('source', '')
            
            log(f"sender: {sender}, query: {query[:50]}, source: {source}")
            
            # Send to Telegram
            success = False
            error_msg = ""
            
            if sender.startswith('telegram_'):
                chat = sender.replace('telegram_', '')
                log(f"Sending to Telegram chat: {chat}")
                log(f"Token exists: {bool(TG.get('token'))}")
                
                try:
                    url = f"https://api.telegram.org/bot{TG['token']}/sendMessage"
                    log(f"POST to {url[:50]}...")
                    
                    r = requests.post(
                        url,
                        json={"chat_id": chat, "text": f"🐌 Agent: '{query}'"},
                        timeout=10
                    )
                    
                    log(f"Telegram response status: {r.status_code}")
                    log(f"Telegram response: {r.text[:200]}")
                    
                    if r.status_code == 200:
                        success = True
                        log("✅ Telegram send SUCCESS")
                    else:
                        error_msg = f"HTTP {r.status_code}: {r.text[:100]}"
                        log(f"❌ Telegram FAILED: {error_msg}")
                        
                except Exception as e:
                    error_msg = str(e)
                    log(f"❌ Telegram EXCEPTION: {e}")
                    import traceback
                    log(traceback.format_exc())
            else:
                log(f"Not a telegram sender: {sender}")
                error_msg = "Not telegram source"
            
            # Return response
            response = {
                'response': '🐌 Message received by agent.',
                'delivery_success': success,
                'error': error_msg if not success else ''
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
            log(f"Returned: delivery_success={success}")
            log("=== REQUEST COMPLETE ===\n")
            
        except Exception as e:
            log(f"❌ CRITICAL ERROR: {e}")
            import traceback
            log(traceback.format_exc())
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

log("🚀 Agent starting on port 9095...")
HTTPServer(('', 9095), Handler).serve_forever()
