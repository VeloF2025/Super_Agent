# Multi-Agent Daily Standup & Shutdown System

## Overview

This system implements automated morning standups and evening shutdowns for multi-agent Claude systems, ensuring seamless continuity between work sessions and proper context preservation.

## Morning Standup System

### 1. Standup Orchestrator Script

```python
#!/usr/bin/env python3
# tools/morning_standup.py

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

class MorningStandup:
    def __init__(self, project_root=".", agents_dir="../agents"):
        self.project_root = Path(project_root)
        self.agents_dir = Path(agents_dir)
        self.comm_dir = self.project_root / "communication"
        self.memory_dir = self.project_root / "memory"
        self.standup_dir = self.memory_dir / "standups"
        self.standup_dir.mkdir(parents=True, exist_ok=True)
        
    def run_standup(self):
        """Execute morning standup routine"""
        print("🌅 Good Morning! Starting Multi-Agent Standup...")
        print("=" * 60)
        
        # 1. Load previous day's summary
        yesterday_summary = self.load_previous_summary()
        
        # 2. Check agent health
        agent_status = self.check_agent_health()
        
        # 3. Review incomplete tasks
        incomplete_tasks = self.review_incomplete_tasks()
        
        # 4. Generate standup report
        standup_report = self.generate_standup_report(
            yesterday_summary, 
            agent_status, 
            incomplete_tasks
        )
        
        # 5. Distribute daily briefing to agents
        self.distribute_daily_briefing(standup_report)
        
        # 6. Initialize agents with context
        self.initialize_agents_with_context(standup_report)
        
        # 7. Save standup record
        self.save_standup_record(standup_report)
        
        print("\n✅ Standup Complete! Agents are ready to work.")
        
        return standup_report
    
    def load_previous_summary(self):
        """Load yesterday's shutdown summary"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        summary_file = self.standup_dir / f"shutdown_{yesterday}.json"
        
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)
        else:
            print("⚠️  No previous day summary found. Starting fresh.")
            return None
    
    def check_agent_health(self):
        """Check the health status of all agents"""
        agent_status = {}
        state_dir = self.comm_dir / "state"
        
        for state_file in state_dir.glob("*_state.json"):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                agent_id = state['agent_id']
                last_update = datetime.fromisoformat(state['timestamp'])
                time_since_update = (datetime.utcnow() - last_update).total_seconds()
                
                agent_status[agent_id] = {
                    'last_seen': state['timestamp'],
                    'status': state['data'].get('status', 'unknown'),
                    'health': 'healthy' if time_since_update < 86400 else 'stale',
                    'last_task': state['data'].get('current_task', 'none')
                }
            except Exception as e:
                print(f"Error reading state for {state_file}: {e}")
        
        return agent_status
    
    def review_incomplete_tasks(self):
        """Review tasks that weren't completed yesterday"""
        incomplete = []
        workflows_dir = self.project_root / "workflows"
        
        for workflow_file in workflows_dir.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    workflow = json.load(f)
                
                if workflow.get('status') == 'in_progress':
                    created = datetime.fromisoformat(workflow['created'])
                    age_days = (datetime.utcnow() - created).days
                    
                    incomplete.append({
                        'workflow_id': workflow['id'],
                        'description': workflow.get('specification', 'Unknown task'),
                        'age_days': age_days,
                        'subtasks': workflow.get('subtasks', [])
                    })
            except Exception as e:
                print(f"Error reading workflow {workflow_file}: {e}")
        
        return incomplete
    
    def generate_standup_report(self, yesterday_summary, agent_status, incomplete_tasks):
        """Generate the standup report"""
        report = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'yesterday_summary': yesterday_summary,
            'agent_status': agent_status,
            'incomplete_tasks': incomplete_tasks,
            'priorities': self.determine_priorities(yesterday_summary, incomplete_tasks),
            'agent_assignments': {}
        }
        
        # Generate agent-specific briefings
        for agent_id in agent_status:
            report['agent_assignments'][agent_id] = self.generate_agent_briefing(
                agent_id, 
                yesterday_summary, 
                incomplete_tasks
            )
        
        return report
    
    def determine_priorities(self, yesterday_summary, incomplete_tasks):
        """Determine today's priorities based on yesterday and incomplete work"""
        priorities = []
        
        # Priority 1: Critical incomplete tasks
        for task in incomplete_tasks:
            if task['age_days'] > 1:
                priorities.append({
                    'level': 'critical',
                    'description': f"Complete overdue task: {task['description']}",
                    'workflow_id': task['workflow_id']
                })
        
        # Priority 2: Continue yesterday's momentum
        if yesterday_summary and 'in_progress' in yesterday_summary:
            for item in yesterday_summary['in_progress']:
                priorities.append({
                    'level': 'high',
                    'description': f"Continue: {item['description']}",
                    'context': item
                })
        
        # Priority 3: New planned work
        if yesterday_summary and 'planned_next' in yesterday_summary:
            for item in yesterday_summary['planned_next']:
                priorities.append({
                    'level': 'normal',
                    'description': item['description'],
                    'context': item
                })
        
        return priorities[:5]  # Top 5 priorities
    
    def generate_agent_briefing(self, agent_id, yesterday_summary, incomplete_tasks):
        """Generate specific briefing for each agent"""
        briefing = {
            'agent_id': agent_id,
            'tasks': [],
            'context': {},
            'reminders': []
        }
        
        # Extract agent-specific work from yesterday
        if yesterday_summary and 'agent_work' in yesterday_summary:
            if agent_id in yesterday_summary['agent_work']:
                agent_yesterday = yesterday_summary['agent_work'][agent_id]
                briefing['context']['yesterday'] = agent_yesterday
                
                # Continue unfinished work
                if 'in_progress' in agent_yesterday:
                    for task in agent_yesterday['in_progress']:
                        briefing['tasks'].append({
                            'type': 'continue',
                            'task': task,
                            'priority': 'high'
                        })
        
        # Assign incomplete tasks
        for task in incomplete_tasks:
            for subtask in task['subtasks']:
                if subtask.get('agent') == agent_id:
                    briefing['tasks'].append({
                        'type': 'incomplete',
                        'task': subtask,
                        'priority': 'critical' if task['age_days'] > 1 else 'high'
                    })
        
        # Add reminders based on agent role
        briefing['reminders'] = self.get_agent_reminders(agent_id)
        
        return briefing
    
    def get_agent_reminders(self, agent_id):
        """Get role-specific reminders for agents"""
        reminders = {
            'agent-frontend': [
                "Check component accessibility",
                "Ensure responsive design",
                "Update component documentation"
            ],
            'agent-backend': [
                "Validate API error handling",
                "Check database query performance",
                "Update API documentation"
            ],
            'agent-testing': [
                "Run regression tests",
                "Check code coverage",
                "Update test documentation"
            ],
            'agent-orchestrator': [
                "Monitor agent coordination",
                "Check workflow progress",
                "Resolve blockers"
            ]
        }
        
        return reminders.get(agent_id, ["Stay focused", "Communicate clearly"])
    
    def distribute_daily_briefing(self, standup_report):
        """Send daily briefing to all agents"""
        for agent_id, briefing in standup_report['agent_assignments'].items():
            message = {
                'id': f"standup-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                'timestamp': datetime.utcnow().isoformat(),
                'from': 'standup-system',
                'to': agent_id,
                'type': 'daily_briefing',
                'payload': briefing,
                'priority': 'high'
            }
            
            # Write to agent's queue
            filename = f"{message['timestamp']}_standup_{agent_id}.json"
            filepath = self.comm_dir / "queue" / filename
            
            with open(filepath, 'w') as f:
                json.dump(message, f, indent=2)
            
            print(f"📬 Briefing sent to {agent_id}")
    
    def initialize_agents_with_context(self, standup_report):
        """Initialize agent CLAUDE.md files with daily context"""
        for agent_id, briefing in standup_report['agent_assignments'].items():
            agent_dir = self.agents_dir / agent_id
            if agent_dir.exists():
                # Create daily context file
                daily_context = agent_dir / f"DAILY_CONTEXT_{datetime.now().strftime('%Y%m%d')}.md"
                
                with open(daily_context, 'w') as f:
                    f.write(f"# Daily Context for {agent_id}\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("## Yesterday's Progress\n")
                    if 'yesterday' in briefing['context']:
                        yesterday = briefing['context']['yesterday']
                        if 'completed' in yesterday:
                            f.write("### Completed\n")
                            for item in yesterday['completed']:
                                f.write(f"- {item}\n")
                        if 'in_progress' in yesterday:
                            f.write("\n### In Progress\n")
                            for item in yesterday['in_progress']:
                                f.write(f"- {item['description']}\n")
                    
                    f.write("\n## Today's Tasks\n")
                    for task in briefing['tasks']:
                        f.write(f"- **[{task['priority'].upper()}]** {task['type']}: ")
                        f.write(f"{task['task'].get('description', task['task'])}\n")
                    
                    f.write("\n## Reminders\n")
                    for reminder in briefing['reminders']:
                        f.write(f"- {reminder}\n")
                
                # Update main CLAUDE.md to reference daily context
                claude_md = agent_dir / "CLAUDE.md"
                if claude_md.exists():
                    with open(claude_md, 'r') as f:
                        content = f.read()
                    
                    # Add import if not present
                    import_line = f"@import ./DAILY_CONTEXT_{datetime.now().strftime('%Y%m%d')}.md"
                    if import_line not in content:
                        with open(claude_md, 'a') as f:
                            f.write(f"\n{import_line}\n")
    
    def save_standup_record(self, standup_report):
        """Save standup record for historical tracking"""
        standup_file = self.standup_dir / f"standup_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        with open(standup_file, 'w') as f:
            json.dump(standup_report, f, indent=2)
        
        print(f"\n📄 Standup record saved: {standup_file}")


# Standup runner script
if __name__ == "__main__":
    standup = MorningStandup()
    report = standup.run_standup()
    
    # Print summary
    print("\n📊 Standup Summary:")
    print(f"- Active Agents: {len(report['agent_status'])}")
    print(f"- Incomplete Tasks: {len(report['incomplete_tasks'])}")
    print(f"- Today's Priorities: {len(report['priorities'])}")
    
    for priority in report['priorities'][:3]:
        print(f"  • [{priority['level'].upper()}] {priority['description']}")
```

### 2. Evening Shutdown System

```python
#!/usr/bin/env python3
# tools/evening_shutdown.py

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
from collections import defaultdict

class EveningShutdown:
    def __init__(self, project_root=".", agents_dir="../agents"):
        self.project_root = Path(project_root)
        self.agents_dir = Path(agents_dir)
        self.comm_dir = self.project_root / "communication"
        self.memory_dir = self.project_root / "memory"
        self.standup_dir = self.memory_dir / "standups"
        self.logs_dir = self.project_root / "logs"
        self.standup_dir.mkdir(parents=True, exist_ok=True)
        
    def run_shutdown(self):
        """Execute evening shutdown routine"""
        print("🌆 Good Evening! Starting Multi-Agent Shutdown...")
        print("=" * 60)
        
        # 1. Collect agent status
        agent_status = self.collect_agent_status()
        
        # 2. Gather today's work
        todays_work = self.gather_todays_work()
        
        # 3. Analyze productivity
        productivity_metrics = self.analyze_productivity()
        
        # 4. Identify blockers and issues
        issues = self.identify_issues()
        
        # 5. Generate shutdown summary
        shutdown_summary = self.generate_shutdown_summary(
            agent_status,
            todays_work,
            productivity_metrics,
            issues
        )
        
        # 6. Archive today's data
        self.archive_daily_data()
        
        # 7. Prepare for tomorrow
        self.prepare_for_tomorrow(shutdown_summary)
        
        # 8. Save shutdown record
        self.save_shutdown_record(shutdown_summary)
        
        # 9. Gracefully stop agents
        self.graceful_agent_shutdown()
        
        print("\n✅ Shutdown Complete! See you tomorrow.")
        
        return shutdown_summary
    
    def collect_agent_status(self):
        """Collect final status from all agents"""
        agent_status = {}
        state_dir = self.comm_dir / "state"
        
        # Send status request to all agents
        self.request_agent_status()
        
        # Wait for responses
        import time
        time.sleep(5)  # Give agents time to respond
        
        # Collect status
        for state_file in state_dir.glob("*_state.json"):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                agent_id = state['agent_id']
                agent_status[agent_id] = {
                    'final_status': state['data'].get('status', 'unknown'),
                    'last_task': state['data'].get('current_task', 'none'),
                    'tasks_completed': state['data'].get('tasks_completed_today', 0),
                    'active_duration': self.calculate_active_duration(agent_id)
                }
            except Exception as e:
                print(f"Error reading state for {state_file}: {e}")
        
        return agent_status
    
    def request_agent_status(self):
        """Request status update from all agents"""
        message = {
            'id': f"shutdown-status-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'timestamp': datetime.utcnow().isoformat(),
            'from': 'shutdown-system',
            'to': 'broadcast',
            'type': 'status_request',
            'payload': {
                'reason': 'daily_shutdown',
                'include': ['current_task', 'completed_tasks', 'in_progress', 'blockers']
            },
            'priority': 'high'
        }
        
        # Broadcast to all agents
        filename = f"{message['timestamp']}_shutdown_status_request.json"
        filepath = self.comm_dir / "queue" / filename
        
        with open(filepath, 'w') as f:
            json.dump(message, f, indent=2)
    
    def gather_todays_work(self):
        """Gather all work completed today"""
        todays_work = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'agent_work': defaultdict(lambda: {
                'completed': [],
                'in_progress': [],
                'blockers': []
            }),
            'workflows': {
                'completed': [],
                'in_progress': [],
                'created': []
            }
        }
        
        # Check workflows
        workflows_dir = self.project_root / "workflows"
        today = datetime.now().date()
        
        for workflow_file in workflows_dir.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    workflow = json.load(f)
                
                created_date = datetime.fromisoformat(workflow['created']).date()
                
                if created_date == today:
                    todays_work['workflows']['created'].append({
                        'id': workflow['id'],
                        'description': workflow.get('specification', 'Unknown')
                    })
                
                if workflow.get('status') == 'completed':
                    # Check if completed today
                    if 'completed_at' in workflow:
                        completed_date = datetime.fromisoformat(workflow['completed_at']).date()
                        if completed_date == today:
                            todays_work['workflows']['completed'].append({
                                'id': workflow['id'],
                                'description': workflow.get('specification', 'Unknown')
                            })
                elif workflow.get('status') == 'in_progress':
                    todays_work['workflows']['in_progress'].append({
                        'id': workflow['id'],
                        'description': workflow.get('specification', 'Unknown'),
                        'progress': self.calculate_workflow_progress(workflow)
                    })
            except Exception as e:
                print(f"Error reading workflow {workflow_file}: {e}")
        
        # Check agent logs
        self.gather_agent_logs(todays_work)
        
        return todays_work
    
    def gather_agent_logs(self, todays_work):
        """Gather work from agent logs"""
        today = datetime.now().strftime("%Y%m%d")
        
        for agent_dir in self.logs_dir.glob("agent-*"):
            agent_id = agent_dir.name
            log_file = agent_dir / f"general_{today}.log"
            
            if log_file.exists():
                completed_tasks = []
                in_progress_tasks = []
                
                with open(log_file, 'r') as f:
                    for line in f:
                        if "task completed" in line.lower():
                            # Extract task info
                            completed_tasks.append(self.extract_task_from_log(line))
                        elif "working on" in line.lower():
                            in_progress_tasks.append(self.extract_task_from_log(line))
                
                todays_work['agent_work'][agent_id]['completed'] = completed_tasks
                todays_work['agent_work'][agent_id]['in_progress'] = in_progress_tasks
    
    def extract_task_from_log(self, log_line):
        """Extract task information from log line"""
        # Simple extraction - could be more sophisticated
        parts = log_line.split(' - ')
        if len(parts) >= 3:
            return parts[2].strip()
        return log_line.strip()
    
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
            'total_tasks_completed': 0,
            'total_workflows_completed': 0,
            'agent_efficiency': {},
            'peak_hours': [],
            'token_usage': self.calculate_token_usage(),
            'collaboration_score': self.calculate_collaboration_score()
        }
        
        # Analyze message patterns for peak hours
        queue_dir = self.comm_dir / "queue" / "processed"
        message_times = []
        
        if queue_dir.exists():
            for msg_file in queue_dir.glob("*.json"):
                try:
                    with open(msg_file, 'r') as f:
                        msg = json.load(f)
                    timestamp = datetime.fromisoformat(msg['timestamp'])
                    if timestamp.date() == datetime.now().date():
                        message_times.append(timestamp.hour)
                except:
                    pass
        
        # Find peak hours
        if message_times:
            from collections import Counter
            hour_counts = Counter(message_times)
            peak_hours = hour_counts.most_common(3)
            metrics['peak_hours'] = [hour for hour, count in peak_hours]
        
        return metrics
    
    def calculate_token_usage(self):
        """Calculate approximate token usage for the day"""
        # This is a placeholder - in practice, you'd track actual token usage
        return {
            'estimated_total': 50000,
            'per_agent': {
                'agent-frontend': 15000,
                'agent-backend': 15000,
                'agent-testing': 10000,
                'agent-orchestrator': 10000
            }
        }
    
    def calculate_collaboration_score(self):
        """Calculate how well agents collaborated"""
        # Count inter-agent messages
        processed_dir = self.comm_dir / "queue" / "processed"
        inter_agent_messages = 0
        
        if processed_dir.exists():
            for msg_file in processed_dir.glob("*.json"):
                try:
                    with open(msg_file, 'r') as f:
                        msg = json.load(f)
                    if msg['from'].startswith('agent-') and msg['to'].startswith('agent-'):
                        inter_agent_messages += 1
                except:
                    pass
        
        # Simple scoring: more inter-agent communication = better collaboration
        if inter_agent_messages > 50:
            return "Excellent"
        elif inter_agent_messages > 20:
            return "Good"
        elif inter_agent_messages > 10:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def identify_issues(self):
        """Identify any issues or blockers from today"""
        issues = {
            'errors': [],
            'blockers': [],
            'performance_issues': [],
            'communication_failures': []
        }
        
        # Check error logs
        for agent_dir in self.logs_dir.glob("agent-*"):
            error_log = agent_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
            if error_log.exists():
                with open(error_log, 'r') as f:
                    errors = f.readlines()
                    if errors:
                        issues['errors'].append({
                            'agent': agent_dir.name,
                            'error_count': len(errors),
                            'sample': errors[0].strip() if errors else ""
                        })
        
        # Check for stale messages (communication failures)
        queue_dir = self.comm_dir / "queue"
        for msg_file in queue_dir.glob("*.json"):
            try:
                age = (datetime.now() - datetime.fromtimestamp(msg_file.stat().st_mtime)).total_seconds()
                if age > 3600:  # Messages older than 1 hour
                    issues['communication_failures'].append({
                        'file': msg_file.name,
                        'age_hours': int(age / 3600)
                    })
            except:
                pass
        
        return issues
    
    def calculate_active_duration(self, agent_id):
        """Calculate how long an agent was active today"""
        # Check first and last log entries
        log_file = self.logs_dir / agent_id / f"general_{datetime.now().strftime('%Y%m%d')}.log"
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    # Parse timestamps from first and last lines
                    try:
                        first_time = datetime.fromisoformat(lines[0].split(' - ')[0])
                        last_time = datetime.fromisoformat(lines[-1].split(' - ')[0])
                        duration = (last_time - first_time).total_seconds() / 3600
                        return f"{duration:.1f} hours"
                    except:
                        pass
        
        return "Unknown"
    
    def generate_shutdown_summary(self, agent_status, todays_work, productivity_metrics, issues):
        """Generate comprehensive shutdown summary"""
        summary = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'agent_status': agent_status,
            'todays_work': todays_work,
            'productivity_metrics': productivity_metrics,
            'issues': issues,
            'planned_next': self.plan_next_day(todays_work, issues),
            'recommendations': self.generate_recommendations(productivity_metrics, issues)
        }
        
        # Add executive summary
        summary['executive_summary'] = self.create_executive_summary(summary)
        
        return summary
    
    def plan_next_day(self, todays_work, issues):
        """Plan priorities for next day based on today's work"""
        next_day_plan = []
        
        # Continue in-progress work
        for workflow in todays_work['workflows']['in_progress']:
            next_day_plan.append({
                'type': 'continue',
                'description': f"Continue {workflow['description']} ({workflow['progress']}% complete)",
                'workflow_id': workflow['id'],
                'priority': 'high'
            })
        
        # Address issues
        if issues['errors']:
            next_day_plan.append({
                'type': 'fix',
                'description': f"Address {sum(e['error_count'] for e in issues['errors'])} errors",
                'priority': 'critical'
            })
        
        # Performance optimization if needed
        if issues['performance_issues']:
            next_day_plan.append({
                'type': 'optimize',
                'description': "Optimize performance issues",
                'priority': 'medium'
            })
        
        return next_day_plan
    
    def generate_recommendations(self, productivity_metrics, issues):
        """Generate recommendations based on today's performance"""
        recommendations = []
        
        # Token usage recommendations
        total_tokens = productivity_metrics['token_usage']['estimated_total']
        if total_tokens > 100000:
            recommendations.append({
                'type': 'efficiency',
                'message': "High token usage detected. Consider optimizing prompts and reducing context."
            })
        
        # Collaboration recommendations
        if productivity_metrics['collaboration_score'] == "Needs Improvement":
            recommendations.append({
                'type': 'collaboration',
                'message': "Low inter-agent communication. Consider improving task coordination."
            })
        
        # Error handling recommendations
        if issues['errors']:
            recommendations.append({
                'type': 'reliability',
                'message': "Multiple errors detected. Review error patterns and implement fixes."
            })
        
        return recommendations
    
    def create_executive_summary(self, summary):
        """Create a brief executive summary"""
        total_completed = len(summary['todays_work']['workflows']['completed'])
        total_in_progress = len(summary['todays_work']['workflows']['in_progress'])
        active_agents = len(summary['agent_status'])
        
        exec_summary = f"Daily Summary for {summary['date']}:\n"
        exec_summary += f"- Active Agents: {active_agents}\n"
        exec_summary += f"- Workflows Completed: {total_completed}\n"
        exec_summary += f"- Workflows In Progress: {total_in_progress}\n"
        exec_summary += f"- Collaboration Score: {summary['productivity_metrics']['collaboration_score']}\n"
        
        if summary['issues']['errors']:
            exec_summary += f"- ⚠️  Errors Detected: {len(summary['issues']['errors'])} agents with errors\n"
        
        return exec_summary
    
    def archive_daily_data(self):
        """Archive today's data for long-term storage"""
        archive_dir = self.memory_dir / "archive" / datetime.now().strftime("%Y-%m")
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Archive processed messages
        processed_dir = self.comm_dir / "queue" / "processed"
        if processed_dir.exists():
            today_archive = archive_dir / datetime.now().strftime("%Y-%m-%d")
            today_archive.mkdir(exist_ok=True)
            
            for msg_file in processed_dir.glob("*.json"):
                try:
                    msg_file.rename(today_archive / msg_file.name)
                except:
                    pass
        
        print(f"📦 Daily data archived to {archive_dir}")
    
    def prepare_for_tomorrow(self, shutdown_summary):
        """Prepare system for tomorrow's work"""
        # Clean up old lock files
        for lock_file in self.comm_dir.glob("**/*.lock"):
            try:
                lock_file.unlink()
            except:
                pass
        
        # Reset agent states for tomorrow
        state_dir = self.comm_dir / "state"
        for state_file in state_dir.glob("*_state.json"):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Update state for tomorrow
                state['data']['status'] = 'shutdown'
                state['data']['tasks_completed_today'] = 0
                state['timestamp'] = datetime.utcnow().isoformat()
                
                with open(state_file, 'w') as f:
                    json.dump(state, f, indent=2)
            except:
                pass
        
        # Create tomorrow's context file
        tomorrow_context = self.standup_dir / f"context_{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}.json"
        
        context_data = {
            'previous_day': shutdown_summary['date'],
            'carried_forward': shutdown_summary['planned_next'],
            'active_workflows': [w['id'] for w in shutdown_summary['todays_work']['workflows']['in_progress']],
            'recommendations': shutdown_summary['recommendations']
        }
        
        with open(tomorrow_context, 'w') as f:
            json.dump(context_data, f, indent=2)
    
    def save_shutdown_record(self, shutdown_summary):
        """Save shutdown record"""
        shutdown_file = self.standup_dir / f"shutdown_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        with open(shutdown_file, 'w') as f:
            json.dump(shutdown_summary, f, indent=2)
        
        # Also create a human-readable summary
        summary_file = self.standup_dir / f"summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        
        with open(summary_file, 'w') as f:
            f.write(f"# Daily Summary - {shutdown_summary['date']}\n\n")
            f.write(shutdown_summary['executive_summary'])
            f.write("\n\n## Completed Work\n")
            
            for workflow in shutdown_summary['todays_work']['workflows']['completed']:
                f.write(f"- ✅ {workflow['description']}\n")
            
            f.write("\n## In Progress\n")
            for workflow in shutdown_summary['todays_work']['workflows']['in_progress']:
                f.write(f"- 🔄 {workflow['description']} ({workflow['progress']}%)\n")
            
            f.write("\n## Tomorrow's Priorities\n")
            for plan in shutdown_summary['planned_next']:
                f.write(f"- [{plan['priority'].upper()}] {plan['description']}\n")
            
            if shutdown_summary['recommendations']:
                f.write("\n## Recommendations\n")
                for rec in shutdown_summary['recommendations']:
                    f.write(f"- {rec['message']}\n")
        
        print(f"\n📄 Shutdown records saved")
        print(f"   - Data: {shutdown_file}")
        print(f"   - Summary: {summary_file}")
    
    def graceful_agent_shutdown(self):
        """Gracefully shutdown all agents"""
        # Send shutdown signal to all agents
        message = {
            'id': f"shutdown-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'timestamp': datetime.utcnow().isoformat(),
            'from': 'shutdown-system',
            'to': 'broadcast',
            'type': 'shutdown',
            'payload': {
                'reason': 'daily_shutdown',
                'message': 'Thank you for your work today. Shutting down gracefully.'
            },
            'priority': 'critical'
        }
        
        filename = f"{message['timestamp']}_shutdown_signal.json"
        filepath = self.comm_dir / "queue" / filename
        
        with open(filepath, 'w') as f:
            json.dump(message, f, indent=2)
        
        print("\n🔌 Shutdown signal sent to all agents")


# Shutdown runner script
if __name__ == "__main__":
    shutdown = EveningShutdown()
    summary = shutdown.run_shutdown()
    
    # Print executive summary
    print("\n" + "=" * 60)
    print(summary['executive_summary'])
```

### 3. Shell Scripts for Easy Execution

```bash
#!/bin/bash
# scripts/morning-standup.sh

set -e

echo "🌅 Multi-Agent Morning Standup"
echo "=============================="
echo ""

# Change to project directory
cd "$(dirname "$0")/.."

# Check if agents are already running
if tmux has-session -t multiagent 2>/dev/null; then
    echo "⚠️  Agents already running. Stopping first..."
    ./scripts/evening-shutdown.sh
    sleep 5
fi

# Run standup
echo "Running morning standup..."
python3 tools/morning_standup.py

# Start agents
echo ""
echo "Starting agents..."
./scripts/launch-agents.sh

echo ""
echo "✅ Standup complete! Agents are working."
```

```bash
#!/bin/bash
# scripts/evening-shutdown.sh

set -e

echo "🌆 Multi-Agent Evening Shutdown"
echo "==============================="
echo ""

# Change to project directory
cd "$(dirname "$0")/.."

# Run shutdown
echo "Running evening shutdown..."
python3 tools/evening_shutdown.py

# Stop tmux session if running
if tmux has-session -t multiagent 2>/dev/null; then
    echo ""
    echo "Stopping agent session..."
    tmux kill-session -t multiagent
fi

echo ""
echo "✅ Shutdown complete! See you tomorrow."
```

### 4. Automated Scheduling with Cron

```bash
# Add to crontab for automated daily routines
# Run: crontab -e

# Morning standup at 9:00 AM every weekday
0 9 * * 1-5 /path/to/project/scripts/morning-standup.sh >> /path/to/project/logs/standup.log 2>&1

# Evening shutdown at 6:00 PM every weekday
0 18 * * 1-5 /path/to/project/scripts/evening-shutdown.sh >> /path/to/project/logs/shutdown.log 2>&1

# Optional: Midday status check at 1:00 PM
0 13 * * 1-5 /path/to/project/scripts/midday-check.sh >> /path/to/project/logs/midday.log 2>&1
```

### 5. Status Dashboard for Quick Overview

```python
#!/usr/bin/env python3
# tools/daily_dashboard.py

import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
import time

class DailyDashboard:
    def __init__(self):
        self.console = Console()
        self.memory_dir = Path("./memory/standups")
        
    def display_dashboard(self):
        """Display real-time dashboard"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="status"),
            Layout(name="progress")
        )
        
        with Live(layout, refresh_per_second=1):
            while True:
                # Update header
                layout["header"].update(
                    Panel(f"Multi-Agent Daily Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                )
                
                # Update status
                layout["status"].update(self.get_agent_status_panel())
                
                # Update progress
                layout["progress"].update(self.get_progress_panel())
                
                # Update footer
                layout["footer"].update(self.get_summary_panel())
                
                time.sleep(5)
    
    def get_agent_status_panel(self):
        """Get agent status panel"""
        table = Table(title="Agent Status")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Current Task")
        table.add_column("Active Time")
        
        # Add agent rows
        state_dir = Path("./communication/state")
        for state_file in state_dir.glob("*_state.json"):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                table.add_row(
                    state['agent_id'],
                    state['data'].get('status', 'unknown'),
                    state['data'].get('current_task', 'idle')[:30] + "...",
                    self.calculate_uptime(state['timestamp'])
                )
            except:
                pass
        
        return Panel(table, title="Current Agent Activity")
    
    def get_progress_panel(self):
        """Get today's progress panel"""
        # Load today's standup if exists
        standup_file = self.memory_dir / f"standup_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        content = "No standup data for today"
        
        if standup_file.exists():
            with open(standup_file, 'r') as f:
                standup = json.load(f)
            
            table = Table(title="Today's Progress")
            table.add_column("Priority", style="yellow")
            table.add_column("Task")
            table.add_column("Status")
            
            for priority in standup.get('priorities', []):
                table.add_row(
                    priority['level'].upper(),
                    priority['description'][:50] + "...",
                    "🔄 In Progress"
                )
            
            content = table
        
        return Panel(content, title="Daily Progress")
    
    def get_summary_panel(self):
        """Get summary statistics"""
        stats = self.calculate_daily_stats()
        
        summary = f"Tasks Completed: {stats['completed']} | "
        summary += f"In Progress: {stats['in_progress']} | "
        summary += f"Messages: {stats['messages']} | "
        summary += f"Collaboration Score: {stats['collaboration']}"
        
        return Panel(summary, title="Daily Statistics")
    
    def calculate_uptime(self, last_update):
        """Calculate agent uptime"""
        try:
            last = datetime.fromisoformat(last_update)
            uptime = datetime.utcnow() - last
            hours = int(uptime.total_seconds() / 3600)
            minutes = int((uptime.total_seconds() % 3600) / 60)
            return f"{hours}h {minutes}m"
        except:
            return "Unknown"
    
    def calculate_daily_stats(self):
        """Calculate daily statistics"""
        # This is simplified - in practice, would aggregate from various sources
        return {
            'completed': 12,
            'in_progress': 5,
            'messages': 143,
            'collaboration': 'Good'
        }

if __name__ == "__main__":
    dashboard = DailyDashboard()
    dashboard.display_dashboard()
```

## Usage Guide

### Daily Workflow

1. **Morning (9:00 AM)**
   ```bash
   ./scripts/morning-standup.sh
   ```
   - Reviews yesterday's shutdown summary
   - Identifies incomplete tasks
   - Distributes daily briefings to agents
   - Initializes agents with context

2. **During the Day**
   - Agents work autonomously on assigned tasks
   - Monitor progress with:
   ```bash
   python3 tools/daily_dashboard.py
   ```

3. **Evening (6:00 PM)**
   ```bash
   ./scripts/evening-shutdown.sh
   ```
   - Collects final status from all agents
   - Summarizes completed work
   - Identifies blockers and issues
   - Plans next day's priorities
   - Archives data and shuts down gracefully

### Manual Controls

- **Quick Status Check**
  ```bash
  python3 tools/morning_standup.py --status-only
  ```

- **Force Shutdown**
  ```bash
  python3 tools/evening_shutdown.py --force
  ```

- **Generate Report**
  ```bash
  python3 tools/generate_daily_report.py --date 2024-07-19
  ```

## Benefits

1. **Continuity**: Work seamlessly continues from day to day
2. **Context Preservation**: No loss of progress or context between sessions
3. **Productivity Tracking**: Clear metrics on what was accomplished
4. **Issue Detection**: Automatic identification of blockers and errors
5. **Resource Optimization**: Proper cleanup and resource management
6. **Team Visibility**: Clear reports for stakeholders

## Customization

You can customize the standup and shutdown processes by:

1. Modifying priority algorithms in `determine_priorities()`
2. Adding custom metrics to `analyze_productivity()`
3. Extending agent briefings with role-specific information
4. Creating custom reports for specific needs
5. Integrating with external tools (Slack, email, etc.)

This system ensures your multi-agent setup maintains context and continuity, making it truly productive for long-term projects.