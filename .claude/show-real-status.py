#!/usr/bin/env python3
"""
Show REAL status of the Super Agent System
No mock data - only actual system state
"""

import json
import os
from pathlib import Path
from datetime import datetime
import requests

def show_real_status():
    workspace = Path(r"C:\Jarvis\AI Workspace\Super Agent")
    
    print("=" * 70)
    print("SUPER AGENT SYSTEM - REAL STATUS")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Agent Status from Dashboard API
    print("AGENT STATUS (from dashboard):")
    print("-" * 40)
    try:
        response = requests.get("http://localhost:3001/api/agents")
        agents = response.json()
        
        online_count = sum(1 for a in agents if a['status'] == 'active')
        print(f"Total Agents: {len(agents)}")
        print(f"Online: {online_count}")
        print(f"Offline: {len(agents) - online_count}\n")
        
        print("Agents:")
        for agent in agents:
            status_icon = "🟢" if agent['status'] == 'active' else "🔴"
            print(f"  {status_icon} {agent['name']} ({agent['type']}) - {agent['status'].upper()}")
            if agent.get('last_seen'):
                print(f"     Last seen: {agent['last_seen']}")
    except Exception as e:
        print(f"  Error connecting to dashboard: {e}")
    
    print("\n" + "-" * 40)
    
    # 2. Heartbeat Files
    print("HEARTBEAT FILES:")
    heartbeat_dir = workspace / "shared" / "heartbeats"
    if heartbeat_dir.exists():
        heartbeats = list(heartbeat_dir.glob("*.heartbeat"))
        print(f"Active heartbeat files: {len(heartbeats)}")
        
        now = datetime.now().timestamp()
        for hb_file in heartbeats[:5]:  # Show first 5
            try:
                age = now - hb_file.stat().st_mtime
                print(f"  - {hb_file.name}: {int(age)}s ago")
            except:
                pass
    
    print("\n" + "-" * 40)
    
    # 3. Log Activity
    print("LOG ACTIVITY:")
    logs_dir = workspace / "logs"
    if logs_dir.exists():
        active_logs = 0
        for agent_log_dir in logs_dir.glob("agent-*"):
            if agent_log_dir.is_dir():
                log_files = list(agent_log_dir.glob("*.log"))
                if log_files:
                    active_logs += 1
                    print(f"  - {agent_log_dir.name}: {len(log_files)} log files")
        
        if active_logs == 0:
            print("  No agent log files found")
    
    print("\n" + "-" * 40)
    
    # 4. Communication Queue
    print("COMMUNICATION QUEUE:")
    queue_dir = workspace / "shared" / "communication" / "queue"
    if queue_dir.exists():
        for queue_type in ["incoming", "processing", "completed"]:
            queue_path = queue_dir / queue_type
            if queue_path.exists():
                messages = list(queue_path.glob("*.json"))
                print(f"  {queue_type}: {len(messages)} messages")
    
    print("\n" + "-" * 40)
    
    # 5. Projects
    print("PROJECTS:")
    projects_dir = workspace / "projects"
    if projects_dir.exists():
        projects = [d for d in projects_dir.iterdir() if d.is_dir()]
        print(f"Total projects: {len(projects)}")
        for project in projects:
            print(f"  - {project.name}")
            
            # Check for agent workspace
            agent_workspace = project / "agent-workspace"
            if agent_workspace.exists():
                agents_in_project = list((agent_workspace / "agents").glob("agent-*")) if (agent_workspace / "agents").exists() else []
                print(f"    Agents: {len(agents_in_project)}")
    
    print("\n" + "-" * 40)
    
    # 6. System Resources
    print("SYSTEM RESOURCES:")
    try:
        import psutil
        print(f"  CPU: {psutil.cpu_percent(interval=1)}%")
        print(f"  Memory: {psutil.virtual_memory().percent}%")
        print(f"  Disk: {psutil.disk_usage(str(workspace)).percent}%")
    except ImportError:
        print("  Install psutil for system metrics: pip install psutil")
    
    print("\n" + "=" * 70)
    print("This is REAL data - no simulations or mock data")
    print("=" * 70)

if __name__ == "__main__":
    show_real_status()