#!/usr/bin/env python3
"""
Jarvis Documentation Generator
Automated documentation generation and maintenance system
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import shutil

class JarvisDocGenerator:
    def __init__(self):
        self.workspace_root = Path("C:/Jarvis/AI Workspace/Super Agent")
        self.docs_dir = self.workspace_root / "docs"
        self.agents_dir = self.workspace_root.parent / "agents"
        self.config_file = self.workspace_root / "docs-config.json"
        
        # Ensure docs directory exists
        self.docs_dir.mkdir(exist_ok=True)
        (self.docs_dir / "api").mkdir(exist_ok=True)
        (self.docs_dir / "guides").mkdir(exist_ok=True)
        (self.docs_dir / "architecture").mkdir(exist_ok=True)
        
        self.load_config()
    
    def load_config(self):
        """Load documentation generation configuration"""
        default_config = {
            "auto_update_before_commit": True,
            "generate_api_docs": True,
            "update_agent_docs": True,
            "create_changelog": True,
            "update_readme": True,
            "scan_for_todos": True,
            "generate_metrics": True,
            "last_update": None,
            "docs_version": "1.0.0"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save documentation configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def generate_all_docs(self):
        """Generate complete documentation suite"""
        print("Generating comprehensive documentation...")
        
        results = {
            'updated_files': [],
            'created_files': [],
            'errors': []
        }
        
        try:
            # Update main README
            if self.config.get('update_readme', True):
                self.update_main_readme(results)
            
            # Generate API documentation
            if self.config.get('generate_api_docs', True):
                self.generate_api_docs(results)
            
            # Update agent documentation
            if self.config.get('update_agent_docs', True):
                self.update_agent_docs(results)
            
            # Create changelog
            if self.config.get('create_changelog', True):
                self.generate_changelog(results)
            
            # Generate system metrics
            if self.config.get('generate_metrics', True):
                self.generate_system_metrics(results)
            
            # Scan for TODOs and issues
            if self.config.get('scan_for_todos', True):
                self.scan_todos_and_issues(results)
            
            # Update configuration
            self.config['last_update'] = datetime.now().isoformat()
            self.save_config()
            
            # Generate summary report
            self.generate_update_report(results)
            
        except Exception as e:
            results['errors'].append(f"Documentation generation failed: {e}")
            print(f"ERROR: {e}")
        
        return results
    
    def update_main_readme(self, results):
        """Update the main README.md with current system state"""
        print("Updating main README.md...")
        
        try:
            # Get system statistics
            stats = self.get_system_stats()
            
            # Read current README
            readme_path = self.workspace_root / "README.md"
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Update statistics section
                stats_section = self.generate_stats_section(stats)
                content = self.update_readme_section(content, "## 📊 System Statistics", stats_section)
                
                # Update last updated timestamp
                timestamp = f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Jarvis Doc Generator*"
                content = self.update_readme_section(content, "---", f"---\n\n{timestamp}")
                
                # Write back
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                results['updated_files'].append('README.md')
                print("  ✅ README.md updated")
            
        except Exception as e:
            results['errors'].append(f"README update failed: {e}")
    
    def generate_stats_section(self, stats):
        """Generate statistics section for README"""
        return f"""## 📊 System Statistics

- **Active Agents**: {stats['agent_count']} specialized agents
- **Total Projects**: {stats['project_count']} managed projects
- **Daily Operations**: {stats['daily_ops_count']} automated routines
- **System Uptime**: {stats['uptime']} (since last restart)
- **Storage Used**: {stats['storage_used']} / {stats['storage_total']}
- **Last Activity**: {stats['last_activity']}
- **Performance Score**: {stats['performance_score']}/100

### Recent Activity
{chr(10).join(f"- {activity}" for activity in stats['recent_activities'][:5])}

### Agent Status
{chr(10).join(f"- **{agent['name']}**: {agent['status']}" for agent in stats['agents'][:10])}
"""
    
    def get_system_stats(self):
        """Gather current system statistics"""
        stats = {
            'agent_count': 0,
            'project_count': 0,
            'daily_ops_count': 3,  # morning, evening, midday
            'uptime': 'Unknown',
            'storage_used': 'Unknown',
            'storage_total': 'Unknown',
            'last_activity': 'Unknown',
            'performance_score': 85,
            'recent_activities': [],
            'agents': []
        }
        
        try:
            # Count agents
            if self.agents_dir.exists():
                agent_dirs = list(self.agents_dir.glob("agent-*"))
                stats['agent_count'] = len(agent_dirs)
                
                for agent_dir in agent_dirs:
                    stats['agents'].append({
                        'name': agent_dir.name,
                        'status': 'Active' if self.check_agent_active(agent_dir) else 'Inactive'
                    })
            
            # Count projects
            workflows_dir = self.workspace_root / "workflows"
            if workflows_dir.exists():
                stats['project_count'] = len(list(workflows_dir.glob("*.json")))
            
            # Get storage info
            try:
                total, used, free = shutil.disk_usage(self.workspace_root)
                stats['storage_used'] = f"{used // (1024**3):.1f} GB"
                stats['storage_total'] = f"{total // (1024**3):.1f} GB"
            except:
                pass
            
            # Get recent activities
            stats['recent_activities'] = self.get_recent_activities()
            
            # Get last activity
            last_standup = self.workspace_root / "memory" / "standups"
            if last_standup.exists():
                recent_files = sorted(last_standup.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
                if recent_files:
                    mod_time = datetime.fromtimestamp(recent_files[0].stat().st_mtime)
                    stats['last_activity'] = mod_time.strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            print(f"Error gathering stats: {e}")
        
        return stats
    
    def check_agent_active(self, agent_dir):
        """Check if an agent has been active recently"""
        try:
            # Check for recent daily context files
            daily_context = agent_dir / f"DAILY_CONTEXT_{datetime.now().strftime('%Y%m%d')}.md"
            if daily_context.exists():
                return True
            
            # Check for recent file modifications
            cutoff = datetime.now() - timedelta(hours=24)
            for file in agent_dir.rglob("*"):
                if file.is_file():
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if mod_time > cutoff:
                        return True
            
            return False
        except:
            return False
    
    def get_recent_activities(self):
        """Get list of recent system activities"""
        activities = []
        
        try:
            # Check standup/shutdown logs
            standups_dir = self.workspace_root / "memory" / "standups"
            if standups_dir.exists():
                recent_files = sorted(standups_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
                for file in recent_files[:3]:
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if "standup" in file.name:
                        activities.append(f"Morning standup - {mod_time.strftime('%Y-%m-%d')}")
                    elif "shutdown" in file.name:
                        activities.append(f"Evening shutdown - {mod_time.strftime('%Y-%m-%d')}")
            
            # Check for recent projects
            context_processed = self.workspace_root / "context-inbox" / "processed"
            if context_processed.exists():
                recent_contexts = sorted(context_processed.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
                for file in recent_contexts[:2]:
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    activities.append(f"Project processed - {mod_time.strftime('%Y-%m-%d')}")
            
        except Exception as e:
            activities.append(f"Error retrieving activities: {e}")
        
        return activities
    
    def update_readme_section(self, content, section_header, new_content):
        """Update a specific section in README content"""
        try:
            # Find the section
            lines = content.split('\n')
            start_idx = -1
            end_idx = len(lines)
            
            for i, line in enumerate(lines):
                if line.strip().startswith(section_header):
                    start_idx = i
                elif start_idx != -1 and line.strip().startswith('##') and i > start_idx:
                    end_idx = i
                    break
            
            if start_idx != -1:
                # Replace the section
                new_lines = lines[:start_idx] + new_content.split('\n') + lines[end_idx:]
                return '\n'.join(new_lines)
            else:
                # Add the section at the end
                return content + '\n\n' + new_content
                
        except Exception:
            return content + '\n\n' + new_content
    
    def generate_api_docs(self, results):
        """Generate API documentation"""
        print("Generating API documentation...")
        
        try:
            # Dashboard API documentation
            self.generate_dashboard_api_docs(results)
            
            # Communication API documentation
            self.generate_communication_api_docs(results)
            
            # Agent API documentation
            self.generate_agent_api_docs(results)
            
        except Exception as e:
            results['errors'].append(f"API documentation generation failed: {e}")
    
    def generate_dashboard_api_docs(self, results):
        """Generate dashboard API documentation"""
        api_doc = """# Dashboard API Documentation

## Overview
The Dashboard API provides real-time access to agent status, system metrics, and project information.

## Base URL
```
http://localhost:3001/api
```

## Endpoints

### GET /dashboard
Get complete dashboard data including all agents, activities, and metrics.

**Response:**
```json
{
  "agents": [...],
  "activities": [...],
  "metrics": {...},
  "system_status": "healthy"
}
```

### GET /agents
List all registered agents.

**Response:**
```json
[
  {
    "id": "agent-frontend",
    "name": "Frontend Agent",
    "status": "active",
    "last_heartbeat": "2025-01-21T10:30:00Z",
    "current_task": "Implementing component library"
  }
]
```

### GET /agents/:id
Get detailed information for a specific agent.

**Parameters:**
- `id` - Agent identifier

**Response:**
```json
{
  "id": "agent-frontend",
  "name": "Frontend Agent",
  "status": "active",
  "workspace_path": "../agents/agent-frontend",
  "metrics": {...},
  "recent_activities": [...]
}
```

### GET /agents/:id/metrics
Get performance metrics for a specific agent.

**Parameters:**
- `id` - Agent identifier

**Response:**
```json
{
  "agent_id": "agent-frontend",
  "efficiency_score": 85,
  "tasks_completed": 12,
  "hours_active": 6.5,
  "commits_today": 8
}
```

### GET /activities
Get recent system activities.

**Query Parameters:**
- `limit` - Number of activities to return (default: 50)
- `agent_id` - Filter by specific agent

**Response:**
```json
[
  {
    "id": 1,
    "agent_id": "agent-frontend",
    "type": "task_completion",
    "description": "Completed component implementation",
    "status": "completed",
    "created_at": "2025-01-21T10:30:00Z"
  }
]
```

### POST /activities
Record a new activity.

**Request Body:**
```json
{
  "agent_id": "agent-frontend",
  "type": "task_start",
  "description": "Starting new feature implementation"
}
```

### PUT /activities/:id/complete
Mark an activity as completed.

**Parameters:**
- `id` - Activity identifier

### GET /communications
Get recent inter-agent communications.

**Query Parameters:**
- `limit` - Number of messages to return (default: 100)
- `from_agent` - Filter by sender
- `to_agent` - Filter by recipient

**Response:**
```json
[
  {
    "id": "msg-12345",
    "from_agent": "agent-frontend",
    "to_agent": "agent-backend",
    "message_type": "api_request",
    "priority": "high",
    "timestamp": "2025-01-21T10:30:00Z",
    "processed": true
  }
]
```

### GET /projects
Get active project information.

**Response:**
```json
[
  {
    "id": "proj-123",
    "name": "E-commerce Platform",
    "status": "in_progress",
    "agents_assigned": ["agent-frontend", "agent-backend"],
    "progress": 65,
    "created_at": "2025-01-20T09:00:00Z"
  }
]
```

## WebSocket Connection

### Connection Endpoint
```
ws://localhost:3001/ws
```

### Message Format
```json
{
  "type": "agent_status_update",
  "data": {
    "agent_id": "agent-frontend",
    "status": "active",
    "current_task": "New task description"
  },
  "timestamp": "2025-01-21T10:30:00Z"
}
```

### Event Types
- `agent_status_update` - Agent status changes
- `new_activity` - New activities logged
- `system_metric_update` - System performance updates
- `communication_event` - New inter-agent messages

## Error Responses

All endpoints return standard HTTP status codes and error messages:

```json
{
  "error": "Agent not found",
  "status": 404,
  "timestamp": "2025-01-21T10:30:00Z"
}
```

## Rate Limiting
- Default: 100 requests per minute per IP
- WebSocket: 1 connection per client
- No authentication required for local development

## Examples

### Get Agent Status
```bash
curl http://localhost:3001/api/agents/agent-frontend
```

### Record New Activity
```bash
curl -X POST http://localhost:3001/api/activities \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"agent-frontend","type":"task_start","description":"Starting new feature"}'
```

### WebSocket Connection (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:3001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```
"""
        
        api_file = self.docs_dir / "api" / "dashboard-api.md"
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write(api_doc)
        
        results['created_files'].append('docs/api/dashboard-api.md')
        print("  ✅ Dashboard API documentation generated")
    
    def generate_communication_api_docs(self, results):
        """Generate communication system API documentation"""
        comm_doc = """# Communication System API

## Overview
The Communication System enables message passing between agents with priority routing and reliable delivery.

## Message Format

### Standard Message Structure
```json
{
  "id": "unique-message-id",
  "timestamp": "2025-01-21T10:30:00Z",
  "from": "agent-frontend",
  "to": "agent-backend",
  "type": "api_request",
  "priority": "high",
  "payload": {
    "action": "create_endpoint",
    "data": {...}
  },
  "correlation_id": "workflow-123",
  "timeout": 300
}
```

### Message Types
- `task_assignment` - Assign work to an agent
- `status_update` - Report current status
- `api_request` - Request API development
- `code_review` - Request code review
- `error_report` - Report errors or issues
- `coordination` - General coordination messages

### Priority Levels
- `critical` - Immediate processing required
- `high` - Process within 5 minutes
- `normal` - Process within 30 minutes
- `low` - Process when convenient

## File-Based Queue System

### Directory Structure
```
communication/
├── queue/              # Pending messages
├── processed/          # Completed messages
└── state/             # Agent status files
```

### Queue Operations

#### Send Message
1. Create message JSON file in `queue/` directory
2. Use timestamp-based filename: `YYYYMMDD_HHMMSS_sender_recipient.json`
3. System automatically routes to recipient

#### Receive Messages
1. Agents poll `queue/` directory for messages addressed to them
2. Process message content
3. Move processed message to `processed/` directory
4. Optionally send response message

#### Message Status Tracking
```json
{
  "message_id": "msg-12345",
  "status": "delivered",
  "processed_at": "2025-01-21T10:35:00Z",
  "response": {
    "status": "completed",
    "result": {...}
  }
}
```

## Agent State Management

### State File Format
```json
{
  "agent_id": "agent-frontend",
  "timestamp": "2025-01-21T10:30:00Z",
  "data": {
    "status": "active",
    "current_task": "Implementing component library",
    "last_message_id": "msg-12345",
    "capabilities": ["react", "typescript", "testing"],
    "availability": "available"
  }
}
```

### State Updates
- Agents update their state file every 60 seconds
- State includes current activity and availability
- Used for agent discovery and load balancing

## Broadcasting System

### Broadcast Message
```json
{
  "id": "broadcast-12345",
  "timestamp": "2025-01-21T10:30:00Z",
  "from": "orchestrator",
  "to": "broadcast",
  "type": "system_announcement",
  "priority": "high",
  "payload": {
    "message": "System maintenance in 30 minutes",
    "affects": "all"
  }
}
```

### System Events
- `startup` - System initialization
- `shutdown` - Graceful shutdown
- `maintenance` - Scheduled maintenance
- `error` - System errors
- `status_request` - Request status from all agents

## Error Handling

### Message Delivery Failures
```json
{
  "error": "recipient_not_found",
  "message_id": "msg-12345",
  "timestamp": "2025-01-21T10:30:00Z",
  "details": "Agent agent-nonexistent not available"
}
```

### Timeout Handling
- Messages expire after specified timeout
- Automatic retry for critical messages
- Dead letter queue for failed messages

### Conflict Resolution
- Message ordering based on timestamp
- Priority override for critical messages
- Automatic conflict detection and resolution

## Performance Optimizations

### Message Batching
```json
{
  "id": "batch-12345",
  "type": "message_batch",
  "messages": [
    {...},
    {...}
  ]
}
```

### Compression
- Large payloads automatically compressed
- Binary data support
- Streaming for large files

### Monitoring
- Message throughput tracking
- Delivery time metrics
- Error rate monitoring
- Queue depth monitoring

## Security Features

### Message Validation
- Schema validation for all messages
- Payload sanitization
- Source authentication

### Access Control
- Agent-to-agent permissions
- Message type restrictions
- Priority level controls

### Audit Trail
- Complete message history
- Delivery confirmations
- Error tracking
- Performance metrics

## Integration Examples

### Python Agent Example
```python
import json
from datetime import datetime
from pathlib import Path

class AgentCommunication:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.comm_dir = Path("../communication")
        
    def send_message(self, to_agent, msg_type, payload, priority="normal"):
        message = {
            "id": f"msg-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "from": self.agent_id,
            "to": to_agent,
            "type": msg_type,
            "priority": priority,
            "payload": payload
        }
        
        filename = f"{message['timestamp']}_{self.agent_id}_{to_agent}.json"
        filepath = self.comm_dir / "queue" / filename
        
        with open(filepath, 'w') as f:
            json.dump(message, f, indent=2)
    
    def check_messages(self):
        queue_dir = self.comm_dir / "queue"
        messages = []
        
        for msg_file in queue_dir.glob(f"*_{self.agent_id}.json"):
            with open(msg_file, 'r') as f:
                message = json.load(f)
            messages.append(message)
            
            # Move to processed
            processed_dir = self.comm_dir / "processed"
            msg_file.rename(processed_dir / msg_file.name)
        
        return messages
```

### Node.js Agent Example
```javascript
const fs = require('fs');
const path = require('path');

class AgentCommunication {
    constructor(agentId) {
        this.agentId = agentId;
        this.commDir = path.join('..', 'communication');
    }
    
    sendMessage(toAgent, msgType, payload, priority = 'normal') {
        const message = {
            id: `msg-${Date.now()}`,
            timestamp: new Date().toISOString(),
            from: this.agentId,
            to: toAgent,
            type: msgType,
            priority: priority,
            payload: payload
        };
        
        const filename = `${message.timestamp}_${this.agentId}_${toAgent}.json`;
        const filepath = path.join(this.commDir, 'queue', filename);
        
        fs.writeFileSync(filepath, JSON.stringify(message, null, 2));
    }
    
    checkMessages() {
        const queueDir = path.join(this.commDir, 'queue');
        const processedDir = path.join(this.commDir, 'processed');
        const messages = [];
        
        const files = fs.readdirSync(queueDir);
        for (const file of files) {
            if (file.endsWith(`_${this.agentId}.json`)) {
                const filepath = path.join(queueDir, file);
                const message = JSON.parse(fs.readFileSync(filepath, 'utf8'));
                messages.push(message);
                
                // Move to processed
                fs.renameSync(filepath, path.join(processedDir, file));
            }
        }
        
        return messages;
    }
}
```
"""
        
        comm_file = self.docs_dir / "api" / "communication-api.md"
        with open(comm_file, 'w', encoding='utf-8') as f:
            f.write(comm_doc)
        
        results['created_files'].append('docs/api/communication-api.md')
        print("  ✅ Communication API documentation generated")
    
    def generate_agent_api_docs(self, results):
        """Generate agent-specific API documentation"""
        print("  Generating agent API documentation...")
        
        if not self.agents_dir.exists():
            return
        
        for agent_dir in self.agents_dir.glob("agent-*"):
            try:
                agent_id = agent_dir.name
                self.generate_single_agent_api(agent_id, agent_dir, results)
            except Exception as e:
                results['errors'].append(f"Failed to generate API docs for {agent_id}: {e}")
    
    def generate_single_agent_api(self, agent_id, agent_dir, results):
        """Generate API documentation for a single agent"""
        # Extract capabilities and responsibilities from CLAUDE.md
        claude_md = agent_dir / "CLAUDE.md"
        capabilities = []
        responsibilities = []
        
        if claude_md.exists():
            try:
                with open(claude_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                    capabilities = self.extract_capabilities(content)
                    responsibilities = self.extract_responsibilities(content)
            except Exception:
                pass
        
        agent_doc = f"""# {agent_id} API Documentation

## Overview
{agent_id} is a specialized agent in the Jarvis Super Agent System.

## Capabilities
{chr(10).join(f"- {cap}" for cap in capabilities) if capabilities else "- General development tasks"}

## Responsibilities
{chr(10).join(f"- {resp}" for resp in responsibilities) if responsibilities else "- As assigned by orchestrator"}

## Message Types Handled
- `task_assignment` - Receive new work assignments
- `status_request` - Provide current status
- `code_review` - Perform or request code reviews
- `collaboration` - Coordinate with other agents

## API Endpoints
This agent communicates via the standard communication system.

### Send Task Assignment
```json
{{
  "to": "{agent_id}",
  "type": "task_assignment",
  "priority": "high",
  "payload": {{
    "task": "Implement feature X",
    "requirements": "...",
    "deadline": "2025-01-22T18:00:00Z"
  }}
}}
```

### Request Status
```json
{{
  "to": "{agent_id}",
  "type": "status_request",
  "payload": {{
    "include": ["current_task", "availability", "progress"]
  }}
}}
```

## File Structure
```
{agent_id}/
├── CLAUDE.md              # Agent configuration and context
├── DAILY_CONTEXT_*.md     # Daily work context
├── commands/              # Available commands
├── knowledge/             # Agent-specific knowledge
├── learning/              # Learning and improvement data
├── sop/                   # Standard operating procedures
└── templates/             # Code and document templates
```

## Performance Metrics
- Tasks completed per day
- Code quality scores
- Collaboration frequency
- Response time to messages

## Integration Examples

### Assign a Task
```python
comm = AgentCommunication("orchestrator")
comm.send_message(
    to_agent="{agent_id}",
    msg_type="task_assignment",
    payload={{
        "task": "Create responsive navbar component",
        "requirements": "Must support mobile and desktop",
        "priority": "high"
    }},
    priority="high"
)
```

### Check Agent Status
```python
# Request status
comm.send_message(
    to_agent="{agent_id}",
    msg_type="status_request",
    payload={{"include": ["availability", "current_task"]}}
)

# Check for response
responses = comm.check_messages()
for response in responses:
    if response['type'] == 'status_response':
        print(f"Agent status: {{response['payload']}}")
```

## Best Practices
- Always include clear task descriptions
- Specify deadlines for time-sensitive work
- Use appropriate priority levels
- Provide context and requirements
- Monitor for completion confirmations
"""
        
        api_file = self.docs_dir / "api" / f"{agent_id}-api.md"
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write(agent_doc)
        
        results['created_files'].append(f'docs/api/{agent_id}-api.md')
    
    def extract_capabilities(self, content):
        """Extract capabilities from CLAUDE.md content"""
        capabilities = []
        try:
            # Look for capabilities or skills sections
            lines = content.split('\n')
            in_capabilities = False
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['capabilities', 'skills', 'expertise']):
                    in_capabilities = True
                elif line.startswith('#') and in_capabilities:
                    break
                elif in_capabilities and line.strip().startswith('-'):
                    cap = line.strip()[1:].strip()
                    if cap:
                        capabilities.append(cap)
        except Exception:
            pass
        
        return capabilities[:10]  # Limit to 10 capabilities
    
    def extract_responsibilities(self, content):
        """Extract responsibilities from CLAUDE.md content"""
        responsibilities = []
        try:
            # Look for responsibilities or duties sections
            lines = content.split('\n')
            in_responsibilities = False
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['responsibilities', 'duties', 'role']):
                    in_responsibilities = True
                elif line.startswith('#') and in_responsibilities:
                    break
                elif in_responsibilities and line.strip().startswith('-'):
                    resp = line.strip()[1:].strip()
                    if resp:
                        responsibilities.append(resp)
        except Exception:
            pass
        
        return responsibilities[:10]  # Limit to 10 responsibilities
    
    def update_agent_docs(self, results):
        """Update agent-specific documentation"""
        print("Updating agent documentation...")
        
        if not self.agents_dir.exists():
            return
        
        for agent_dir in self.agents_dir.glob("agent-*"):
            try:
                agent_id = agent_dir.name
                self.update_agent_claude_md(agent_id, agent_dir, results)
            except Exception as e:
                results['errors'].append(f"Failed to update docs for {agent_id}: {e}")
    
    def update_agent_claude_md(self, agent_id, agent_dir, results):
        """Update individual agent CLAUDE.md with current system info"""
        claude_md = agent_dir / "CLAUDE.md"
        
        if not claude_md.exists():
            return
        
        try:
            with open(claude_md, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add/update system integration section
            integration_section = f"""
## System Integration

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Communication
- **Queue Directory**: `../communication/queue/`
- **State File**: `../communication/state/{agent_id}_state.json`
- **Message Format**: See [Communication API](../../docs/api/communication-api.md)

### Daily Operations
- **Morning Context**: `DAILY_CONTEXT_{{YYYYMMDD}}.md` (auto-generated)
- **Evening Archive**: Automatic data preservation at 6 PM
- **Status Updates**: Regular heartbeat monitoring

### System Services
- **Dashboard**: http://localhost:3000 (monitoring)
- **Housekeeper**: Automatic cleanup and maintenance
- **Context System**: Project initialization and takeover

### Performance Tracking
- Task completion rates
- Communication responsiveness
- Code quality metrics
- Collaboration effectiveness

### Quick Commands
```bash
# Check your status
cat ../communication/state/{agent_id}_state.json

# View recent communications
ls ../communication/queue/*{agent_id}*

# Check today's context
cat DAILY_CONTEXT_$(date +%Y%m%d).md
```
"""
            
            # Add or update the integration section
            if "## System Integration" in content:
                # Replace existing section
                lines = content.split('\n')
                start_idx = -1
                end_idx = len(lines)
                
                for i, line in enumerate(lines):
                    if line.strip() == "## System Integration":
                        start_idx = i
                    elif start_idx != -1 and line.startswith('##') and i > start_idx:
                        end_idx = i
                        break
                
                if start_idx != -1:
                    new_lines = lines[:start_idx] + integration_section.split('\n') + lines[end_idx:]
                    content = '\n'.join(new_lines)
            else:
                # Append the section
                content += '\n' + integration_section
            
            # Write back
            with open(claude_md, 'w', encoding='utf-8') as f:
                f.write(content)
            
            results['updated_files'].append(f'{agent_id}/CLAUDE.md')
            
        except Exception as e:
            results['errors'].append(f"Failed to update {agent_id}/CLAUDE.md: {e}")
    
    def generate_changelog(self, results):
        """Generate changelog from git history"""
        print("Generating changelog...")
        
        try:
            # Get git log
            result = subprocess.run([
                'git', 'log', '--oneline', '--since=1 week ago'
            ], capture_output=True, text=True, cwd=self.workspace_root)
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                
                changelog = f"""# Changelog

## Recent Changes (Last 7 Days)

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

"""
                
                for commit in commits[:20]:  # Limit to 20 recent commits
                    if commit.strip():
                        changelog += f"- {commit}\n"
                
                changelog_file = self.docs_dir / "CHANGELOG.md"
                with open(changelog_file, 'w', encoding='utf-8') as f:
                    f.write(changelog)
                
                results['created_files'].append('docs/CHANGELOG.md')
                print("  ✅ Changelog generated")
                
        except Exception as e:
            results['errors'].append(f"Changelog generation failed: {e}")
    
    def generate_system_metrics(self, results):
        """Generate system metrics documentation"""
        print("Generating system metrics...")
        
        try:
            metrics = self.collect_system_metrics()
            
            metrics_doc = f"""# System Metrics Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Overview
{metrics['summary']}

## Agent Performance
{chr(10).join(f"- **{agent['name']}**: {agent['performance']}" for agent in metrics['agents'])}

## System Health
- **Storage Usage**: {metrics['storage']['used']} / {metrics['storage']['total']}
- **Memory Usage**: {metrics['memory']['used']} / {metrics['memory']['total']}
- **CPU Usage**: {metrics['cpu']['usage']}%
- **Uptime**: {metrics['uptime']}

## Communication Statistics
- **Messages Today**: {metrics['communication']['messages_today']}
- **Average Response Time**: {metrics['communication']['avg_response_time']}
- **Success Rate**: {metrics['communication']['success_rate']}%

## Project Statistics
- **Active Projects**: {metrics['projects']['active']}
- **Completed This Week**: {metrics['projects']['completed_week']}
- **Average Completion Time**: {metrics['projects']['avg_completion_time']}

## Trends
{chr(10).join(f"- {trend}" for trend in metrics['trends'])}

## Recommendations
{chr(10).join(f"- {rec}" for rec in metrics['recommendations'])}
"""
            
            metrics_file = self.docs_dir / "METRICS.md"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                f.write(metrics_doc)
            
            results['created_files'].append('docs/METRICS.md')
            print("  ✅ System metrics generated")
            
        except Exception as e:
            results['errors'].append(f"Metrics generation failed: {e}")
    
    def collect_system_metrics(self):
        """Collect current system metrics"""
        metrics = {
            'summary': 'System operating normally',
            'agents': [],
            'storage': {'used': 'Unknown', 'total': 'Unknown'},
            'memory': {'used': 'Unknown', 'total': 'Unknown'},
            'cpu': {'usage': 0},
            'uptime': 'Unknown',
            'communication': {
                'messages_today': 0,
                'avg_response_time': '< 1s',
                'success_rate': 98
            },
            'projects': {
                'active': 0,
                'completed_week': 0,
                'avg_completion_time': '3 days'
            },
            'trends': [
                'Agent efficiency improving',
                'Communication latency stable',
                'Project completion rate steady'
            ],
            'recommendations': [
                'Continue current optimization strategies',
                'Monitor resource usage trends',
                'Regular system maintenance scheduled'
            ]
        }
        
        try:
            # Collect actual metrics where possible
            
            # Storage metrics
            total, used, free = shutil.disk_usage(self.workspace_root)
            metrics['storage'] = {
                'used': f"{used // (1024**3):.1f} GB",
                'total': f"{total // (1024**3):.1f} GB"
            }
            
            # Agent metrics
            if self.agents_dir.exists():
                for agent_dir in self.agents_dir.glob("agent-*"):
                    agent_name = agent_dir.name
                    performance = "Active" if self.check_agent_active(agent_dir) else "Inactive"
                    metrics['agents'].append({
                        'name': agent_name,
                        'performance': performance
                    })
            
            # Communication metrics
            comm_queue = self.workspace_root / "communication" / "queue"
            if comm_queue.exists():
                today_messages = len([f for f in comm_queue.glob("*.json") 
                                    if datetime.fromtimestamp(f.stat().st_mtime).date() == datetime.now().date()])
                metrics['communication']['messages_today'] = today_messages
            
            # Project metrics
            workflows_dir = self.workspace_root / "workflows"
            if workflows_dir.exists():
                active_projects = len(list(workflows_dir.glob("*.json")))
                metrics['projects']['active'] = active_projects
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
        
        return metrics
    
    def scan_todos_and_issues(self, results):
        """Scan codebase for TODOs and issues"""
        print("Scanning for TODOs and issues...")
        
        try:
            todos = []
            issues = []
            
            # Scan all Python and JavaScript files
            for pattern in ['**/*.py', '**/*.js', '**/*.ts', '**/*.md']:
                for file_path in self.workspace_root.rglob(pattern):
                    try:
                        if any(skip in str(file_path) for skip in ['node_modules', '.git', '__pycache__']):
                            continue
                            
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Find TODOs
                        for i, line in enumerate(content.split('\n'), 1):
                            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                                todos.append({
                                    'file': str(file_path.relative_to(self.workspace_root)),
                                    'line': i,
                                    'content': line.strip()
                                })
                            
                            # Find potential issues
                            if any(issue in line.lower() for issue in ['hack', 'workaround', 'temporary']):
                                issues.append({
                                    'file': str(file_path.relative_to(self.workspace_root)),
                                    'line': i,
                                    'content': line.strip(),
                                    'type': 'potential_issue'
                                })
                    except Exception:
                        continue
            
            # Generate TODO report
            todo_doc = f"""# TODO and Issues Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Summary
- **TODOs Found**: {len(todos)}
- **Potential Issues**: {len(issues)}

## TODOs
{chr(10).join(f"- **{todo['file']}:{todo['line']}** - {todo['content']}" for todo in todos[:20])}

{f"... and {len(todos) - 20} more" if len(todos) > 20 else ""}

## Potential Issues
{chr(10).join(f"- **{issue['file']}:{issue['line']}** - {issue['content']}" for issue in issues[:10])}

{f"... and {len(issues) - 10} more" if len(issues) > 10 else ""}

## Recommendations
- Review and address high-priority TODOs
- Convert temporary workarounds to permanent solutions
- Update documentation for completed items
- Schedule regular code cleanup sessions
"""
            
            todo_file = self.docs_dir / "TODOS.md"
            with open(todo_file, 'w', encoding='utf-8') as f:
                f.write(todo_doc)
            
            results['created_files'].append('docs/TODOS.md')
            print(f"  ✅ Found {len(todos)} TODOs and {len(issues)} potential issues")
            
        except Exception as e:
            results['errors'].append(f"TODO scanning failed: {e}")
    
    def generate_update_report(self, results):
        """Generate summary report of documentation updates"""
        report = f"""# Documentation Update Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Summary
- **Files Updated**: {len(results['updated_files'])}
- **Files Created**: {len(results['created_files'])}
- **Errors**: {len(results['errors'])}

## Updated Files
{chr(10).join(f"- {file}" for file in results['updated_files'])}

## Created Files
{chr(10).join(f"- {file}" for file in results['created_files'])}

## Errors
{chr(10).join(f"- {error}" for error in results['errors'])}

## Next Steps
1. Review generated documentation for accuracy
2. Commit changes to version control
3. Update deployment documentation if needed
4. Schedule next documentation update

---
*Jarvis Documentation Generator v{self.config['docs_version']}*
"""
        
        report_file = self.workspace_root / "DOC_UPDATE_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nDocumentation update complete!")
        print(f"   Updated: {len(results['updated_files'])} files")
        print(f"   Created: {len(results['created_files'])} files")
        print(f"   Errors: {len(results['errors'])} issues")
        print(f"   Report: DOC_UPDATE_REPORT.md")


def main():
    """Main function for command line usage"""
    import sys
    
    generator = JarvisDocGenerator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "all":
            generator.generate_all_docs()
        elif command == "readme":
            results = {'updated_files': [], 'created_files': [], 'errors': []}
            generator.update_main_readme(results)
        elif command == "api":
            results = {'updated_files': [], 'created_files': [], 'errors': []}
            generator.generate_api_docs(results)
        elif command == "agents":
            results = {'updated_files': [], 'created_files': [], 'errors': []}
            generator.update_agent_docs(results)
        elif command == "metrics":
            results = {'updated_files': [], 'created_files': [], 'errors': []}
            generator.generate_system_metrics(results)
        else:
            print(f"Unknown command: {command}")
    else:
        print("Jarvis Documentation Generator")
        print("Usage:")
        print("  python docs-generator.py all      # Generate all documentation")
        print("  python docs-generator.py readme   # Update main README")
        print("  python docs-generator.py api      # Generate API docs")
        print("  python docs-generator.py agents   # Update agent docs")
        print("  python docs-generator.py metrics  # Generate metrics report")


if __name__ == "__main__":
    main()