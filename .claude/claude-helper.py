#!/usr/bin/env python3
"""
Claude Helper - Main CLI tool for context management
Combines all context management functionality
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Import our modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    from enhance_context import ContextEnhancer
    from context_monitor import ContextMonitor, ContextCache
    from context_router import ContextRouter
except ImportError:
    print("Error: Could not import required modules")
    print("Make sure you're running from the .claude directory")
    sys.exit(1)

class ClaudeHelper:
    def __init__(self, workspace_root: str = None):
        if not workspace_root:
            workspace_root = Path.cwd().parent  # Assume we're in .claude dir
        
        self.workspace_root = Path(workspace_root)
        self.enhancer = ContextEnhancer(self.workspace_root)
        self.monitor = ContextMonitor(self.workspace_root)
        self.router = ContextRouter(self.workspace_root)
        
    def status(self) -> Dict:
        """Get comprehensive system status"""
        print("=== Claude Context Management Status ===\n")
        
        # System resources
        resources = self.monitor.check_system_resources()
        print(f"System Resources:")
        print(f"  CPU: {resources['cpu_percent']}%")
        print(f"  Memory: {resources['memory']['percent']}% used")
        print(f"  Disk: {resources['disk']['free_gb']:.1f} GB free")
        
        # Active instances
        instances = self.monitor.check_agent_instances()
        print(f"\nActive Instances: {len(instances)}")
        for inst in instances:
            print(f"  - {inst['agent']} (PID: {inst['pid']})")
        
        # Context info
        context = self.router.get_active_context()
        print(f"\nCurrent Context:")
        print(f"  Working Dir: {context['working_directory']}")
        print(f"  Active Contexts: {len(context['active_contexts'])}")
        for ctx in context['active_contexts']:
            print(f"    - {ctx['level']}: {Path(ctx['path']).name}")
        
        # Available agents
        agents = self.router.list_available_agents()
        print(f"\nAvailable Agents: {len(agents)}")
        
        # Validation issues
        issues = self.router.validate_context_hierarchy()
        if issues:
            print(f"\nValidation Issues: {len(issues)}")
            for issue in issues[:3]:
                print(f"  - [{issue['level']}] {issue['message']}")
        else:
            print("\nValidation: ✓ All contexts valid")
        
        # Recommendations
        recommendations = self.monitor._get_recommendations()
        if recommendations:
            print("\nRecommendations:")
            for rec in recommendations:
                print(f"  ⚠ {rec}")
    
    def init(self):
        """Initialize development environment"""
        print("Initializing Claude context management...\n")
        
        # Create directory structure
        dirs_created = 0
        for dir_name in ["contexts/private", "contexts/templates", "cache", "logs"]:
            dir_path = self.workspace_root / ".claude" / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
                dirs_created += 1
        
        print(f"✓ Created {dirs_created} directories")
        
        # Create config.local.json if needed
        local_config = self.workspace_root / ".claude" / "config.local.json"
        if not local_config.exists():
            example = self.workspace_root / ".claude" / "config.local.example.json"
            if example.exists():
                local_config.write_text(example.read_text())
                print("✓ Created config.local.json from template")
                print("  Please edit it with your settings")
        
        # Run validation
        issues = self.router.validate_context_hierarchy()
        print(f"\n✓ Validation complete: {len(issues)} issues found")
        
        print("\nInitialization complete!")
    
    def enhance(self, dry_run: bool = True):
        """Enhance all CLAUDE.md files"""
        print("Analyzing CLAUDE.md files for enhancement...\n")
        
        results = self.enhancer.batch_enhance(dry_run=dry_run)
        
        total_changes = sum(len(r.get('changes', [])) for r in results)
        
        if dry_run:
            print(f"\nDry run complete: {len(results)} files analyzed")
            print(f"Total changes that would be made: {total_changes}")
            print("\nRun with --apply to make these changes")
        else:
            print(f"\n✓ Enhanced {len(results)} files")
            print("Original files backed up with .bak extension")
    
    def clean(self):
        """Clean cache and temporary files"""
        print("Cleaning cache and temporary files...\n")
        
        results = self.monitor.optimize_cache()
        
        print(f"✓ Cleaned {results['cleaned_files']} files")
        print(f"✓ Freed {results['space_freed_mb']:.2f} MB")
        
        if results['errors']:
            print(f"\nErrors encountered: {len(results['errors'])}")
    
    def switch(self, agent_name: str):
        """Switch to agent context"""
        print(f"Switching to agent: {agent_name}\n")
        
        result = self.router.switch_context(agent_name)
        
        if "error" in result:
            print(f"✗ Error: {result['error']}")
        else:
            print(f"✓ Switched to: {result['switched_to']}")
            print(f"✓ Working dir: {result['new_working_dir']}")
            print(f"✓ Contexts loaded: {result['context_loaded']}")
    
    def doctor(self):
        """Run diagnostics and fix common issues"""
        print("Running Claude context diagnostics...\n")
        
        fixes_applied = 0
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            print("✓ Python version OK")
        else:
            print("✗ Python 3.8+ required")
        
        # Check required directories
        for dir_name in ["contexts", "cache", "logs"]:
            dir_path = self.workspace_root / ".claude" / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
                fixes_applied += 1
                print(f"✓ Created missing directory: {dir_name}")
        
        # Check .gitignore
        gitignore = self.workspace_root / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            if ".claude/config.local.json" not in content:
                print("⚠ .gitignore missing Claude entries - run 'claude-helper.py init' to fix")
        
        # Clean stale locks
        locks_cleaned = 0
        for lock_file in (self.workspace_root / ".claude" / "cache").glob("*.lock"):
            try:
                lock_data = json.loads(lock_file.read_text())
                import psutil
                if not psutil.pid_exists(lock_data.get("pid", 0)):
                    lock_file.unlink()
                    locks_cleaned += 1
            except:
                pass
        
        if locks_cleaned:
            print(f"✓ Cleaned {locks_cleaned} stale lock files")
            fixes_applied += locks_cleaned
        
        # Validate contexts
        issues = self.router.validate_context_hierarchy()
        
        print(f"\n{'✓' if not issues else '⚠'} Context validation: {len(issues)} issues")
        
        if fixes_applied:
            print(f"\n✓ Applied {fixes_applied} fixes")
        else:
            print("\n✓ No issues found!")


def main():
    parser = argparse.ArgumentParser(
        description="Claude Context Management Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-helper.py status              # Show system status
  claude-helper.py init                # Initialize environment
  claude-helper.py enhance --check     # Check what would be enhanced
  claude-helper.py enhance --apply     # Apply enhancements
  claude-helper.py clean               # Clean cache
  claude-helper.py switch orchestrator # Switch to orchestrator context
  claude-helper.py doctor              # Run diagnostics
        """
    )
    
    parser.add_argument(
        "command",
        choices=["status", "init", "enhance", "clean", "switch", "doctor"],
        help="Command to run"
    )
    
    parser.add_argument(
        "--workspace",
        default=str(Path.cwd().parent),
        help="Workspace root directory"
    )
    
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (for enhance command)"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check only, don't apply changes"
    )
    
    parser.add_argument(
        "agent",
        nargs="?",
        help="Agent name (for switch command)"
    )
    
    args = parser.parse_args()
    
    helper = ClaudeHelper(args.workspace)
    
    try:
        if args.command == "status":
            helper.status()
        elif args.command == "init":
            helper.init()
        elif args.command == "enhance":
            helper.enhance(dry_run=not args.apply)
        elif args.command == "clean":
            helper.clean()
        elif args.command == "switch":
            if not args.agent:
                print("Error: Agent name required for switch command")
                sys.exit(1)
            helper.switch(args.agent)
        elif args.command == "doctor":
            helper.doctor()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()