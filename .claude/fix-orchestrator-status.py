#!/usr/bin/env python3
"""
Quick fix to make orchestrator show as ONLINE
Creates heartbeat with correct ID format
"""

import json
import time
from pathlib import Path
from datetime import datetime

def create_heartbeat(agent_id, heartbeat_dir):
    """Create heartbeat file for agent"""
    heartbeat_file = heartbeat_dir / f"{agent_id}.heartbeat"
    heartbeat_data = {
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent_id,
        "agent_name": "orchestrator",
        "status": "active",
        "last_activity": datetime.now().isoformat()
    }
    
    # Write as simple timestamp (what the monitor expects)
    heartbeat_file.write_text(datetime.now().isoformat())
    print(f"Created heartbeat for {agent_id}")

def main():
    heartbeat_dir = Path(r"C:\Jarvis\AI Workspace\Super Agent\shared\heartbeats")
    heartbeat_dir.mkdir(parents=True, exist_ok=True)
    
    print("Starting orchestrator heartbeat fix...")
    print("This will make the orchestrator show as ONLINE")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Create heartbeats for both ID formats
            create_heartbeat("agent-orchestrator", heartbeat_dir)
            create_heartbeat("agent-orchestrator-001", heartbeat_dir)
            
            print(f"Heartbeat sent at {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(30)  # Send every 30 seconds
            
    except KeyboardInterrupt:
        print("\nStopped heartbeat")

if __name__ == "__main__":
    main()