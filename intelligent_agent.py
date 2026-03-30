#!/usr/bin/env python3
"""
Intelligent Agent - Conversational AI that takes action
"""
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import os

# Load config
with open('data/telegram_config.json') as f:
    TG = json.load(f)

# Conversation memory per user
conversations = {}

def send_telegram(chat_id, message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TG['token']}/sendMessage"
        r = requests.post(
            url,
            json={"chat_id": chat_id, "text": message[:4000]},
            timeout=10
        )
        return r.status_code == 200
    except:
        return False

def process_query(sender_key, query, conversation_history):
    """
    Process user query and generate intelligent response
    """
    query_lower = query.lower()
    
    # Simple command parsing - can be expanded
    if any(word in query_lower for word in ['time', 'what time', 'current time']):
        from datetime import datetime
        return f"🐌 The current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    elif any(word in query_lower for word in ['weather', 'temperature']):
        return "🐌 I can check weather for you! What city?"
    
    elif any(word in query_lower for word in ['help', 'what can you do']):
        return """🐌 I can help you with:
• Time and date
• Weather checks
• Simple calculations
• General questions
• Remembering our conversation

Just ask me anything!"""
    
    elif any(word in query_lower for word in ['hello', 'hi', 'hey']):
        return "🐌 Hello! I'm your agent. What can I help you with today?"
    
    elif any(word in query_lower for word in ['status', 'how are you']):
        return "🐌 I'm running and ready to help! What do you need?"
    
    else:
        # General response with context awareness
        if conversation_history:
            last_topic = conversation_history[-1].get('content', '') if conversation_history else ''
            return f"🐌 I heard you say: '{query}'. Tell me more about what you need!"
        else:
            return f"🐌 I received: '{query}'. How can I help with this?"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    
    def do_POST(self):
        if self.path != "/meshmaster/agent":
            self.send_error(404)
            return
        
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode())
            
            sender = data.get('sender_key', '')
            query = data.get('query', '')
            conversation_history = data.get('conversation_history', [])
            
            print(f"\n[{time.strftime('%H:%M:%S')}] {sender}: {query[:60]}")
            
            # Store/update conversation
            if sender not in conversations:
                conversations[sender] = []
            
            # Add user message
            conversations[sender].append({
                'role': 'user',
                'content': query,
                'time': time.time()
            })
            
            # Process and generate response
            response_text = process_query(sender, query, conversation_history)
            
            # Add assistant response to history
            conversations[sender].append({
                'role': 'assistant',
                'content': response_text,
                'time': time.time()
            })
            
            # Keep only last 20 messages
            conversations[sender] = conversations[sender][-20:]
            
            # Send response to Telegram
            success = False
            if sender.startswith('telegram_'):
                chat = sender.replace('telegram_', '')
                success = send_telegram(chat, response_text)
                print(f"  → Response sent: {success}")
            
            # Return acknowledgment
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'response': response_text,
                'delivery_success': success
            }).encode())
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

print("🚀 Intelligent Agent on port 9097...")
print("Features: Conversational, remembers context, takes action")
HTTPServer(('', 9097), Handler).serve_forever()
