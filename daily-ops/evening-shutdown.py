#!/usr/bin/env python3
"""
Jarvis Evening Shutdown System
Automated evening routine for data preservation and agent coordination
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from collections import defaultdict

class JarvisShutdown:
    def __init__(self):
        self.workspace_root = Path("C:/Jarvis/AI Workspace/Super Agent")
        self.memory_dir = self.workspace_root / "memory"
        self.standup_dir = self.memory_dir / "standups"
        self.comm_dir = self.workspace_root / "communication"
        self.workflows_dir = self.workspace_root / "workflows"
        self.logs_dir = self.workspace_root / "logs"
        self.archive_dir = self.memory_dir / "archive"
        
        # Ensure directories exist
        for dir_path in [self.standup_dir, self.archive_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def run_shutdown(self):
        """Execute evening shutdown routine"""
        print("\n" + "="*60)
        print("🌆 JARVIS EVENING SHUTDOWN")
        print("="*60)
        print(f"Date: {datetime.now().strftime('%A, %B %d, %Y')}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 1. Collect agent status
        print("🤖 COLLECTING AGENT STATUS")
        print("-" * 30)
        agent_status = self.collect_final_agent_status()
        
        # 2. Gather today's work
        print("\n📊 GATHERING TODAY'S WORK")
        print("-" * 30)
        todays_work = self.gather_todays_work()
        
        # 3. Analyze productivity
        print("\n📈 ANALYZING PRODUCTIVITY")
        print("-" * 30)
        productivity = self.analyze_productivity()
        
        # 4. Identify issues
        print("\n🔍 IDENTIFYING ISSUES")
        print("-" * 30)
        issues = self.identify_issues()
        
        # 5. Plan tomorrow
        print("\n🎯 PLANNING TOMORROW")
        print("-" * 30)
        tomorrow_plan = self.plan_tomorrow(todays_work, issues)
        
        # 6. Archive data
        print("\n📦 ARCHIVING DATA")
        print("-" * 30)
        archive_summary = self.archive_daily_data()
        
        # 7. Generate summary
        shutdown_summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'agent_status': agent_status,
            'todays_work': todays_work,
            'productivity_metrics': productivity,
            'issues': issues,
            'planned_next': tomorrow_plan,
            'archive_summary': archive_summary,
            'executive_summary': None  # Will be generated
        }
        
        shutdown_summary['executive_summary'] = self.create_executive_summary(shutdown_summary)
        
        # 8. Save records
        self.save_shutdown_record(shutdown_summary)
        
        # 9. Cleanup and prepare for tomorrow
        print("\n🧹 CLEANUP & PREPARATION")
        print("-" * 30)
        self.cleanup_and_prepare()
        
        print("\n✅ SHUTDOWN COMPLETE!")
        print("All data preserved. Ready for tomorrow's standup.")
        print("="*60)
        
        return shutdown_summary
    
    def collect_final_agent_status(self):
        """Collect final status from all agents"""
        agent_status = {}
        agents_parent = self.workspace_root.parent / "agents"
        
        if not agents_parent.exists():
            print("No agent directories found")
            return agent_status
        
        agent_dirs = list(agents_parent.glob("agent-*"))
        print(f"Checking {len(agent_dirs)} agents...")
        
        for agent_dir in agent_dirs:
            agent_id = agent_dir.name
            
            try:
                # Check if agent has daily context (was active today)
                daily_context = agent_dir / f"DAILY_CONTEXT_{datetime.now().strftime('%Y%m%d')}.md"
                
                status = {
                    'active_today': daily_context.exists(),
                    'last_modified': None,
                    'estimated_work_hours': 0,
                    'commits_today': self.count_agent_commits(agent_dir),
                    'files_modified': self.count_modified_files(agent_dir)
                }
                
                if daily_context.exists():
                    mod_time = datetime.fromtimestamp(daily_context.stat().st_mtime)
                    status['last_modified'] = mod_time.isoformat()
                    
                    # Estimate work hours based on file activity
                    status['estimated_work_hours'] = self.estimate_work_hours(agent_dir)
                
                agent_status[agent_id] = status
                
                active_icon = "✅" if status['active_today'] else "⏸️"
                print(f"  {active_icon} {agent_id}: {status['estimated_work_hours']:.1f}h, {status['commits_today']} commits")
                
            except Exception as e:
                print(f"  ❌ {agent_id}: Error - {e}")
                agent_status[agent_id] = {'error': str(e)}
        
        return agent_status
    
    def count_agent_commits(self, agent_dir):
        """Count commits made by agent today (if git repo)"""
        try:
            import subprocess
            
            # Check if it's a git repo
            if not (agent_dir / ".git").exists():
                return 0
            
            # Get today's commits
            today = datetime.now().strftime("%Y-%m-%d")
            result = subprocess.run([
                'git', 'log', '--oneline', f'--since={today}', '--until={today} 23:59:59'
            ], cwd=agent_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                return len([line for line in result.stdout.strip().split('\n') if line])
            
        except Exception:
            pass
        
        return 0
    
    def count_modified_files(self, agent_dir):
        """Count files modified today"""
        try:
            today = datetime.now().date()
            modified_count = 0
            
            for file_path in agent_dir.rglob('*'):
                if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                    mod_date = datetime.fromtimestamp(file_path.stat().st_mtime).date()
                    if mod_date == today:
                        modified_count += 1
            
            return modified_count
        except Exception:
            return 0
    
    def estimate_work_hours(self, agent_dir):
        """Estimate work hours based on file activity"""
        try:
            today = datetime.now().date()
            modification_times = []
            
            for file_path in agent_dir.rglob('*'):
                if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                    mod_datetime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mod_datetime.date() == today:
                        modification_times.append(mod_datetime)
            
            if len(modification_times) < 2:
                return 0.5 if modification_times else 0
            
            # Calculate work span
            modification_times.sort()
            first_activity = modification_times[0]
            last_activity = modification_times[-1]
            
            # Estimate hours (with some assumptions about breaks)
            total_span = (last_activity - first_activity).total_seconds() / 3600
            estimated_hours = min(total_span * 0.7, 8)  # Assume 70% active time, max 8 hours
            
            return max(estimated_hours, 0.5)  # Minimum 30 minutes if any activity
            
        except Exception:
            return 0
    
    def gather_todays_work(self):
        """Gather all work completed today"""
        todays_work = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'workflows': {
                'completed': [],
                'in_progress': [],
                'created': []
            },
            'agent_activity': {},
            'files_created': 0,
            'files_modified': 0,
            'total_commits': 0
        }
        
        # Check workflows
        if self.workflows_dir.exists():
            today = datetime.now().date()
            
            for workflow_file in self.workflows_dir.glob("*.json"):
                try:
                    with open(workflow_file, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                    
                    created_date = datetime.fromisoformat(workflow.get('created', datetime.now().isoformat())).date()
                    
                    workflow_info = {
                        'id': workflow.get('id', workflow_file.stem),
                        'description': workflow.get('specification', workflow.get('description', 'Unknown'))[:80]
                    }
                    
                    if created_date == today:
                        todays_work['workflows']['created'].append(workflow_info)
                    
                    if workflow.get('status') == 'completed':
                        if 'completed_at' in workflow:
                            completed_date = datetime.fromisoformat(workflow['completed_at']).date()
                            if completed_date == today:
                                todays_work['workflows']['completed'].append(workflow_info)
                    
                    elif workflow.get('status') == 'in_progress':
                        progress = self.calculate_workflow_progress(workflow)
                        workflow_info['progress'] = progress
                        todays_work['workflows']['in_progress'].append(workflow_info)
                        
                except Exception as e:
                    print(f"Error reading workflow {workflow_file}: {e}")
        
        # Gather agent activity
        agents_parent = self.workspace_root.parent / "agents"
        if agents_parent.exists():
            for agent_dir in agents_parent.glob("agent-*"):
                agent_id = agent_dir.name
                
                activity = {
                    'commits': self.count_agent_commits(agent_dir),
                    'files_modified': self.count_modified_files(agent_dir),
                    'work_hours': self.estimate_work_hours(agent_dir)
                }
                
                todays_work['agent_activity'][agent_id] = activity
                todays_work['total_commits'] += activity['commits']
                todays_work['files_modified'] += activity['files_modified']
        
        print(f"Workflows: {len(todays_work['workflows']['completed'])} completed, {len(todays_work['workflows']['in_progress'])} in progress")
        print(f"Agent Activity: {todays_work['total_commits']} commits, {todays_work['files_modified']} files modified")
        
        return todays_work
    
    def calculate_workflow_progress(self, workflow):
        """Calculate workflow completion percentage"""
        if 'subtasks' not in workflow:
            return 0
        
        total = len(workflow['subtasks'])
        completed = sum(1 for task in workflow['subtasks'] if task.get('status') == 'completed')
        
        return int((completed / total) * 100) if total > 0 else 0
    
    def analyze_productivity(self):
        """Analyze today's productivity metrics"""
        metrics = {
            'total_active_hours': 0,
            'collaboration_score': 'Unknown',
            'efficiency_rating': 'Unknown',
            'peak_activity_hours': [],
            'agent_performance': {}
        }
        
        # Analyze agent performance
        agents_parent = self.workspace_root.parent / "agents"
        if agents_parent.exists():
            total_hours = 0
            active_agents = 0
            
            for agent_dir in agents_parent.glob("agent-*"):
                agent_id = agent_dir.name
                work_hours = self.estimate_work_hours(agent_dir)
                commits = self.count_agent_commits(agent_dir)
                
                if work_hours > 0:
                    active_agents += 1
                    total_hours += work_hours
                    
                    # Calculate efficiency (commits per hour)
                    efficiency = commits / work_hours if work_hours > 0 else 0
                    
                    metrics['agent_performance'][agent_id] = {
                        'hours': work_hours,
                        'commits': commits,
                        'efficiency': efficiency
                    }
            
            metrics['total_active_hours'] = total_hours
            
            # Overall efficiency rating
            if active_agents > 0:
                avg_efficiency = sum(perf['efficiency'] for perf in metrics['agent_performance'].values()) / active_agents
                if avg_efficiency > 2:
                    metrics['efficiency_rating'] = 'Excellent'
                elif avg_efficiency > 1:
                    metrics['efficiency_rating'] = 'Good'
                elif avg_efficiency > 0.5:
                    metrics['efficiency_rating'] = 'Fair'
                else:
                    metrics['efficiency_rating'] = 'Needs Improvement'
        
        # Collaboration score based on inter-agent communication
        metrics['collaboration_score'] = self.calculate_collaboration_score()
        
        print(f"Total Active Hours: {metrics['total_active_hours']:.1f}")
        print(f"Efficiency Rating: {metrics['efficiency_rating']}")
        print(f"Collaboration Score: {metrics['collaboration_score']}")
        
        return metrics
    
    def calculate_collaboration_score(self):
        """Calculate collaboration score based on communication"""
        # Check for inter-agent messages in communication queue
        processed_dir = self.comm_dir / "queue" / "processed"
        
        if not processed_dir.exists():
            return "No Data"
        
        inter_agent_messages = 0
        today = datetime.now().date()
        
        for msg_file in processed_dir.glob("*.json"):
            try:
                file_date = datetime.fromtimestamp(msg_file.stat().st_mtime).date()
                if file_date == today:
                    with open(msg_file, 'r', encoding='utf-8') as f:
                        msg = json.load(f)
                    
                    if (msg.get('from', '').startswith('agent-') and 
                        msg.get('to', '').startswith('agent-')):
                        inter_agent_messages += 1
            except Exception:
                pass
        
        if inter_agent_messages > 20:
            return "Excellent"
        elif inter_agent_messages > 10:
            return "Good"
        elif inter_agent_messages > 5:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def identify_issues(self):
        """Identify issues and blockers from today"""
        issues = {
            'errors': [],
            'warnings': [],
            'performance_issues': [],
            'stale_files': [],
            'disk_usage_high': False
        }
        
        # Check disk usage
        try:
            total, used, free = shutil.disk_usage(self.workspace_root)
            usage_percent = (used / total) * 100
            if usage_percent > 80:
                issues['disk_usage_high'] = True
                issues['warnings'].append(f"High disk usage: {usage_percent:.1f}%")
        except Exception:
            pass
        
        # Check for stale files in communication queue
        queue_dir = self.comm_dir / "queue"
        if queue_dir.exists():
            for msg_file in queue_dir.glob("*.json"):
                try:
                    age_hours = (datetime.now() - datetime.fromtimestamp(msg_file.stat().st_mtime)).total_seconds() / 3600
                    if age_hours > 2:  # Messages older than 2 hours
                        issues['stale_files'].append({
                            'file': msg_file.name,
                            'age_hours': round(age_hours, 1)
                        })
                except Exception:
                    pass
        
        # Check housekeeper status
        hk_log = self.workspace_root / "housekeeper" / "cleanup.log"
        if hk_log.exists():
            try:
                mod_time = datetime.fromtimestamp(hk_log.stat().st_mtime)
                hours_since_hk = (datetime.now() - mod_time).total_seconds() / 3600
                if hours_since_hk > 12:
                    issues['warnings'].append(f"Housekeeper hasn't run in {hours_since_hk:.1f} hours")
            except Exception:
                pass
        
        issue_count = len(issues['errors']) + len(issues['warnings']) + len(issues['stale_files'])
        print(f"Issues found: {issue_count} total")
        
        for warning in issues['warnings']:
            print(f"  ⚠️ {warning}")
        
        if issues['stale_files']:
            print(f"  📁 {len(issues['stale_files'])} stale communication files")
        
        return issues
    
    def plan_tomorrow(self, todays_work, issues):
        """Plan priorities for tomorrow"""
        tomorrow_plan = []
        
        # Continue in-progress workflows
        for workflow in todays_work['workflows']['in_progress']:
            tomorrow_plan.append({
                'type': 'continue_workflow',
                'description': f"Continue {workflow['description']} ({workflow['progress']}% complete)",
                'workflow_id': workflow['id'],
                'priority': 'high'
            })
        
        # Address issues
        if issues['errors']:
            tomorrow_plan.append({
                'type': 'fix_errors',
                'description': f"Address {len(issues['errors'])} errors from today",
                'priority': 'critical'
            })
        
        if issues['warnings']:
            tomorrow_plan.append({
                'type': 'resolve_warnings',
                'description': f"Resolve {len(issues['warnings'])} system warnings",
                'priority': 'medium'
            })
        
        # Cleanup tasks
        if issues['stale_files']:
            tomorrow_plan.append({
                'type': 'cleanup',
                'description': f"Clean up {len(issues['stale_files'])} stale files",
                'priority': 'low'
            })
        
        # System maintenance if high disk usage
        if issues['disk_usage_high']:
            tomorrow_plan.append({
                'type': 'maintenance',
                'description': "System cleanup and disk space optimization",
                'priority': 'high'
            })
        
        # If no specific tasks, add general productivity
        if not tomorrow_plan:
            tomorrow_plan.append({
                'type': 'new_work',
                'description': "Focus on new feature development and improvements",
                'priority': 'normal'
            })
        
        print(f"Tomorrow's plan: {len(tomorrow_plan)} priorities identified")
        for plan in tomorrow_plan[:3]:
            print(f"  • [{plan['priority'].upper()}] {plan['description']}")
        
        return tomorrow_plan
    
    def archive_daily_data(self):
        """Archive today's data"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        month_dir = self.archive_dir / datetime.now().strftime('%Y-%m')
        today_archive = month_dir / today_str
        today_archive.mkdir(parents=True, exist_ok=True)
        
        archive_summary = {
            'archived_files': 0,
            'archive_location': str(today_archive),
            'compressed_size': 0
        }
        
        # Archive processed communication files
        processed_dir = self.comm_dir / "queue" / "processed"
        if processed_dir.exists():
            comm_archive = today_archive / "communication"
            comm_archive.mkdir(exist_ok=True)
            
            for msg_file in processed_dir.glob("*.json"):
                try:
                    file_date = datetime.fromtimestamp(msg_file.stat().st_mtime).date()
                    if file_date == datetime.now().date():
                        shutil.move(str(msg_file), str(comm_archive / msg_file.name))
                        archive_summary['archived_files'] += 1
                except Exception:
                    pass
        
        # Archive daily context files from agents
        agents_parent = self.workspace_root.parent / "agents"
        if agents_parent.exists():
            agent_archive = today_archive / "agent_contexts"
            agent_archive.mkdir(exist_ok=True)
            
            for agent_dir in agents_parent.glob("agent-*"):
                daily_context = agent_dir / f"DAILY_CONTEXT_{datetime.now().strftime('%Y%m%d')}.md"
                if daily_context.exists():
                    try:
                        shutil.copy2(str(daily_context), str(agent_archive / f"{agent_dir.name}_{daily_context.name}"))
                        archive_summary['archived_files'] += 1
                    except Exception:
                        pass
        
        print(f"Archived {archive_summary['archived_files']} files to {today_archive}")
        
        return archive_summary
    
    def create_executive_summary(self, shutdown_summary):
        """Create executive summary"""
        date = shutdown_summary['date']
        todays_work = shutdown_summary['todays_work']
        productivity = shutdown_summary['productivity_metrics']
        issues = shutdown_summary['issues']
        
        # Count active agents
        active_agents = sum(1 for status in shutdown_summary['agent_status'].values() 
                          if status.get('active_today', False))
        
        # Count completed work
        completed_workflows = len(todays_work['workflows']['completed'])
        in_progress_workflows = len(todays_work['workflows']['in_progress'])
        total_commits = todays_work['total_commits']
        
        summary = f"""Daily Summary for {date}:
• Active Agents: {active_agents}
• Workflows Completed: {completed_workflows}
• Workflows In Progress: {in_progress_workflows}
• Total Commits: {total_commits}
• Total Active Hours: {productivity['total_active_hours']:.1f}
• Efficiency Rating: {productivity['efficiency_rating']}
• Collaboration Score: {productivity['collaboration_score']}"""
        
        # Add warnings if any
        issue_count = len(issues['errors']) + len(issues['warnings'])
        if issue_count > 0:
            summary += f"\n• ⚠️ Issues to Address: {issue_count}"
        
        return summary
    
    def save_shutdown_record(self, shutdown_summary):
        """Save shutdown record"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # JSON record
        shutdown_file = self.standup_dir / f"shutdown_{date_str}.json"
        with open(shutdown_file, 'w', encoding='utf-8') as f:
            json.dump(shutdown_summary, f, indent=2)
        
        # Human-readable summary
        summary_file = self.standup_dir / f"daily_summary_{date_str}.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Daily Summary - {date_str}\n\n")
            f.write(shutdown_summary['executive_summary'])
            f.write("\n\n## Today's Accomplishments\n")
            
            for workflow in shutdown_summary['todays_work']['workflows']['completed']:
                f.write(f"✅ {workflow['description']}\n")
            
            if shutdown_summary['todays_work']['workflows']['in_progress']:
                f.write("\n## Work In Progress\n")
                for workflow in shutdown_summary['todays_work']['workflows']['in_progress']:
                    f.write(f"🔄 {workflow['description']} ({workflow.get('progress', 0)}%)\n")
            
            f.write("\n## Tomorrow's Priorities\n")
            for plan in shutdown_summary['planned_next']:
                f.write(f"• **[{plan['priority'].upper()}]** {plan['description']}\n")
            
            if shutdown_summary['issues']['warnings']:
                f.write("\n## Issues to Address\n")
                for warning in shutdown_summary['issues']['warnings']:
                    f.write(f"⚠️ {warning}\n")
            
            # Agent performance
            f.write("\n## Agent Performance\n")
            for agent_id, status in shutdown_summary['agent_status'].items():
                if status.get('active_today'):
                    hours = status.get('estimated_work_hours', 0)
                    commits = status.get('commits_today', 0)
                    f.write(f"• {agent_id}: {hours:.1f}h, {commits} commits\n")
        
        print(f"\nShutdown records saved:")
        print(f"  📄 Data: {shutdown_file}")
        print(f"  📝 Summary: {summary_file}")
    
    def cleanup_and_prepare(self):
        """Cleanup and prepare for tomorrow"""
        cleanup_tasks = []
        
        # Clear any lock files
        for lock_file in self.workspace_root.rglob("*.lock"):
            try:
                lock_file.unlink()
                cleanup_tasks.append(f"Removed lock file: {lock_file.name}")
            except Exception:
                pass
        
        # Clean old daily context files (keep last 3 days)
        agents_parent = self.workspace_root.parent / "agents"
        if agents_parent.exists():
            cutoff_date = datetime.now() - timedelta(days=3)
            
            for agent_dir in agents_parent.glob("agent-*"):
                for context_file in agent_dir.glob("DAILY_CONTEXT_*.md"):
                    try:
                        file_date = datetime.fromtimestamp(context_file.stat().st_mtime)
                        if file_date < cutoff_date:
                            context_file.unlink()
                            cleanup_tasks.append(f"Removed old context: {context_file.name}")
                    except Exception:
                        pass
        
        # Prepare tomorrow's context directory
        tomorrow_context_dir = self.memory_dir / "tomorrow"
        tomorrow_context_dir.mkdir(exist_ok=True)
        
        print(f"Cleanup completed: {len(cleanup_tasks)} tasks")
        print("System prepared for tomorrow's standup")


if __name__ == "__main__":
    print("🌆 Jarvis Evening Shutdown System")
    shutdown = JarvisShutdown()
    shutdown.run_shutdown()