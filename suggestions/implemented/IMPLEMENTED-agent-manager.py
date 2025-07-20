#!/usr/bin/env python3
"""
Agent Manager - Orchestrates multi-agent development projects
Run this from the agents/ directory in Cursor
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import sys

class AgentManager:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.agents_dir = self.base_dir
        self.projects_dir = self.base_dir.parent / "projects"
        self.shared_dir = self.agents_dir / "shared"
        
        # Ensure directories exist
        self.projects_dir.mkdir(exist_ok=True)
        self.shared_dir.mkdir(exist_ok=True)
        (self.shared_dir / "communication").mkdir(exist_ok=True)
        (self.shared_dir / "memory").mkdir(exist_ok=True)
    
    def create_project(self, project_name, project_type="fullstack", agent_count=4):
        """Create a new project with proper structure"""
        print(f"\n🚀 Creating new project: {project_name}")
        print(f"   Type: {project_type}")
        print(f"   Agents: {agent_count}")
        
        # Create project directories
        project_path = self.projects_dir / project_name
        if project_path.exists():
            print(f"❌ Project {project_name} already exists!")
            return None
        
        # Create directory structure
        agent_workspace = project_path / "agent-workspace"
        app_dir = project_path / "app"
        
        # Create all directories
        for dir_path in [
            agent_workspace / "agents",
            agent_workspace / "logs",
            agent_workspace / "docs",
            agent_workspace / "communication" / "queue",
            agent_workspace / "communication" / "events",
            agent_workspace / "communication" / "state",
            agent_workspace / "memory",
            app_dir / "src",
            app_dir / "public",
            app_dir / "tests"
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitignore for agent-workspace
        gitignore_content = """# Agent workspace - not for deployment
*
!.gitignore
"""
        with open(agent_workspace / ".gitignore", "w") as f:
            f.write(gitignore_content)
        
        # Create project configuration
        project_config = {
            "project": {
                "name": project_name,
                "type": project_type,
                "created": datetime.utcnow().isoformat(),
                "status": "initializing"
            },
            "agents": {
                "max_count": agent_count,
                "active": [],
                "roles": self._get_agent_roles(project_type)
            },
            "paths": {
                "root": str(project_path),
                "agent_workspace": str(agent_workspace),
                "app": str(app_dir),
                "communication": str(agent_workspace / "communication")
            }
        }
        
        # Save project config
        with open(agent_workspace / "project.json", "w") as f:
            json.dump(project_config, f, indent=2)
        
        # Initialize git repository
        self._init_git_repo(project_path)
        
        # Create initial app structure based on type
        self._create_app_skeleton(app_dir, project_type)
        
        print(f"✅ Project created at: {project_path}")
        print(f"   Agent workspace: {agent_workspace}")
        print(f"   Deployable app: {app_dir}")
        
        return project_path
    
    def deploy_agents(self, project_name, agent_roles=None):
        """Deploy agents to work on a project"""
        project_path = self.projects_dir / project_name
        if not project_path.exists():
            print(f"❌ Project {project_name} not found!")
            return
        
        # Load project config
        config_path = project_path / "agent-workspace" / "project.json"
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Use provided roles or get from config
        if not agent_roles:
            agent_roles = config["agents"]["roles"]
        
        print(f"\n🤖 Deploying agents for: {project_name}")
        
        deployed = []
        for role in agent_roles:
            agent_id = f"agent-{role}-001"
            success = self._deploy_single_agent(project_path, agent_id, role)
            if success:
                deployed.append(agent_id)
                print(f"   ✅ Deployed: {agent_id}")
            else:
                print(f"   ❌ Failed: {agent_id}")
        
        # Update config
        config["agents"]["active"] = deployed
        config["project"]["status"] = "active"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Deployed {len(deployed)} agents")
        return deployed
    
    def _deploy_single_agent(self, project_path, agent_id, role):
        """Deploy a single agent using git worktree"""
        agent_workspace = project_path / "agent-workspace" / "agents" / agent_id
        
        try:
            # Create git worktree
            os.chdir(project_path)
            branch_name = f"agent/{role}"
            
            # Create branch if it doesn't exist
            subprocess.run(["git", "checkout", "-b", branch_name], 
                         capture_output=True, check=False)
            subprocess.run(["git", "checkout", "main"], 
                         capture_output=True, check=False)
            
            # Add worktree
            subprocess.run([
                "git", "worktree", "add", 
                str(agent_workspace), 
                branch_name
            ], check=True)
            
            # Create agent configuration
            agent_config = {
                "agent_id": agent_id,
                "role": role,
                "project": project_path.name,
                "created": datetime.utcnow().isoformat(),
                "workspace": str(agent_workspace),
                "communication": {
                    "queue": str(project_path / "agent-workspace" / "communication" / "queue"),
                    "events": str(project_path / "agent-workspace" / "communication" / "events"),
                    "state": str(project_path / "agent-workspace" / "communication" / "state")
                }
            }
            
            with open(agent_workspace / ".agent-config.json", "w") as f:
                json.dump(agent_config, f, indent=2)
            
            # Create agent-specific CLAUDE.md
            self._create_agent_claude_md(agent_workspace, role)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Git error: {e}")
            return False
        except Exception as e:
            print(f"Error deploying agent: {e}")
            return False
        finally:
            os.chdir(self.base_dir)
    
    def coordinate_task(self, project_name, task_description, target_agents=None):
        """Coordinate a task across multiple agents"""
        project_path = self.projects_dir / project_name
        comm_queue = project_path / "agent-workspace" / "communication" / "queue"
        
        # Create task ID
        task_id = f"task-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Load project config to get active agents
        config_path = project_path / "agent-workspace" / "project.json"
        with open(config_path, "r") as f:
            config = json.load(f)
        
        agents = target_agents or config["agents"]["active"]
        
        print(f"\n📋 Coordinating task: {task_description}")
        print(f"   Task ID: {task_id}")
        print(f"   Agents: {', '.join(agents)}")
        
        # Decompose task (simplified - in practice, use AI for this)
        subtasks = self._decompose_task(task_description, agents)
        
        # Send tasks to agents
        for subtask in subtasks:
            message = {
                "id": f"{task_id}-{subtask['agent']}",
                "from": "orchestrator",
                "to": subtask["agent"],
                "type": "task",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "task_id": task_id,
                    "description": subtask["description"],
                    "requirements": subtask.get("requirements", []),
                    "dependencies": subtask.get("dependencies", [])
                }
            }
            
            # Write to queue
            message_file = comm_queue / f"{message['timestamp']}_{message['id']}.json"
            with open(message_file, "w") as f:
                json.dump(message, f, indent=2)
            
            print(f"   📤 Sent to {subtask['agent']}: {subtask['description']}")
        
        return task_id
    
    def show_status(self, project_name=None):
        """Show status of projects and agents"""
        print("\n📊 Multi-Agent System Status")
        print("=" * 50)
        
        if project_name:
            projects = [self.projects_dir / project_name]
        else:
            projects = [p for p in self.projects_dir.iterdir() if p.is_dir()]
        
        for project in projects:
            config_path = project / "agent-workspace" / "project.json"
            if not config_path.exists():
                continue
            
            with open(config_path, "r") as f:
                config = json.load(f)
            
            print(f"\n📁 Project: {config['project']['name']}")
            print(f"   Type: {config['project']['type']}")
            print(f"   Status: {config['project']['status']}")
            print(f"   Active Agents: {len(config['agents']['active'])}")
            
            # Check agent states
            state_dir = project / "agent-workspace" / "communication" / "state"
            for state_file in state_dir.glob("*.json"):
                with open(state_file, "r") as f:
                    state = json.load(f)
                
                print(f"   🤖 {state['agent_id']}: {state.get('status', 'unknown')}")
        
        print("\n" + "=" * 50)
    
    def _get_agent_roles(self, project_type):
        """Get default agent roles based on project type"""
        roles = {
            "fullstack": ["frontend", "backend", "database", "testing"],
            "frontend": ["ui", "styling", "testing"],
            "backend": ["api", "database", "testing"],
            "mobile": ["ios", "android", "backend", "testing"],
            "data": ["pipeline", "analysis", "visualization", "testing"]
        }
        return roles.get(project_type, ["developer", "testing"])
    
    def _init_git_repo(self, project_path):
        """Initialize git repository for the project"""
        os.chdir(project_path)
        subprocess.run(["git", "init"], check=True)
        
        # Create initial commit
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial project structure"], check=True)
        
        os.chdir(self.base_dir)
    
    def _create_app_skeleton(self, app_dir, project_type):
        """Create initial app structure based on project type"""
        if project_type in ["fullstack", "frontend"]:
            # Create package.json
            package_json = {
                "name": app_dir.parent.name,
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "test": "jest"
                }
            }
            with open(app_dir / "package.json", "w") as f:
                json.dump(package_json, f, indent=2)
            
            # Create README
            readme = f"""# {app_dir.parent.name}

This is the deployable application directory. Only production code goes here.

## Structure
- `src/` - Source code
- `public/` - Static assets
- `tests/` - Test files

## Development
The actual development is managed by AI agents in the agent-workspace directory.
"""
            with open(app_dir / "README.md", "w") as f:
                f.write(readme)
    
    def _create_agent_claude_md(self, workspace, role):
        """Create role-specific CLAUDE.md for agent"""
        templates = {
            "frontend": """# Frontend Agent

You are responsible for all frontend/UI development.

## Your Domain
- Everything in app/src/components
- Everything in app/src/pages
- Styling and CSS
- Client-side state management

## Key Responsibilities
1. Create React/Vue/Angular components
2. Implement responsive designs
3. Handle user interactions
4. Integrate with backend APIs

## Communication
- Report progress to orchestrator
- Coordinate with backend agent for APIs
- Work with testing agent for component tests
""",
            "backend": """# Backend Agent  

You are responsible for all backend/API development.

## Your Domain
- Everything in app/src/api
- Everything in app/src/server
- Database schemas and migrations
- Server-side logic

## Key Responsibilities
1. Design and implement APIs
2. Handle authentication/authorization
3. Manage database operations
4. Implement business logic

## Communication
- Report progress to orchestrator
- Coordinate with frontend agent on API contracts
- Work with database agent on schema design
""",
            "testing": """# Testing Agent

You are responsible for all testing and quality assurance.

## Your Domain
- Everything in app/tests
- Test configurations
- CI/CD pipeline setup

## Key Responsibilities
1. Write unit tests
2. Create integration tests
3. Implement E2E tests
4. Ensure code coverage

## Communication
- Report test results to orchestrator
- Coordinate with all agents for testing needs
- Flag quality issues immediately
"""
        }
        
        content = templates.get(role, f"# {role.title()} Agent\n\nYou are responsible for {role} tasks.")
        
        with open(workspace / "CLAUDE.md", "w") as f:
            f.write(content)
    
    def _decompose_task(self, task_description, agents):
        """Decompose task into subtasks for agents"""
        # This is simplified - in practice, you'd use Claude to do intelligent decomposition
        subtasks = []
        
        task_lower = task_description.lower()
        
        if "authentication" in task_lower or "auth" in task_lower:
            if "agent-backend-001" in agents:
                subtasks.append({
                    "agent": "agent-backend-001",
                    "description": "Implement authentication API endpoints (login, logout, register)",
                    "requirements": ["JWT tokens", "Password hashing", "Session management"]
                })
            if "agent-frontend-001" in agents:
                subtasks.append({
                    "agent": "agent-frontend-001",
                    "description": "Create authentication UI components (login form, register form)",
                    "requirements": ["Form validation", "Error handling", "Loading states"],
                    "dependencies": ["agent-backend-001"]
                })
            if "agent-database-001" in agents:
                subtasks.append({
                    "agent": "agent-database-001",
                    "description": "Design user authentication database schema",
                    "requirements": ["Users table", "Sessions table", "Password reset tokens"]
                })
            if "agent-testing-001" in agents:
                subtasks.append({
                    "agent": "agent-testing-001",
                    "description": "Create authentication test suite",
                    "requirements": ["Unit tests", "Integration tests", "Security tests"],
                    "dependencies": ["agent-backend-001", "agent-frontend-001"]
                })
        else:
            # Generic task distribution
            for agent in agents:
                role = agent.split("-")[1]
                subtasks.append({
                    "agent": agent,
                    "description": f"Handle {role} aspects of: {task_description}"
                })
        
        return subtasks


def main():
    parser = argparse.ArgumentParser(description="Manage multi-agent development projects")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create project command
    create_parser = subparsers.add_parser("create", help="Create new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--type", default="fullstack", help="Project type")
    create_parser.add_argument("--agents", type=int, default=4, help="Number of agents")
    
    # Deploy agents command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy agents to project")
    deploy_parser.add_argument("project", help="Project name")
    deploy_parser.add_argument("--roles", nargs="+", help="Agent roles to deploy")
    
    # Coordinate task command
    task_parser = subparsers.add_parser("task", help="Coordinate task across agents")
    task_parser.add_argument("project", help="Project name")
    task_parser.add_argument("description", help="Task description")
    task_parser.add_argument("--agents", nargs="+", help="Target agents")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument("--project", help="Specific project name")
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = AgentManager()
    
    # Execute command
    if args.command == "create":
        manager.create_project(args.name, args.type, args.agents)
    elif args.command == "deploy":
        manager.deploy_agents(args.project, args.roles)
    elif args.command == "task":
        manager.coordinate_task(args.project, args.description, args.agents)
    elif args.command == "status":
        manager.show_status(args.project)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()