#!/usr/bin/env python3
"""
Jarvis Super Agent - Automated Setup Script
Makes installation and configuration as simple as possible.
"""

import os
import sys
import json
import subprocess
import platform
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

console = Console()

class JarvisSetup:
    """Automated setup wizard for Jarvis Super Agent System."""
    
    def __init__(self):
        self.root_path = Path.cwd()
        self.config = {}
        self.system_info = {
            'os': platform.system(),
            'python_version': sys.version.split()[0],
            'node_version': None,
            'npm_version': None
        }
        
    def run(self):
        """Run the complete setup process."""
        try:
            self.show_welcome()
            self.check_prerequisites()
            self.configure_system()
            self.install_dependencies()
            self.setup_database()
            self.configure_agents()
            self.create_first_project()
            self.start_services()
            self.show_success()
        except KeyboardInterrupt:
            console.print("\n[red]Setup cancelled by user.[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Setup failed: {e}[/red]")
            sys.exit(1)
    
    def show_welcome(self):
        """Display welcome message and overview."""
        console.clear()
        welcome_text = """
[bold cyan]Welcome to Jarvis Super Agent System[/bold cyan]
[dim]The most advanced AI orchestration platform[/dim]

This setup wizard will help you:
• Check system requirements
• Configure your environment
• Install all dependencies
• Create your first project
• Launch the system

The entire process takes about 5 minutes.
        """
        console.print(Panel(welcome_text, title="🚀 Setup Wizard", border_style="cyan"))
        
        if not Confirm.ask("\n[yellow]Ready to begin?[/yellow]", default=True):
            sys.exit(0)
    
    def check_prerequisites(self):
        """Check and install prerequisites."""
        console.print("\n[bold]Checking Prerequisites...[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Check Python
            task = progress.add_task("Checking Python...", total=1)
            if sys.version_info < (3, 8):
                console.print("[red]✗ Python 3.8+ required[/red]")
                sys.exit(1)
            console.print(f"[green]✓ Python {self.system_info['python_version']}[/green]")
            progress.update(task, completed=1)
            
            # Check Node.js
            task = progress.add_task("Checking Node.js...", total=1)
            try:
                node_version = subprocess.check_output(['node', '--version'], text=True).strip()
                self.system_info['node_version'] = node_version
                console.print(f"[green]✓ Node.js {node_version}[/green]")
            except:
                console.print("[yellow]⚠ Node.js not found. Installing...[/yellow]")
                self.install_nodejs()
            progress.update(task, completed=1)
            
            # Check npm
            task = progress.add_task("Checking npm...", total=1)
            try:
                npm_version = subprocess.check_output(['npm', '--version'], text=True).strip()
                self.system_info['npm_version'] = npm_version
                console.print(f"[green]✓ npm {npm_version}[/green]")
            except:
                console.print("[red]✗ npm not found[/red]")
                sys.exit(1)
            progress.update(task, completed=1)
            
            # Check Git
            task = progress.add_task("Checking Git...", total=1)
            try:
                subprocess.check_output(['git', '--version'])
                console.print("[green]✓ Git installed[/green]")
            except:
                console.print("[red]✗ Git not found[/red]")
                sys.exit(1)
            progress.update(task, completed=1)
    
    def install_nodejs(self):
        """Install Node.js based on the platform."""
        if self.system_info['os'] == 'Windows':
            console.print("\n[yellow]Please install Node.js from: https://nodejs.org/[/yellow]")
            console.print("After installation, restart this setup script.")
            sys.exit(1)
        elif self.system_info['os'] == 'Darwin':  # macOS
            if shutil.which('brew'):
                subprocess.run(['brew', 'install', 'node'])
            else:
                console.print("\n[yellow]Please install Node.js from: https://nodejs.org/[/yellow]")
                sys.exit(1)
        else:  # Linux
            subprocess.run(['curl', '-fsSL', 'https://deb.nodesource.com/setup_lts.x', '|', 'sudo', '-E', 'bash', '-'])
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'nodejs'])
    
    def configure_system(self):
        """Configure system settings."""
        console.print("\n[bold]System Configuration[/bold]\n")
        
        # API Keys
        console.print("[cyan]API Keys Configuration[/cyan]")
        console.print("[dim]You can skip these and add them later to .env file[/dim]\n")
        
        self.config['openai_api_key'] = Prompt.ask(
            "OpenAI API Key", 
            default="skip",
            password=True if Prompt.ask("Hide input?", choices=["y", "n"], default="y") == "y" else False
        )
        
        self.config['anthropic_api_key'] = Prompt.ask(
            "Anthropic API Key (for Claude)", 
            default="skip",
            password=True if Prompt.ask("Hide input?", choices=["y", "n"], default="y") == "y" else False
        )
        
        # System Settings
        console.print("\n[cyan]System Settings[/cyan]")
        
        self.config['agent_count'] = Prompt.ask(
            "Number of initial agents",
            default="5",
            choices=["3", "5", "10", "custom"]
        )
        
        if self.config['agent_count'] == "custom":
            self.config['agent_count'] = Prompt.ask("Enter number of agents", default="5")
        
        self.config['dashboard_port'] = Prompt.ask(
            "Dashboard port",
            default="3000"
        )
        
        self.config['api_port'] = Prompt.ask(
            "API port",
            default="8000"
        )
        
        # Save configuration
        self.save_config()
    
    def save_config(self):
        """Save configuration to files."""
        # Create .env file
        env_content = f"""# Jarvis Super Agent Configuration
# Generated by setup wizard

# API Keys
OPENAI_API_KEY={self.config['openai_api_key'] if self.config['openai_api_key'] != 'skip' else ''}
ANTHROPIC_API_KEY={self.config['anthropic_api_key'] if self.config['anthropic_api_key'] != 'skip' else ''}

# System Configuration
AGENT_COUNT={self.config['agent_count']}
DASHBOARD_PORT={self.config['dashboard_port']}
API_PORT={self.config['api_port']}

# Database
DATABASE_PATH=./data/jarvis.db
CONTEXT_DB_PATH=./memory/context/jarvis/jarvis_context.db

# Features
ENABLE_ML_OPTIMIZATION=true
ENABLE_COLLABORATIVE_LEARNING=true
ENABLE_CRASH_RECOVERY=true
AUTO_CHECKPOINT_INTERVAL=30

# Monitoring
ENABLE_MONITORING=true
METRICS_INTERVAL=60
HEALTH_CHECK_INTERVAL=300
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        # Create config.json
        config_json = {
            "version": "2.0",
            "system": {
                "name": "Jarvis Super Agent System",
                "mode": "production",
                "features": {
                    "ml_optimization": True,
                    "collaborative_learning": True,
                    "crash_recovery": True,
                    "real_time_monitoring": True
                }
            },
            "agents": {
                "count": int(self.config['agent_count']),
                "types": [
                    "orchestrator",
                    "architect", 
                    "researcher",
                    "quality",
                    "communicator"
                ]
            },
            "dashboard": {
                "port": int(self.config['dashboard_port']),
                "host": "localhost",
                "auto_open": True
            },
            "api": {
                "port": int(self.config['api_port']),
                "host": "0.0.0.0"
            }
        }
        
        with open('config.json', 'w') as f:
            json.dump(config_json, f, indent=2)
        
        console.print("[green]✓ Configuration saved[/green]")
    
    def install_dependencies(self):
        """Install all dependencies."""
        console.print("\n[bold]Installing Dependencies[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Python dependencies
            task = progress.add_task("Installing Python packages...", total=1)
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         capture_output=True)
            console.print("[green]✓ Python packages installed[/green]")
            progress.update(task, completed=1)
            
            # Node dependencies - Root
            task = progress.add_task("Installing root Node packages...", total=1)
            subprocess.run(['npm', 'install'], capture_output=True)
            console.print("[green]✓ Root packages installed[/green]")
            progress.update(task, completed=1)
            
            # Dashboard dependencies
            if (self.root_path / 'agent-dashboard').exists():
                task = progress.add_task("Installing dashboard packages...", total=1)
                os.chdir('agent-dashboard')
                subprocess.run(['npm', 'install'], capture_output=True)
                
                # Client dependencies
                if (Path.cwd() / 'client').exists():
                    os.chdir('client')
                    subprocess.run(['npm', 'install'], capture_output=True)
                    os.chdir('..')
                
                os.chdir('..')
                console.print("[green]✓ Dashboard packages installed[/green]")
                progress.update(task, completed=1)
    
    def setup_database(self):
        """Initialize databases."""
        console.print("\n[bold]Setting up Databases[/bold]\n")
        
        # Create data directories
        directories = [
            'data',
            'memory/context/jarvis',
            'memory/context/jarvis/checkpoints',
            'logs',
            'projects',
            'shared/heartbeats'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        console.print("[green]✓ Directory structure created[/green]")
        
        # Initialize context database
        try:
            from memory.context.jarvis.jarvis_context_manager import JarvisContextManager
            cm = JarvisContextManager()
            console.print("[green]✓ Context database initialized[/green]")
        except:
            console.print("[yellow]⚠ Context database will be initialized on first run[/yellow]")
    
    def configure_agents(self):
        """Configure initial agents."""
        console.print("\n[bold]Configuring Agents[/bold]\n")
        
        agent_configs = []
        agent_count = int(self.config['agent_count'])
        
        # Default agent types
        default_agents = [
            {
                "id": "agent-orchestrator-001",
                "name": "Orchestrator Prime",
                "type": "orchestrator",
                "capabilities": ["task_assignment", "coordination", "monitoring"]
            },
            {
                "id": "agent-architect-001", 
                "name": "System Architect",
                "type": "architect",
                "capabilities": ["system_design", "architecture", "planning"]
            },
            {
                "id": "agent-researcher-001",
                "name": "Research Specialist", 
                "type": "researcher",
                "capabilities": ["research", "analysis", "documentation"]
            },
            {
                "id": "agent-quality-001",
                "name": "Quality Guardian",
                "type": "quality",
                "capabilities": ["testing", "validation", "quality_assurance"]
            },
            {
                "id": "agent-communicator-001",
                "name": "Communication Hub",
                "type": "communicator", 
                "capabilities": ["communication", "reporting", "coordination"]
            }
        ]
        
        # Use default agents up to requested count
        for i in range(min(agent_count, len(default_agents))):
            agent_configs.append(default_agents[i])
        
        # Add generic agents if more requested
        for i in range(len(default_agents), agent_count):
            agent_configs.append({
                "id": f"agent-generic-{i+1:03d}",
                "name": f"Agent {i+1}",
                "type": "generic",
                "capabilities": ["general", "support"]
            })
        
        # Save agent configuration
        with open('config/agents.json', 'w') as f:
            json.dump({"agents": agent_configs}, f, indent=2)
        
        console.print(f"[green]✓ Configured {len(agent_configs)} agents[/green]")
    
    def create_first_project(self):
        """Create first example project."""
        console.print("\n[bold]Creating Your First Project[/bold]\n")
        
        project_name = Prompt.ask(
            "Project name",
            default="My First Project"
        )
        
        project_type = Prompt.ask(
            "Project type",
            choices=["web_app", "api", "data_analysis", "automation", "other"],
            default="web_app"
        )
        
        # Create project structure
        project_path = Path('projects') / project_name.lower().replace(' ', '_')
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create project config
        project_config = {
            "id": f"project-{int(time.time())}",
            "name": project_name,
            "type": project_type,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "agents": ["agent-orchestrator-001"],
            "tasks": [
                {
                    "id": "task-001",
                    "description": "Initialize project structure",
                    "status": "pending"
                }
            ]
        }
        
        with open(project_path / 'project.json', 'w') as f:
            json.dump(project_config, f, indent=2)
        
        # Create README
        readme_content = f"""# {project_name}

## Overview
This is your first Jarvis-managed project. The AI agents will help you build and manage this project.

## Project Type
{project_type.replace('_', ' ').title()}

## Getting Started
1. The Orchestrator agent has been assigned to this project
2. View progress in the dashboard at http://localhost:{self.config['dashboard_port']}
3. Add tasks through the dashboard or API

## AI Agents
The following agents are available to help:
- Orchestrator: Coordinates tasks and agents
- Architect: Designs system architecture  
- Researcher: Gathers information and analyzes requirements
- Quality: Ensures code quality and testing
- Communicator: Handles documentation and reporting
"""
        
        with open(project_path / 'README.md', 'w') as f:
            f.write(readme_content)
        
        console.print(f"[green]✓ Created project: {project_name}[/green]")
        self.config['first_project'] = str(project_path)
    
    def start_services(self):
        """Start all services."""
        console.print("\n[bold]Starting Services[/bold]\n")
        
        # Create start script
        if self.system_info['os'] == 'Windows':
            script_content = f"""@echo off
echo Starting Jarvis Super Agent System...

REM Start API Server
start "Jarvis API" cmd /k "cd /d %~dp0 && python -m uvicorn api.main:app --port {self.config['api_port']} --reload"

REM Start ML Optimization Service
start "ML Optimization" cmd /k "cd /d %~dp0 && python memory/context/jarvis/ml_optimization_integration.py"

REM Wait for API to start
timeout /t 5 /nobreak > nul

REM Start Dashboard
start "Dashboard" cmd /k "cd /d %~dp0agent-dashboard && npm run dev"

REM Open dashboard in browser
timeout /t 5 /nobreak > nul
start http://localhost:{self.config['dashboard_port']}

echo.
echo Jarvis is running!
echo.
echo Dashboard: http://localhost:{self.config['dashboard_port']}
echo API: http://localhost:{self.config['api_port']}/docs
echo.
echo Press any key to stop all services...
pause > nul
"""
            script_name = 'start-jarvis.bat'
        else:
            script_content = f"""#!/bin/bash
echo "Starting Jarvis Super Agent System..."

# Start API Server
python -m uvicorn api.main:app --port {self.config['api_port']} --reload &
API_PID=$!

# Start ML Optimization Service  
python memory/context/jarvis/ml_optimization_integration.py &
ML_PID=$!

# Wait for API to start
sleep 5

# Start Dashboard
cd agent-dashboard && npm run dev &
DASHBOARD_PID=$!

# Open dashboard in browser
sleep 5
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:{self.config['dashboard_port']}
elif command -v open > /dev/null; then
    open http://localhost:{self.config['dashboard_port']}
fi

echo ""
echo "Jarvis is running!"
echo ""
echo "Dashboard: http://localhost:{self.config['dashboard_port']}"
echo "API: http://localhost:{self.config['api_port']}/docs"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for Ctrl+C
trap 'kill $API_PID $ML_PID $DASHBOARD_PID; exit' INT
wait
"""
            script_name = 'start-jarvis.sh'
            
        with open(script_name, 'w') as f:
            f.write(script_content)
        
        if self.system_info['os'] != 'Windows':
            os.chmod(script_name, 0o755)
        
        console.print(f"[green]✓ Created start script: {script_name}[/green]")
        
        # Ask to start now
        if Confirm.ask("\n[yellow]Start Jarvis now?[/yellow]", default=True):
            if self.system_info['os'] == 'Windows':
                subprocess.Popen(['cmd', '/c', script_name])
            else:
                subprocess.Popen(['bash', script_name])
    
    def show_success(self):
        """Show success message and next steps."""
        success_panel = f"""
[bold green]✨ Setup Complete![/bold green]

Your Jarvis Super Agent System is ready to use!

[bold]Quick Start Commands:[/bold]
• Start Jarvis: [cyan]./start-jarvis.{'bat' if self.system_info['os'] == 'Windows' else 'sh'}[/cyan]
• Stop Jarvis: Press Ctrl+C in the terminal

[bold]Access Points:[/bold]
• Dashboard: [link]http://localhost:{self.config['dashboard_port']}[/link]
• API Docs: [link]http://localhost:{self.config['api_port']}/docs[/link]
• First Project: [cyan]{self.config.get('first_project', 'projects/my_first_project')}[/cyan]

[bold]Next Steps:[/bold]
1. Open the dashboard to see your agents
2. Check out your first project
3. Create tasks through the dashboard
4. Watch the AI agents collaborate!

[bold]Need Help?[/bold]
• Documentation: [link]https://github.com/yourusername/jarvis-docs[/link]
• Quick Tutorial: Run [cyan]python tutorial.py[/cyan]
• Discord Community: [link]https://discord.gg/jarvis-ai[/link]
"""
        
        console.print(Panel(success_panel, title="🎉 Success", border_style="green"))
        
        # Create quick reference card
        self.create_quick_reference()
    
    def create_quick_reference(self):
        """Create a quick reference file."""
        reference = f"""# Jarvis Quick Reference

## Starting & Stopping
- Start: `./start-jarvis.{'bat' if self.system_info['os'] == 'Windows' else 'sh'}`
- Stop: Press Ctrl+C

## URLs
- Dashboard: http://localhost:{self.config['dashboard_port']}
- API: http://localhost:{self.config['api_port']}/docs
- ML Optimization: http://localhost:{self.config['dashboard_port']}/#/ml-optimization

## Common Commands
```bash
# Check agent status
curl http://localhost:{self.config['api_port']}/api/agents/status

# Create a new task
curl -X POST http://localhost:{self.config['api_port']}/api/tasks \\
  -H "Content-Type: application/json" \\
  -d '{{"description": "Your task", "project_id": "project-1"}}'

# Trigger ML learning cycle
curl -X POST http://localhost:{self.config['api_port']}/api/jarvis/ml-optimization/trigger-learning-cycle
```

## Project Structure
```
jarvis/
├── projects/          # Your projects
├── agent-dashboard/   # Web dashboard
├── memory/           # Agent memory & learning
├── config/           # Configuration files
├── logs/            # System logs
└── data/            # Databases
```

## Troubleshooting
- Agents not responding: Check `logs/agents.log`
- Dashboard not loading: Verify port {self.config['dashboard_port']} is free
- API errors: Check `logs/api.log`

## Configuration Files
- `.env` - Environment variables and API keys
- `config.json` - System configuration
- `config/agents.json` - Agent definitions
"""
        
        with open('QUICK_REFERENCE.md', 'w') as f:
            f.write(reference)


if __name__ == "__main__":
    # Check if rich is installed
    try:
        from rich import print
    except ImportError:
        print("Installing required setup dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'rich', 'requests'])
        from rich import print
    
    setup = JarvisSetup()
    setup.run()