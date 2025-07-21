#!/usr/bin/env python3
"""
Housekeeper Schedule Monitor
Ensures the housekeeper agent maintains its schedule and reports status
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import psutil

class HousekeeperScheduleMonitor:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.housekeeper_path = self.base_path / "housekeeper"
        self.config_file = self.housekeeper_path / "config.json"
        self.log_file = self.housekeeper_path / "cleanup.log"
        self.heartbeat_file = self.base_path / "shared" / "heartbeats" / "agent-housekeeper-001.heartbeat"
        
    def load_config(self):
        """Load housekeeper configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get_housekeeper_status(self):
        """Get current housekeeper agent status"""
        status = {
            "agent_running": False,
            "heartbeat_active": False,
            "last_cleanup": None,
            "next_cleanup_due": None,
            "pid": None
        }
        
        # Check heartbeat file
        if self.heartbeat_file.exists():
            try:
                with open(self.heartbeat_file, 'r') as f:
                    heartbeat = json.load(f)
                    status["heartbeat_active"] = True
                    status["pid"] = heartbeat.get("pid")
                    
                    # Check if process is actually running
                    if status["pid"]:
                        try:
                            proc = psutil.Process(status["pid"])
                            if proc.is_running():
                                status["agent_running"] = True
                        except psutil.NoSuchProcess:
                            status["agent_running"] = False
                            
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Check last cleanup from log
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if "cleanup completed" in line.lower():
                            timestamp_str = line.split(' - ')[0]
                            try:
                                last_cleanup = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                status["last_cleanup"] = last_cleanup.isoformat()
                                
                                # Calculate next cleanup (every 6 hours per config)
                                config = self.load_config()
                                interval_hours = config.get("auto_cleanup_interval_hours", 6)
                                next_cleanup = last_cleanup + timedelta(hours=interval_hours)
                                status["next_cleanup_due"] = next_cleanup.isoformat()
                                break
                            except ValueError:
                                continue
            except FileNotFoundError:
                pass
                
        return status
    
    def check_schedule_compliance(self):
        """Check if housekeeper is maintaining its schedule"""
        status = self.get_housekeeper_status()
        config = self.load_config()
        
        compliance = {
            "compliant": True,
            "issues": [],
            "status": status,
            "config": config
        }
        
        # Check if agent is running
        if not status["agent_running"]:
            compliance["compliant"] = False
            compliance["issues"].append("Housekeeper agent is not running")
        
        # Check if heartbeat is active
        if not status["heartbeat_active"]:
            compliance["compliant"] = False
            compliance["issues"].append("Housekeeper heartbeat is not active")
        
        # Check if cleanup schedule is being maintained
        if status["last_cleanup"]:
            last_cleanup = datetime.fromisoformat(status["last_cleanup"])
            time_since_cleanup = datetime.now() - last_cleanup
            interval_hours = config.get("auto_cleanup_interval_hours", 6)
            
            if time_since_cleanup > timedelta(hours=interval_hours + 1):  # 1 hour grace period
                compliance["compliant"] = False
                compliance["issues"].append(f"Last cleanup was {time_since_cleanup} ago, exceeds {interval_hours}h schedule")
        else:
            compliance["issues"].append("No cleanup activity found in logs")
        
        return compliance
    
    def restart_housekeeper_if_needed(self):
        """Restart housekeeper if it's not running properly"""
        status = self.get_housekeeper_status()
        
        if not status["agent_running"]:
            print("Housekeeper agent not running, attempting restart...")
            try:
                # Start housekeeper using agent starter
                agent_starter_path = self.base_path / "shared" / "tools" / "agent_starter.py"
                if agent_starter_path.exists():
                    os.system(f'python "{agent_starter_path}" housekeeper')
                    time.sleep(5)  # Give it time to start
                    
                    # Verify restart
                    new_status = self.get_housekeeper_status()
                    if new_status["agent_running"]:
                        print("[SUCCESS] Housekeeper agent restarted successfully")
                        return True
                    else:
                        print("[ERROR] Failed to restart housekeeper agent")
                        return False
                else:
                    print("[ERROR] Agent starter not found")
                    return False
            except Exception as e:
                print(f"[ERROR] Exception during restart: {e}")
                return False
        
        return True
    
    def generate_report(self):
        """Generate comprehensive status report"""
        compliance = self.check_schedule_compliance()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "compliance_check": compliance,
            "recommendations": []
        }
        
        if not compliance["compliant"]:
            report["recommendations"].append("Restart housekeeper agent immediately")
            
        if compliance["status"]["last_cleanup"]:
            last_cleanup = datetime.fromisoformat(compliance["status"]["last_cleanup"])
            hours_since = (datetime.now() - last_cleanup).total_seconds() / 3600
            if hours_since > 12:
                report["recommendations"].append("Consider reducing cleanup interval")
        
        return report

def main():
    """Main monitoring function"""
    monitor = HousekeeperScheduleMonitor()
    
    print("=== Housekeeper Schedule Monitor ===")
    
    # Check current status
    status = monitor.get_housekeeper_status()
    print(f"Agent Running: {status['agent_running']}")
    print(f"Heartbeat Active: {status['heartbeat_active']}")
    print(f"Process ID: {status.get('pid', 'N/A')}")
    print(f"Last Cleanup: {status.get('last_cleanup', 'Never')}")
    print(f"Next Cleanup Due: {status.get('next_cleanup_due', 'Unknown')}")
    
    # Check compliance
    compliance = monitor.check_schedule_compliance()
    print(f"\nSchedule Compliance: {'[COMPLIANT]' if compliance['compliant'] else '[NON-COMPLIANT]'}")
    
    if compliance["issues"]:
        print("Issues found:")
        for issue in compliance["issues"]:
            print(f"  - {issue}")
    
    # Auto-restart if needed
    if not compliance["compliant"]:
        print("\nAttempting automatic remediation...")
        if monitor.restart_housekeeper_if_needed():
            print("Housekeeper has been restarted successfully")
        else:
            print("Failed to restart housekeeper - manual intervention required")
    
    # Generate report
    report = monitor.generate_report()
    report_file = monitor.housekeeper_path / f"schedule_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    main()