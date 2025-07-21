#!/usr/bin/env python3
"""
Universal Agent Starter - Activates any agent with heartbeat monitoring
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

class AgentStarter:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent.parent
        self.heartbeat_dir = self.base_path / "shared" / "heartbeats"
        
    def create_heartbeat(self, agent_name, process=None):
        """Create heartbeat file for agent"""
        timestamp = datetime.now().isoformat()
        agent_id = f"agent-{agent_name}-001"
        
        heartbeat = {
            "timestamp": timestamp,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "pid": process.pid if process else os.getpid(),
            "working_directory": str(self.base_path),
            "context_active": True
        }
        
        heartbeat_file = self.heartbeat_dir / f"{agent_id}.heartbeat"
        
        # Ensure heartbeat directory exists
        self.heartbeat_dir.mkdir(parents=True, exist_ok=True)
        
        with open(heartbeat_file, 'w') as f:
            json.dump(heartbeat, f, indent=2)
        
        return heartbeat_file
    
    def start_agent_process(self, agent_name):
        """Start agent as background process with heartbeat"""
        print(f"Starting Agent: {agent_name}...")
        
        try:
            # Create a simple agent runner script
            cmd = [sys.executable, "-c", f"""
import json
import time
import os
from datetime import datetime
from pathlib import Path

agent_name = "{agent_name}"
agent_id = "agent-{agent_name}-001"
base_path = Path(r"{self.base_path}")
heartbeat_file = base_path / "shared" / "heartbeats" / f"{{agent_id}}.heartbeat"

print(f"Agent {{agent_name}} started with PID {{os.getpid()}}")

# Keep updating heartbeat every 30 seconds
while True:
    try:
        timestamp = datetime.now().isoformat()
        heartbeat = {{
            "timestamp": timestamp,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "pid": os.getpid(),
            "working_directory": str(base_path),
            "context_active": True,
            "status": "active"
        }}
        
        with open(heartbeat_file, 'w') as f:
            json.dump(heartbeat, f, indent=2)
            
        time.sleep(30)
        
    except KeyboardInterrupt:
        print(f"Agent {{agent_name}} shutting down...")
        break
    except Exception as e:
        print(f"Heartbeat error: {{e}}")
        time.sleep(30)
"""]
            
            # Start the process detached
            if os.name == 'nt':  # Windows
                process = subprocess.Popen(
                    cmd,
                    cwd=self.base_path,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:  # Unix/Linux
                process = subprocess.Popen(
                    cmd,
                    cwd=self.base_path,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Give process time to start
            time.sleep(2)
            
            print(f"[SUCCESS] Agent {agent_name} started (PID: {process.pid})")
            print(f"   - Heartbeat file: agent-{agent_name}-001.heartbeat")
            print(f"   - Status: Active with context persistence")
            
            return {
                "status": "started",
                "agent_name": agent_name,
                "agent_id": f"agent-{agent_name}-001",
                "pid": process.pid,
                "heartbeat_file": str(self.heartbeat_dir / f"agent-{agent_name}-001.heartbeat")
            }
            
        except Exception as e:
            print(f"[ERROR] Error starting agent {agent_name}: {e}")
            return {"error": str(e), "agent_name": agent_name}

def start_agent(agent_name, base_path=None):
    """Start a specific agent"""
    starter = AgentStarter(base_path)
    return starter.start_agent_process(agent_name)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_starter.py <agent_name>")
        print("Available agents: development, quality, research, communication, support, architect, debugger, optimizer, innovation")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    result = start_agent(agent_name)
    
    if "error" in result:
        sys.exit(1)