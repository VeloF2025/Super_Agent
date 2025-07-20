#!/usr/bin/env python3
"""
Project Manager - Enhanced for existing Super Agent Team
Integrates with current agent structure, no new agents created
Run from agents/ directory in Cursor
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import sys

class ProjectManager:
    def __init__(self, base_dir=None):
        # Detect if we're in the agents directory
        current_dir = Path.cwd()
        if current_dir.name == "agents":
            self.agents_dir = current_dir
            self.base_dir = current_dir.parent
        else:
            # Assume we're in Super Agent root
            self.base_dir = Path(base_dir) if base_dir else current_dir
            self.agents_dir = self.base_dir / "agents"
        
        self.projects_dir = self.base_dir / "projects"
        self.shared_dir = self.base_dir / "shared"
        
        # Ensure directories exist
        self.projects_dir.mkdir(exist_ok=True)
        
        # Reference existing agents (no new agents created)
        self.available_agents = {
            "agent-orchestrator": "Master coordination and task decomposition",
            "agent-development": "Full-stack development and implementation",
            "agent-research": "Research and analysis",
            "agent-quality": "Testing and quality assurance", 
            "agent-communication": "Documentation and user interface",
            "agent-architect": "System design and architecture",
            "agent-optimizer": "Performance optimization",
            "agent-innovation": "Innovation and enhancement research"
        }
    
    def create_project(self, project_name, project_type="fullstack", agent_roles=None):
        """Create a new project with proper structure using existing agents"""
        print(f"\n🚀 Creating new project: {project_name}")
        print(f"   Type: {project_type}")
        
        # Create project directories
        project_path = self.projects_dir / project_name
        if project_path.exists():
            print(f"❌ Project {project_name} already exists!")
            return None
        
        # Create directory structure
        agent_workspace = project_path / "agent-workspace"
        app_dir = project_path / "app"
        
        # Create all directories
        directories = [
            agent_workspace / "agents",
            agent_workspace / "logs",
            agent_workspace / "docs",
            agent_workspace / "communication" / "queue",
            agent_workspace / "communication" / "events", 
            agent_workspace / "communication" / "state",
            agent_workspace / "memory",
            app_dir / "src",
            app_dir / "public",
            app_dir / "tests",
            app_dir / "docs"
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitignore for agent-workspace
        gitignore_content = """# Agent workspace - not for deployment
*.log
*.tmp
**/communication/queue/*
**/communication/events/*
**/communication/state/*
**/memory/temporary/*
.agent-temp/
"""
        with open(agent_workspace / ".gitignore", "w") as f:
            f.write(gitignore_content)
        
        # Create app-level .gitignore
        app_gitignore = """# Dependencies
node_modules/
*.lock

# Build outputs
/build/
/dist/
*.tsbuildinfo

# Environment
.env
.env.local
.env.production.local

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# OS
.DS_Store
Thumbs.db
"""
        with open(app_dir / ".gitignore", "w") as f:
            f.write(app_gitignore)
        
        # Determine agent roles based on project type
        if not agent_roles:
            agent_roles = self._get_project_agent_roles(project_type)
        
        # Create project configuration
        project_config = {
            "project": {
                "name": project_name,
                "type": project_type,
                "created": datetime.utcnow().isoformat(),
                "status": "initializing",
                "structure_version": "1.0"
            },
            "agents": {
                "assigned_roles": agent_roles,
                "active_agents": [],
                "communication_protocol": "json_queue"
            },
            "paths": {
                "root": str(project_path),
                "agent_workspace": str(agent_workspace),
                "app": str(app_dir),
                "communication": str(agent_workspace / "communication")
            },
            "deployment": {
                "target_directory": "app",
                "exclude_patterns": ["agent-workspace", "*.log", "*.tmp"]
            }
        }
        
        # Save project config
        with open(agent_workspace / "project.json", "w") as f:
            json.dump(project_config, f, indent=2)
        
        # Initialize git repository
        self._init_git_repo(project_path)
        
        # Create initial app structure based on type
        self._create_app_skeleton(app_dir, project_type, project_name)
        
        # Create communication system
        self._setup_communication_system(agent_workspace / "communication")
        
        print(f"✅ Project created at: {project_path}")
        print(f"   Agent workspace: {agent_workspace}")
        print(f"   Deployable app: {app_dir}")
        print(f"   Assigned agents: {', '.join(agent_roles)}")
        
        return project_path
    
    def deploy_agents_to_project(self, project_name, specific_agents=None):
        """Deploy existing agents to work on a specific project"""
        project_path = self.projects_dir / project_name
        if not project_path.exists():
            print(f"❌ Project {project_name} not found!")
            return
        
        # Load project config
        config_path = project_path / "agent-workspace" / "project.json"
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Use specified agents or get from config
        agents_to_deploy = specific_agents or config["agents"]["assigned_roles"]
        
        print(f"\n🤖 Deploying agents for: {project_name}")
        
        deployed = []
        for agent_role in agents_to_deploy:
            # Use existing agents, don't create new ones
            agent_id = f"agent-{agent_role}" if not agent_role.startswith("agent-") else agent_role
            
            if agent_id not in self.available_agents:
                print(f"   ⚠️  Agent {agent_id} not available in current team")
                continue
            
            success = self._setup_agent_workspace(project_path, agent_id, agent_role)
            if success:
                deployed.append(agent_id)
                print(f"   ✅ Deployed: {agent_id}")
            else:
                print(f"   ❌ Failed: {agent_id}")
        
        # Update config
        config["agents"]["active_agents"] = deployed
        config["project"]["status"] = "active"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Deployed {len(deployed)} existing agents to project")
        return deployed
    
    def _setup_agent_workspace(self, project_path, agent_id, role):
        """Setup workspace for existing agent in project"""
        agent_workspace = project_path / "agent-workspace" / "agents" / agent_id
        
        try:
            # Create agent workspace directory
            agent_workspace.mkdir(parents=True, exist_ok=True)
            
            # Create agent project configuration
            agent_config = {
                "agent_id": agent_id,
                "role": role,
                "project": project_path.name,
                "workspace": str(agent_workspace),
                "created": datetime.utcnow().isoformat(),
                "communication": {
                    "queue": str(project_path / "agent-workspace" / "communication" / "queue"),
                    "events": str(project_path / "agent-workspace" / "communication" / "events"),
                    "state": str(project_path / "agent-workspace" / "communication" / "state")
                },
                "output_target": str(project_path / "app"),
                "source_agent_config": str(self.agents_dir / agent_id / ".agent-config.json")
            }
            
            with open(agent_workspace / ".agent-project-config.json", "w") as f:
                json.dump(agent_config, f, indent=2)
            
            # Create project-specific CLAUDE.md context
            self._create_project_agent_context(agent_workspace, agent_id, role, project_path.name)
            
            # Create work directories
            work_dirs = ["current-tasks", "completed", "drafts", "resources"]
            for work_dir in work_dirs:
                (agent_workspace / work_dir).mkdir(exist_ok=True)
            
            return True
            
        except Exception as e:
            print(f"Error setting up workspace for {agent_id}: {e}")
            return False
    
    def coordinate_task(self, project_name, task_description, target_agents=None):
        """Coordinate a task across existing agents"""
        project_path = self.projects_dir / project_name
        comm_queue = project_path / "agent-workspace" / "communication" / "queue"
        
        if not project_path.exists():
            print(f"❌ Project {project_name} not found!")
            return
        
        # Create task ID
        task_id = f"task-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Load project config
        config_path = project_path / "agent-workspace" / "project.json"
        with open(config_path, "r") as f:
            config = json.load(f)
        
        agents = target_agents or config["agents"]["active_agents"]
        
        print(f"\n📋 Coordinating task: {task_description}")
        print(f"   Task ID: {task_id}")
        print(f"   Target agents: {', '.join(agents)}")
        
        # Decompose task using existing agent capabilities
        subtasks = self._decompose_task_for_existing_agents(task_description, agents)
        
        # Send tasks to agents via communication queue
        for subtask in subtasks:
            message = {
                "id": f"{task_id}-{subtask['agent']}",
                "from": "agent-orchestrator",
                "to": subtask["agent"],
                "type": "project_task",
                "timestamp": datetime.utcnow().isoformat(),
                "project": project_name,
                "payload": {
                    "task_id": task_id,
                    "description": subtask["description"],
                    "requirements": subtask.get("requirements", []),
                    "dependencies": subtask.get("dependencies", []),
                    "output_location": str(project_path / "app"),
                    "context": f"Project: {project_name}, Type: {config['project']['type']}"
                }
            }
            
            # Write to communication queue
            timestamp = message['timestamp'].replace(':', '-').replace('.', '-')
            message_file = comm_queue / f"{timestamp}_{message['id']}.json"
            with open(message_file, "w") as f:
                json.dump(message, f, indent=2)
            
            print(f"   📤 Sent to {subtask['agent']}: {subtask['description']}")
        
        return task_id
    
    def show_project_status(self, project_name=None):
        """Show status of projects and agent activities"""
        print("\n📊 Multi-Agent Project Status")
        print("=" * 60)
        
        if project_name:
            projects = [self.projects_dir / project_name]
        else:
            projects = [p for p in self.projects_dir.iterdir() if p.is_dir()]
        
        if not projects:
            print("No projects found.")
            return
        
        for project in projects:
            config_path = project / "agent-workspace" / "project.json"
            if not config_path.exists():
                continue
            
            with open(config_path, "r") as f:
                config = json.load(f)
            
            print(f"\n📁 Project: {config['project']['name']}")
            print(f"   Type: {config['project']['type']}")
            print(f"   Status: {config['project']['status']}")
            print(f"   Created: {config['project']['created'][:10]}")
            print(f"   Active Agents: {len(config['agents']['active_agents'])}")
            
            # Check communication queue status
            queue_dir = project / "agent-workspace" / "communication" / "queue"
            if queue_dir.exists():
                pending_tasks = len(list(queue_dir.glob("*.json")))
                print(f"   Pending Tasks: {pending_tasks}")
            
            # Check agent states
            state_dir = project / "agent-workspace" / "communication" / "state"
            if state_dir.exists():
                for state_file in state_dir.glob("*.json"):
                    try:
                        with open(state_file, "r") as f:
                            state = json.load(f)
                        print(f"   🤖 {state['agent_id']}: {state.get('status', 'unknown')}")
                    except:
                        continue
        
        print("\n" + "=" * 60)
    
    def _get_project_agent_roles(self, project_type):
        """Get recommended agent roles based on project type"""
        role_mapping = {
            "fullstack": ["development", "quality", "communication", "architect"],
            "frontend": ["development", "quality", "communication"],
            "backend": ["development", "quality", "architect"],
            "mobile": ["development", "quality", "communication"],
            "data": ["research", "development", "quality"],
            "research": ["research", "communication", "quality"],
            "documentation": ["communication", "quality"],
            "optimization": ["optimizer", "quality", "development"]
        }
        return role_mapping.get(project_type, ["development", "quality"])
    
    def _init_git_repo(self, project_path):
        """Initialize git repository for the project"""
        original_dir = os.getcwd()
        try:
            os.chdir(project_path)
            subprocess.run(["git", "init"], check=True, capture_output=True)
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial project structure"], 
                         check=True, capture_output=True)
            print("   ✅ Git repository initialized")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Git initialization failed: {e}")
        finally:
            os.chdir(original_dir)
    
    def _create_app_skeleton(self, app_dir, project_type, project_name):
        """Create initial app structure based on project type"""
        if project_type in ["fullstack", "frontend"]:
            # Create package.json
            package_json = {
                "name": project_name.lower().replace(" ", "-"),
                "version": "0.1.0",
                "private": True,
                "description": f"Multi-agent developed {project_type} application",
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "test": "jest",
                    "lint": "eslint .",
                    "type-check": "tsc --noEmit"
                },
                "dependencies": {},
                "devDependencies": {},
                "keywords": ["multi-agent", "ai-developed", project_type]
            }
            with open(app_dir / "package.json", "w") as f:
                json.dump(package_json, f, indent=2)
        
        # Create README for app
        readme_content = f"""# {project_name}

> Multi-agent developed {project_type} application

## Overview
This application was developed using a multi-agent AI system with clean separation between development infrastructure and deployable code.

## Structure
- `src/` - Application source code
- `public/` - Static assets  
- `tests/` - Test files
- `docs/` - User documentation

## Development
This project uses a multi-agent development approach where AI specialists handle different aspects:
- Frontend development
- Backend services
- Quality assurance
- Documentation

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Deployment
Only this `app/` directory is deployed. The agent development infrastructure remains separate.

---

*Developed by Super Agent Team - Multi-Agent AI Development System*
"""
        with open(app_dir / "README.md", "w") as f:
            f.write(readme_content)
        
        # Create basic src structure
        src_dir = app_dir / "src"
        (src_dir / "components").mkdir(exist_ok=True)
        (src_dir / "utils").mkdir(exist_ok=True)
        
        if project_type in ["fullstack", "backend"]:
            (src_dir / "api").mkdir(exist_ok=True)
            (src_dir / "services").mkdir(exist_ok=True)
    
    def _setup_communication_system(self, comm_dir):
        """Setup communication system for project"""
        # Create communication protocol documentation
        protocol_doc = {
            "communication_protocol": {
                "version": "1.0",
                "message_format": {
                    "id": "unique-message-id",
                    "from": "source-agent-id",
                    "to": "target-agent-id",
                    "type": "message_type",
                    "timestamp": "ISO-8601-timestamp",
                    "project": "project-name",
                    "payload": "message-specific-data"
                },
                "message_types": [
                    "project_task",
                    "task_complete", 
                    "status_update",
                    "coordination_request",
                    "resource_request"
                ]
            }
        }
        
        with open(comm_dir / "protocol.json", "w") as f:
            json.dump(protocol_doc, f, indent=2)
    
    def _create_project_agent_context(self, workspace, agent_id, role, project_name):
        """Create project-specific context for existing agent"""
        context_content = f"""# Project Context: {project_name}

## Agent Assignment
- **Agent**: {agent_id}
- **Project Role**: {role}
- **Project**: {project_name}
- **Workspace**: {workspace}

## Project-Specific Instructions

### Output Location
ALL deliverable code MUST go to the `app/` directory only:
- Source code → `app/src/`
- Tests → `app/tests/`
- Documentation → `app/docs/`
- Configuration → `app/` (root level)

### Development Guidelines
1. **Clean Separation**: Never put agent files in app/ directory
2. **Coordination**: Use communication queue for agent coordination
3. **Quality**: Follow project quality standards
4. **Documentation**: Maintain both technical (here) and user (app/) docs

### Communication Protocol
- Queue Location: `communication/queue/`
- Status Updates: `communication/state/`
- Event Broadcasting: `communication/events/`

## Role Responsibilities for {role.title()}
{self._get_role_responsibilities(role)}

## Project Integration
- Work in this workspace directory
- Coordinate with other project agents
- Output deliverables to app/ directory only
- Maintain project quality standards

---

*This context is specific to project {project_name}. Refer to your main CLAUDE.md for general capabilities.*
"""
        
        with open(workspace / "PROJECT_CONTEXT.md", "w") as f:
            f.write(context_content)
    
    def _get_role_responsibilities(self, role):
        """Get role-specific responsibilities"""
        responsibilities = {
            "development": """
- Implement features and functionality
- Write clean, maintainable code
- Follow coding standards and best practices
- Create unit tests for new code
- Integrate with other system components""",
            "quality": """
- Review code quality and standards
- Create and execute test plans
- Perform integration testing
- Validate functionality against requirements
- Report and track issues""",
            "communication": """
- Create user documentation
- Maintain project README and guides
- Handle user interface copy and content
- Coordinate team communication
- Document APIs and system interfaces""",
            "research": """
- Investigate technical solutions
- Analyze requirements and constraints
- Research best practices and patterns
- Evaluate tools and technologies
- Provide technical recommendations""",
            "architect": """
- Design system architecture
- Define technical standards
- Plan integration strategies
- Review technical decisions
- Ensure scalability and maintainability""",
            "optimizer": """
- Analyze performance bottlenecks
- Optimize code and system performance
- Monitor resource usage
- Implement performance improvements
- Establish performance benchmarks"""
        }
        return responsibilities.get(role, f"Handle {role}-specific tasks for the project")
    
    def _decompose_task_for_existing_agents(self, task_description, agents):
        """Decompose task for existing agents based on their capabilities"""
        subtasks = []
        task_lower = task_description.lower()
        
        # Map agents to their core capabilities
        agent_capabilities = {
            "agent-development": ["implement", "code", "feature", "build", "create"],
            "agent-quality": ["test", "validate", "verify", "review", "check"],
            "agent-communication": ["document", "write", "interface", "content", "guide"],
            "agent-research": ["analyze", "investigate", "research", "study", "evaluate"],
            "agent-architect": ["design", "architecture", "structure", "plan", "pattern"],
            "agent-optimizer": ["optimize", "performance", "improve", "efficient", "speed"]
        }
        
        # Smart task decomposition based on keywords and agent capabilities
        for agent in agents:
            if agent in agent_capabilities:
                keywords = agent_capabilities[agent]
                relevance_score = sum(1 for keyword in keywords if keyword in task_lower)
                
                if relevance_score > 0 or agent == "agent-orchestrator":
                    subtask = self._generate_agent_subtask(agent, task_description, task_lower)
                    if subtask:
                        subtasks.append(subtask)
        
        # Ensure at least development agent gets involved
        if not any(s['agent'] == 'agent-development' for s in subtasks):
            subtasks.append({
                "agent": "agent-development",
                "description": f"Implement core functionality for: {task_description}",
                "requirements": ["Follow project coding standards", "Output to app/ directory"]
            })
        
        return subtasks
    
    def _generate_agent_subtask(self, agent, full_task, task_lower):
        """Generate specific subtask for an agent"""
        subtask_map = {
            "agent-development": {
                "description": f"Implement and code: {full_task}",
                "requirements": ["Write clean, testable code", "Follow project structure", "Output to app/src/"]
            },
            "agent-quality": {
                "description": f"Create test suite and quality validation for: {full_task}",
                "requirements": ["Unit tests", "Integration tests", "Quality checklist"]
            },
            "agent-communication": {
                "description": f"Create documentation and user guides for: {full_task}",
                "requirements": ["User documentation", "API documentation", "README updates"]
            },
            "agent-research": {
                "description": f"Research best practices and solutions for: {full_task}",
                "requirements": ["Technical analysis", "Recommendations", "Implementation options"]
            },
            "agent-architect": {
                "description": f"Design system architecture for: {full_task}",
                "requirements": ["Architecture design", "Integration plan", "Scalability considerations"]
            },
            "agent-optimizer": {
                "description": f"Optimize performance aspects of: {full_task}",
                "requirements": ["Performance analysis", "Optimization recommendations", "Benchmarking"]
            }
        }
        
        return subtask_map.get(agent)


def main():
    parser = argparse.ArgumentParser(description="Manage multi-agent projects with existing Super Agent Team")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create project command
    create_parser = subparsers.add_parser("create", help="Create new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--type", default="fullstack", 
                             choices=["fullstack", "frontend", "backend", "mobile", "data", "research"],
                             help="Project type")
    create_parser.add_argument("--agents", nargs="+", help="Specific agents to assign")
    
    # Deploy agents command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy agents to project")
    deploy_parser.add_argument("project", help="Project name")
    deploy_parser.add_argument("--agents", nargs="+", help="Specific agents to deploy")
    
    # Coordinate task command
    task_parser = subparsers.add_parser("task", help="Coordinate task across agents")
    task_parser.add_argument("project", help="Project name")
    task_parser.add_argument("description", help="Task description")
    task_parser.add_argument("--agents", nargs="+", help="Target specific agents")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument("--project", help="Specific project name")
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = ProjectManager()
    
    # Execute command
    if args.command == "create":
        project_path = manager.create_project(args.name, args.type, args.agents)
        if project_path:
            manager.deploy_agents_to_project(args.name, args.agents)
    elif args.command == "deploy":
        manager.deploy_agents_to_project(args.project, args.agents)
    elif args.command == "task":
        manager.coordinate_task(args.project, args.description, args.agents)
    elif args.command == "status":
        manager.show_project_status(args.project)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()