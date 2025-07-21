# Project Takeover Context Engineering Process

## Overview

When the Orchestrator Agent (OA) takes over an existing project, it performs intelligent analysis to understand the codebase, architecture, and project state. This process combines automated scanning with targeted questions to quickly onboard all agents.

## Quick Start Commands

```bash
# Take over existing project
./orchestrator takeover --scan-depth=full

# Quick takeover (surface scan only)
./orchestrator takeover --quick

# Takeover with specific focus
./orchestrator takeover --focus=backend-refactor

# Combine with existing docs
./orchestrator takeover --docs=./project-docs
```

## Phase 1: Automated Project Analysis (5-10 minutes)

### 1.1 Project Scanner

The OA performs comprehensive scanning:

```python
class ProjectTakeoverScanner:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.analysis_results = {
            'structure': {},
            'technologies': {},
            'patterns': {},
            'issues': [],
            'metrics': {}
        }
    
    def full_scan(self):
        """Perform complete project analysis"""
        print("🔍 Starting project analysis...")
        
        # Step 1: Project structure
        self.analyze_structure()
        
        # Step 2: Technology detection
        self.detect_technologies()
        
        # Step 3: Code analysis
        self.analyze_codebase()
        
        # Step 4: Dependency analysis
        self.analyze_dependencies()
        
        # Step 5: Documentation scan
        self.scan_documentation()
        
        # Step 6: Git history analysis
        self.analyze_git_history()
        
        # Step 7: Issue detection
        self.detect_issues()
        
        return self.generate_report()
    
    def analyze_structure(self):
        """Analyze project directory structure"""
        structure = {
            'type': 'unknown',
            'layout': {},
            'key_directories': [],
            'entry_points': []
        }
        
        # Detect project type from structure
        if (self.project_root / 'package.json').exists():
            structure['type'] = 'node'
            pkg_json = json.loads((self.project_root / 'package.json').read_text())
            structure['name'] = pkg_json.get('name', 'unknown')
            structure['entry_points'].append(pkg_json.get('main', 'index.js'))
            
        elif (self.project_root / 'requirements.txt').exists():
            structure['type'] = 'python'
            
        elif (self.project_root / 'go.mod').exists():
            structure['type'] = 'go'
        
        # Map directory structure
        for item in self.project_root.rglob('*'):
            if item.is_dir() and not any(skip in str(item) for skip in ['.git', 'node_modules', '__pycache__']):
                rel_path = item.relative_to(self.project_root)
                
                # Identify key directories
                if any(key in item.name for key in ['src', 'lib', 'components', 'api', 'models', 'views']):
                    structure['key_directories'].append(str(rel_path))
        
        self.analysis_results['structure'] = structure
    
    def detect_technologies(self):
        """Detect technologies used in the project"""
        tech = {
            'frontend': [],
            'backend': [],
            'database': [],
            'testing': [],
            'build_tools': [],
            'dependencies': {}
        }
        
        # Frontend detection
        if (self.project_root / 'package.json').exists():
            pkg = json.loads((self.project_root / 'package.json').read_text())
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            
            # Framework detection
            if 'react' in deps:
                tech['frontend'].append('React')
            if 'vue' in deps:
                tech['frontend'].append('Vue')
            if '@angular/core' in deps:
                tech['frontend'].append('Angular')
            
            # Build tools
            if 'webpack' in deps:
                tech['build_tools'].append('Webpack')
            if 'vite' in deps:
                tech['build_tools'].append('Vite')
            
            # Testing
            if 'jest' in deps:
                tech['testing'].append('Jest')
            if 'cypress' in deps:
                tech['testing'].append('Cypress')
        
        # Backend detection
        if (self.project_root / 'server.js').exists() or (self.project_root / 'app.js').exists():
            tech['backend'].append('Node.js')
            
        # Database detection from config files or imports
        self.detect_database_tech(tech)
        
        self.analysis_results['technologies'] = tech
    
    def analyze_codebase(self):
        """Analyze code patterns and quality"""
        patterns = {
            'architecture': 'unknown',
            'design_patterns': [],
            'code_style': {},
            'component_count': 0,
            'api_endpoints': [],
            'complexity_warnings': []
        }
        
        # Architecture detection
        if (self.project_root / 'src' / 'components').exists():
            patterns['architecture'] = 'component-based'
        elif (self.project_root / 'mvc').exists() or (self.project_root / 'models').exists():
            patterns['architecture'] = 'mvc'
        elif (self.project_root / 'layers').exists():
            patterns['architecture'] = 'layered'
        
        # Count components/modules
        for ext in ['*.jsx', '*.tsx', '*.vue', '*.component.ts']:
            patterns['component_count'] += len(list(self.project_root.rglob(ext)))
        
        # Find API endpoints
        patterns['api_endpoints'] = self.scan_api_endpoints()
        
        # Detect code complexity issues
        patterns['complexity_warnings'] = self.detect_complexity_issues()
        
        self.analysis_results['patterns'] = patterns
    
    def scan_api_endpoints(self):
        """Scan for API endpoint definitions"""
        endpoints = []
        
        # Node.js/Express patterns
        for js_file in self.project_root.rglob('*.js'):
            try:
                content = js_file.read_text()
                # Find Express routes
                routes = re.findall(r'app\.(get|post|put|delete|patch)\([\'"](.+?)[\'"]', content)
                endpoints.extend([{'method': method.upper(), 'path': path} for method, path in routes])
            except:
                pass
        
        return endpoints
    
    def analyze_git_history(self):
        """Analyze git history for insights"""
        try:
            import subprocess
            
            # Get recent activity
            result = subprocess.run(
                ['git', 'log', '--oneline', '-20'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            recent_commits = result.stdout.strip().split('\n') if result.returncode == 0 else []
            
            # Get contributors
            result = subprocess.run(
                ['git', 'shortlog', '-sn'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            contributors = []
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    match = re.match(r'\s*(\d+)\s+(.+)', line)
                    if match:
                        contributors.append({
                            'commits': int(match.group(1)),
                            'name': match.group(2)
                        })
            
            # Get last modified dates for key files
            key_files = ['README.md', 'package.json', 'requirements.txt']
            last_updates = {}
            
            for file in key_files:
                if (self.project_root / file).exists():
                    result = subprocess.run(
                        ['git', 'log', '-1', '--format=%cd', '--date=relative', file],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root
                    )
                    if result.returncode == 0:
                        last_updates[file] = result.stdout.strip()
            
            self.analysis_results['git_info'] = {
                'recent_activity': recent_commits[:5],
                'contributors': contributors[:5],
                'last_updates': last_updates,
                'total_commits': len(recent_commits)
            }
            
        except Exception as e:
            self.analysis_results['git_info'] = {'error': str(e)}
    
    def detect_issues(self):
        """Detect potential issues and technical debt"""
        issues = []
        
        # Check for missing documentation
        if not (self.project_root / 'README.md').exists():
            issues.append({
                'type': 'documentation',
                'severity': 'high',
                'message': 'No README.md found',
                'suggestion': 'Create comprehensive project documentation'
            })
        
        # Check for outdated dependencies
        if (self.project_root / 'package.json').exists():
            # Would integrate with npm outdated or similar
            pass
        
        # Check for TODO/FIXME comments
        todo_count = 0
        for ext in ['*.js', '*.py', '*.ts', '*.jsx', '*.tsx']:
            for file in self.project_root.rglob(ext):
                try:
                    content = file.read_text()
                    todos = len(re.findall(r'(TODO|FIXME|XXX|HACK)', content, re.I))
                    todo_count += todos
                except:
                    pass
        
        if todo_count > 10:
            issues.append({
                'type': 'technical_debt',
                'severity': 'medium',
                'message': f'Found {todo_count} TODO/FIXME comments',
                'suggestion': 'Address technical debt items'
            })
        
        # Check for large files
        for file in self.project_root.rglob('*'):
            if file.is_file() and file.stat().st_size > 1_000_000:  # 1MB
                if not any(skip in str(file) for skip in ['node_modules', '.git', 'dist', 'build']):
                    issues.append({
                        'type': 'performance',
                        'severity': 'low',
                        'message': f'Large file detected: {file.relative_to(self.project_root)}',
                        'suggestion': 'Consider splitting or optimizing'
                    })
        
        self.analysis_results['issues'] = issues
```

### 1.2 Intelligent Context Builder

Combines scan results with any existing documentation:

```python
class TakeoverContextBuilder:
    def __init__(self, scan_results, existing_docs=None):
        self.scan_results = scan_results
        self.existing_docs = existing_docs
        self.context = {}
    
    def build_takeover_context(self):
        """Build comprehensive context from scan and docs"""
        
        # Start with scan results
        self.context = {
            'project_name': self.extract_project_name(),
            'project_type': self.determine_project_type(),
            'current_state': self.assess_project_state(),
            'tech_stack': self.scan_results['technologies'],
            'architecture': self.scan_results['patterns']['architecture'],
            'team_size': len(self.scan_results.get('git_info', {}).get('contributors', [])),
            'last_activity': self.get_last_activity(),
            'discovered_features': self.extract_features(),
            'identified_issues': self.scan_results['issues'],
            'next_steps': self.recommend_next_steps()
        }
        
        # Merge with existing documentation if available
        if self.existing_docs:
            self.merge_with_docs()
        
        # Fill gaps with targeted questions
        self.context = self.fill_context_gaps(self.context)
        
        return self.context
    
    def extract_features(self):
        """Extract features from codebase analysis"""
        features = []
        
        # From API endpoints
        endpoints = self.scan_results['patterns'].get('api_endpoints', [])
        endpoint_groups = {}
        for ep in endpoints:
            base = ep['path'].split('/')[1] if '/' in ep['path'] else ep['path']
            if base not in endpoint_groups:
                endpoint_groups[base] = []
            endpoint_groups[base].append(ep)
        
        for group, eps in endpoint_groups.items():
            features.append(f"{group.title()} management ({len(eps)} endpoints)")
        
        # From directory structure
        for key_dir in self.scan_results['structure'].get('key_directories', []):
            if 'auth' in key_dir.lower():
                features.append("Authentication system")
            elif 'payment' in key_dir.lower():
                features.append("Payment processing")
            elif 'admin' in key_dir.lower():
                features.append("Admin panel")
        
        return features
    
    def assess_project_state(self):
        """Assess the current state of the project"""
        state = {
            'phase': 'unknown',
            'health': 'unknown',
            'activity': 'unknown'
        }
        
        # Determine phase
        if self.scan_results['patterns']['component_count'] < 10:
            state['phase'] = 'early-development'
        elif self.scan_results['patterns']['component_count'] < 50:
            state['phase'] = 'active-development'
        else:
            state['phase'] = 'mature'
        
        # Assess health
        issue_count = len(self.scan_results['issues'])
        if issue_count == 0:
            state['health'] = 'excellent'
        elif issue_count < 5:
            state['health'] = 'good'
        elif issue_count < 10:
            state['health'] = 'fair'
        else:
            state['health'] = 'needs-attention'
        
        # Activity level
        git_info = self.scan_results.get('git_info', {})
        if 'last_updates' in git_info:
            # Parse relative dates
            if any('hour' in update or 'day' in update for update in git_info['last_updates'].values()):
                state['activity'] = 'active'
            elif any('week' in update for update in git_info['last_updates'].values()):
                state['activity'] = 'moderate'
            else:
                state['activity'] = 'inactive'
        
        return state
    
    def recommend_next_steps(self):
        """Recommend immediate next steps based on analysis"""
        steps = []
        
        # Based on issues
        for issue in self.scan_results['issues']:
            if issue['severity'] == 'high':
                steps.append({
                    'priority': 'high',
                    'action': issue['suggestion'],
                    'reason': issue['message']
                })
        
        # Based on project state
        state = self.assess_project_state()
        if state['health'] == 'needs-attention':
            steps.append({
                'priority': 'high',
                'action': 'Address technical debt and critical issues',
                'reason': 'Multiple issues detected'
            })
        
        # Based on missing elements
        if not self.scan_results['technologies'].get('testing'):
            steps.append({
                'priority': 'medium',
                'action': 'Implement testing infrastructure',
                'reason': 'No testing framework detected'
            })
        
        return steps
```

## Phase 2: Interactive Gap Filling (3-5 minutes)

### 2.1 Targeted Questions

Based on scan results, ask only necessary questions:

```python
class TakeoverInterviewer:
    def __init__(self, initial_context):
        self.context = initial_context
    
    def conduct_takeover_interview(self):
        """Ask targeted questions based on what's missing"""
        
        print("\n🎯 Let me ask a few questions to complete the context...\n")
        
        # Project goals (usually not in code)
        if not self.context.get('business_goal'):
            self.context['business_goal'] = input(
                "📊 What is the main business goal of this project? "
            )
        
        # Current challenges
        self.context['current_challenges'] = input(
            "⚠️  What are the main challenges or issues you're facing? "
        )
        
        # Immediate priorities
        print("\n🎯 What should we prioritize? (select up to 3)")
        priorities = [
            "Fix critical bugs",
            "Add new features",
            "Improve performance",
            "Refactor code",
            "Add tests",
            "Update documentation",
            "Modernize tech stack"
        ]
        
        for i, p in enumerate(priorities):
            print(f"  {i+1}. {p}")
        
        selected = input("\nYour priorities (e.g., 1,3,5): ")
        priority_indices = [int(x.strip())-1 for x in selected.split(',') if x.strip().isdigit()]
        self.context['priorities'] = [priorities[i] for i in priority_indices if i < len(priorities)]
        
        # Specific goals for agents
        if 'Refactor code' in self.context['priorities']:
            self.context['refactor_focus'] = input(
                "🔧 Which parts need refactoring most? "
            )
        
        if 'Add new features' in self.context['priorities']:
            self.context['new_features'] = input(
                "✨ What features do you want to add? "
            )
        
        return self.context
```

### 2.2 Context Synthesis Report

Generate comprehensive takeover report:

```python
def generate_takeover_report(context):
    """Generate a comprehensive takeover report"""
    
    report = f"""
# Project Takeover Report

## Project Overview
- **Name**: {context['project_name']}
- **Type**: {context['project_type']}
- **Business Goal**: {context.get('business_goal', 'Not specified')}
- **Current Phase**: {context['current_state']['phase']}
- **Health Status**: {context['current_state']['health']}

## Technical Stack
- **Frontend**: {', '.join(context['tech_stack']['frontend']) or 'None detected'}
- **Backend**: {', '.join(context['tech_stack']['backend']) or 'None detected'}
- **Database**: {', '.join(context['tech_stack']['database']) or 'None detected'}
- **Testing**: {', '.join(context['tech_stack']['testing']) or 'None detected'}

## Current Features
{chr(10).join(f"- {feature}" for feature in context['discovered_features'])}

## Identified Issues ({len(context['identified_issues'])})
{chr(10).join(f"- [{issue['severity'].upper()}] {issue['message']}" for issue in context['identified_issues'][:5])}

## Priorities
{chr(10).join(f"{i+1}. {priority}" for i, priority in enumerate(context['priorities']))}

## Recommended Agent Allocation
{generate_agent_recommendations(context)}

## Immediate Next Steps
{chr(10).join(f"{i+1}. {step['action']} ({step['reason']})" for i, step in enumerate(context['next_steps'][:5]))}
"""
    
    return report
```

## Phase 3: Agent-Specific Context Distribution (2-3 minutes)

### 3.1 Customized Agent Briefings

Each agent receives tailored context based on the takeover analysis:

```python
def generate_agent_briefings(takeover_context):
    """Generate specific briefings for each agent"""
    
    briefings = {}
    
    # Frontend Agent Briefing
    if takeover_context['tech_stack']['frontend']:
        briefings['frontend'] = f"""
# Frontend Agent Takeover Briefing

## Current State
- Framework: {', '.join(takeover_context['tech_stack']['frontend'])}
- Components: {takeover_context['patterns']['component_count']} found
- Architecture: {takeover_context['architecture']}

## Your Focus Areas
{generate_frontend_tasks(takeover_context)}

## Known Issues
{filter_issues_for_frontend(takeover_context['identified_issues'])}

## Integration Points
{list_api_endpoints_for_frontend(takeover_context)}
"""
    
    # Backend Agent Briefing
    if takeover_context['tech_stack']['backend']:
        briefings['backend'] = f"""
# Backend Agent Takeover Briefing

## Current State
- Technology: {', '.join(takeover_context['tech_stack']['backend'])}
- API Endpoints: {len(takeover_context['patterns']['api_endpoints'])} found
- Database: {', '.join(takeover_context['tech_stack']['database'])}

## Your Focus Areas
{generate_backend_tasks(takeover_context)}

## Technical Debt
{filter_technical_debt_items(takeover_context)}
"""
    
    return briefings
```

### 3.2 Collaborative Understanding Phase

Agents work together to build complete understanding:

```yaml
# takeover-coordination.yaml
takeover_phases:
  phase_1_discovery:
    duration: "30 minutes"
    parallel_tasks:
      frontend_agent:
        - "Audit component structure"
        - "Identify UI patterns"
        - "Check accessibility"
      backend_agent:
        - "Map API endpoints"
        - "Analyze database schema"
        - "Review business logic"
      testing_agent:
        - "Assess test coverage"
        - "Identify missing tests"
        - "Review test quality"
  
  phase_2_synthesis:
    duration: "20 minutes"
    collaborative_tasks:
      all_agents:
        - "Share findings"
        - "Identify dependencies"
        - "Align on priorities"
  
  phase_3_planning:
    duration: "10 minutes"
    output:
      - "Unified improvement plan"
      - "Task allocation"
      - "Timeline estimation"
```

## Phase 4: Continuous Context Updates

### 4.1 Learning from the Codebase

As agents work, they continuously update context:

```python
class ContinuousContextUpdater:
    def __init__(self, initial_context):
        self.context = initial_context
        self.discoveries = []
    
    def agent_discovery(self, agent_id, discovery_type, details):
        """Record new discoveries from agents"""
        discovery = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent': agent_id,
            'type': discovery_type,
            'details': details
        }
        
        self.discoveries.append(discovery)
        
        # Update context based on discovery
        if discovery_type == 'hidden_feature':
            self.context['discovered_features'].append(details['feature'])
        elif discovery_type == 'architecture_pattern':
            self.context['architecture_details'] = details
        elif discovery_type == 'business_rule':
            if 'business_rules' not in self.context:
                self.context['business_rules'] = []
            self.context['business_rules'].append(details)
    
    def generate_updated_briefing(self):
        """Generate updated briefings with new discoveries"""
        return {
            'new_findings': len(self.discoveries),
            'updated_features': self.context['discovered_features'],
            'refined_architecture': self.context.get('architecture_details', {}),
            'discovered_rules': self.context.get('business_rules', [])
        }
```

## Implementation Example

```bash
#!/bin/bash
# takeover.sh - Complete project takeover script

echo "🚀 Starting Project Takeover Process"
echo "===================================="

# Step 1: Initial scan
echo "📊 Phase 1: Scanning project..."
./orchestrator takeover --scan > scan_results.json

# Step 2: Process existing docs if available
if [ -d "./docs" ] || [ -d "./documentation" ]; then
    echo "📄 Found documentation, incorporating..."
    ./orchestrator takeover --merge-docs
fi

# Step 3: Interactive gap filling
echo "💬 Phase 2: Completing context..."
./orchestrator takeover --interview

# Step 4: Generate agent briefings
echo "📋 Phase 3: Creating agent briefings..."
./orchestrator takeover --generate-briefings

# Step 5: Deploy agents with context
echo "🤖 Phase 4: Deploying agents..."
for agent in frontend backend database testing; do
    git worktree add ../agents/agent-$agent takeover/$agent
    cp briefings/$agent-briefing.md ../agents/agent-$agent/CLAUDE.md
done

echo "✅ Takeover complete! Agents are ready to work."
```

## Benefits of Takeover Process

1. **Fast Onboarding**: Get productive in 15-20 minutes instead of days
2. **Comprehensive Understanding**: Combines code analysis with human knowledge
3. **Issue Detection**: Identifies technical debt and problems immediately
4. **Accurate Estimation**: Based on actual codebase complexity
5. **Coordinated Approach**: All agents start with shared understanding
6. **Continuous Learning**: Context improves as agents work

This takeover process ensures that when agents begin working on an existing project, they have the full context needed to make intelligent decisions and avoid breaking existing functionality.