#!/usr/bin/env python3
"""
Context Monitor for Super Agent System
Monitors agent performance and prevents crashes
"""

import os
import json
import psutil
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import threading
import queue

class ContextMonitor:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.claude_dir = self.workspace_root / ".claude"
        self.cache_dir = self.claude_dir / "cache"
        self.logs_dir = self.claude_dir / "logs"
        self.metrics = {}
        self.alerts = queue.Queue()
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def check_system_resources(self) -> Dict:
        """Check current system resource usage"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available_gb": psutil.virtual_memory().available / (1024**3),
                "total_gb": psutil.virtual_memory().total / (1024**3)
            },
            "disk": {
                "percent": psutil.disk_usage(str(self.workspace_root)).percent,
                "free_gb": psutil.disk_usage(str(self.workspace_root)).free / (1024**3)
            }
        }
    
    def check_agent_instances(self) -> List[Dict]:
        """Detect running agent instances"""
        instances = []
        lock_files = list(self.cache_dir.glob("*.lock"))
        
        for lock_file in lock_files:
            try:
                lock_data = json.loads(lock_file.read_text())
                # Check if process is still running
                if psutil.pid_exists(lock_data.get("pid", 0)):
                    instances.append({
                        "agent": lock_data.get("agent", "unknown"),
                        "pid": lock_data.get("pid"),
                        "started": lock_data.get("started"),
                        "lock_file": str(lock_file)
                    })
                else:
                    # Clean up stale lock
                    lock_file.unlink()
            except:
                pass
        
        return instances
    
    def check_context_size(self) -> Dict:
        """Monitor context file sizes"""
        context_sizes = {}
        total_size = 0
        
        for claude_file in self.workspace_root.rglob("CLAUDE.md"):
            size = claude_file.stat().st_size
            total_size += size
            
            if size > 50000:  # Files larger than 50KB
                context_sizes[str(claude_file.relative_to(self.workspace_root))] = {
                    "size_kb": size / 1024,
                    "warning": "Large context file"
                }
        
        return {
            "total_size_mb": total_size / (1024**2),
            "large_files": context_sizes,
            "file_count": len(list(self.workspace_root.rglob("CLAUDE.md")))
        }
    
    def create_instance_lock(self, agent_name: str, instance_id: str) -> Path:
        """Create a lock file for an agent instance"""
        lock_file = self.cache_dir / f"{agent_name}-{instance_id}.lock"
        
        lock_data = {
            "agent": agent_name,
            "instance_id": instance_id,
            "pid": os.getpid(),
            "started": datetime.now().isoformat(),
            "workspace": str(self.workspace_root)
        }
        
        lock_file.write_text(json.dumps(lock_data, indent=2))
        return lock_file
    
    def release_instance_lock(self, lock_file: Path):
        """Release an instance lock"""
        if lock_file.exists():
            lock_file.unlink()
    
    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        return {
            "system_resources": self.check_system_resources(),
            "active_instances": self.check_agent_instances(),
            "context_sizes": self.check_context_size(),
            "recommendations": self._get_recommendations()
        }
    
    def _get_recommendations(self) -> List[str]:
        """Generate recommendations based on current state"""
        recommendations = []
        resources = self.check_system_resources()
        
        if resources["memory"]["percent"] > 80:
            recommendations.append("High memory usage detected. Consider closing unused applications.")
        
        if resources["cpu_percent"] > 80:
            recommendations.append("High CPU usage. Consider reducing concurrent agent instances.")
        
        instances = self.check_agent_instances()
        if len(instances) > 3:
            recommendations.append(f"Multiple agent instances detected ({len(instances)}). This may cause conflicts.")
        
        context = self.check_context_size()
        if context["total_size_mb"] > 10:
            recommendations.append("Large context size. Consider splitting contexts or archiving old data.")
        
        return recommendations
    
    def monitor_realtime(self, duration_seconds: int = 60):
        """Monitor system in real-time"""
        print(f"Monitoring for {duration_seconds} seconds...")
        print("Press Ctrl+C to stop\n")
        
        start_time = time.time()
        try:
            while time.time() - start_time < duration_seconds:
                resources = self.check_system_resources()
                
                # Clear screen (Windows)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("=== Claude Context Monitor ===")
                print(f"Time: {resources['timestamp']}")
                print(f"\nCPU: {resources['cpu_percent']}%")
                print(f"Memory: {resources['memory']['percent']}% "
                      f"({resources['memory']['available_gb']:.1f} GB available)")
                print(f"Disk: {resources['disk']['percent']}% used "
                      f"({resources['disk']['free_gb']:.1f} GB free)")
                
                instances = self.check_agent_instances()
                print(f"\nActive Instances: {len(instances)}")
                for inst in instances:
                    print(f"  - {inst['agent']} (PID: {inst['pid']})")
                
                recommendations = self._get_recommendations()
                if recommendations:
                    print("\nRecommendations:")
                    for rec in recommendations:
                        print(f"  ⚠ {rec}")
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    
    def optimize_cache(self) -> Dict:
        """Clean up and optimize cache"""
        results = {
            "cleaned_files": 0,
            "space_freed_mb": 0,
            "errors": []
        }
        
        # Clean old cache files (older than 7 days)
        cutoff_time = time.time() - (7 * 24 * 60 * 60)
        
        for cache_file in self.cache_dir.rglob("*"):
            if cache_file.is_file():
                try:
                    if cache_file.stat().st_mtime < cutoff_time:
                        size = cache_file.stat().st_size
                        cache_file.unlink()
                        results["cleaned_files"] += 1
                        results["space_freed_mb"] += size / (1024**2)
                except Exception as e:
                    results["errors"].append(str(e))
        
        # Clean stale locks
        for lock_file in self.cache_dir.glob("*.lock"):
            try:
                lock_data = json.loads(lock_file.read_text())
                if not psutil.pid_exists(lock_data.get("pid", 0)):
                    lock_file.unlink()
                    results["cleaned_files"] += 1
            except:
                pass
        
        return results


class ContextCache:
    """Intelligent context caching to prevent repeated loading"""
    
    def __init__(self, cache_dir: Path, max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.cache_index = self._load_index()
        
    def _load_index(self) -> Dict:
        """Load cache index"""
        index_file = self.cache_dir / "index.json"
        if index_file.exists():
            return json.loads(index_file.read_text())
        return {"entries": {}, "total_size": 0}
    
    def _save_index(self):
        """Save cache index"""
        index_file = self.cache_dir / "index.json"
        index_file.write_text(json.dumps(self.cache_index, indent=2))
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached context"""
        if key in self.cache_index["entries"]:
            entry = self.cache_index["entries"][key]
            cache_file = self.cache_dir / entry["file"]
            
            if cache_file.exists():
                # Check if source file has been modified
                source_file = Path(entry["source"])
                if source_file.exists():
                    if source_file.stat().st_mtime > entry["cached_time"]:
                        # Source is newer, invalidate cache
                        self.invalidate(key)
                        return None
                
                # Return cached content
                return json.loads(cache_file.read_text())
        
        return None
    
    def set(self, key: str, content: Dict, source_path: str):
        """Cache context content"""
        # Check cache size limit
        if self.cache_index["total_size"] > self.max_size_mb * 1024 * 1024:
            self._evict_oldest()
        
        # Create cache entry
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps(content, indent=2))
        
        # Update index
        self.cache_index["entries"][key] = {
            "file": cache_file.name,
            "source": source_path,
            "cached_time": time.time(),
            "size": cache_file.stat().st_size
        }
        
        self.cache_index["total_size"] = sum(
            e["size"] for e in self.cache_index["entries"].values()
        )
        
        self._save_index()
    
    def invalidate(self, key: str):
        """Invalidate cache entry"""
        if key in self.cache_index["entries"]:
            entry = self.cache_index["entries"][key]
            cache_file = self.cache_dir / entry["file"]
            
            if cache_file.exists():
                cache_file.unlink()
            
            del self.cache_index["entries"][key]
            self._save_index()
    
    def _evict_oldest(self):
        """Remove oldest cache entries"""
        # Sort by cached time
        sorted_entries = sorted(
            self.cache_index["entries"].items(),
            key=lambda x: x[1]["cached_time"]
        )
        
        # Remove oldest 25%
        to_remove = len(sorted_entries) // 4
        for key, entry in sorted_entries[:to_remove]:
            self.invalidate(key)


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Context Monitor")
    parser.add_argument("command", choices=["status", "monitor", "clean", "lock", "unlock"])
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument("--agent", help="Agent name for lock/unlock")
    parser.add_argument("--instance", help="Instance ID for lock/unlock")
    parser.add_argument("--duration", type=int, default=60, help="Monitor duration in seconds")
    
    args = parser.parse_args()
    
    monitor = ContextMonitor(args.workspace)
    
    if args.command == "status":
        report = monitor.get_performance_report()
        print(json.dumps(report, indent=2))
    
    elif args.command == "monitor":
        monitor.monitor_realtime(args.duration)
    
    elif args.command == "clean":
        results = monitor.optimize_cache()
        print(f"Cleaned {results['cleaned_files']} files")
        print(f"Freed {results['space_freed_mb']:.2f} MB")
        if results['errors']:
            print(f"Errors: {results['errors']}")
    
    elif args.command == "lock" and args.agent and args.instance:
        lock_file = monitor.create_instance_lock(args.agent, args.instance)
        print(f"Created lock: {lock_file}")
    
    elif args.command == "unlock" and args.agent and args.instance:
        lock_file = monitor.cache_dir / f"{args.agent}-{args.instance}.lock"
        monitor.release_instance_lock(lock_file)
        print(f"Released lock: {lock_file}")