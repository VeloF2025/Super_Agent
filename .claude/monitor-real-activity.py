#!/usr/bin/env python3
"""
Monitor REAL agent activity - no simulations
Watches actual logs, queues, and agent work
"""

import json
import time
from pathlib import Path
from datetime import datetime
import os

class RealActivityMonitor:
    def __init__(self):
        self.workspace = Path(r"C:\Jarvis\AI Workspace\Super Agent")
        self.logs_dir = self.workspace / "logs"
        self.queue_dir = self.workspace / "shared" / "communication" / "queue"
        self.metrics_dir = self.workspace / "metrics"
        
    def check_agent_logs(self):
        """Check real log files for agent activity"""
        activities = []
        
        if not self.logs_dir.exists():
            return activities
            
        for agent_log_dir in self.logs_dir.glob("agent-*"):
            if agent_log_dir.is_dir():
                # Check for recent log files
                for log_file in agent_log_dir.glob("*.log"):
                    try:
                        stat = log_file.stat()
                        if time.time() - stat.st_mtime < 300:  # Modified in last 5 min
                            activities.append({
                                "agent": agent_log_dir.name,
                                "file": log_file.name,
                                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "size": stat.st_size
                            })
                    except:
                        pass
                        
        return activities
    
    def check_communication_queue(self):
        """Check real communication queue for messages"""
        messages = {
            "incoming": [],
            "processing": [],
            "completed": []
        }
        
        for queue_type in ["incoming", "processing", "completed"]:
            queue_path = self.queue_dir / queue_type
            if queue_path.exists():
                for msg_file in queue_path.glob("*.json"):
                    try:
                        with open(msg_file, 'r') as f:
                            msg_data = json.load(f)
                            messages[queue_type].append({
                                "file": msg_file.name,
                                "from": msg_data.get("from", "unknown"),
                                "to": msg_data.get("to", "unknown"),
                                "timestamp": msg_data.get("timestamp", "unknown")
                            })
                    except:
                        pass
                        
        return messages
    
    def check_project_activity(self):
        """Check real project directories for activity"""
        projects = []
        projects_dir = self.workspace / "projects"
        
        if projects_dir.exists():
            for project_dir in projects_dir.glob("*"):
                if project_dir.is_dir():
                    # Check for recent modifications
                    try:
                        recent_files = []
                        for file_path in project_dir.rglob("*"):
                            if file_path.is_file():
                                stat = file_path.stat()
                                if time.time() - stat.st_mtime < 3600:  # Modified in last hour
                                    recent_files.append(str(file_path.relative_to(project_dir)))
                                    
                        if recent_files:
                            projects.append({
                                "name": project_dir.name,
                                "recent_activity": len(recent_files),
                                "sample_files": recent_files[:5]
                            })
                    except:
                        pass
                        
        return projects
    
    def get_system_metrics(self):
        """Get real system performance metrics"""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage(str(self.workspace)).percent,
                "process_count": len(psutil.pids())
            }
        except ImportError:
            return {"error": "psutil not installed"}
    
    def monitor_realtime(self):
        """Monitor all real activity in real-time"""
        print("=" * 60)
        print("Super Agent System - Real Activity Monitor")
        print("=" * 60)
        print("Monitoring actual agent work - NO simulations")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"=== Real Activity Monitor === {timestamp}")
                
                # System metrics
                metrics = self.get_system_metrics()
                print(f"\nSystem Metrics:")
                for key, value in metrics.items():
                    print(f"  {key}: {value}")
                
                # Log activity
                log_activity = self.check_agent_logs()
                print(f"\nRecent Log Activity ({len(log_activity)} active):")
                for activity in log_activity[:5]:
                    print(f"  - {activity['agent']}: {activity['file']} ({activity['size']} bytes)")
                
                # Communication queue
                messages = self.check_communication_queue()
                print(f"\nCommunication Queue:")
                print(f"  Incoming: {len(messages['incoming'])}")
                print(f"  Processing: {len(messages['processing'])}")
                print(f"  Completed: {len(messages['completed'])}")
                
                if messages['incoming']:
                    print("  Recent messages:")
                    for msg in messages['incoming'][:3]:
                        print(f"    - {msg['from']} -> {msg['to']}")
                
                # Project activity
                projects = self.check_project_activity()
                if projects:
                    print(f"\nActive Projects:")
                    for project in projects:
                        print(f"  - {project['name']}: {project['recent_activity']} recent changes")
                
                print("\n" + "=" * 60)
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    monitor = RealActivityMonitor()
    monitor.monitor_realtime()