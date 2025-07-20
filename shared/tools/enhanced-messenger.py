#!/usr/bin/env python3
"""
Enhanced Messenger - Extension for existing communication system
Adds project-awareness while maintaining full compatibility
"""

import json
import os
from pathlib import Path
from datetime import datetime
import time
import uuid

class EnhancedMessenger:
    """Enhanced messenger that supports both regular and project-scoped communication"""
    
    def __init__(self, agent_id=None, project_context=None):
        # Auto-detect agent_id from config if not provided
        if not agent_id:
            config_path = Path(".agent-config.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    agent_id = config["agent_id"]
            else:
                # Try to detect from current directory
                current_dir = Path.cwd()
                if current_dir.name.startswith("agent-"):
                    agent_id = current_dir.name
                else:
                    raise ValueError("Could not determine agent_id")
        
        self.agent_id = agent_id
        self.project_context = project_context
        
        # Use existing communication system paths
        super_agent_root = self._find_super_agent_root()
        self.shared_comm = super_agent_root / "shared" / "communication"
        
        # Standard communication paths (existing system)
        self.queue = self.shared_comm / "queue"
        self.events = self.shared_comm / "events"
        self.state = self.shared_comm / "state"
        
        # Project-specific paths (if in project context)
        if project_context:
            project_root = super_agent_root / "projects" / project_context["project_name"]
            self.project_comm = project_root / "agent-workspace" / "communication"
            self.project_queue = self.project_comm / "queue"
            self.project_events = self.project_comm / "events"
            self.project_state = self.project_comm / "state"
            
            # Ensure project communication directories exist
            for dir_path in [self.project_queue, self.project_events, self.project_state]:
                dir_path.mkdir(parents=True, exist_ok=True)
    
    def _find_super_agent_root(self):
        """Find Super Agent root directory"""
        current = Path.cwd()
        while current.parent != current:
            if (current / "agents").exists() and (current / "shared").exists():
                return current
            current = current.parent
        
        # Default fallback
        return Path("C:/Jarvis/Super Agent")
    
    def send_task_assignment(self, to_agent, task_description, priority="medium", 
                           project_specific=False, **kwargs):
        """Send task assignment using existing message format with project support"""
        
        message = {
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "from_agent": self.agent_id,
            "to_agent": to_agent,
            "task_id": kwargs.get("task_id", f"task-{int(time.time() * 1000)}"),
            "task_description": task_description,
            "priority_level": priority,
            "quality_requirements": kwargs.get("quality_requirements", "standard_excellence"),
            "evidence_requirements": kwargs.get("evidence_requirements", "documentation_required"),
            "innovation_potential": kwargs.get("innovation_potential", "evaluate_opportunities"),
            "first_principles_analysis": kwargs.get("first_principles_analysis", "recommended"),
            "deadline": kwargs.get("deadline", "reasonable_timeline"),
            "success_criteria": kwargs.get("success_criteria", "meets_quality_standards")
        }
        
        # Add project context if applicable
        if self.project_context or project_specific:
            message.update({
                "project_context": self.project_context,
                "project_name": self.project_context.get("project_name") if self.project_context else kwargs.get("project_name"),
                "output_target_directory": kwargs.get("output_target", "app"),
                "deployment_scope": kwargs.get("deployment_scope", "app_only")
            })
        
        # Add optional fields
        for field in ["context_links", "dependency_tasks", "resource_requirements", "learning_objectives"]:
            if field in kwargs:
                message[field] = kwargs[field]
        
        return self._send_message(message, "task_assignment", project_specific)
    
    def send_status_update(self, task_id, status, progress_percentage, 
                          quality_score=99.0, project_specific=False, **kwargs):
        """Send status update using existing format"""
        
        message = {
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "from_agent": self.agent_id,
            "task_id": task_id,
            "status": status,
            "progress_percentage": progress_percentage,
            "quality_score": quality_score,
            "evidence_validation": kwargs.get("evidence_validation", "verified"),
            "innovation_insights": kwargs.get("innovation_insights", "evaluated"),
            "next_steps": kwargs.get("next_steps", "continue_as_planned")
        }
        
        # Add optional fields
        for field in ["blockers", "resource_needs", "learning_discoveries", "breakthrough_opportunities"]:
            if field in kwargs:
                message[field] = kwargs[field]
        
        return self._send_message(message, "status_update", project_specific)
    
    def send_project_coordination(self, coordination_type, project_name, 
                                assigned_agents, deliverable_targets, **kwargs):
        """Send project coordination message (new capability)"""
        
        message = {
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "from_agent": self.agent_id,
            "project_name": project_name,
            "coordination_type": coordination_type,
            "project_phase": kwargs.get("project_phase", "development"),
            "assigned_agents": assigned_agents,
            "deliverable_targets": deliverable_targets,
            "quality_requirements": kwargs.get("quality_requirements", "standard_excellence")
        }
        
        # Add optional fields
        for field in ["project_type", "deadline", "resource_allocation", 
                     "communication_protocol", "deployment_strategy"]:
            if field in kwargs:
                message[field] = kwargs[field]
        
        return self._send_message(message, "project_coordination", project_specific=True)
    
    def _send_message(self, message, message_type, project_specific=False):
        """Send message to appropriate queue"""
        
        # Choose queue based on context
        if project_specific and hasattr(self, 'project_queue'):
            queue_dir = self.project_queue
            queue_type = "project"
        else:
            queue_dir = self.queue / "incoming"
            queue_type = "system"
        
        # Create filename using existing naming convention
        timestamp = message['timestamp'].replace(':', '-').replace('.', '-')
        filename = f"{timestamp}_{self.agent_id}_{message_type}.json"
        filepath = queue_dir / filename
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Write message
        with open(filepath, "w") as f:
            json.dump(message, f, indent=2)
        
        print(f"📤 Sent {message_type} to {queue_type} queue: {filename}")
        return message["message_id"]
    
    def receive_messages(self, project_specific=False, message_types=None):
        """Check for new messages in appropriate queue"""
        messages = []
        
        # Choose queue based on context
        if project_specific and hasattr(self, 'project_queue'):
            check_dirs = [self.project_queue]
        else:
            check_dirs = [self.queue / "incoming", self.queue / "processing"]
        
        for queue_dir in check_dirs:
            if not queue_dir.exists():
                continue
                
            for filepath in sorted(queue_dir.glob("*.json")):
                try:
                    with open(filepath, "r") as f:
                        message = json.load(f)
                    
                    # Check if message is for this agent
                    if message.get("to_agent") in [self.agent_id, "all", "broadcast"]:
                        # Filter by message type if specified
                        if message_types and filepath.name.split("_")[-1].replace(".json", "") not in message_types:
                            continue
                            
                        messages.append(message)
                        
                        # Move to processed (maintain existing behavior)
                        processed = queue_dir / "processed"
                        processed.mkdir(exist_ok=True)
                        filepath.rename(processed / filepath.name)
                        
                except Exception as e:
                    print(f"Error reading message {filepath}: {e}")
                    continue
        
        return messages
    
    def update_agent_status(self, status, details=None, project_specific=False):
        """Update agent status in appropriate state directory"""
        
        state_data = {
            "agent_id": self.agent_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        # Add project context if applicable
        if self.project_context:
            state_data["project_context"] = self.project_context
        
        # Choose state directory
        if project_specific and hasattr(self, 'project_state'):
            state_dir = self.project_state
        else:
            state_dir = self.state
        
        state_dir.mkdir(parents=True, exist_ok=True)
        filepath = state_dir / f"{self.agent_id}_state.json"
        
        with open(filepath, "w") as f:
            json.dump(state_data, f, indent=2)
    
    def broadcast_event(self, event_type, data, project_specific=False):
        """Broadcast event using existing event system"""
        
        event = {
            "id": f"evt-{int(time.time() * 1000)}",
            "agent_id": self.agent_id,
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Add project context if applicable
        if self.project_context:
            event["project_context"] = self.project_context
        
        # Choose events directory
        if project_specific and hasattr(self, 'project_events'):
            events_dir = self.project_events / "triggers"
        else:
            events_dir = self.events / "triggers"
        
        events_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = event['timestamp'].replace(':', '-').replace('.', '-')
        filename = f"{timestamp}_{event['type']}_{self.agent_id}.json"
        filepath = events_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(event, f, indent=2)
        
        print(f"📢 Broadcast event: {event_type}")
    
    def set_project_context(self, project_name, project_type=None, output_target=None):
        """Set project context for this messenger instance"""
        self.project_context = {
            "project_name": project_name,
            "project_type": project_type,
            "output_target": output_target or "app",
            "agent_workspace": f"projects/{project_name}/agent-workspace/agents/{self.agent_id}"
        }
        
        # Update project communication paths
        super_agent_root = self._find_super_agent_root()
        project_root = super_agent_root / "projects" / project_name
        self.project_comm = project_root / "agent-workspace" / "communication"
        self.project_queue = self.project_comm / "queue"
        self.project_events = self.project_comm / "events"
        self.project_state = self.project_comm / "state"
        
        print(f"🎯 Project context set: {project_name}")


# Example usage demonstrating both existing and project capabilities
if __name__ == "__main__":
    # Standard usage (existing functionality)
    messenger = EnhancedMessenger("agent-development-001")
    
    # Send regular system task
    messenger.send_task_assignment(
        to_agent="agent-quality-001",
        task_description="Review code quality standards",
        priority="high"
    )
    
    # Set project context and send project-specific task
    messenger.set_project_context("my-saas-app", "fullstack", "app")
    
    task_id = messenger.send_task_assignment(
        to_agent="agent-frontend-001",
        task_description="Create login component",
        priority="medium",
        project_specific=True,
        output_target="app/src/components",
        deployment_scope="app_only"
    )
    
    # Send project coordination message
    messenger.send_project_coordination(
        coordination_type="task_distribution",
        project_name="my-saas-app",
        assigned_agents=["agent-frontend-001", "agent-backend-001"],
        deliverable_targets=["app_directory", "documentation"],
        project_phase="development"
    )
    
    # Update status for project work
    messenger.send_status_update(
        task_id=task_id,
        status="in_progress",
        progress_percentage=75,
        project_specific=True
    )
    
    # Check for both system and project messages
    system_messages = messenger.receive_messages(project_specific=False)
    project_messages = messenger.receive_messages(project_specific=True)
    
    print(f"System messages: {len(system_messages)}")
    print(f"Project messages: {len(project_messages)}")