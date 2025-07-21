#!/usr/bin/env python3
"""
Context Router for Super Agent System
Manages context switching and agent communication
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

class ContextRouter:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.claude_dir = self.workspace_root / ".claude"
        self.comm_dir = self.workspace_root / "shared" / "communication"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load both public and private configs"""
        config = {}
        
        # Load public config
        public_config = self.claude_dir / "config.json"
        if public_config.exists():
            config.update(json.loads(public_config.read_text()))
        
        # Load private config (overrides public)
        private_config = self.claude_dir / "config.local.json"
        if private_config.exists():
            private_data = json.loads(private_config.read_text())
            config = self._deep_merge(config, private_data)
        
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_active_context(self, working_dir: Path = None) -> Dict:
        """Determine active context based on current directory"""
        if not working_dir:
            working_dir = Path.cwd()
        
        contexts = []
        
        # 1. Root context (if exists)
        root_claude = self.workspace_root.parent / "CLAUDE.md"
        if root_claude.exists():
            contexts.append({
                "level": "root",
                "path": root_claude,
                "content": self._load_context_file(root_claude)
            })
        
        # 2. Workspace base context
        base_context = self.claude_dir / "contexts" / "base.md"
        if base_context.exists():
            contexts.append({
                "level": "workspace",
                "path": base_context,
                "content": self._load_context_file(base_context)
            })
        
        # 3. Agent-specific context
        relative_path = working_dir.relative_to(self.workspace_root)
        if "agents" in relative_path.parts:
            # Find agent directory
            for i, part in enumerate(relative_path.parts):
                if part == "agents" and i + 1 < len(relative_path.parts):
                    agent_name = relative_path.parts[i + 1]
                    agent_claude = self.workspace_root / "agents" / agent_name / "CLAUDE.md"
                    
                    if agent_claude.exists():
                        contexts.append({
                            "level": "agent",
                            "path": agent_claude,
                            "content": self._load_context_file(agent_claude)
                        })
                    
                    # Load private context if exists
                    private_context = self.claude_dir / "contexts" / "private" / f"{agent_name}.md"
                    if private_context.exists():
                        contexts.append({
                            "level": "private",
                            "path": private_context,
                            "content": self._load_context_file(private_context)
                        })
                    
                    break
        
        # 4. Project-specific context
        if "projects" in relative_path.parts:
            for i, part in enumerate(relative_path.parts):
                if part == "projects" and i + 1 < len(relative_path.parts):
                    project_name = relative_path.parts[i + 1]
                    project_claude = self.workspace_root / "projects" / project_name / "CLAUDE.md"
                    
                    if project_claude.exists():
                        contexts.append({
                            "level": "project",
                            "path": project_claude,
                            "content": self._load_context_file(project_claude)
                        })
                    break
        
        return {
            "working_directory": str(working_dir),
            "active_contexts": contexts,
            "merged_content": self._merge_contexts(contexts),
            "context_hash": self._calculate_context_hash(contexts)
        }
    
    def _load_context_file(self, path: Path) -> str:
        """Load context file with size limit"""
        max_size = self.config.get("standards", {}).get("context_length_max", 8000)
        
        content = path.read_text()
        if len(content) > max_size:
            # Truncate and add notice
            content = content[:max_size - 100] + "\n\n[Context truncated due to size limit]"
        
        return content
    
    def _merge_contexts(self, contexts: List[Dict]) -> str:
        """Merge multiple contexts into one"""
        merged = []
        
        for ctx in contexts:
            merged.append(f"# Context Level: {ctx['level'].upper()}")
            merged.append(f"# Source: {ctx['path']}")
            merged.append("")
            merged.append(ctx['content'])
            merged.append("\n---\n")
        
        return "\n".join(merged)
    
    def _calculate_context_hash(self, contexts: List[Dict]) -> str:
        """Calculate hash of active contexts for caching"""
        content = "".join(ctx['content'] for ctx in contexts)
        return hashlib.md5(content.encode()).hexdigest()
    
    def route_to_agent(self, task: Dict, from_agent: str = "user") -> Tuple[str, Dict]:
        """Route task to appropriate agent based on capabilities"""
        task_type = task.get("type", "general")
        required_capabilities = task.get("requires", [])
        
        # Load agent capabilities from config
        agents = self.config.get("agents", {})
        
        # Find best matching agent
        best_agent = None
        best_score = 0
        
        for agent_name, agent_config in agents.items():
            capabilities = agent_config.get("capabilities", [])
            
            # Calculate match score
            score = sum(1 for cap in required_capabilities if cap in capabilities)
            
            # Bonus for specific task types
            if task_type in capabilities:
                score += 2
            
            if score > best_score:
                best_score = score
                best_agent = agent_name
        
        # Default to orchestrator if no match
        if not best_agent:
            best_agent = "orchestrator"
        
        # Create routed message
        routed_message = {
            "id": f"{from_agent}-to-{best_agent}-{datetime.now().timestamp()}",
            "from": from_agent,
            "to": best_agent,
            "task": task,
            "routed_at": datetime.now().isoformat(),
            "routing_score": best_score,
            "context_hash": self.get_active_context()["context_hash"]
        }
        
        return best_agent, routed_message
    
    def switch_context(self, target_agent: str) -> Dict:
        """Switch to a different agent's context"""
        agent_dir = self.workspace_root / "agents" / f"agent-{target_agent}"
        
        if not agent_dir.exists():
            return {"error": f"Agent directory not found: {agent_dir}"}
        
        # Change working directory
        os.chdir(str(agent_dir))
        
        # Get new context
        new_context = self.get_active_context(agent_dir)
        
        return {
            "switched_to": target_agent,
            "new_working_dir": str(agent_dir),
            "context_loaded": len(new_context["active_contexts"]),
            "context_hash": new_context["context_hash"]
        }
    
    def create_handoff_package(self, from_agent: str, to_agent: str, 
                              task_data: Dict, context_data: Dict = None) -> Dict:
        """Create a complete handoff package for agent communication"""
        handoff = {
            "handoff_id": f"handoff-{datetime.now().timestamp()}",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "timestamp": datetime.now().isoformat(),
            "task": task_data,
            "context": context_data or {},
            "return_path": str(Path.cwd()),
            "parent_contexts": [ctx["level"] for ctx in self.get_active_context()["active_contexts"]]
        }
        
        # Save to communication queue
        queue_dir = self.comm_dir / "queue" / "incoming"
        queue_dir.mkdir(parents=True, exist_ok=True)
        
        handoff_file = queue_dir / f"{handoff['handoff_id']}.json"
        handoff_file.write_text(json.dumps(handoff, indent=2))
        
        return handoff
    
    def list_available_agents(self) -> List[Dict]:
        """List all available agents with their status"""
        agents = []
        
        for agent_dir in (self.workspace_root / "agents").glob("agent-*"):
            if agent_dir.is_dir():
                agent_info = {
                    "name": agent_dir.name,
                    "path": str(agent_dir),
                    "has_claude_md": (agent_dir / "CLAUDE.md").exists(),
                    "has_private_context": (self.claude_dir / "contexts" / "private" / f"{agent_dir.name}.md").exists()
                }
                
                # Check if agent has active tasks
                agent_queue = self.comm_dir / "queue" / "incoming"
                agent_tasks = list(agent_queue.glob(f"*to-{agent_dir.name}*.json"))
                agent_info["pending_tasks"] = len(agent_tasks)
                
                agents.append(agent_info)
        
        return agents
    
    def validate_context_hierarchy(self) -> List[Dict]:
        """Validate context files and hierarchy"""
        issues = []
        
        # Check base context
        base_context = self.claude_dir / "contexts" / "base.md"
        if not base_context.exists():
            issues.append({
                "level": "error",
                "message": "Missing base context file",
                "path": str(base_context)
            })
        
        # Check agent contexts
        for agent_dir in (self.workspace_root / "agents").glob("agent-*"):
            claude_file = agent_dir / "CLAUDE.md"
            
            if not claude_file.exists():
                issues.append({
                    "level": "warning",
                    "message": f"Agent missing CLAUDE.md: {agent_dir.name}",
                    "path": str(claude_file)
                })
            else:
                # Check for required sections
                content = claude_file.read_text()
                required_sections = ["## Core Identity", "## Core Responsibilities", "## Integration Points"]
                
                for section in required_sections:
                    if section not in content:
                        issues.append({
                            "level": "info",
                            "message": f"Missing section '{section}' in {agent_dir.name}",
                            "path": str(claude_file)
                        })
        
        return issues


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Context Router")
    parser.add_argument("command", choices=["status", "route", "switch", "list", "validate"])
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument("--agent", help="Target agent name")
    parser.add_argument("--task", help="Task description or JSON")
    parser.add_argument("--from", dest="from_agent", default="user", help="Source agent")
    
    args = parser.parse_args()
    
    router = ContextRouter(args.workspace)
    
    if args.command == "status":
        context = router.get_active_context()
        print(f"Working Directory: {context['working_directory']}")
        print(f"Active Contexts: {len(context['active_contexts'])}")
        for ctx in context['active_contexts']:
            print(f"  - {ctx['level']}: {ctx['path']}")
        print(f"Context Hash: {context['context_hash']}")
    
    elif args.command == "route" and args.task:
        task_data = {"description": args.task} if not args.task.startswith("{") else json.loads(args.task)
        agent, message = router.route_to_agent(task_data, args.from_agent)
        print(f"Routed to: {agent}")
        print(f"Message: {json.dumps(message, indent=2)}")
    
    elif args.command == "switch" and args.agent:
        result = router.switch_context(args.agent)
        print(json.dumps(result, indent=2))
    
    elif args.command == "list":
        agents = router.list_available_agents()
        print("Available Agents:")
        for agent in agents:
            status = "✓" if agent["has_claude_md"] else "✗"
            print(f"  {status} {agent['name']} - {agent['pending_tasks']} pending tasks")
    
    elif args.command == "validate":
        issues = router.validate_context_hierarchy()
        if issues:
            print(f"Found {len(issues)} issues:")
            for issue in issues:
                print(f"  [{issue['level'].upper()}] {issue['message']}")
        else:
            print("All contexts valid!")