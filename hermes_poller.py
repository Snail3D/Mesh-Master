#!/usr/bin/env python3
"""
Hermes Request Poller - Automatically process agent requests
This runs continuously and triggers Hermes when new requests arrive
"""

import json
import os
import time
import subprocess
import sys

REQUESTS_FILE = "/home/snailpi/Mesh-Master/data/hermes_requests.json"
POLL_INTERVAL = 5  # Check every 5 seconds

def get_pending_requests():
    """Get all pending requests from the queue"""
    try:
        if not os.path.exists(REQUESTS_FILE):
            return []
        with open(REQUESTS_FILE, 'r') as f:
            requests = json.load(f)
        return [r for r in requests if r.get('status') == 'pending']
    except Exception as e:
        print(f"Error reading requests: {e}")
        return []

def mark_request_processing(request_id):
    """Mark a request as being processed"""
    try:
        with open(REQUESTS_FILE, 'r') as f:
            requests = json.load(f)
        for r in requests:
            if r['id'] == request_id:
                r['status'] = 'processing'
                break
        with open(REQUESTS_FILE, 'w') as f:
            json.dump(requests, f, indent=2)
    except Exception as e:
        print(f"Error marking request: {e}")

def notify_hermes(request):
    """Notify Hermes about a new request via Discord/CLI"""
    sender = request.get('sender_key', 'unknown')
    query = request.get('query', '')
    
    # Create notification message
    notification = f"""
🔔 **NEW AGENT REQUEST**

From: `{sender}`
Query: {query[:100]}{'...' if len(query) > 100 else ''}

Reply with: `agent respond {request['id']} <your response>`
"""
    
    # Write to a notification file that Hermes can watch
    notify_file = "/home/snailpi/Mesh-Master/data/hermes_notify.txt"
    with open(notify_file, 'a') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {sender}: {query[:80]}\n")
    
    # Also try to use notify-send if available (desktop notification)
    try:
        subprocess.run([
            'notify-send', 
            'Meshmaster Agent Request', 
            f"From {sender}: {query[:60]}..."
        ], check=False, timeout=2)
    except:
        pass
    
    print(notification)

def main():
    print("🐌 Hermes Request Poller started")
    print(f"Monitoring: {REQUESTS_FILE}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print("Press Ctrl+C to stop\n")
    
    processed_ids = set()
    
    try:
        while True:
            pending = get_pending_requests()
            
            for req in pending:
                req_id = req['id']
                if req_id not in processed_ids:
                    processed_ids.add(req_id)
                    print(f"\n[{time.strftime('%H:%M:%S')}] New request detected!")
                    notify_hermes(req)
                    # Mark as processing so we don't notify again
                    mark_request_processing(req_id)
            
            # Clean up old processed IDs (keep last 100)
            if len(processed_ids) > 100:
                processed_ids = set(list(processed_ids)[-100:])
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
