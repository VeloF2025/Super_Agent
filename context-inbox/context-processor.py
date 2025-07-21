#!/usr/bin/env python3
"""
Context Processor for OA
Transforms collected information into actionable agent contexts
"""

import json
import re
from pathlib import Path
from datetime import datetime

class ContextProcessor:
    def __init__(self):
        self.inbox_path = Path("C:/Jarvis/AI Workspace/Super Agent/context-inbox")
        self.processed = self.inbox_path / "processed"
        self.agent_contexts = self.inbox_path / "agent-contexts"
        self.agent_contexts.mkdir(exist_ok=True)
        
    def process_pending_contexts(self):
        """Process all pending context files"""
        pending = []
        
        for file in self.processed.iterdir():
            if file.suffix == '.json' and 'context.json' in file.name:
                with open(file, 'r', encoding='utf-8') as f:
                    context = json.load(f)
                    
                if context.get('status') in ['pending_review', 'pending_agent_analysis']:
                    pending.append((file, context))
                    
        return pending
    
    def generate_full_context(self, context_data):
        """Generate comprehensive project context"""
        if context_data['request_type'] == 'new_project':
            return self.process_new_project_context(context_data)
        else:
            return self.process_takeover_context(context_data)
    
    def process_new_project_context(self, context_data):
        """Process new project request into full context"""
        content = context_data['content']
        
        # Extract information using patterns
        extracted = {
            'project_name': self.extract_project_name(content),
            'project_type': self.extract_project_type(content),
            'tech_stack': self.extract_tech_stack(content),
            'features': self.extract_features(content),
            'constraints': self.extract_constraints(content)
        }
        
        # Generate comprehensive context
        full_context = {
            'context_id': context_data['context_id'],
            'created_at': datetime.now().isoformat(),
            'project_info': extracted,
            'agent_allocation': self.suggest_agents(extracted),
            'initial_tasks': self.generate_initial_tasks(extracted),
            'risk_assessment': self.assess_project_risks(extracted)
        }
        
        return full_context
    
    def extract_project_name(self, content):
        """Extract project name from content"""
        patterns = [
            r'project\s*name\s*[:=]\s*([^\n]+)',
            r'name\s*[:=]\s*([^\n]+)',
            r'#\s*([^\n]+)',  # First heading
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return "Unnamed Project"
    
    def extract_tech_stack(self, content):
        """Extract technology stack"""
        tech_keywords = {
            'frontend': ['react', 'vue', 'angular', 'next.js', 'svelte'],
            'backend': ['node.js', 'python', 'django', 'express', 'fastapi', 'java', 'spring'],
            'database': ['postgresql', 'mysql', 'mongodb', 'firebase', 'supabase', 'redis'],
            'cloud': ['aws', 'azure', 'gcp', 'vercel', 'netlify', 'heroku']
        }
        
        found_tech = {}
        content_lower = content.lower()
        
        for category, keywords in tech_keywords.items():
            found = [tech for tech in keywords if tech in content_lower]
            if found:
                found_tech[category] = found
                
        return found_tech
    
    def extract_features(self, content):
        """Extract project features"""
        features = []
        
        # Look for bullet points or numbered lists
        bullet_pattern = r'[-*]\s*([^\n]+)'
        numbered_pattern = r'\d+\.\s*([^\n]+)'
        
        for pattern in [bullet_pattern, numbered_pattern]:
            matches = re.findall(pattern, content)
            features.extend([m.strip() for m in matches if len(m.strip()) > 5])
            
        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for feature in features:
            if feature.lower() not in seen:
                seen.add(feature.lower())
                unique_features.append(feature)
                
        return unique_features[:10]  # Limit to top 10
    
    def suggest_agents(self, extracted_info):
        """Suggest agent allocation based on project info"""
        agents = []
        
        # Always need an orchestrator
        agents.append({
            'type': 'orchestrator',
            'role': 'Project coordination and context management',
            'priority': 'high'
        })
        
        # Frontend agent
        if extracted_info.get('tech_stack', {}).get('frontend'):
            agents.append({
                'type': 'frontend',
                'role': 'UI/UX implementation',
                'tech': extracted_info['tech_stack']['frontend'],
                'priority': 'high'
            })
            
        # Backend agent
        if extracted_info.get('tech_stack', {}).get('backend'):
            agents.append({
                'type': 'backend',
                'role': 'API and business logic',
                'tech': extracted_info['tech_stack']['backend'],
                'priority': 'high'
            })
            
        # Database agent
        if extracted_info.get('tech_stack', {}).get('database'):
            agents.append({
                'type': 'database',
                'role': 'Data modeling and optimization',
                'tech': extracted_info['tech_stack']['database'],
                'priority': 'medium'
            })
            
        # Testing agent
        if len(extracted_info.get('features', [])) > 3:
            agents.append({
                'type': 'testing',
                'role': 'Quality assurance and test automation',
                'priority': 'medium'
            })
            
        return agents
    
    def generate_initial_tasks(self, extracted_info):
        """Generate initial tasks for the project"""
        tasks = []
        
        # Project setup tasks
        tasks.append({
            'task': 'Initialize project repository and structure',
            'assigned_to': 'orchestrator',
            'priority': 1
        })
        
        # Tech-specific tasks
        if 'frontend' in extracted_info.get('tech_stack', {}):
            tasks.append({
                'task': 'Set up frontend framework and tooling',
                'assigned_to': 'frontend',
                'priority': 2
            })
            
        if 'backend' in extracted_info.get('tech_stack', {}):
            tasks.append({
                'task': 'Create API structure and database schema',
                'assigned_to': 'backend',
                'priority': 2
            })
            
        # Feature implementation tasks
        for i, feature in enumerate(extracted_info.get('features', [])[:3]):
            tasks.append({
                'task': f'Implement: {feature}',
                'assigned_to': 'auto',
                'priority': 3 + i
            })
            
        return tasks
    
    def assess_project_risks(self, extracted_info):
        """Basic risk assessment"""
        risks = []
        
        # Check for complexity indicators
        feature_count = len(extracted_info.get('features', []))
        if feature_count > 10:
            risks.append({
                'type': 'scope',
                'level': 'high',
                'description': f'Large feature set ({feature_count} features) may impact timeline'
            })
            
        # Check for tech diversity
        tech_categories = len(extracted_info.get('tech_stack', {}))
        if tech_categories > 3:
            risks.append({
                'type': 'complexity',
                'level': 'medium',
                'description': 'Multiple technology stacks increase integration complexity'
            })
            
        return risks
    
    def save_processed_context(self, context_file, full_context):
        """Save the processed context"""
        # Create final context file
        output_file = self.agent_contexts / f"{full_context['context_id']}-complete.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(full_context, f, indent=2)
            
        # Update original context status
        with open(context_file, 'r', encoding='utf-8') as f:
            original = json.load(f)
            
        original['status'] = 'completed'
        original['completed_at'] = datetime.now().isoformat()
        original['output_file'] = str(output_file)
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(original, f, indent=2)
            
        return output_file
    
    def generate_agent_claude_md(self, full_context, agent_type):
        """Generate CLAUDE.md file for specific agent"""
        project_info = full_context['project_info']
        
        content = f"""# CLAUDE.md - {agent_type.title()} Agent

## Project: {project_info['project_name']}

This file provides context for the {agent_type} agent working on this project.

## Your Role

{self.get_agent_role_description(agent_type, full_context)}

## Project Overview

**Type**: {project_info.get('project_type', 'General Application')}
**Context ID**: {full_context['context_id']}

## Technical Stack

{self.format_tech_stack(project_info.get('tech_stack', {}), agent_type)}

## Features to Implement

{self.format_features_for_agent(project_info.get('features', []), agent_type)}

## Your Tasks

{self.format_tasks_for_agent(full_context.get('initial_tasks', []), agent_type)}

## Integration Points

{self.get_integration_points(full_context, agent_type)}

## Success Criteria

{self.get_success_criteria(agent_type, full_context)}
"""
        
        return content
    
    def get_agent_role_description(self, agent_type, context):
        """Get role description for specific agent type"""
        roles = {
            'frontend': "You are responsible for all user interface implementation, ensuring a responsive, accessible, and performant frontend application.",
            'backend': "You handle server-side logic, API development, and data processing, ensuring scalable and secure backend services.",
            'database': "You design and optimize data models, manage database performance, and ensure data integrity.",
            'testing': "You ensure code quality through comprehensive testing strategies, including unit, integration, and end-to-end tests.",
            'orchestrator': "You coordinate all agents, manage project context, and ensure smooth collaboration across the team."
        }
        return roles.get(agent_type, "You are a specialized agent working on this project.")
    
    def format_tech_stack(self, tech_stack, agent_type):
        """Format tech stack for specific agent"""
        if not tech_stack:
            return "No specific technology requirements identified."
            
        relevant_tech = tech_stack.get(agent_type, [])
        if relevant_tech:
            return f"**Your Technologies**: {', '.join(relevant_tech)}"
        else:
            return "**Related Technologies**:\n" + '\n'.join(
                f"- {category}: {', '.join(techs)}"
                for category, techs in tech_stack.items()
            )
    
    def format_features_for_agent(self, features, agent_type):
        """Format features relevant to agent"""
        if not features:
            return "No specific features identified yet."
            
        # In a real implementation, would filter by agent relevance
        return '\n'.join(f"- {feature}" for feature in features[:5])
    
    def format_tasks_for_agent(self, tasks, agent_type):
        """Format tasks for specific agent"""
        agent_tasks = [
            t for t in tasks 
            if t.get('assigned_to') == agent_type or t.get('assigned_to') == 'auto'
        ]
        
        if not agent_tasks:
            return "No specific tasks assigned yet. Coordinate with orchestrator."
            
        return '\n'.join(
            f"{i+1}. {task['task']} (Priority: {task['priority']})"
            for i, task in enumerate(agent_tasks)
        )
    
    def get_integration_points(self, context, agent_type):
        """Define integration points for agent"""
        points = {
            'frontend': "- Backend API endpoints\n- Authentication flow\n- Real-time updates (if applicable)",
            'backend': "- Database queries\n- Frontend API contracts\n- External service integrations",
            'database': "- ORM/query interfaces\n- Migration strategies\n- Backup procedures",
            'testing': "- CI/CD pipeline\n- Test coverage reporting\n- Performance benchmarks"
        }
        return points.get(agent_type, "- Coordinate with other agents for integration points")
    
    def get_success_criteria(self, agent_type, context):
        """Define success criteria for agent"""
        criteria = {
            'frontend': "- [ ] All UI components are responsive\n- [ ] Accessibility standards met (WCAG 2.1)\n- [ ] Performance targets achieved\n- [ ] Cross-browser compatibility",
            'backend': "- [ ] API endpoints documented\n- [ ] Security best practices implemented\n- [ ] Performance optimized\n- [ ] Error handling comprehensive",
            'database': "- [ ] Schema optimized for queries\n- [ ] Indexes properly configured\n- [ ] Backup strategy implemented\n- [ ] Data integrity maintained",
            'testing': "- [ ] 80%+ code coverage\n- [ ] All critical paths tested\n- [ ] Performance tests passing\n- [ ] Security tests implemented"
        }
        return criteria.get(agent_type, "- [ ] Tasks completed successfully\n- [ ] Integration verified")


if __name__ == "__main__":
    processor = ContextProcessor()
    
    # Process pending contexts
    pending = processor.process_pending_contexts()
    
    if pending:
        print(f"📋 Found {len(pending)} pending contexts to process")
        
        for context_file, context_data in pending:
            print(f"\n🔄 Processing: {context_file.name}")
            
            # Generate full context
            full_context = processor.generate_full_context(context_data)
            
            # Save processed context
            output_file = processor.save_processed_context(context_file, full_context)
            
            print(f"✅ Completed: {output_file.name}")
            
            # Generate agent-specific CLAUDE.md files
            for agent in full_context['agent_allocation']:
                agent_type = agent['type']
                claude_md = processor.generate_agent_claude_md(full_context, agent_type)
                
                # Save CLAUDE.md for agent
                agent_file = processor.agent_contexts / f"{full_context['context_id']}-{agent_type}-CLAUDE.md"
                with open(agent_file, 'w', encoding='utf-8') as f:
                    f.write(claude_md)
                    
                print(f"   📄 Generated: {agent_file.name}")
    else:
        print("✨ No pending contexts to process")