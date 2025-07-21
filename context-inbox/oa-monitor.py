#!/usr/bin/env python3
"""
OA Context Engineering Monitor
Watches for new project requests and processes them
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import time
import hashlib

class ContextInboxMonitor:
    def __init__(self):
        self.inbox_path = Path("C:/Jarvis/AI Workspace/Super Agent/context-inbox")
        self.new_projects = self.inbox_path / "new-projects"
        self.existing_projects = self.inbox_path / "existing-projects"
        self.processed = self.inbox_path / "processed"
        self.processing_log = self.inbox_path / "processing.log"
        
    def scan_for_new_requests(self):
        """Check for new files in monitored folders"""
        new_files = []
        
        # Check new projects
        for file in self.new_projects.iterdir():
            if file.is_file() and not file.name.startswith('.'):
                new_files.append(('new', file))
                
        # Check existing projects
        for file in self.existing_projects.iterdir():
            if file.is_file() and not file.name.startswith('.'):
                new_files.append(('existing', file))
                
        return new_files
    
    def process_new_project(self, file_path):
        """Process a new project request"""
        print(f"🚀 Processing new project: {file_path.name}")
        
        # Read file content
        content = self.read_file_safely(file_path)
        
        # Generate context
        context = {
            'request_type': 'new_project',
            'timestamp': datetime.now().isoformat(),
            'source_file': file_path.name,
            'content': content,
            'status': 'pending_review',
            'context_id': self.generate_context_id(content)
        }
        
        # Save context for OA processing
        context_file = self.processed / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-{file_path.stem}-context.json"
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2)
        
        # Move original file to processed
        shutil.move(str(file_path), str(self.processed / f"original-{file_path.name}"))
        
        self.log_processing(f"New project '{file_path.name}' processed -> {context_file.name}")
        return context_file
    
    def process_existing_project(self, file_path):
        """Process an existing project takeover request"""
        print(f"🔄 Processing takeover request: {file_path.name}")
        
        # Read file content
        content = self.read_file_safely(file_path)
        
        # Generate preliminary context
        context = {
            'request_type': 'project_takeover',
            'timestamp': datetime.now().isoformat(),
            'source_file': file_path.name,
            'content': content,
            'status': 'pending_agent_analysis',
            'context_id': self.generate_context_id(content),
            'agent_findings': {}  # Agents will populate this
        }
        
        # Save context for agent analysis
        context_file = self.processed / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-{file_path.stem}-takeover-context.json"
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2)
        
        # Move original file to processed
        shutil.move(str(file_path), str(self.processed / f"original-{file_path.name}"))
        
        self.log_processing(f"Takeover request '{file_path.name}' processed -> {context_file.name}")
        return context_file
    
    def read_file_safely(self, file_path):
        """Read file content safely, handling different encodings"""
        try:
            # Try UTF-8 first
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                return file_path.read_text(encoding='latin-1')
            except:
                return f"[Binary file or unsupported encoding: {file_path.name}]"
    
    def generate_context_id(self, content):
        """Generate unique ID for context"""
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def log_processing(self, message):
        """Log processing activities"""
        with open(self.processing_log, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    def run_monitor(self, check_interval=30):
        """Run the monitoring loop"""
        print("👁️ OA Context Monitor Started")
        print(f"📁 Watching: {self.new_projects}")
        print(f"📁 Watching: {self.existing_projects}")
        print(f"⏱️ Check interval: {check_interval} seconds\n")
        
        while True:
            try:
                new_files = self.scan_for_new_requests()
                
                if new_files:
                    print(f"\n📨 Found {len(new_files)} new requests")
                    
                    for request_type, file_path in new_files:
                        if request_type == 'new':
                            self.process_new_project(file_path)
                        else:
                            self.process_existing_project(file_path)
                            
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 Monitor stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                self.log_processing(f"ERROR: {e}")
                time.sleep(check_interval)


class ContextHousekeeper:
    """Clean up old processed files"""
    
    def __init__(self, retention_days=7):
        self.inbox_path = Path("C:/Jarvis/AI Workspace/Super Agent/context-inbox")
        self.processed = self.inbox_path / "processed"
        self.archive = self.inbox_path / "archive"
        self.retention_days = retention_days
        
    def cleanup_old_files(self):
        """Archive or delete old processed files"""
        if not self.processed.exists():
            return
            
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cleaned_count = 0
        
        for file in self.processed.iterdir():
            if file.is_file():
                # Check file age
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                
                if mtime < cutoff_date:
                    # Archive completed contexts
                    if 'context-complete' in file.name:
                        self.archive_file(file)
                    else:
                        # Delete temporary files
                        file.unlink()
                    cleaned_count += 1
                    
        if cleaned_count > 0:
            print(f"🧹 Cleaned up {cleaned_count} old files")
            
    def archive_file(self, file_path):
        """Archive important files"""
        if not self.archive.exists():
            self.archive.mkdir(parents=True)
            
        # Create year-month subfolder
        archive_folder = self.archive / datetime.now().strftime("%Y-%m")
        archive_folder.mkdir(exist_ok=True)
        
        # Move file to archive
        shutil.move(str(file_path), str(archive_folder / file_path.name))
        
    def run_cleanup(self, interval_hours=24):
        """Run periodic cleanup"""
        print(f"🧹 Housekeeper started (retention: {self.retention_days} days)")
        
        while True:
            try:
                self.cleanup_old_files()
                time.sleep(interval_hours * 3600)
            except KeyboardInterrupt:
                print("\n👋 Housekeeper stopped")
                break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        # Run housekeeper
        housekeeper = ContextHousekeeper()
        housekeeper.run_cleanup()
    else:
        # Run monitor
        monitor = ContextInboxMonitor()
        monitor.run_monitor()