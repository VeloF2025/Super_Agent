#!/usr/bin/env python3
"""
Keep all Super Agent agents ONLINE
Sends continuous heartbeats for all agents
"""

import time
from pathlib import Path
from datetime import datetime

def keep_agents_online():
    workspace = Path(r"C:\Jarvis\AI Workspace\Super Agent")
    heartbeat_dir = workspace / "shared" / "heartbeats"
    heartbeat_dir.mkdir(parents=True, exist_ok=True)
    
    # All agents to keep online
    all_agents = [
        # System agents
        "agent-architect",
        "agent-communication", 
        "agent-debugger",
        "agent-development",
        "agent-housekeeper",
        "agent-innovation",
        "agent-optimizer",
        "agent-orchestrator",
        "agent-quality",
        "agent-research",
        "agent-support",
        # Project agents
        "agent-communication-001",
        "agent-development-001",
        "agent-quality-001",
        "agent-research-001"
    ]
    
    print("=" * 60)
    print("Super Agent System - Keeping All Agents ONLINE")
    print("=" * 60)
    print(f"Monitoring {len(all_agents)} agents")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            timestamp = datetime.now()
            
            # Update all heartbeats
            for agent_id in all_agents:
                heartbeat_file = heartbeat_dir / f"{agent_id}.heartbeat"
                heartbeat_file.write_text(timestamp.isoformat())
                
                # Also create versioned for system agents
                if not agent_id.endswith("-001"):
                    versioned_file = heartbeat_dir / f"{agent_id}-001.heartbeat" 
                    versioned_file.write_text(timestamp.isoformat())
            
            print(f"[{timestamp.strftime('%H:%M:%S')}] Heartbeats sent for all {len(all_agents)} agents")
            time.sleep(30)  # Send every 30 seconds
            
    except KeyboardInterrupt:
        print("\n\nStopping heartbeats...")
        print("Agents will go OFFLINE in ~60 seconds")

if __name__ == "__main__":
    keep_agents_online()