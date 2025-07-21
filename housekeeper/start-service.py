#!/usr/bin/env python3
"""
Start Housekeeper Service - Python version
For when OA needs to start the service programmatically
"""

import subprocess
import sys
import os
from pathlib import Path

def start_housekeeper():
    """Start the housekeeper service"""
    
    print("Starting Housekeeper Service...")
    
    # Get current directory
    current_dir = Path(__file__).parent
    
    try:
        # Start the housekeeper in a new process
        cmd = [sys.executable, "auto-housekeeper.py", "start"]
        
        # Start the process detached (so it continues running)
        if os.name == 'nt':  # Windows
            # Use CREATE_NEW_PROCESS_GROUP to detach
            process = subprocess.Popen(
                cmd,
                cwd=current_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:  # Unix/Linux
            process = subprocess.Popen(
                cmd,
                cwd=current_dir,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        print(f"✅ Housekeeper service started (PID: {process.pid})")
        print("   - Automatic cleanup every 6 hours")
        print("   - Instruction checking every 5 minutes")
        print("   - Service running in background")
        
        return {
            "status": "started",
            "pid": process.pid,
            "message": "Housekeeper service is now running in the background"
        }
        
    except Exception as e:
        print(f"❌ Error starting housekeeper: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = start_housekeeper()
    if "error" in result:
        sys.exit(1)