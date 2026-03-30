#!/usr/bin/env python3
"""
Simple working agent - no threads, no complexity
"""
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load config once
with open('data/telegram_config.json') as f:
    TG = json.load(f)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    
    def do_POST(self):
        if self.path != "/meshmaster/agent":
            self.send_error(404)
            return
        
        # Read request
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length).decode())
        
        sender = data.get('sender_key', '')
        query = data.get('query', '')
        
        print(f"[{__import__('time').strftime('%H:%M:%S')}] Got: {query[:40]}")
        
        # Send response to Telegram NOW
        success = False
        if sender.startswith('telegram_'):
            chat = sender.replace('telegram_', '')
            try:
                r = requests.post(
                    f"https://api.telegram.org/bot{TG['token']}/sendMessage",
                    json={"chat_id": chat, "text": f"🐌 Got: '{query}'"},
                    timeout=10
                )
                success = r.status_code == 200
                print(f"  Telegram: {'OK' if success else 'FAIL'}")
            except Exception as e:
                print(f"  Error: {e}")
        
        # Return acknowledgment
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'response': '🐌 Message received by agent.',
            'delivery_success': success
        }).encode())

print("🚀 Agent on port 9093...")
HTTPServer(('', 9093), Handler).serve_forever()
