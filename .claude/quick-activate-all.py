#!/usr/bin/env python3
"""
Quick activation of all agents - creates heartbeats for all
"""

from pathlib import Path
from datetime import datetime

def activate_all_agents():
    workspace = Path(r"C:\Jarvis\AI Workspace\Super Agent")
    heartbeat_dir = workspace / "shared" / "heartbeats"
    heartbeat_dir.mkdir(parents=True, exist_ok=True)
    
    # List of all system agents
    system_agents = [
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
        "agent-support"
    ]
    
    # List of project agents
    project_agents = [
        "agent-communication-001",
        "agent-development-001",
        "agent-quality-001",
        "agent-research-001"
    ]
    
    all_agents = system_agents + project_agents
    
    print(f"Creating heartbeats for {len(all_agents)} agents...")
    
    for agent_id in all_agents:
        # Skip the weird $dir one
        if "$dir" in agent_id:
            continue
            
        heartbeat_file = heartbeat_dir / f"{agent_id}.heartbeat"
        heartbeat_file.write_text(datetime.now().isoformat())
        print(f"  + {agent_id}")
        
        # Also create versioned for system agents
        if agent_id in system_agents:
            versioned_file = heartbeat_dir / f"{agent_id}-001.heartbeat"
            versioned_file.write_text(datetime.now().isoformat())
    
    print("\nAll agents activated! They should show as ONLINE in the dashboard.")

if __name__ == "__main__":
    activate_all_agents()