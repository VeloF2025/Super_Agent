#!/usr/bin/env python3
"""
Super Agent Housekeeper - Automated Cleanup System
Runs automatically and responds to OA instructions
"""

import os
import json
import shutil
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

class SuperAgentHousekeeper:
    def __init__(self):
        self.workspace_root = Path("C:/Jarvis/AI Workspace/Super Agent")
        self.config_file = self.workspace_root / "housekeeper" / "config.json"
        self.log_file = self.workspace_root / "housekeeper" / "cleanup.log"
        self.instructions_file = self.workspace_root / "housekeeper" / "instructions.json"
        
        # Create housekeeper directory
        (self.workspace_root / "housekeeper").mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self.load_config()
        
    def load_config(self):
        """Load housekeeper configuration"""
        default_config = {
            "retention_days": 7,
            "auto_cleanup_interval_hours": 6,
            "cleanup_targets": [
                {
                    "path": "context-inbox/processed",
                    "retention_days": 7,
                    "archive_to": "context-inbox/archive"
                },
                {
                    "path": "suggestions/incoming",
                    "retention_days": 1,
                    "archive_to": "suggestions/processed"
                },
                {
                    "path": "temp",
                    "retention_days": 1,
                    "delete_after": True
                },
                {
                    "path": "logs",
                    "retention_days": 30,
                    "compress_after": 7
                }
            ],
            "watch_patterns": [
                "*.tmp",
                "*.temp",
                "*-processing.json",
                "*.log.old"
            ],
            "auto_enabled": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                
        # Save default config
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        return default_config
    
    def check_instructions(self):
        """Check for OA instructions"""
        if not self.instructions_file.exists():
            return []
            
        try:
            with open(self.instructions_file, 'r') as f:
                instructions = json.load(f)
                
            # Process unprocessed instructions
            new_instructions = [
                inst for inst in instructions 
                if inst.get('status') == 'pending'
            ]
            
            return new_instructions
            
        except Exception as e:
            self.logger.error(f"Error reading instructions: {e}")
            return []
    
    def process_instruction(self, instruction):
        """Process a single OA instruction"""
        self.logger.info(f"Processing instruction: {instruction.get('command')}")
        
        command = instruction.get('command')
        params = instruction.get('params', {})
        
        result = {"status": "completed", "timestamp": datetime.now().isoformat()}
        
        try:
            if command == "cleanup_folder":
                path = params.get('path')
                days = params.get('retention_days', self.config['retention_days'])
                result['cleaned_files'] = self.cleanup_folder(path, days)
                
            elif command == "archive_folder":
                source = params.get('source')
                target = params.get('target')
                result['archived_files'] = self.archive_folder(source, target)
                
            elif command == "deep_clean":
                result['cleanup_summary'] = self.deep_clean()
                
            elif command == "compress_logs":
                result['compressed_files'] = self.compress_old_logs()
                
            elif command == "emergency_cleanup":
                result['emergency_summary'] = self.emergency_cleanup()
                
            elif command == "start_service":
                result['service_start'] = self.start_housekeeper_service()
                
            else:
                result['status'] = 'unknown_command'
                result['error'] = f"Unknown command: {command}"
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            self.logger.error(f"Error processing instruction: {e}")
        
        # Update instruction status
        instruction.update(result)
        self.save_instruction_result(instruction)
        
        return result
    
    def save_instruction_result(self, instruction):
        """Save instruction result back to file"""
        try:
            if self.instructions_file.exists():
                with open(self.instructions_file, 'r') as f:
                    all_instructions = json.load(f)
            else:
                all_instructions = []
            
            # Update the instruction
            for i, inst in enumerate(all_instructions):
                if inst.get('id') == instruction.get('id'):
                    all_instructions[i] = instruction
                    break
            else:
                all_instructions.append(instruction)
            
            with open(self.instructions_file, 'w') as f:
                json.dump(all_instructions, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving instruction result: {e}")
    
    def cleanup_folder(self, folder_path, retention_days):
        """Clean up a specific folder"""
        full_path = self.workspace_root / folder_path
        
        if not full_path.exists():
            return {"error": f"Path {folder_path} does not exist"}
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cleaned_files = []
        
        for file_path in full_path.rglob('*'):
            if file_path.is_file():
                file_age = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_age < cutoff_date:
                    try:
                        file_path.unlink()
                        cleaned_files.append(str(file_path.relative_to(self.workspace_root)))
                    except Exception as e:
                        self.logger.error(f"Error deleting {file_path}: {e}")
        
        self.logger.info(f"Cleaned {len(cleaned_files)} files from {folder_path}")
        return {"cleaned_count": len(cleaned_files), "files": cleaned_files}
    
    def archive_folder(self, source_path, target_path):
        """Archive files from source to target"""
        source = self.workspace_root / source_path
        target = self.workspace_root / target_path
        
        if not source.exists():
            return {"error": f"Source {source_path} does not exist"}
        
        target.mkdir(parents=True, exist_ok=True)
        archived_files = []
        
        # Create dated subfolder
        date_folder = target / datetime.now().strftime("%Y-%m")
        date_folder.mkdir(exist_ok=True)
        
        for file_path in source.iterdir():
            if file_path.is_file():
                try:
                    target_file = date_folder / file_path.name
                    shutil.move(str(file_path), str(target_file))
                    archived_files.append(str(file_path.relative_to(self.workspace_root)))
                except Exception as e:
                    self.logger.error(f"Error archiving {file_path}: {e}")
        
        self.logger.info(f"Archived {len(archived_files)} files from {source_path}")
        return {"archived_count": len(archived_files), "files": archived_files}
    
    def deep_clean(self):
        """Perform comprehensive cleanup"""
        summary = {"total_cleaned": 0, "folders_processed": []}
        
        for target in self.config['cleanup_targets']:
            path = target['path']
            retention_days = target.get('retention_days', self.config['retention_days'])
            
            if target.get('delete_after'):
                result = self.cleanup_folder(path, retention_days)
            elif target.get('archive_to'):
                result = self.archive_folder(path, target['archive_to'])
            else:
                result = self.cleanup_folder(path, retention_days)
            
            if 'error' not in result:
                summary['total_cleaned'] += result.get('cleaned_count', result.get('archived_count', 0))
                summary['folders_processed'].append(path)
        
        # Clean up by patterns
        pattern_cleaned = self.cleanup_by_patterns()
        summary['pattern_cleaned'] = pattern_cleaned
        
        self.logger.info(f"Deep clean completed: {summary['total_cleaned']} files processed")
        return summary
    
    def cleanup_by_patterns(self):
        """Clean up files matching specific patterns"""
        cleaned_files = []
        
        for pattern in self.config.get('watch_patterns', []):
            for file_path in self.workspace_root.rglob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        cleaned_files.append(str(file_path.relative_to(self.workspace_root)))
                    except Exception as e:
                        self.logger.error(f"Error deleting pattern file {file_path}: {e}")
        
        return {"cleaned_count": len(cleaned_files), "files": cleaned_files}
    
    def compress_old_logs(self):
        """Compress old log files"""
        import gzip
        
        logs_path = self.workspace_root / "logs"
        if not logs_path.exists():
            return {"error": "No logs directory found"}
        
        cutoff_date = datetime.now() - timedelta(days=7)
        compressed_files = []
        
        for log_file in logs_path.rglob("*.log"):
            if log_file.is_file():
                file_age = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_age < cutoff_date and not log_file.name.endswith('.gz'):
                    try:
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        log_file.unlink()
                        compressed_files.append(str(log_file.relative_to(self.workspace_root)))
                    except Exception as e:
                        self.logger.error(f"Error compressing {log_file}: {e}")
        
        return {"compressed_count": len(compressed_files), "files": compressed_files}
    
    def emergency_cleanup(self):
        """Emergency cleanup for space issues"""
        summary = {"freed_space_mb": 0, "actions": []}
        
        # Clean temp files immediately
        temp_result = self.cleanup_folder("temp", 0)  # Delete all temp files
        if 'error' not in temp_result:
            summary['actions'].append("Cleaned all temp files")
        
        # Compress all logs
        compress_result = self.compress_old_logs()
        if 'error' not in compress_result:
            summary['actions'].append(f"Compressed {compress_result['compressed_count']} log files")
        
        # Archive old contexts
        archive_result = self.archive_folder("context-inbox/processed", "context-inbox/archive")
        if 'error' not in archive_result:
            summary['actions'].append(f"Archived {archive_result['archived_count']} context files")
        
        self.logger.info("Emergency cleanup completed")
        return summary
    
    def start_housekeeper_service(self):
        """Start the housekeeper service"""
        import subprocess
        import sys
        
        try:
            # Use the Python start service script
            start_script = self.workspace_root / "housekeeper" / "start-service.py"
            
            if not start_script.exists():
                return {"error": "start-service.py not found"}
            
            # Execute the start script
            result = subprocess.run(
                [sys.executable, str(start_script)], 
                cwd=str(start_script.parent),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("Housekeeper service started successfully")
                return {
                    "status": "started",
                    "message": "Housekeeper service has been started",
                    "output": result.stdout
                }
            else:
                return {
                    "error": f"Failed to start service: {result.stderr}",
                    "returncode": result.returncode
                }
                
        except Exception as e:
            self.logger.error(f"Error starting housekeeper service: {e}")
            return {"error": str(e)}
    
    def automated_cleanup(self):
        """Run automated cleanup routine"""
        if not self.config.get('auto_enabled', True):
            return
        
        self.logger.info("Starting automated cleanup routine")
        
        # Process any pending OA instructions first
        instructions = self.check_instructions()
        for instruction in instructions:
            self.process_instruction(instruction)
        
        # Run regular cleanup
        summary = self.deep_clean()
        
        self.logger.info(f"Automated cleanup completed: {summary}")
    
    def run_scheduler(self):
        """Run the automated scheduler"""
        interval_hours = self.config.get('auto_cleanup_interval_hours', 6)
        
        # Schedule automated cleanup
        schedule.every(interval_hours).hours.do(self.automated_cleanup)
        
        # Schedule instruction checking every 5 minutes
        schedule.every(5).minutes.do(self.check_and_process_instructions)
        
        self.logger.info(f"Housekeeper scheduler started (cleanup every {interval_hours} hours)")
        
        # Run initial cleanup
        self.automated_cleanup()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("Housekeeper scheduler stopped")
                break
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def check_and_process_instructions(self):
        """Check and process any new instructions"""
        instructions = self.check_instructions()
        for instruction in instructions:
            self.process_instruction(instruction)


class OAHousekeeperInterface:
    """Interface for OA to give instructions to housekeeper"""
    
    def __init__(self):
        self.workspace_root = Path("C:/Jarvis/AI Workspace/Super Agent")
        self.instructions_file = self.workspace_root / "housekeeper" / "instructions.json"
        
    def give_instruction(self, command, params=None, priority="normal"):
        """Give an instruction to the housekeeper"""
        instruction = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "params": params or {},
            "priority": priority,
            "status": "pending"
        }
        
        # Load existing instructions
        if self.instructions_file.exists():
            with open(self.instructions_file, 'r') as f:
                instructions = json.load(f)
        else:
            instructions = []
        
        instructions.append(instruction)
        
        # Save instructions
        with open(self.instructions_file, 'w') as f:
            json.dump(instructions, f, indent=2)
        
        return instruction['id']
    
    def cleanup_folder(self, folder_path, retention_days=7):
        """Instruct housekeeper to clean up a specific folder"""
        return self.give_instruction("cleanup_folder", {
            "path": folder_path,
            "retention_days": retention_days
        })
    
    def archive_files(self, source_path, target_path):
        """Instruct housekeeper to archive files"""
        return self.give_instruction("archive_folder", {
            "source": source_path,
            "target": target_path
        })
    
    def emergency_cleanup(self):
        """Request emergency cleanup"""
        return self.give_instruction("emergency_cleanup", {}, priority="high")
    
    def deep_clean(self):
        """Request deep cleaning"""
        return self.give_instruction("deep_clean")
    
    def get_status(self):
        """Get status of recent instructions"""
        if not self.instructions_file.exists():
            return []
        
        with open(self.instructions_file, 'r') as f:
            instructions = json.load(f)
        
        # Return last 10 instructions
        return instructions[-10:]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "start":
            # Start the automated housekeeper
            housekeeper = SuperAgentHousekeeper()
            housekeeper.run_scheduler()
            
        elif sys.argv[1] == "manual":
            # Run manual cleanup
            housekeeper = SuperAgentHousekeeper()
            result = housekeeper.deep_clean()
            print(f"Manual cleanup completed: {result}")
            
        elif sys.argv[1] == "status":
            # Show status
            interface = OAHousekeeperInterface()
            status = interface.get_status()
            print("Recent instructions:")
            for inst in status:
                print(f"  {inst['timestamp']}: {inst['command']} - {inst['status']}")
                
    else:
        print("Usage:")
        print("  python auto-housekeeper.py start    # Start automated housekeeper")
        print("  python auto-housekeeper.py manual   # Run manual cleanup")
        print("  python auto-housekeeper.py status   # Show status")