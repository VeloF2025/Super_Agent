#!/usr/bin/env python3
"""
Process communication queue messages and add them to dashboard
"""

import json
import requests
from pathlib import Path
from datetime import datetime

def process_queue_messages():
    workspace = Path(r"C:\Jarvis\AI Workspace\Super Agent")
    queue_dir = workspace / "shared" / "communication" / "queue" / "incoming"
    
    if not queue_dir.exists():
        print("No queue directory found")
        return
    
    messages = list(queue_dir.glob("*.json"))
    print(f"Found {len(messages)} messages in queue\n")
    
    for msg_file in messages:
        try:
            # Read message
            with open(msg_file, 'r') as f:
                message = json.load(f)
            
            print(f"Processing: {message['from']} -> {message['to']}")
            
            # Send to dashboard API
            response = requests.post(
                "http://localhost:3001/api/communications",
                json={
                    "from_agent": message["from"],
                    "to_agent": message["to"],
                    "message_type": message["type"],
                    "priority": message.get("priority", "normal"),
                    "content": message["content"]
                }
            )
            
            if response.status_code == 200:
                print(f"  + Added to dashboard")
                
                # Move to completed
                completed_dir = workspace / "shared" / "communication" / "queue" / "completed"
                completed_dir.mkdir(parents=True, exist_ok=True)
                
                new_path = completed_dir / msg_file.name
                msg_file.rename(new_path)
                print(f"  + Moved to completed")
            else:
                print(f"  ! Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ! Error processing {msg_file.name}: {e}")
    
    print(f"\nProcessed {len(messages)} messages")
    print("Communications should now appear in the dashboard!")

if __name__ == "__main__":
    process_queue_messages()