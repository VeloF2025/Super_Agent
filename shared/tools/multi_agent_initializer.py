#!/usr/bin/env python3
"""
Multi-Agent Initialization System
Ensures all agents are properly initialized when @Jarvis is triggered
"""

import json
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path
import psutil

class MultiAgentInitializer:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.heartbeat_dir = self.base_path / "shared" / "heartbeats"
        self.agent_starter = self.base_path / "shared" / "tools" / "agent_starter.py"
        
        # Define all required agents
        self.required_agents = [
            "orchestrator",
            "development", 
            "quality",
            "research",
            "communication",
            "support", 
            "architect",
            "housekeeper",
            "debugger",
            "optimizer",
            "innovation"
        ]
    
    def get_active_agents(self):
        """Get list of currently active agents"""
        active = []
        
        if not self.heartbeat_dir.exists():
            return active
            
        for heartbeat_file in self.heartbeat_dir.glob("*.heartbeat"):
            try:
                with open(heartbeat_file, 'r') as f:
                    data = json.load(f)
                    
                # Check if heartbeat is recent (within 2 minutes)
                timestamp_str = data.get("timestamp", "")
                if timestamp_str:
                    heartbeat_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').replace('Z', ''))
                    time_diff = (datetime.now() - heartbeat_time).total_seconds()
                    
                    if time_diff < 120:  # 2 minutes
                        # Verify process is actually running
                        pid = data.get("pid")
                        if pid:
                            try:
                                if psutil.Process(pid).is_running():
                                    active.append({
                                        "agent_name": data.get("agent_name"),
                                        "agent_id": data.get("agent_id"),
                                        "pid": pid,
                                        "status": data.get("status", "unknown"),
                                        "last_heartbeat": timestamp_str
                                    })
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # Process not running, skip
                                pass
                                
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
                
        return active
    
    def start_missing_agents(self):
        """Start any missing required agents"""
        active_agents = self.get_active_agents()
        active_names = [agent["agent_name"] for agent in active_agents]
        
        missing_agents = [name for name in self.required_agents if name not in active_names]
        
        started_agents = []
        failed_agents = []
        
        for agent_name in missing_agents:
            try:
                print(f"Starting {agent_name} agent...")
                
                # Use agent starter to launch agent
                result = subprocess.run([
                    "python", 
                    str(self.agent_starter),
                    agent_name
                ], 
                capture_output=True, 
                text=True, 
                timeout=10,
                cwd=str(self.base_path)
                )
                
                if result.returncode == 0:
                    started_agents.append(agent_name)
                    print(f"[SUCCESS] {agent_name} agent started")
                else:
                    failed_agents.append({
                        "agent": agent_name,
                        "error": result.stderr or result.stdout
                    })
                    print(f"[ERROR] Failed to start {agent_name}: {result.stderr}")
                
                # Brief pause between starts
                time.sleep(2)
                
            except subprocess.TimeoutExpired:
                failed_agents.append({
                    "agent": agent_name,
                    "error": "Startup timeout"
                })
                print(f"[ERROR] {agent_name} startup timed out")
                
            except Exception as e:
                failed_agents.append({
                    "agent": agent_name,
                    "error": str(e)
                })
                print(f"[ERROR] Exception starting {agent_name}: {e}")
        
        return {
            "started": started_agents,
            "failed": failed_agents,
            "already_active": active_names
        }
    
    def verify_system_readiness(self):
        """Verify all systems are ready after initialization"""
        active_agents = self.get_active_agents()
        
        readiness = {
            "total_agents": len(active_agents),
            "required_agents": len(self.required_agents),
            "coverage": len(active_agents) / len(self.required_agents) * 100,
            "agents": active_agents,
            "missing": [],
            "system_ready": False
        }
        
        active_names = [agent["agent_name"] for agent in active_agents]
        readiness["missing"] = [name for name in self.required_agents if name not in active_names]
        readiness["system_ready"] = len(readiness["missing"]) <= 2  # Allow up to 2 missing for "ready"
        
        return readiness
    
    def initialize_full_system(self):
        """Complete system initialization sequence"""
        print("[ROBOT] JARVIS SUPER AGENT SYSTEM INITIALIZATION")
        print("=" * 50)
        
        # Step 1: Check current status
        print("Step 1: Assessing current agent status...")
        active_before = self.get_active_agents()
        print(f"Found {len(active_before)} active agents")
        
        # Step 2: Start missing agents
        print("\nStep 2: Starting missing agents...")
        startup_results = self.start_missing_agents()
        
        if startup_results["started"]:
            print(f"[SUCCESS] Started {len(startup_results['started'])} new agents:")
            for agent in startup_results["started"]:
                print(f"   - {agent}")
        
        if startup_results["failed"]:
            print(f"[FAILED] Failed to start {len(startup_results['failed'])} agents:")
            for failure in startup_results["failed"]:
                print(f"   - {failure['agent']}: {failure['error']}")
        
        # Step 3: Wait for stabilization
        print("\nStep 3: Waiting for system stabilization...")
        time.sleep(10)
        
        # Step 4: Final verification
        print("\nStep 4: Final system verification...")
        readiness = self.verify_system_readiness()
        
        print(f"\n[TARGET] SYSTEM STATUS:")
        print(f"   Active Agents: {readiness['total_agents']}/{readiness['required_agents']}")
        print(f"   System Coverage: {readiness['coverage']:.1f}%")
        print(f"   System Ready: {'[YES]' if readiness['system_ready'] else '[NO]'}")
        
        if readiness["missing"]:
            print(f"   Missing: {', '.join(readiness['missing'])}")
        
        # Step 5: Generate initialization report
        report = {
            "initialization_time": datetime.now().isoformat(),
            "startup_results": startup_results,
            "final_status": readiness,
            "initialization_successful": readiness["system_ready"]
        }
        
        report_file = self.base_path / "logs" / "system" / f"jarvis_init_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[REPORT] Initialization report: {report_file}")
        print("\n[ROCKET] JARVIS SUPER AGENT SYSTEM READY FOR OPERATIONS")
        
        # Initialize auto-acceptance system
        self._initialize_auto_acceptance()
        
    def _initialize_auto_acceptance(self):
        """Initialize the auto-acceptance system"""
        try:
            auto_accept_path = self.base_path / "memory" / "context" / "jarvis" / "jarvis_auto_acceptance.py"
            if auto_accept_path.exists():
                import subprocess
                result = subprocess.run([
                    "python", str(auto_accept_path), "--start-service"
                ], capture_output=True, text=True, cwd=str(auto_accept_path.parent))
                
                if result.returncode == 0:
                    print("[ACCEPT] Auto-acceptance system initialized successfully")
                else:
                    print(f"[WARNING] Auto-acceptance initialization issues: {result.stderr}")
            else:
                print("[WARNING] Auto-acceptance system not found")
        except Exception as e:
            print(f"[ERROR] Failed to initialize auto-acceptance: {e}")

def main():
    """Main initialization function"""
    initializer = MultiAgentInitializer()
    return initializer.initialize_full_system()

if __name__ == "__main__":
    main()