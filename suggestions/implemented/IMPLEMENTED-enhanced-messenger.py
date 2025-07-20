#!/usr/bin/env python3
"""
Simple messaging system for agents
Place this in each agent's workspace
"""

import json
import os
from pathlib import Path
from datetime import datetime
import time

class SimpleMessenger:
    def __init__(self, agent_id=None):
        # Auto-detect agent_id from config if not provided
        if not agent_id:
            config_path = Path(".agent-config.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    agent_id = config["agent_id"]
                    self.comm_paths = config["communication"]
        
        self.agent_id = agent_id
        self.queue = Path(self.comm_paths["queue"])
        self.events = Path(self.comm_paths["events"])
        self.state = Path(self.comm_paths["state"])
    
    def send(self, to_agent, message_type, data):
        """Send a message to another agent"""
        message = {
            "id": f"{self.agent_id}-{int(time.time() * 1000)}",
            "from": self.agent_id,
            "to": to_agent,
            "type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": data
        }
        
        filename = f"{message['timestamp']}_{message['id']}.json"
        filepath = self.queue / filename
        
        with open(filepath, "w") as f:
            json.dump(message, f, indent=2)
        
        print(f"📤 Sent {message_type} to {to_agent}")
        return message["id"]
    
    def receive(self):
        """Check for new messages"""
        messages = []
        
        for filepath in sorted(self.queue.glob("*.json")):
            try:
                with open(filepath, "r") as f:
                    message = json.load(f)
                
                # Check if message is for this agent
                if message["to"] in [self.agent_id, "all", "broadcast"]:
                    messages.append(message)
                    # Move to processed
                    processed = self.queue / "processed"
                    processed.mkdir(exist_ok=True)
                    filepath.rename(processed / filepath.name)
            except:
                pass
        
        return messages
    
    def update_status(self, status, details=None):
        """Update agent status"""
        state_data = {
            "agent_id": self.agent_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        filepath = self.state / f"{self.agent_id}_state.json"
        with open(filepath, "w") as f:
            json.dump(state_data, f, indent=2)
    
    def broadcast_event(self, event_type, data):
        """Broadcast an event to all agents"""
        event = {
            "id": f"evt-{int(time.time() * 1000)}",
            "agent_id": self.agent_id,
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        filename = f"{event['timestamp']}_{event['type']}_{self.agent_id}.json"
        filepath = self.events / filename
        
        with open(filepath, "w") as f:
            json.dump(event, f, indent=2)
        
        print(f"📢 Broadcast event: {event_type}")


# Example usage for agents
if __name__ == "__main__":
    # This would be used by each agent
    messenger = SimpleMessenger()
    
    # Update status
    messenger.update_status("working", {"current_task": "Creating login component"})
    
    # Send message to another agent
    messenger.send("agent-backend-001", "api_request", {
        "need": "authentication endpoints",
        "format": "REST API"
    })
    
    # Check for messages
    messages = messenger.receive()
    for msg in messages:
        print(f"📥 Received {msg['type']} from {msg['from']}")
        print(f"   Data: {msg['payload']}")
    
    # Broadcast completion
    messenger.broadcast_event("component_ready", {
        "component": "LoginForm",
        "path": "src/components/auth/LoginForm.jsx"
    })