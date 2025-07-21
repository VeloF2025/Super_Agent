#!/usr/bin/env python3
"""
Agent Heartbeat Integration for Claude Context Management
Keeps agents showing as ONLINE in the dashboard
"""

import os
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class AgentHeartbeat:
    def __init__(self, workspace_root: str, agent_name: str = None):
        self.workspace_root = Path(workspace_root)
        self.heartbeat_dir = self.workspace_root / "shared" / "heartbeats"
        self.claude_dir = self.workspace_root / ".claude"
        
        # Auto-detect agent from current directory if not specified
        if not agent_name:
            agent_name = self._detect_agent_name()
        
        self.agent_name = agent_name
        self.agent_id = self._get_agent_id()
        self.heartbeat_thread = None
        self.running = False
        
        # Ensure heartbeat directory exists
        self.heartbeat_dir.mkdir(parents=True, exist_ok=True)
        
    def _detect_agent_name(self) -> str:
        """Detect agent name from current directory"""
        cwd = Path.cwd()
        
        # Check if we're in an agent directory
        if "agents" in cwd.parts:
            for i, part in enumerate(cwd.parts):
                if part == "agents" and i + 1 < len(cwd.parts):
                    agent_dir = cwd.parts[i + 1]
                    if agent_dir.startswith("agent-"):
                        return agent_dir.replace("agent-", "")
        
        # Default to orchestrator
        return "orchestrator"
    
    def _get_agent_id(self) -> str:
        """Get agent ID from config or generate one"""
        # Try to load from local config
        local_config = self.claude_dir / "config.local.json"
        if local_config.exists():
            try:
                config = json.loads(local_config.read_text())
                agent_config = config.get("agents", {}).get(self.agent_name, {})
                if "instance_id" in agent_config:
                    return agent_config["instance_id"]
            except:
                pass
        
        # Generate default ID
        return f"agent-{self.agent_name}-001"
    
    def start(self, interval: int = 30):
        """Start sending heartbeats"""
        if self.running:
            print(f"Heartbeat already running for {self.agent_id}")
            return
        
        self.running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(interval,),
            daemon=True
        )
        self.heartbeat_thread.start()
        
        print(f"Started heartbeat for {self.agent_id} (interval: {interval}s)")
        
        # Send initial heartbeat
        self.send_heartbeat()
    
    def stop(self):
        """Stop sending heartbeats"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        print(f"Stopped heartbeat for {self.agent_id}")
    
    def send_heartbeat(self) -> bool:
        """Send a single heartbeat"""
        try:
            heartbeat_file = self.heartbeat_dir / f"{self.agent_id}.heartbeat"
            heartbeat_data = {
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "pid": os.getpid(),
                "working_directory": str(Path.cwd()),
                "context_active": self._is_context_active()
            }
            
            # Write heartbeat file
            heartbeat_file.write_text(json.dumps(heartbeat_data, indent=2))
            
            # Also update the file modification time
            os.utime(heartbeat_file, None)
            
            return True
        except Exception as e:
            print(f"Error sending heartbeat: {e}")
            return False
    
    def _heartbeat_loop(self, interval: int):
        """Background thread for sending heartbeats"""
        while self.running:
            self.send_heartbeat()
            time.sleep(interval)
    
    def _is_context_active(self) -> bool:
        """Check if Claude context is currently active"""
        # Check for lock files in cache
        cache_dir = self.claude_dir / "cache"
        if cache_dir.exists():
            lock_files = list(cache_dir.glob("*.lock"))
            for lock_file in lock_files:
                try:
                    lock_data = json.loads(lock_file.read_text())
                    if lock_data.get("agent") == self.agent_name:
                        return True
                except:
                    pass
        
        return False
    
    def register_agent(self):
        """Register agent with the system"""
        try:
            # Create/update agent config
            agent_config_file = self.workspace_root / "agents" / f"agent-{self.agent_name}" / ".agent-config.json"
            
            if agent_config_file.exists():
                config = json.loads(agent_config_file.read_text())
            else:
                config = {}
            
            # Update with current info
            config.update({
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "last_registered": datetime.now().isoformat(),
                "heartbeat_enabled": True,
                "context_management": "claude-v2"
            })
            
            # Save config
            agent_config_file.parent.mkdir(parents=True, exist_ok=True)
            agent_config_file.write_text(json.dumps(config, indent=2))
            
            print(f"Registered {self.agent_id} with the system")
            return True
            
        except Exception as e:
            print(f"Error registering agent: {e}")
            return False


class HeartbeatManager:
    """Manages heartbeats for all agents"""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.agents = {}
        
    def start_agent(self, agent_name: str, interval: int = 30):
        """Start heartbeat for a specific agent"""
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentHeartbeat(
                str(self.workspace_root),
                agent_name
            )
        
        heartbeat = self.agents[agent_name]
        heartbeat.register_agent()
        heartbeat.start(interval)
        
    def stop_agent(self, agent_name: str):
        """Stop heartbeat for a specific agent"""
        if agent_name in self.agents:
            self.agents[agent_name].stop()
            del self.agents[agent_name]
    
    def start_all(self):
        """Start heartbeats for all discovered agents"""
        agents_dir = self.workspace_root / "agents"
        
        for agent_dir in agents_dir.glob("agent-*"):
            if agent_dir.is_dir():
                agent_name = agent_dir.name.replace("agent-", "")
                self.start_agent(agent_name)
    
    def stop_all(self):
        """Stop all heartbeats"""
        for agent_name in list(self.agents.keys()):
            self.stop_agent(agent_name)
    
    def status(self) -> Dict[str, bool]:
        """Get status of all managed heartbeats"""
        status = {}
        
        for agent_name, heartbeat in self.agents.items():
            status[agent_name] = heartbeat.running
        
        return status


# Integration with Claude context system
def integrate_with_context():
    """Add heartbeat to Claude context loading"""
    integration_code = '''
# Auto-start heartbeat when loading context
from agent_heartbeat import AgentHeartbeat
heartbeat = AgentHeartbeat(".")
heartbeat.start()
'''
    
    # Add to context templates
    template_file = Path(".claude/contexts/templates/heartbeat_integration.py")
    template_file.parent.mkdir(parents=True, exist_ok=True)
    template_file.write_text(integration_code)
    
    print("Created heartbeat integration template")


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Heartbeat Manager")
    parser.add_argument("command", choices=["start", "stop", "status", "register", "start-all"])
    parser.add_argument("--agent", help="Agent name")
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument("--interval", type=int, default=30, help="Heartbeat interval in seconds")
    
    args = parser.parse_args()
    
    if args.command in ["start", "stop", "register"] and not args.agent:
        # Auto-detect agent
        heartbeat = AgentHeartbeat(args.workspace)
        agent_name = heartbeat.agent_name
    else:
        agent_name = args.agent
    
    if args.command == "start":
        heartbeat = AgentHeartbeat(args.workspace, agent_name)
        heartbeat.register_agent()
        heartbeat.start(args.interval)
        
        print(f"\nHeartbeat running for {heartbeat.agent_id}")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            heartbeat.stop()
    
    elif args.command == "stop":
        heartbeat = AgentHeartbeat(args.workspace, agent_name)
        heartbeat.stop()
    
    elif args.command == "status":
        heartbeat_dir = Path(args.workspace) / "shared" / "heartbeats"
        
        if heartbeat_dir.exists():
            print("Active Heartbeats:")
            now = time.time()
            
            for hb_file in heartbeat_dir.glob("*.heartbeat"):
                try:
                    data = json.loads(hb_file.read_text())
                    age = now - hb_file.stat().st_mtime
                    
                    status = "ONLINE" if age < 60 else "OFFLINE"
                    print(f"  {data['agent_id']}: {status} (last: {int(age)}s ago)")
                except:
                    pass
        else:
            print("No heartbeats found")
    
    elif args.command == "register":
        heartbeat = AgentHeartbeat(args.workspace, agent_name)
        if heartbeat.register_agent():
            print("Registration successful")
    
    elif args.command == "start-all":
        manager = HeartbeatManager(args.workspace)
        manager.start_all()
        
        print("\nStarted heartbeats for all agents")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop_all()