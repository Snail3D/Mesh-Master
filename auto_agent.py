#!/usr/bin/env python3
"""
Auto Agent Responder - Continuously monitors and responds to /agent requests
Run this alongside Meshmaster for automatic agent responses
"""

import json
import time
import os
import sys

REQUESTS_FILE = "/home/snailpi/Mesh-Master/data/hermes_requests.json"
RESPONSES_FILE = "/home/snailpi/Mesh-Master/data/hermes_responses.json"
POLL_INTERVAL = 3  # Check every 3 seconds

def load_json_file(filepath, default=None):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return default if default is not None else []

def save_json_file(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False

def process_request(request):
    """Process a single request and return response text"""
    query = request.get('query', '').lower()
    sender = request.get('sender_key', 'unknown')
    
    # Simple response logic - expand as needed
    if 'time' in query:
        from datetime import datetime
        return f"🐌 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elif 'weather' in query:
        return "🐌 I can help you check weather. What location?"
    elif 'help' in query:
        return "🐌 Agent commands I understand: time, weather, status, help"
    elif 'status' in query:
        return "🐌 Agent is running and monitoring for requests."
    else:
        return f"🐌 Received: '{request.get('query', '')}'. I'm the Hermes agent integrated with Meshmaster. Your message was processed successfully."

def main():
    print("🐌 Auto Agent Responder started")
    print(f"Monitoring: {REQUESTS_FILE}")
    print(f"Responses: {RESPONSES_FILE}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print("Press Ctrl+C to stop\n")
    
    processed_ids = set()
    
    try:
        while True:
            requests = load_json_file(REQUESTS_FILE, [])
            responses = load_json_file(RESPONSES_FILE, [])
            
            pending = [r for r in requests if r.get('status') == 'pending' and r['id'] not in processed_ids]
            
            for req in pending:
                req_id = req['id']
                processed_ids.add(req_id)
                
                print(f"[{time.strftime('%H:%M:%S')}] Processing request from {req['sender_key']}: {req['query'][:50]}...")
                
                # Generate response
                response_text = process_request(req)
                
                # Create response entry
                response = {
                    "id": f"resp_{req_id}",
                    "sender_key": req['sender_key'],
                    "message": response_text,
                    "source": req.get('source', 'telegram'),
                    "channel_idx": req.get('channel_idx'),
                    "is_direct": req.get('is_direct', True),
                    "timestamp": time.time(),
                    "status": "pending_delivery"
                }
                responses.append(response)
                
                # Mark request as completed
                for r in requests:
                    if r['id'] == req_id:
                        r['status'] = 'completed'
                
                print(f"  → Response created: {response_text[:60]}...")
            
            # Save if we processed anything
            if pending:
                save_json_file(RESPONSES_FILE, responses)
                save_json_file(REQUESTS_FILE, requests)
                print(f"  → Saved {len(pending)} responses\n")
            
            # Cleanup old processed IDs
            if len(processed_ids) > 1000:
                processed_ids = set(list(processed_ids)[-500:])
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nShutting down auto-agent...")
        sys.exit(0)

if __name__ == "__main__":
    main()
