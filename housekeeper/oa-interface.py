#!/usr/bin/env python3
"""
OA Housekeeper Interface
Simple interface for OA to instruct the housekeeper
"""

import json
from datetime import datetime
from pathlib import Path

class OAHousekeeperInterface:
    """Simple interface for OA to give cleaning instructions"""
    
    def __init__(self):
        self.workspace_root = Path("C:/Jarvis/AI Workspace/Super Agent")
        self.instructions_file = self.workspace_root / "housekeeper" / "instructions.json"
        self.instructions_file.parent.mkdir(exist_ok=True)
        
    def instruct(self, action, **kwargs):
        """Give a cleaning instruction to the housekeeper"""
        
        instruction_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        instruction = {
            "id": instruction_id,
            "timestamp": datetime.now().isoformat(),
            "command": action,
            "params": kwargs,
            "status": "pending",
            "priority": kwargs.get('priority', 'normal')
        }
        
        # Load existing instructions
        if self.instructions_file.exists():
            with open(self.instructions_file, 'r') as f:
                instructions = json.load(f)
        else:
            instructions = []
        
        instructions.append(instruction)
        
        # Save back to file
        with open(self.instructions_file, 'w') as f:
            json.dump(instructions, f, indent=2)
        
        print(f"Instruction queued: {action} (ID: {instruction_id})")
        return instruction_id
    
    # Convenience methods for common operations
    
    def clean_folder(self, folder_path, days=7):
        """Clean files older than X days from a folder"""
        return self.instruct("cleanup_folder", path=folder_path, retention_days=days)
    
    def archive_folder(self, source, target):
        """Archive files from source to target folder"""
        return self.instruct("archive_folder", source=source, target=target)
    
    def emergency_clean(self):
        """Emergency cleanup - free up space immediately"""
        return self.instruct("emergency_cleanup", priority="high")
    
    def deep_clean(self):
        """Full system cleanup"""
        return self.instruct("deep_clean")
    
    def compress_logs(self):
        """Compress old log files"""
        return self.instruct("compress_logs")
    
    def start_housekeeper(self):
        """Start the automated housekeeper service"""
        return self.instruct("start_service", priority="high")
    
    def status(self):
        """Get status of recent instructions"""
        if not self.instructions_file.exists():
            print("No instructions found")
            return []
        
        with open(self.instructions_file, 'r') as f:
            instructions = json.load(f)
        
        print("Recent Housekeeper Instructions:")
        print("=" * 50)
        
        for inst in instructions[-5:]:  # Show last 5
            status_icon = "[DONE]" if inst['status'] == 'completed' else "[WAIT]" if inst['status'] == 'pending' else "[ERR]"
            print(f"{status_icon} {inst['timestamp'][:16]} | {inst['command']} | {inst['status']}")
            
            if inst['status'] == 'completed' and 'cleaned_files' in inst:
                print(f"   --> Cleaned {inst['cleaned_files'].get('cleaned_count', 0)} files")
            elif inst['status'] == 'error':
                print(f"   --> Error: {inst.get('error', 'Unknown error')}")
        
        return instructions


# Quick CLI interface for OA
def main():
    """Command line interface for OA"""
    import sys
    
    oa = OAHousekeeperInterface()
    
    if len(sys.argv) == 1:
        print("OA Housekeeper Interface")
        print("Usage:")
        print("  python oa-interface.py status")
        print("  python oa-interface.py clean <folder> [days]")
        print("  python oa-interface.py archive <source> <target>")
        print("  python oa-interface.py emergency")
        print("  python oa-interface.py deep")
        print("  python oa-interface.py start")
        print()
        print("Examples:")
        print("  python oa-interface.py clean 'context-inbox/processed' 7")
        print("  python oa-interface.py archive 'suggestions/incoming' 'suggestions/processed'")
        print("  python oa-interface.py emergency  # Free up space now")
        print("  python oa-interface.py start      # Start housekeeper service")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        oa.status()
        
    elif command == "clean":
        if len(sys.argv) < 3:
            print("ERROR: Usage: clean <folder> [days]")
            return
        folder = sys.argv[2]
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        oa.clean_folder(folder, days)
        
    elif command == "archive":
        if len(sys.argv) < 4:
            print("ERROR: Usage: archive <source> <target>")
            return
        source = sys.argv[2]
        target = sys.argv[3]
        oa.archive_folder(source, target)
        
    elif command == "emergency":
        oa.emergency_clean()
        print("Emergency cleanup requested")
        
    elif command == "deep":
        oa.deep_clean()
        print("Deep cleaning requested")
        
    elif command == "start":
        oa.start_housekeeper()
        print("Housekeeper service start requested")
        
    else:
        print(f"ERROR: Unknown command: {command}")


if __name__ == "__main__":
    main()