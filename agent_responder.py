#!/usr/bin/env python3
"""
Agent Responder - Process Hermes requests and send responses back to Meshmaster
This runs as part of the Hermes agent to respond to /agent commands
"""

import json
import os
import time
import requests

REQUESTS_FILE = "/home/snailpi/Mesh-Master/data/hermes_requests.json"
RESPONSES_FILE = "/home/snailpi/Mesh-Master/data/hermes_responses.json"
MESHMASTER_PORT = 5001

class MeshmasterResponder:
    def __init__(self):
        self.processed_ids = set()
        
    def get_pending_requests(self):
        """Get pending requests from the queue"""
        try:
            if not os.path.exists(REQUESTS_FILE):
                return []
            with open(REQUESTS_FILE, 'r') as f:
                requests = json.load(f)
            return [r for r in requests if r.get('status') == 'pending']
        except Exception as e:
            print(f"Error reading requests: {e}")
            return []
    
    def mark_request_processing(self, request_id):
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
            print(f"Error updating request: {e}")
    
    def mark_request_complete(self, request_id, response_text):
        """Mark a request as complete with response"""
        try:
            with open(REQUESTS_FILE, 'r') as f:
                requests = json.load(f)
            for r in requests:
                if r['id'] == request_id:
                    r['status'] = 'completed'
                    r['response'] = response_text
                    r['completed_at'] = time.time()
                    break
            with open(REQUESTS_FILE, 'w') as f:
                json.dump(requests, f, indent=2)
        except Exception as e:
            print(f"Error completing request: {e}")
    
    def send_to_meshmaster(self, sender_key, message, source, channel_idx=None, is_direct=True):
        """Send response back to Meshmaster for delivery"""
        try:
            # Store response for Meshmaster to pick up
            response_entry = {
                'id': str(time.time()),
                'sender_key': sender_key,
                'message': message,
                'source': source,
                'channel_idx': channel_idx,
                'is_direct': is_direct,
                'timestamp': time.time(),
                'status': 'pending_delivery'
            }
            
            if os.path.exists(RESPONSES_FILE):
                with open(RESPONSES_FILE, 'r') as f:
                    responses = json.load(f)
            else:
                responses = []
            
            responses.append(response_entry)
            
            # Keep file size manageable
            if len(responses) > 100:
                responses = responses[-100:]
            
            with open(RESPONSES_FILE, 'w') as f:
                json.dump(responses, f, indent=2)
            
            print(f"[Responder] Queued response for {sender_key}")
            return True
            
        except Exception as e:
            print(f"Error sending to Meshmaster: {e}")
            return False
    
    def process_request(self, request):
        """Process a single request - this is called by Hermes"""
        request_id = request['id']
        sender_key = request['sender_key']
        query = request['query']
        source = request.get('source', 'unknown')
        
        print(f"[Responder] Processing request {request_id}: {query[:50]}...")
        
        # Mark as processing
        self.mark_request_processing(request_id)
        
        # Return the query for Hermes to process
        # Hermes will call this and then provide the response
        return {
            'id': request_id,
            'sender_key': sender_key,
            'query': query,
            'source': source,
            'channel_idx': request.get('channel_idx'),
            'is_direct': request.get('is_direct', True)
        }
    
    def submit_response(self, request_id, response_text):
        """Submit a response from Hermes back to be delivered"""
        try:
            with open(REQUESTS_FILE, 'r') as f:
                requests = json.load(f)
            
            request = None
            for r in requests:
                if r['id'] == request_id:
                    request = r
                    break
            
            if not request:
                print(f"[Responder] Request {request_id} not found")
                return False
            
            # Mark complete
            self.mark_request_complete(request_id, response_text)
            
            # Queue for delivery
            self.send_to_meshmaster(
                request['sender_key'],
                response_text,
                request.get('source', 'unknown'),
                request.get('channel_idx'),
                request.get('is_direct', True)
            )
            
            print(f"[Responder] Response submitted for {request_id}")
            return True
            
        except Exception as e:
            print(f"Error submitting response: {e}")
            return False


if __name__ == "__main__":
    # Simple test
    responder = MeshmasterResponder()
    pending = responder.get_pending_requests()
    print(f"Found {len(pending)} pending requests")
    for req in pending:
        print(f"  - {req['sender_key']}: {req['query'][:50]}...")
