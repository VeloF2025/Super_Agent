#!/usr/bin/env python3
"""
Context Manager for Super Agent System
Handles separation of public/private configurations and context loading
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import shutil
from datetime import datetime

class ContextManager:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.public_suffix = "CLAUDE.md"
        self.private_suffix = ".claude-private.md"
        self.dev_suffix = ".claude-dev.md"
        
    def separate_existing_claude_md(self, file_path: Path) -> Dict[str, str]:
        """
        Separates an existing CLAUDE.md into public and private components
        """
        if not file_path.exists():
            return {"error": f"File {file_path} not found"}
        
        content = file_path.read_text()
        
        # Patterns that indicate private information
        private_patterns = [
            r'Agent ID.*?:.*?-\d{3}',
            r'Working Directory:.*?C:\\',
            r'Current.*?:.*?(?=\n)',
            r'Performance.*?:.*?\d+',
            r'API.*?:.*?(?=\n)',
            r'Personal.*?:.*?(?=\n)',
            r'Local.*?:.*?(?=\n)',
        ]
        
        # Extract private content
        private_content = ["# Private Configuration\n\n"]
        public_content = content
        
        for pattern in private_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                private_content.append(match + "\n")
                public_content = public_content.replace(match, "[See private config]")
        
        # Extract metrics section if present
        metrics_match = re.search(
            r'## Performance Metrics.*?(?=##|\Z)', 
            content, 
            re.DOTALL
        )
        if metrics_match:
            private_content.append("\n" + metrics_match.group())
            public_content = public_content.replace(
                metrics_match.group(), 
                "## Performance Metrics\n[See private config]\n"
            )
        
        return {
            "public": public_content,
            "private": "\n".join(private_content) if len(private_content) > 1 else ""
        }
    
    def create_gitignore(self):
        """Creates or updates .gitignore with privacy patterns"""
        gitignore_path = self.workspace_root / ".gitignore"
        
        privacy_patterns = """
# Claude Private Configurations
.claude-private.md
.claude-dev.md
**/private/
**/.env
**/.env.local
**/.env.*.local

# Personal/Instance Data
**/logs/
**/metrics/
**/temp/
**/recycle-bin/
**/cache/
**/.cache/

# Instance-specific IDs
agent-*-[0-9][0-9][0-9]/
*-personal/
*-dev/

# Local configurations
*.local.json
*.local.yaml
config.local.*

# Development artifacts
**/agent-workspace/
**/node_modules/
**/__pycache__/
*.pyc

# IDE
.vscode/
.idea/
*.swp
*.swo
"""
        
        if gitignore_path.exists():
            existing = gitignore_path.read_text()
            if "# Claude Private Configurations" not in existing:
                with gitignore_path.open('a') as f:
                    f.write("\n" + privacy_patterns)
                return "Updated .gitignore with privacy patterns"
        else:
            gitignore_path.write_text(privacy_patterns.strip())
            return "Created .gitignore with privacy patterns"
    
    def validate_privacy(self, check_all: bool = False) -> List[Dict]:
        """
        Validates that no private information is in public files
        """
        issues = []
        
        # Patterns that might indicate private info
        private_indicators = [
            (r'C:\\[^\s]+', "Absolute Windows path"),
            (r'/home/[^\s]+', "Absolute Unix home path"),
            (r'sk-[a-zA-Z0-9]+', "API key pattern"),
            (r'agent-\w+-\d{3}', "Personal agent ID"),
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "IP address"),
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "Email address"),
        ]
        
        # Files to check
        if check_all:
            files_to_check = list(self.workspace_root.rglob("*.md"))
        else:
            files_to_check = list(self.workspace_root.rglob("CLAUDE.md"))
        
        for file_path in files_to_check:
            # Skip private files
            if any(private in str(file_path) for private in ['.claude-private', 'private/', '.git/']):
                continue
                
            try:
                content = file_path.read_text()
                
                for pattern, description in private_indicators:
                    matches = re.findall(pattern, content)
                    if matches:
                        issues.append({
                            "file": str(file_path.relative_to(self.workspace_root)),
                            "issue": description,
                            "examples": matches[:3]  # First 3 examples
                        })
            except Exception as e:
                issues.append({
                    "file": str(file_path),
                    "issue": "Error reading file",
                    "examples": [str(e)]
                })
        
        return issues
    
    def init_dev_environment(self, agent_path: Optional[Path] = None):
        """
        Initializes development environment with proper separation
        """
        if agent_path:
            agents = [agent_path]
        else:
            agents = [d for d in (self.workspace_root / "agents").iterdir() if d.is_dir()]
        
        results = []
        
        for agent_dir in agents:
            # Create private config template
            private_config = agent_dir / self.private_suffix
            if not private_config.exists():
                template = f"""# Private Configuration for {agent_dir.name}

## Instance Details
- **Agent ID**: {agent_dir.name}-001-dev
- **Working Directory**: {agent_dir}
- **Environment**: development

## Local Settings
- **Log Level**: debug
- **Cache Directory**: ./cache/
- **Temp Directory**: ./temp/

## Active Development
- **Current Branch**: main
- **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
                private_config.write_text(template)
                results.append(f"Created {private_config}")
            
            # Create dev notes template
            dev_config = agent_dir / self.dev_suffix
            if not dev_config.exists():
                dev_template = f"""# Development Notes for {agent_dir.name}

## TODO
- [ ] 

## Current Issues
- 

## Test Commands
```bash
# Add your test commands here
```

## Local Dependencies
- 
"""
                dev_config.write_text(dev_template)
                results.append(f"Created {dev_config}")
        
        return results

    def load_context_hierarchy(self, current_path: Path) -> List[Dict]:
        """
        Loads all relevant contexts in hierarchy order
        """
        contexts = []
        
        # Load root context
        root_claude = self.workspace_root.parent / "CLAUDE.md"
        if root_claude.exists():
            contexts.append({
                "level": "root",
                "path": str(root_claude),
                "content": root_claude.read_text()[:500] + "..."  # Preview
            })
        
        # Load workspace context
        workspace_claude = self.workspace_root / "CLAUDE.md"
        if workspace_claude.exists():
            contexts.append({
                "level": "workspace", 
                "path": str(workspace_claude),
                "content": workspace_claude.read_text()[:500] + "..."
            })
        
        # Load agent context if in agent directory
        if "agents" in current_path.parts:
            agent_claude = current_path / "CLAUDE.md"
            if agent_claude.exists():
                contexts.append({
                    "level": "agent",
                    "path": str(agent_claude),
                    "content": agent_claude.read_text()[:500] + "..."
                })
                
            # Load private context if exists
            private_claude = current_path / self.private_suffix
            if private_claude.exists():
                contexts.append({
                    "level": "private",
                    "path": str(private_claude),
                    "content": "[Private content not shown]"
                })
        
        return contexts


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Super Agent Context Manager")
    parser.add_argument("command", choices=["separate", "validate", "init", "gitignore", "hierarchy"])
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--file", help="Specific file to process")
    parser.add_argument("--all", action="store_true", help="Check all files, not just CLAUDE.md")
    
    args = parser.parse_args()
    
    manager = ContextManager(args.workspace)
    
    if args.command == "separate" and args.file:
        result = manager.separate_existing_claude_md(Path(args.file))
        print(json.dumps(result, indent=2))
        
    elif args.command == "validate":
        issues = manager.validate_privacy(args.all)
        if issues:
            print(f"Found {len(issues)} privacy issues:")
            for issue in issues:
                print(f"\n{issue['file']}: {issue['issue']}")
                print(f"  Examples: {issue['examples']}")
        else:
            print("No privacy issues found!")
            
    elif args.command == "init":
        results = manager.init_dev_environment()
        for result in results:
            print(result)
            
    elif args.command == "gitignore":
        result = manager.create_gitignore()
        print(result)
        
    elif args.command == "hierarchy":
        contexts = manager.load_context_hierarchy(Path.cwd())
        print("Context Hierarchy:")
        for ctx in contexts:
            print(f"\n[{ctx['level'].upper()}] {ctx['path']}")
            print(ctx['content'])