#!/usr/bin/env python3
"""
Jarvis Health Check System
Automatically detects and fixes common issues to ensure smooth operation.
"""

import os
import sys
import json
import subprocess
import psutil
import socket
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthCheck:
    """Comprehensive health check and auto-fix system."""
    
    def __init__(self):
        self.issues = []
        self.fixes_applied = []
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from various sources."""
        config = {
            'dashboard_port': 3000,
            'api_port': 8000,
            'ws_port': 3010,
            'min_python_version': (3, 8),
            'required_dirs': [
                'data', 'logs', 'memory/context/jarvis',
                'projects', 'config', 'shared/heartbeats'
            ],
            'required_files': ['.env', 'config.json'],
            'critical_services': ['api', 'dashboard', 'ml-optimization']
        }
        
        # Load from .env if exists
        if Path('.env').exists():
            with open('.env') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'DASHBOARD_PORT':
                            config['dashboard_port'] = int(value)
                        elif key == 'API_PORT':
                            config['api_port'] = int(value)
        
        return config
    
    def run(self, auto_fix: bool = True) -> Tuple[bool, List[str]]:
        """Run complete health check."""
        console.print("\n[bold cyan]🏥 Jarvis Health Check System[/bold cyan]\n")
        
        checks = [
            ("System Requirements", self.check_system_requirements),
            ("Python Environment", self.check_python_environment),
            ("Node.js Environment", self.check_node_environment),
            ("Directory Structure", self.check_directories),
            ("Configuration Files", self.check_config_files),
            ("Port Availability", self.check_ports),
            ("Service Health", self.check_services),
            ("Database Health", self.check_databases),
            ("Memory & Disk", self.check_resources),
            ("Agent Health", self.check_agents),
        ]
        
        all_healthy = True
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            for check_name, check_func in checks:
                task = progress.add_task(f"Checking {check_name}...", total=1)
                
                try:
                    is_healthy, issues = check_func()
                    
                    if is_healthy:
                        console.print(f"[green]✓[/green] {check_name}")
                    else:
                        console.print(f"[red]✗[/red] {check_name}")
                        self.issues.extend(issues)
                        all_healthy = False
                        
                        if auto_fix:
                            # Try to fix issues
                            for issue in issues:
                                if self.fix_issue(issue):
                                    self.fixes_applied.append(issue)
                
                except Exception as e:
                    console.print(f"[red]✗[/red] {check_name} - Error: {e}")
                    all_healthy = False
                
                progress.update(task, completed=1)
        
        # Show results
        self.show_results()
        
        return all_healthy, self.fixes_applied
    
    def check_system_requirements(self) -> Tuple[bool, List[str]]:
        """Check basic system requirements."""
        issues = []
        
        # Check Python version
        if sys.version_info < self.config['min_python_version']:
            issues.append({
                'type': 'python_version',
                'message': f"Python {self.config['min_python_version'][0]}.{self.config['min_python_version'][1]}+ required",
                'severity': 'critical',
                'fix': None
            })
        
        # Check OS
        if sys.platform not in ['linux', 'darwin', 'win32']:
            issues.append({
                'type': 'unsupported_os',
                'message': f"Unsupported OS: {sys.platform}",
                'severity': 'warning',
                'fix': None
            })
        
        # Check git
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
        except:
            issues.append({
                'type': 'missing_git',
                'message': "Git is not installed",
                'severity': 'high',
                'fix': 'install_git'
            })
        
        return len(issues) == 0, issues
    
    def check_python_environment(self) -> Tuple[bool, List[str]]:
        """Check Python packages and environment."""
        issues = []
        
        # Check virtual environment
        if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
            issues.append({
                'type': 'no_venv',
                'message': "Not running in virtual environment",
                'severity': 'warning',
                'fix': 'create_venv'
            })
        
        # Check required packages
        required_packages = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'rich',
            'numpy', 'pandas', 'scikit-learn'
        ]
        
        installed_packages = set()
        try:
            import pkg_resources
            installed_packages = {pkg.key for pkg in pkg_resources.working_set}
        except:
            pass
        
        missing_packages = []
        for package in required_packages:
            if package.lower() not in installed_packages:
                missing_packages.append(package)
        
        if missing_packages:
            issues.append({
                'type': 'missing_packages',
                'message': f"Missing Python packages: {', '.join(missing_packages)}",
                'severity': 'high',
                'fix': 'install_packages',
                'data': missing_packages
            })
        
        return len(issues) == 0, issues
    
    def check_node_environment(self) -> Tuple[bool, List[str]]:
        """Check Node.js and npm."""
        issues = []
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            node_version = result.stdout.strip()
            major_version = int(node_version.split('.')[0].replace('v', ''))
            
            if major_version < 14:
                issues.append({
                    'type': 'old_node',
                    'message': f"Node.js 14+ required (found {node_version})",
                    'severity': 'high',
                    'fix': None
                })
        except:
            issues.append({
                'type': 'missing_node',
                'message': "Node.js is not installed",
                'severity': 'critical',
                'fix': 'install_node'
            })
        
        # Check npm
        try:
            subprocess.run(['npm', '--version'], capture_output=True, check=True)
        except:
            issues.append({
                'type': 'missing_npm',
                'message': "npm is not installed",
                'severity': 'critical',
                'fix': None
            })
        
        # Check node_modules
        if not Path('node_modules').exists():
            issues.append({
                'type': 'missing_node_modules',
                'message': "Node modules not installed",
                'severity': 'high',
                'fix': 'npm_install'
            })
        
        if Path('agent-dashboard').exists() and not Path('agent-dashboard/node_modules').exists():
            issues.append({
                'type': 'missing_dashboard_modules',
                'message': "Dashboard node modules not installed",
                'severity': 'high',
                'fix': 'npm_install_dashboard'
            })
        
        return len(issues) == 0, issues
    
    def check_directories(self) -> Tuple[bool, List[str]]:
        """Check required directories exist."""
        issues = []
        
        for dir_path in self.config['required_dirs']:
            if not Path(dir_path).exists():
                issues.append({
                    'type': 'missing_directory',
                    'message': f"Missing directory: {dir_path}",
                    'severity': 'medium',
                    'fix': 'create_directory',
                    'data': dir_path
                })
        
        return len(issues) == 0, issues
    
    def check_config_files(self) -> Tuple[bool, List[str]]:
        """Check configuration files."""
        issues = []
        
        # Check .env
        if not Path('.env').exists():
            issues.append({
                'type': 'missing_env',
                'message': "Missing .env file",
                'severity': 'high',
                'fix': 'create_env'
            })
        else:
            # Check for API keys
            with open('.env') as f:
                env_content = f.read()
                if 'OPENAI_API_KEY=' in env_content and not env_content.split('OPENAI_API_KEY=')[1].split('\n')[0].strip():
                    issues.append({
                        'type': 'missing_api_key',
                        'message': "OpenAI API key not configured",
                        'severity': 'warning',
                        'fix': None
                    })
        
        # Check config.json
        if not Path('config.json').exists():
            issues.append({
                'type': 'missing_config',
                'message': "Missing config.json file",
                'severity': 'high',
                'fix': 'create_config'
            })
        
        return len(issues) == 0, issues
    
    def check_ports(self) -> Tuple[bool, List[str]]:
        """Check if required ports are available."""
        issues = []
        
        ports_to_check = [
            ('Dashboard', self.config['dashboard_port']),
            ('API', self.config['api_port']),
            ('WebSocket', self.config['ws_port'])
        ]
        
        for service_name, port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is in use
                issues.append({
                    'type': 'port_in_use',
                    'message': f"{service_name} port {port} is already in use",
                    'severity': 'high',
                    'fix': 'suggest_alt_port',
                    'data': {'service': service_name, 'port': port}
                })
        
        return len(issues) == 0, issues
    
    def check_services(self) -> Tuple[bool, List[str]]:
        """Check if services are running."""
        issues = []
        
        # Check API
        try:
            import requests
            response = requests.get(f"http://localhost:{self.config['api_port']}/health", timeout=2)
            if response.status_code != 200:
                issues.append({
                    'type': 'api_unhealthy',
                    'message': "API service is not healthy",
                    'severity': 'high',
                    'fix': 'restart_api'
                })
        except:
            issues.append({
                'type': 'api_not_running',
                'message': "API service is not running",
                'severity': 'warning',
                'fix': None  # Don't auto-start services
            })
        
        return len(issues) == 0, issues
    
    def check_databases(self) -> Tuple[bool, List[str]]:
        """Check database health."""
        issues = []
        
        # Check context database
        db_path = Path('memory/context/jarvis/jarvis_context.db')
        if db_path.exists():
            # Check if database is corrupted
            try:
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                conn.execute("SELECT COUNT(*) FROM sqlite_master")
                conn.close()
            except:
                issues.append({
                    'type': 'corrupted_db',
                    'message': "Context database appears corrupted",
                    'severity': 'high',
                    'fix': 'backup_and_recreate_db',
                    'data': str(db_path)
                })
        
        return len(issues) == 0, issues
    
    def check_resources(self) -> Tuple[bool, List[str]]:
        """Check system resources."""
        issues = []
        
        # Check memory
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            issues.append({
                'type': 'low_memory',
                'message': f"Low memory: {memory.percent:.1f}% used",
                'severity': 'warning',
                'fix': None
            })
        
        # Check disk space
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            issues.append({
                'type': 'low_disk',
                'message': f"Low disk space: {disk.percent:.1f}% used",
                'severity': 'warning',
                'fix': 'cleanup_logs'
            })
        
        return len(issues) == 0, issues
    
    def check_agents(self) -> Tuple[bool, List[str]]:
        """Check agent health."""
        issues = []
        
        # Check heartbeat files
        heartbeat_dir = Path('shared/heartbeats')
        if heartbeat_dir.exists():
            now = datetime.now()
            for heartbeat_file in heartbeat_dir.glob('*.heartbeat'):
                try:
                    mtime = datetime.fromtimestamp(heartbeat_file.stat().st_mtime)
                    if now - mtime > timedelta(minutes=10):
                        agent_name = heartbeat_file.stem
                        issues.append({
                            'type': 'stale_agent',
                            'message': f"Agent {agent_name} appears inactive",
                            'severity': 'medium',
                            'fix': 'restart_agent',
                            'data': agent_name
                        })
                except:
                    pass
        
        return len(issues) == 0, issues
    
    def fix_issue(self, issue: Dict[str, Any]) -> bool:
        """Attempt to fix an issue."""
        fix_type = issue.get('fix')
        if not fix_type:
            return False
        
        try:
            if fix_type == 'create_directory':
                Path(issue['data']).mkdir(parents=True, exist_ok=True)
                return True
                
            elif fix_type == 'create_env':
                self.create_default_env()
                return True
                
            elif fix_type == 'create_config':
                self.create_default_config()
                return True
                
            elif fix_type == 'npm_install':
                subprocess.run(['npm', 'install'], check=True)
                return True
                
            elif fix_type == 'npm_install_dashboard':
                os.chdir('agent-dashboard')
                subprocess.run(['npm', 'install'], check=True)
                os.chdir('..')
                return True
                
            elif fix_type == 'install_packages':
                packages = issue.get('data', [])
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + packages, check=True)
                return True
                
            elif fix_type == 'cleanup_logs':
                # Clean old logs
                log_dir = Path('logs')
                if log_dir.exists():
                    for log_file in log_dir.glob('*.log'):
                        if log_file.stat().st_size > 100 * 1024 * 1024:  # 100MB
                            log_file.unlink()
                return True
                
        except Exception as e:
            logger.error(f"Failed to fix {fix_type}: {e}")
            
        return False
    
    def create_default_env(self):
        """Create default .env file."""
        content = """# Jarvis Configuration
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DASHBOARD_PORT=3000
API_PORT=8000
AGENT_COUNT=5
"""
        with open('.env', 'w') as f:
            f.write(content)
    
    def create_default_config(self):
        """Create default config.json."""
        config = {
            "version": "2.0",
            "system": {
                "name": "Jarvis Super Agent System",
                "mode": "production"
            },
            "agents": {
                "count": 5
            }
        }
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
    
    def show_results(self):
        """Show health check results."""
        console.print("\n[bold]Health Check Results[/bold]\n")
        
        if not self.issues:
            console.print(Panel(
                "[bold green]✨ All systems healthy![/bold green]\n\n"
                "Your Jarvis system is running perfectly.",
                title="🎉 Perfect Health",
                border_style="green"
            ))
        else:
            # Group issues by severity
            critical = [i for i in self.issues if i.get('severity') == 'critical']
            high = [i for i in self.issues if i.get('severity') == 'high']
            medium = [i for i in self.issues if i.get('severity') == 'medium']
            warnings = [i for i in self.issues if i.get('severity') == 'warning']
            
            table = Table(title="Issues Found")
            table.add_column("Severity", style="bold")
            table.add_column("Issue")
            table.add_column("Status")
            
            for issue in critical:
                status = "Fixed" if issue in self.fixes_applied else "Needs attention"
                table.add_row("[red]CRITICAL[/red]", issue['message'], status)
                
            for issue in high:
                status = "Fixed" if issue in self.fixes_applied else "Needs attention"
                table.add_row("[yellow]HIGH[/yellow]", issue['message'], status)
                
            for issue in medium:
                status = "Fixed" if issue in self.fixes_applied else "Optional"
                table.add_row("[blue]MEDIUM[/blue]", issue['message'], status)
                
            for issue in warnings:
                status = "Fixed" if issue in self.fixes_applied else "Warning"
                table.add_row("[dim]WARNING[/dim]", issue['message'], status)
            
            console.print(table)
            
            if self.fixes_applied:
                console.print(f"\n[green]✓ Applied {len(self.fixes_applied)} automatic fixes[/green]")
    
    def generate_report(self, output_file: str = "health_report.json"):
        """Generate detailed health report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "os": sys.platform,
                "python_version": sys.version,
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            },
            "issues": self.issues,
            "fixes_applied": self.fixes_applied,
            "recommendations": self.get_recommendations()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on issues found."""
        recommendations = []
        
        if any(i['type'] == 'missing_api_key' for i in self.issues):
            recommendations.append("Configure API keys in .env file for full functionality")
        
        if any(i['type'] == 'no_venv' for i in self.issues):
            recommendations.append("Use a virtual environment for better dependency management")
        
        if any(i['severity'] == 'critical' for i in self.issues):
            recommendations.append("Address critical issues before running the system")
        
        return recommendations


def main():
    """Run health check from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jarvis Health Check System")
    parser.add_argument('--no-fix', action='store_true', help="Don't apply automatic fixes")
    parser.add_argument('--report', action='store_true', help="Generate detailed report")
    parser.add_argument('--quiet', action='store_true', help="Minimal output")
    
    args = parser.parse_args()
    
    health_check = HealthCheck()
    is_healthy, fixes = health_check.run(auto_fix=not args.no_fix)
    
    if args.report:
        report_file = health_check.generate_report()
        console.print(f"\n[blue]Report saved to: {report_file}[/blue]")
    
    # Exit code
    sys.exit(0 if is_healthy else 1)


if __name__ == "__main__":
    main()