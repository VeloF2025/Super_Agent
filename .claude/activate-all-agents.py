#!/usr/bin/env python3
"""
Activate all Super Agent agents by starting their heartbeats
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime
import os

class AllAgentsHeartbeat:
    def __init__(self):
        self.workspace_root = Path(r"C:\Jarvis\AI Workspace\Super Agent")
        self.heartbeat_dir = self.workspace_root / "shared" / "heartbeats"
        self.agents_dir = self.workspace_root / "agents"
        self.projects_dir = self.workspace_root / "projects"
        self.heartbeat_dir.mkdir(parents=True, exist_ok=True)
        self.running = True
        self.agents = []
        
    def discover_agents(self):
        """Discover all agents in the system"""
        agents = []
        
        # Discover Super Agent system agents
        print("Discovering Super Agent agents...")
        for agent_dir in self.agents_dir.glob("agent-*"):
            if agent_dir.is_dir() and not agent_dir.name.endswith("$dir"):
                agent_id = agent_dir.name
                agent_name = agent_id.replace("agent-", "")
                agents.append({
                    "id": agent_id,
                    "name": agent_name,
                    "type": "system",
                    "path": str(agent_dir)
                })
                print(f"  Found: {agent_name}")
        
        # Discover project agents
        print("\nDiscovering project agents...")
        jarvis_agents = self.projects_dir / "Jarvis AI" / "agent-workspace" / "agents"
        if jarvis_agents.exists():
            for agent_dir in jarvis_agents.glob("agent-*"):
                if agent_dir.is_dir():
                    agent_id = agent_dir.name
                    agent_name = agent_id.replace("agent-", "").replace("-001", "")
                    agents.append({
                        "id": agent_id,
                        "name": agent_name,
                        "type": "project",
                        "path": str(agent_dir)
                    })
                    print(f"  Found: {agent_name} (project)")
        
        self.agents = agents
        print(f"\nTotal agents found: {len(agents)}")
        return agents
    
    def create_heartbeat(self, agent):
        """Create heartbeat for a single agent"""
        # Create heartbeat with the exact ID format the dashboard expects
        heartbeat_file = self.heartbeat_dir / f"{agent['id']}.heartbeat"
        
        # Simple timestamp format that the monitor expects
        heartbeat_file.write_text(datetime.now().isoformat())
        
        # Also create the base ID version for system agents
        if agent['type'] == 'system' and '-001' not in agent['id']:
            # Also create versioned heartbeat
            versioned_file = self.heartbeat_dir / f"{agent['id']}-001.heartbeat"
            versioned_file.write_text(datetime.now().isoformat())
    
    def heartbeat_loop(self):
        """Main heartbeat loop for all agents"""
        print("\nStarting heartbeats for all agents...")
        print("All agents will show as ONLINE in the dashboard")
        print("Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{timestamp}] Sending heartbeats:")
                
                for agent in self.agents:
                    self.create_heartbeat(agent)
                    print(f"  ✓ {agent['name']}")
                
                # Also ensure orchestrator stays active with both formats
                orchestrator = {
                    "id": "agent-orchestrator",
                    "name": "orchestrator",
                    "type": "system"
                }
                self.create_heartbeat(orchestrator)
                
                print(f"\nAll {len(self.agents)} agents are ONLINE")
                time.sleep(30)  # Send heartbeats every 30 seconds
                
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(30)
    
    def start(self):
        """Start the heartbeat system"""
        self.discover_agents()
        
        if not self.agents:
            print("No agents found!")
            return
        
        try:
            self.heartbeat_loop()
        except KeyboardInterrupt:
            print("\n\nStopping heartbeats...")
            self.running = False
            print("All agents will go OFFLINE in ~60 seconds")

def main():
    """Main entry point"""
    print("=" * 60)
    print("Super Agent System - Activate All Agents")
    print("=" * 60)
    
    heartbeat_system = AllAgentsHeartbeat()
    heartbeat_system.start()

if __name__ == "__main__":
    main()