#!/usr/bin/env python3
"""
Jarvis Scheduler Integration
Integrates standup/shutdown with existing housekeeper and context systems
"""

import json
import subprocess
import sys
from datetime import datetime, time
from pathlib import Path
import threading
import time as time_module

class JarvisScheduler:
    def __init__(self):
        self.workspace_root = Path("C:/Jarvis/AI Workspace/Super Agent")
        self.daily_ops_dir = self.workspace_root / "daily-ops"
        self.housekeeper_dir = self.workspace_root / "housekeeper"
        self.context_inbox = self.workspace_root / "context-inbox"
        self.config_file = self.daily_ops_dir / "scheduler_config.json"
        
        # Default schedule configuration
        self.default_config = {
            "morning_standup_time": "09:00",
            "evening_shutdown_time": "18:00",
            "midday_check_time": "13:00",
            "weekend_mode": False,
            "auto_housekeeper": True,
            "notifications_enabled": True
        }
        
        self.load_config()
    
    def load_config(self):
        """Load scheduler configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Merge with defaults
                for key, value in self.default_config.items():
                    if key not in self.config:
                        self.config[key] = value
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
    
    def save_config(self):
        """Save scheduler configuration"""
        self.daily_ops_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def run_morning_standup(self):
        """Run morning standup with integrations"""
        print("🌅 Starting Integrated Morning Routine...")
        
        try:
            # 1. Start housekeeper if not running
            if self.config.get('auto_housekeeper', True):
                self.start_housekeeper()
            
            # 2. Process any pending context requests
            self.process_context_inbox()
            
            # 3. Run morning standup
            standup_script = self.daily_ops_dir / "morning-standup.py"
            result = subprocess.run([sys.executable, str(standup_script)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Morning standup completed successfully")
                if self.config.get('notifications_enabled'):
                    self.send_notification("🌅 Jarvis: Morning standup complete. Agents are ready!")
            else:
                print(f"❌ Morning standup failed: {result.stderr}")
                return False
            
            # 4. Generate morning summary
            self.generate_morning_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ Error during morning routine: {e}")
            return False
    
    def run_evening_shutdown(self):
        """Run evening shutdown with integrations"""
        print("🌆 Starting Integrated Evening Routine...")
        
        try:
            # 1. Run evening shutdown
            shutdown_script = self.daily_ops_dir / "evening-shutdown.py"
            result = subprocess.run([sys.executable, str(shutdown_script)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Evening shutdown completed successfully")
            else:
                print(f"❌ Evening shutdown failed: {result.stderr}")
                return False
            
            # 2. Run housekeeper cleanup
            self.run_housekeeper_cleanup()
            
            # 3. Process suggestion files
            self.process_suggestions()
            
            # 4. Generate evening summary
            self.generate_evening_summary()
            
            if self.config.get('notifications_enabled'):
                self.send_notification("🌆 Jarvis: Evening shutdown complete. Data preserved for tomorrow!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during evening routine: {e}")
            return False
    
    def start_housekeeper(self):
        """Start housekeeper service if not running"""
        try:
            hk_interface = self.housekeeper_dir / "oa-interface.py"
            if hk_interface.exists():
                subprocess.run([sys.executable, str(hk_interface), "start"], 
                             cwd=self.housekeeper_dir)
                print("🧹 Housekeeper service started")
            else:
                print("⚠️ Housekeeper interface not found")
        except Exception as e:
            print(f"⚠️ Error starting housekeeper: {e}")
    
    def run_housekeeper_cleanup(self):
        """Run housekeeper cleanup"""
        try:
            hk_interface = self.housekeeper_dir / "oa-interface.py"
            if hk_interface.exists():
                subprocess.run([sys.executable, str(hk_interface), "deep"], 
                             cwd=self.housekeeper_dir)
                print("🧹 Housekeeper cleanup completed")
        except Exception as e:
            print(f"⚠️ Error running housekeeper cleanup: {e}")
    
    def process_context_inbox(self):
        """Process any pending context requests"""
        try:
            if not self.context_inbox.exists():
                return
            
            # Check for new projects
            new_projects = list((self.context_inbox / "new-projects").glob("*"))
            existing_projects = list((self.context_inbox / "existing-projects").glob("*"))
            
            if new_projects or existing_projects:
                print(f"📥 Processing {len(new_projects)} new projects, {len(existing_projects)} takeovers")
                
                # Run context processor
                context_processor = self.context_inbox / "context-processor.py"
                if context_processor.exists():
                    subprocess.run([sys.executable, str(context_processor)], 
                                 cwd=self.context_inbox)
            
        except Exception as e:
            print(f"⚠️ Error processing context inbox: {e}")
    
    def process_suggestions(self):
        """Process suggestion files"""
        try:
            suggestions_incoming = self.workspace_root / "suggestions" / "incoming"
            if suggestions_incoming.exists():
                suggestion_files = list(suggestions_incoming.glob("*"))
                if suggestion_files:
                    print(f"📄 Processing {len(suggestion_files)} suggestion files")
                    
                    # Move to processed folder with timestamp
                    processed_dir = self.workspace_root / "suggestions" / "processed"
                    processed_dir.mkdir(exist_ok=True)
                    
                    for file in suggestion_files:
                        timestamp = datetime.now().strftime("%Y%m%d")
                        new_name = f"{file.stem}-{timestamp}{file.suffix}"
                        file.rename(processed_dir / new_name)
        
        except Exception as e:
            print(f"⚠️ Error processing suggestions: {e}")
    
    def generate_morning_summary(self):
        """Generate morning summary for quick review"""
        summary_file = self.workspace_root / "memory" / "standups" / f"morning_summary_{datetime.now().strftime('%Y-%m-%d')}.txt"
        
        try:
            with open(summary_file, 'w') as f:
                f.write(f"Jarvis Morning Summary - {datetime.now().strftime('%A, %B %d, %Y')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Standup completed at: {datetime.now().strftime('%H:%M:%S')}\n")
                f.write("Systems initialized and agents ready for work.\n")
                
        except Exception as e:
            print(f"⚠️ Error generating morning summary: {e}")
    
    def generate_evening_summary(self):
        """Generate evening summary for quick review"""
        summary_file = self.workspace_root / "memory" / "standups" / f"evening_summary_{datetime.now().strftime('%Y-%m-%d')}.txt"
        
        try:
            with open(summary_file, 'w') as f:
                f.write(f"Jarvis Evening Summary - {datetime.now().strftime('%A, %B %d, %Y')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Shutdown completed at: {datetime.now().strftime('%H:%M:%S')}\n")
                f.write("All data preserved and system prepared for tomorrow.\n")
                
        except Exception as e:
            print(f"⚠️ Error generating evening summary: {e}")
    
    def send_notification(self, message):
        """Send system notification (Windows)"""
        try:
            # For Windows, use a simple popup
            import subprocess
            subprocess.run([
                'powershell', '-Command', 
                f'Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show("{message}", "Jarvis")'
            ], shell=True, capture_output=True)
        except Exception:
            # Fallback: just print
            print(f"🔔 {message}")
    
    def run_midday_check(self):
        """Run midday status check"""
        print("☀️ Midday Status Check...")
        
        try:
            # Quick status check without full shutdown
            agents_parent = self.workspace_root.parent / "agents"
            if agents_parent.exists():
                active_agents = len(list(agents_parent.glob("agent-*")))
                print(f"📊 {active_agents} agent directories found")
            
            # Check housekeeper status
            hk_status = self.housekeeper_dir / "oa-interface.py"
            if hk_status.exists():
                result = subprocess.run([sys.executable, str(hk_status), "status"], 
                                      cwd=self.housekeeper_dir, capture_output=True, text=True)
                if "Recent Housekeeper Instructions" in result.stdout:
                    print("🧹 Housekeeper is responsive")
            
            # Check for any urgent issues
            queue_dir = self.workspace_root / "communication" / "queue"
            if queue_dir.exists():
                pending_messages = len(list(queue_dir.glob("*.json")))
                if pending_messages > 10:
                    print(f"⚠️ {pending_messages} pending messages in queue")
            
            print("✅ Midday check completed")
            
        except Exception as e:
            print(f"❌ Error during midday check: {e}")
    
    def parse_time(self, time_str):
        """Parse time string to time object"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except Exception:
            return time(9, 0)  # Default to 9:00 AM
    
    def schedule_daily_routines(self):
        """Schedule daily routines"""
        print("⏰ Scheduling daily routines...")
        print(f"   Morning Standup: {self.config['morning_standup_time']}")
        print(f"   Evening Shutdown: {self.config['evening_shutdown_time']}")
        print(f"   Midday Check: {self.config['midday_check_time']}")
        
        morning_time = self.parse_time(self.config['morning_standup_time'])
        evening_time = self.parse_time(self.config['evening_shutdown_time'])
        midday_time = self.parse_time(self.config['midday_check_time'])
        
        def check_schedule():
            while True:
                now = datetime.now()
                current_time = now.time()
                is_weekday = now.weekday() < 5  # Monday = 0, Sunday = 6
                
                # Skip weekends unless weekend_mode is enabled
                if not is_weekday and not self.config.get('weekend_mode', False):
                    time_module.sleep(3600)  # Check again in 1 hour
                    continue
                
                # Check if it's time for morning standup
                if (current_time.hour == morning_time.hour and 
                    current_time.minute == morning_time.minute):
                    self.run_morning_standup()
                    time_module.sleep(60)  # Prevent running multiple times
                
                # Check if it's time for evening shutdown
                elif (current_time.hour == evening_time.hour and 
                      current_time.minute == evening_time.minute):
                    self.run_evening_shutdown()
                    time_module.sleep(60)  # Prevent running multiple times
                
                # Check if it's time for midday check
                elif (current_time.hour == midday_time.hour and 
                      current_time.minute == midday_time.minute):
                    self.run_midday_check()
                    time_module.sleep(60)  # Prevent running multiple times
                
                else:
                    time_module.sleep(30)  # Check every 30 seconds
        
        # Run scheduler in background thread
        scheduler_thread = threading.Thread(target=check_schedule, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread


def main():
    """Main function for command line usage"""
    import sys
    
    scheduler = JarvisScheduler()
    
    if len(sys.argv) < 2:
        print("Jarvis Scheduler")
        print("Usage:")
        print("  python jarvis-scheduler.py morning   # Run morning standup")
        print("  python jarvis-scheduler.py evening   # Run evening shutdown")
        print("  python jarvis-scheduler.py midday    # Run midday check")
        print("  python jarvis-scheduler.py auto      # Run automatic scheduler")
        print("  python jarvis-scheduler.py config    # Show configuration")
        return
    
    command = sys.argv[1].lower()
    
    if command == "morning":
        scheduler.run_morning_standup()
    elif command == "evening":
        scheduler.run_evening_shutdown()
    elif command == "midday":
        scheduler.run_midday_check()
    elif command == "auto":
        print("🤖 Starting Jarvis automatic scheduler...")
        thread = scheduler.schedule_daily_routines()
        try:
            thread.join()  # Keep running
        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped")
    elif command == "config":
        print("Current Configuration:")
        for key, value in scheduler.config.items():
            print(f"  {key}: {value}")
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()