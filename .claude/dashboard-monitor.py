#!/usr/bin/env python3
"""
Dashboard Monitor - Automatic restart when backend crashes
Keeps the dashboard healthy and running 24/7
"""

import time
import subprocess
import requests
import os
import signal
import json
from pathlib import Path
from datetime import datetime
import psutil

class DashboardMonitor:
    def __init__(self):
        self.workspace = Path(r"C:\Jarvis\AI Workspace\Super Agent")
        self.dashboard_dir = self.workspace / "agent-dashboard"
        self.log_file = self.workspace / ".claude" / "logs" / "dashboard-monitor.log"
        self.config_file = self.workspace / ".claude" / "monitor-config.json"
        
        # Monitoring settings
        self.check_interval = 30  # seconds
        self.health_url = "http://localhost:3001/health"
        self.api_url = "http://localhost:3001/api/dashboard"
        self.max_restart_attempts = 5
        self.restart_cooldown = 300  # 5 minutes
        
        # State tracking
        self.restart_count = 0
        self.last_restart_time = 0
        self.dashboard_process = None
        self.consecutive_failures = 0
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.load_config()
        
    def load_config(self):
        """Load monitoring configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.check_interval = config.get('check_interval', 30)
                    self.max_restart_attempts = config.get('max_restart_attempts', 5)
                    self.restart_cooldown = config.get('restart_cooldown', 300)
            except:
                self.log("Warning: Could not load config, using defaults")
    
    def save_config(self):
        """Save current configuration"""
        config = {
            'check_interval': self.check_interval,
            'max_restart_attempts': self.max_restart_attempts,
            'restart_cooldown': self.restart_cooldown,
            'last_restart_time': self.last_restart_time,
            'restart_count': self.restart_count
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except:
            pass
    
    def check_health(self):
        """Check if dashboard is responding"""
        try:
            # First check health endpoint
            response = requests.get(self.health_url, timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') == 'healthy':
                    return True, f"Healthy (uptime: {health_data.get('uptime', 0):.1f}s)"
            
            return False, f"Health check failed: {response.status_code}"
            
        except requests.exceptions.ConnectionError:
            return False, "Connection refused - server not running"
        except requests.exceptions.Timeout:
            return False, "Health check timeout"
        except Exception as e:
            return False, f"Health check error: {str(e)}"
    
    def check_api_functionality(self):
        """Check if main API is working"""
        try:
            response = requests.get(self.api_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'agents' in data:
                    return True, f"API working (agents: {len(data.get('agents', []))})"
            
            return False, f"API check failed: {response.status_code}"
            
        except requests.exceptions.ConnectionError:
            return False, "API connection refused"
        except requests.exceptions.Timeout:
            return False, "API timeout"
        except json.JSONDecodeError:
            return False, "Invalid JSON response"
        except Exception as e:
            return False, f"API error: {str(e)}"
    
    def find_dashboard_process(self):
        """Find running dashboard process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('server/index.js' in arg or 'server\\index.js' in arg for arg in cmdline):
                        return proc.info['pid']
                except:
                    pass
        except:
            pass
        return None
    
    def kill_dashboard_process(self):
        """Kill existing dashboard process"""
        pid = self.find_dashboard_process()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(3)  # Give it time to shut down gracefully
                
                # Force kill if still running
                if psutil.pid_exists(pid):
                    os.kill(pid, signal.SIGKILL)
                    
                self.log(f"Killed dashboard process {pid}")
                return True
            except:
                self.log(f"Failed to kill process {pid}")
                return False
        return True
    
    def start_dashboard(self):
        """Start the dashboard server"""
        try:
            # Kill any existing process first
            self.kill_dashboard_process()
            
            # Kill any process on port 3001
            self.kill_port_process(3001)
            
            # Wait a moment
            time.sleep(2)
            
            # Start new process
            self.log("Starting dashboard server...")
            
            # Use the robust server if available
            robust_server = self.dashboard_dir / "server" / "index-robust.js"
            server_script = str(robust_server) if robust_server.exists() else "server/index.js"
            
            self.dashboard_process = subprocess.Popen(
                ["node", server_script],
                cwd=str(self.dashboard_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Wait for startup
            time.sleep(5)
            
            # Verify it's running
            is_healthy, status = self.check_health()
            if is_healthy:
                self.log(f"Dashboard started successfully: {status}")
                self.consecutive_failures = 0
                return True
            else:
                self.log(f"Dashboard start failed: {status}")
                return False
                
        except Exception as e:
            self.log(f"Error starting dashboard: {e}")
            return False
    
    def kill_port_process(self, port):
        """Kill process using specific port"""
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    ['netstat', '-ano'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid], 
                                             capture_output=True, timeout=10)
                                self.log(f"Killed process {pid} on port {port}")
                            except:
                                pass
        except:
            pass
    
    def should_restart(self):
        """Determine if we should attempt a restart"""
        current_time = time.time()
        
        # Check if we're in cooldown period
        if current_time - self.last_restart_time < self.restart_cooldown:
            return False, f"In cooldown (remaining: {int(self.restart_cooldown - (current_time - self.last_restart_time))}s)"
        
        # Check if we've exceeded max restart attempts
        if self.restart_count >= self.max_restart_attempts:
            return False, f"Max restart attempts reached ({self.max_restart_attempts})"
        
        return True, "Ready to restart"
    
    def restart_dashboard(self):
        """Restart the dashboard with safety checks"""
        should_restart, reason = self.should_restart()
        
        if not should_restart:
            self.log(f"Restart skipped: {reason}")
            return False
        
        self.log(f"Attempting dashboard restart (attempt {self.restart_count + 1}/{self.max_restart_attempts})")
        
        if self.start_dashboard():
            self.restart_count += 1
            self.last_restart_time = time.time()
            self.save_config()
            return True
        else:
            self.restart_count += 1
            self.last_restart_time = time.time()
            self.save_config()
            return False
    
    def reset_restart_counter(self):
        """Reset restart counter after successful operation"""
        if self.restart_count > 0:
            self.log("Dashboard stable - resetting restart counter")
            self.restart_count = 0
            self.save_config()
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.log("Dashboard monitoring started")
        self.log(f"Check interval: {self.check_interval}s")
        self.log(f"Health URL: {self.health_url}")
        
        stable_checks = 0
        
        try:
            while True:
                # Check dashboard health
                is_healthy, health_status = self.check_health()
                
                if is_healthy:
                    # Additional API check
                    api_healthy, api_status = self.check_api_functionality()
                    
                    if api_healthy:
                        stable_checks += 1
                        
                        # Reset restart counter after 10 consecutive successful checks
                        if stable_checks >= 10:
                            self.reset_restart_counter()
                            stable_checks = 0
                        
                        self.consecutive_failures = 0
                        status_msg = f"✓ Dashboard healthy: {health_status}, {api_status}"
                        print(f"\r{datetime.now().strftime('%H:%M:%S')} {status_msg}", end='', flush=True)
                    else:
                        self.log(f"API unhealthy: {api_status}")
                        self.consecutive_failures += 1
                        stable_checks = 0
                else:
                    self.log(f"Health check failed: {health_status}")
                    self.consecutive_failures += 1
                    stable_checks = 0
                
                # Restart if multiple consecutive failures
                if self.consecutive_failures >= 3:
                    self.log(f"Dashboard unhealthy for {self.consecutive_failures} checks - attempting restart")
                    
                    if self.restart_dashboard():
                        self.log("Dashboard restart successful")
                        self.consecutive_failures = 0
                    else:
                        self.log("Dashboard restart failed")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.log("Monitor stopped by user")
        except Exception as e:
            self.log(f"Monitor error: {e}")
    
    def status_report(self):
        """Generate status report"""
        print("Dashboard Monitor Status:")
        print(f"  Workspace: {self.workspace}")
        print(f"  Check interval: {self.check_interval}s")
        print(f"  Restart count: {self.restart_count}/{self.max_restart_attempts}")
        print(f"  Last restart: {datetime.fromtimestamp(self.last_restart_time) if self.last_restart_time else 'Never'}")
        
        is_healthy, status = self.check_health()
        print(f"  Current status: {status}")
        
        pid = self.find_dashboard_process()
        print(f"  Dashboard PID: {pid if pid else 'Not found'}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Dashboard Monitor")
    parser.add_argument('command', choices=['start', 'status', 'stop', 'restart'], help='Command to run')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    monitor = DashboardMonitor()
    monitor.check_interval = args.interval
    
    if args.command == 'start':
        monitor.monitor_loop()
    elif args.command == 'status':
        monitor.status_report()
    elif args.command == 'stop':
        monitor.kill_dashboard_process()
        print("Dashboard process stopped")
    elif args.command == 'restart':
        monitor.restart_dashboard()

if __name__ == "__main__":
    main()