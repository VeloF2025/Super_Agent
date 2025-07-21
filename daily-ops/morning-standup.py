#!/usr/bin/env python3
"""
Jarvis Morning Standup System
Automated morning routine for multi-agent coordination
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import shutil

class JarvisStandup:
    def __init__(self):
        self.workspace_root = Path("C:/Jarvis/AI Workspace/Super Agent")
        self.memory_dir = self.workspace_root / "memory"
        self.standup_dir = self.memory_dir / "standups"
        self.comm_dir = self.workspace_root / "communication"
        self.workflows_dir = self.workspace_root / "workflows"
        self.logs_dir = self.workspace_root / "logs"
        
        # Ensure directories exist
        for dir_path in [self.standup_dir, self.comm_dir / "state", 
                        self.comm_dir / "queue", self.workflows_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def run_standup(self):
        """Execute morning standup routine"""
        print("\n" + "="*60)
        print("🌅 JARVIS MORNING STANDUP")
        print("="*60)
        print(f"Date: {datetime.now().strftime('%A, %B %d, %Y')}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 1. System health check
        print("🔍 SYSTEM HEALTH CHECK")
        print("-" * 30)
        system_health = self.check_system_health()
        self.display_health_status(system_health)
        
        # 2. Load yesterday's summary
        print("\n📊 YESTERDAY'S SUMMARY")
        print("-" * 30)
        yesterday_summary = self.load_yesterday_summary()
        self.display_yesterday_summary(yesterday_summary)
        
        # 3. Review incomplete tasks
        print("\n📋 INCOMPLETE TASKS REVIEW")
        print("-" * 30)
        incomplete_tasks = self.review_incomplete_tasks()
        self.display_incomplete_tasks(incomplete_tasks)
        
        # 4. Generate today's plan
        print("\n🎯 TODAY'S PRIORITIES")
        print("-" * 30)
        todays_plan = self.generate_todays_plan(yesterday_summary, incomplete_tasks)
        self.display_todays_plan(todays_plan)
        
        # 5. Initialize agent contexts
        print("\n🤖 AGENT INITIALIZATION")
        print("-" * 30)
        agent_contexts = self.initialize_agent_contexts(todays_plan)
        
        # 6. Create standup record
        standup_record = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'system_health': system_health,
            'yesterday_summary': yesterday_summary,
            'incomplete_tasks': incomplete_tasks,
            'todays_plan': todays_plan,
            'agent_contexts': agent_contexts
        }
        
        self.save_standup_record(standup_record)
        
        print("\n✅ STANDUP COMPLETE!")
        print("Agents are initialized and ready to work.")
        print("="*60)
        
        return standup_record
    
    def check_system_health(self):
        """Check overall system health"""
        health = {
            'status': 'healthy',
            'issues': [],
            'services': {},
            'disk_usage': self.check_disk_usage(),
            'last_housekeeper_run': self.check_housekeeper_status()
        }
        
        # Check if housekeeper is running
        housekeeper_config = self.workspace_root / "housekeeper" / "config.json"
        if housekeeper_config.exists():
            health['services']['housekeeper'] = 'configured'
        else:
            health['issues'].append("Housekeeper not configured")
            
        # Check context system
        context_inbox = self.workspace_root / "context-inbox"
        if context_inbox.exists():
            health['services']['context_system'] = 'active'
        else:
            health['issues'].append("Context system not found")
            
        # Check agent directories
        agents_parent = self.workspace_root.parent / "agents"
        if agents_parent.exists():
            agent_count = len(list(agents_parent.glob("agent-*")))
            health['services']['agents'] = f"{agent_count} agent directories found"
        else:
            health['issues'].append("No agent directories found")
            
        # Set overall status
        if health['issues']:
            health['status'] = 'warning' if len(health['issues']) < 3 else 'critical'
            
        return health
    
    def check_disk_usage(self):
        """Check disk usage of workspace"""
        try:
            total, used, free = shutil.disk_usage(self.workspace_root)
            usage_percent = (used / total) * 100
            return {
                'total_gb': round(total / (1024**3), 2),
                'used_gb': round(used / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'usage_percent': round(usage_percent, 1)
            }
        except:
            return {'error': 'Unable to check disk usage'}
    
    def check_housekeeper_status(self):
        """Check when housekeeper last ran"""
        hk_log = self.workspace_root / "housekeeper" / "cleanup.log"
        if hk_log.exists():
            try:
                mod_time = datetime.fromtimestamp(hk_log.stat().st_mtime)
                hours_ago = (datetime.now() - mod_time).total_seconds() / 3600
                return f"{hours_ago:.1f} hours ago"
            except:
                return "Unknown"
        return "Never"
    
    def display_health_status(self, health):
        """Display system health status"""
        status_icon = "✅" if health['status'] == 'healthy' else "⚠️" if health['status'] == 'warning' else "❌"
        print(f"System Status: {status_icon} {health['status'].upper()}")
        
        if health['issues']:
            print("Issues found:")
            for issue in health['issues']:
                print(f"  • {issue}")
        
        print(f"Disk Usage: {health['disk_usage'].get('usage_percent', 'Unknown')}% used")
        print(f"Last Housekeeper Run: {health['last_housekeeper_run']}")
    
    def load_yesterday_summary(self):
        """Load yesterday's shutdown summary"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        summary_file = self.standup_dir / f"shutdown_{yesterday}.json"
        
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading yesterday's summary: {e}")
                return None
        return None
    
    def display_yesterday_summary(self, summary):
        """Display yesterday's summary"""
        if summary:
            print(f"Yesterday ({summary.get('date', 'Unknown')}):")
            
            if 'executive_summary' in summary:
                print(summary['executive_summary'])
            else:
                print("• Summary data available")
                
            if summary.get('todays_work', {}).get('workflows', {}):
                workflows = summary['todays_work']['workflows']
                completed = len(workflows.get('completed', []))
                in_progress = len(workflows.get('in_progress', []))
                print(f"• Workflows: {completed} completed, {in_progress} in progress")
        else:
            print("No summary from yesterday (starting fresh)")
    
    def review_incomplete_tasks(self):
        """Review incomplete tasks from workflows"""
        incomplete = []
        
        if self.workflows_dir.exists():
            for workflow_file in self.workflows_dir.glob("*.json"):
                try:
                    with open(workflow_file, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                    
                    if workflow.get('status') == 'in_progress':
                        created = datetime.fromisoformat(workflow.get('created', datetime.now().isoformat()))
                        age_days = (datetime.now() - created).days
                        
                        incomplete.append({
                            'workflow_id': workflow.get('id', workflow_file.stem),
                            'description': workflow.get('specification', workflow.get('description', 'Unknown task')),
                            'age_days': age_days,
                            'subtasks': workflow.get('subtasks', []),
                            'priority': workflow.get('priority', 'normal')
                        })
                except Exception as e:
                    print(f"Error reading workflow {workflow_file}: {e}")
        
        return incomplete
    
    def display_incomplete_tasks(self, incomplete_tasks):
        """Display incomplete tasks"""
        if incomplete_tasks:
            print(f"Found {len(incomplete_tasks)} incomplete tasks:")
            for task in incomplete_tasks[:5]:  # Show top 5
                age_indicator = "🔥" if task['age_days'] > 2 else "⏰" if task['age_days'] > 0 else "🆕"
                print(f"  {age_indicator} {task['description'][:60]}... ({task['age_days']} days old)")
            
            if len(incomplete_tasks) > 5:
                print(f"  ... and {len(incomplete_tasks) - 5} more")
        else:
            print("No incomplete tasks found - great job!")
    
    def generate_todays_plan(self, yesterday_summary, incomplete_tasks):
        """Generate today's priority plan"""
        priorities = []
        
        # Critical: Overdue tasks
        for task in incomplete_tasks:
            if task['age_days'] > 2:
                priorities.append({
                    'level': 'critical',
                    'type': 'overdue_task',
                    'description': f"Complete overdue: {task['description'][:50]}...",
                    'workflow_id': task['workflow_id'],
                    'age_days': task['age_days']
                })
        
        # High: Recent incomplete tasks
        for task in incomplete_tasks:
            if task['age_days'] <= 2:
                priorities.append({
                    'level': 'high',
                    'type': 'continue_task', 
                    'description': f"Continue: {task['description'][:50]}...",
                    'workflow_id': task['workflow_id']
                })
        
        # Medium: Yesterday's planned next items
        if yesterday_summary and 'planned_next' in yesterday_summary:
            for item in yesterday_summary['planned_next'][:3]:
                priorities.append({
                    'level': 'medium',
                    'type': 'planned_work',
                    'description': item.get('description', 'Planned work'),
                    'context': item
                })
        
        # Add system maintenance if needed
        if not priorities:
            priorities.append({
                'level': 'low',
                'type': 'maintenance',
                'description': 'System maintenance and optimization'
            })
        
        return priorities[:6]  # Top 6 priorities
    
    def display_todays_plan(self, plan):
        """Display today's priority plan"""
        if plan:
            print("Today's priorities:")
            for i, priority in enumerate(plan, 1):
                level_icon = {"critical": "🔥", "high": "⚡", "medium": "📋", "low": "🔧"}.get(priority['level'], "•")
                print(f"  {i}. {level_icon} [{priority['level'].upper()}] {priority['description']}")
        else:
            print("No specific priorities identified")
    
    def initialize_agent_contexts(self, todays_plan):
        """Initialize agent-specific contexts for today"""
        agents_parent = self.workspace_root.parent / "agents"
        agent_contexts = {}
        
        if not agents_parent.exists():
            print("No agent directories found")
            return agent_contexts
        
        agent_dirs = list(agents_parent.glob("agent-*"))
        print(f"Found {len(agent_dirs)} agent directories")
        
        for agent_dir in agent_dirs:
            agent_id = agent_dir.name
            
            try:
                # Create daily context
                context = self.create_agent_context(agent_id, todays_plan)
                
                # Save to agent directory
                daily_context_file = agent_dir / f"DAILY_CONTEXT_{datetime.now().strftime('%Y%m%d')}.md"
                
                with open(daily_context_file, 'w', encoding='utf-8') as f:
                    f.write(context)
                
                # Update agent's CLAUDE.md
                self.update_agent_claude_md(agent_dir, daily_context_file.name)
                
                agent_contexts[agent_id] = {
                    'context_file': str(daily_context_file),
                    'status': 'initialized'
                }
                
                print(f"  ✅ {agent_id}: Context initialized")
                
            except Exception as e:
                print(f"  ❌ {agent_id}: Error - {e}")
                agent_contexts[agent_id] = {'status': 'error', 'error': str(e)}
        
        return agent_contexts
    
    def create_agent_context(self, agent_id, todays_plan):
        """Create daily context for specific agent"""
        context = f"""# Daily Context for {agent_id}
Generated: {datetime.now().strftime('%A, %B %d, %Y at %H:%M:%S')}

## 🎯 Today's Mission
You are {agent_id} in the Jarvis Super Agent system. Today's focus is on maintaining momentum and delivering quality results.

## 📋 System Priorities
"""
        
        for i, priority in enumerate(todays_plan, 1):
            context += f"{i}. **[{priority['level'].upper()}]** {priority['description']}\n"
        
        context += f"""

## 🤖 Your Role Today
"""
        
        # Role-specific guidance
        role_guidance = {
            'agent-frontend': """
- Focus on user interface implementation and user experience
- Ensure components are responsive and accessible
- Collaborate with backend agent for API integration
- Test across different browsers and devices
- Update component documentation as you work
""",
            'agent-backend': """
- Develop server-side logic and API endpoints
- Ensure data validation and security measures
- Optimize database queries and performance
- Collaborate with frontend agent for API contracts
- Implement proper error handling and logging
""",
            'agent-testing': """
- Write comprehensive test suites for new features
- Run regression tests on existing functionality
- Monitor code coverage and quality metrics
- Identify edge cases and potential bugs
- Automate testing workflows where possible
""",
            'agent-database': """
- Design efficient database schemas
- Optimize queries for performance
- Manage data migrations and integrity
- Monitor database health and usage
- Implement backup and recovery procedures
""",
            'agent-devops': """
- Manage deployment pipelines and infrastructure
- Monitor system performance and availability
- Implement security best practices
- Automate operational tasks
- Manage environment configurations
"""
        }
        
        context += role_guidance.get(agent_id, """
- Work on assigned tasks with focus and quality
- Communicate progress and blockers clearly
- Collaborate effectively with other agents
- Follow established coding standards
- Document your work for future reference
""")
        
        context += f"""

## 📞 Communication
- Use the communication system in `../communication/` for coordination
- Update your status regularly in `../communication/state/{agent_id}_state.json`
- Check queue for messages: `../communication/queue/`

## 📊 Daily Reminders
- Save work frequently and commit logical chunks
- Write clear commit messages
- Test your changes before submitting
- Update documentation as needed
- Take breaks and maintain work-life balance

## 🎯 Success Metrics
- Quality of code delivered
- Collaboration with other agents
- Problem-solving effectiveness
- Communication clarity
- Technical innovation

---
*This context is refreshed daily. Focus on today's priorities while maintaining long-term project goals.*
"""
        
        return context
    
    def update_agent_claude_md(self, agent_dir, daily_context_filename):
        """Update agent's CLAUDE.md to reference daily context"""
        claude_md = agent_dir / "CLAUDE.md"
        
        if claude_md.exists():
            # Read existing content
            with open(claude_md, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add daily context import if not present
            import_line = f"\n<!-- Daily Context Import -->\n@import ./{daily_context_filename}\n"
            
            if daily_context_filename not in content:
                # Remove old daily context imports
                lines = content.split('\n')
                filtered_lines = [line for line in lines 
                                if not (line.startswith('@import ./DAILY_CONTEXT_') or 
                                       'Daily Context Import' in line)]
                
                # Add new import at the end
                content = '\n'.join(filtered_lines) + import_line
                
                with open(claude_md, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def save_standup_record(self, record):
        """Save standup record for history"""
        # JSON record
        standup_file = self.standup_dir / f"standup_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(standup_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2)
        
        # Human-readable summary
        summary_file = self.standup_dir / f"summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Daily Standup Summary - {record['date']}\n\n")
            f.write(f"**Time**: {record['time']}\n")
            f.write(f"**System Health**: {record['system_health']['status']}\n\n")
            
            f.write("## Today's Priorities\n")
            for i, priority in enumerate(record['todays_plan'], 1):
                f.write(f"{i}. **[{priority['level'].upper()}]** {priority['description']}\n")
            
            if record['incomplete_tasks']:
                f.write(f"\n## Incomplete Tasks ({len(record['incomplete_tasks'])})\n")
                for task in record['incomplete_tasks'][:5]:
                    f.write(f"- {task['description'][:60]}... ({task['age_days']} days old)\n")
            
            f.write(f"\n## Agent Status\n")
            for agent_id, context in record['agent_contexts'].items():
                status_icon = "✅" if context['status'] == 'initialized' else "❌"
                f.write(f"- {status_icon} {agent_id}: {context['status']}\n")
        
        print(f"\nStandup records saved:")
        print(f"  📄 Data: {standup_file}")
        print(f"  📝 Summary: {summary_file}")


if __name__ == "__main__":
    print("🌅 Jarvis Morning Standup System")
    standup = JarvisStandup()
    standup.run_standup()