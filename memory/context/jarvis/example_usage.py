#!/usr/bin/env python3
"""
Example usage of JarvisContextManager for context persistence.
Shows integration patterns and best practices.
"""

import asyncio
import logging
import time
from jarvis_context_manager import JarvisContextManager
from jarvis_orchestrator_integration import JarvisOrchestratorWithContext, integrate_context_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example 1: Simple Orchestrator with Context Persistence
class SimpleOrchestrator:
    """Example orchestrator class."""
    
    def __init__(self):
        self.agents = {}
        self.tasks = {}
    
    def assign_task(self, task):
        """Assign task to agent."""
        logger.info(f"Assigning task: {task['id']}")
        # Simulate task assignment
        assigned_agent = "agent-001"
        self.tasks[task['id']] = {
            'assigned_to': [assigned_agent],
            'status': 'assigned'
        }
        return {'assigned_to': [assigned_agent]}
    
    def receive_message(self, message):
        """Process agent message."""
        logger.info(f"Received message from {message['from_agent']}")
        return {'processed': True}
    
    def make_decision(self, decision_type, context):
        """Make orchestration decision."""
        decision = f"Decision for {decision_type}"
        return {
            'decision': decision,
            'reasoning': 'Based on current context',
            'outcome': 'pending'
        }


# Example 2: Using the decorator pattern
@integrate_context_manager
class ContextAwareOrchestrator:
    """Orchestrator with automatic context management."""
    
    def __init__(self):
        self.name = "ContextAwareOrchestrator"
    
    def process_task(self, task_id):
        # Context is automatically saved
        logger.info(f"Processing task {task_id}")
        return True


def example_basic_usage():
    """Basic usage example."""
    print("\n=== Basic Context Manager Usage ===")
    
    # Create context manager
    cm = JarvisContextManager()
    
    # Update task progress
    cm.update_task_progress("task-001", {
        "description": "Process data files",
        "status": "in_progress",
        "percentage": 25,
        "completed_subtasks": ["file_validation"],
        "blockers": []
    })
    
    # Log a decision
    cm.log_decision(
        decision_type="resource_allocation",
        context="High priority task with deadline",
        decision="Allocate agent-001 and agent-002",
        reasoning="Both agents have required capabilities",
        outcome="success"
    )
    
    # Create manual checkpoint
    cm.mark_recovery_point("Completed phase 1 of processing")
    
    # Get status
    status = cm.get_context_status()
    print(f"Current status: {status}")


def example_orchestrator_integration():
    """Example of integrating with existing orchestrator."""
    print("\n=== Orchestrator Integration Example ===")
    
    # Create base orchestrator
    base_orchestrator = SimpleOrchestrator()
    
    # Wrap with context management
    orchestrator = JarvisOrchestratorWithContext(base_orchestrator)
    
    # Use normally - context is automatically tracked
    task = {
        'id': 'task-002',
        'description': 'Analyze system logs',
        'priority': 'high'
    }
    
    result = orchestrator.assign_task(task)
    print(f"Task assigned: {result}")
    
    # Simulate agent message
    message = {
        'from_agent': 'agent-001',
        'type': 'progress_update',
        'content': 'Task 50% complete',
        'task_id': 'task-002',
        'status': 'active'
    }
    
    orchestrator.receive_message(message)
    
    # Make decision
    decision = orchestrator.make_decision(
        decision_type='next_action',
        context={'current_load': 0.7}
    )
    print(f"Decision made: {decision}")
    
    # Check context status
    status = orchestrator.get_context_status()
    print(f"Context status: {status}")


def example_crash_recovery():
    """Example of crash recovery."""
    print("\n=== Crash Recovery Example ===")
    
    # Simulate a crash by creating marker
    cm = JarvisContextManager()
    
    # Add some context
    cm.update_task_progress("task-003", {
        "description": "Critical data processing",
        "status": "in_progress", 
        "percentage": 75,
        "completed_subtasks": ["validation", "transformation"],
        "blockers": []
    })
    
    # Save and simulate crash
    cm.save_context()
    cm.crash_marker.touch()
    
    # Create new instance (simulates restart)
    cm2 = JarvisContextManager()
    
    # Recovery happens automatically in __init__
    # Check recovered context
    if 'task-003' in cm2.active_context['task_progress']:
        print("Successfully recovered task progress!")
        print(f"Task status: {cm2.active_context['task_progress']['task-003']}")


async def example_async_monitoring():
    """Example of real-time monitoring."""
    print("\n=== Async Monitoring Example ===")
    
    cm = JarvisContextManager()
    
    async def monitor_loop():
        """Monitor context changes."""
        for i in range(5):
            status = cm.get_context_status()
            print(f"Monitor update {i}: Active agents: {status['active_agents']}")
            await asyncio.sleep(2)
    
    async def work_loop():
        """Simulate work."""
        for i in range(5):
            cm.update_agent_state(f"agent-{i:03d}", {
                "status": "active",
                "current_task": f"task-{i:03d}"
            })
            await asyncio.sleep(1.5)
    
    # Run both loops concurrently
    await asyncio.gather(monitor_loop(), work_loop())


def example_api_integration():
    """Example of API endpoint integration."""
    print("\n=== API Integration Example ===")
    
    # This would typically be in your FastAPI app
    from context_monitor_api import router, set_context_manager
    
    cm = JarvisContextManager()
    set_context_manager(cm)
    
    print("API endpoints now available:")
    print("- GET  /api/jarvis/context/status")
    print("- GET  /api/jarvis/context/agent-states")
    print("- GET  /api/jarvis/context/task-progress")
    print("- POST /api/jarvis/context/checkpoint")
    print("- GET  /api/jarvis/context/metrics")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    time.sleep(1)
    
    example_orchestrator_integration()
    time.sleep(1)
    
    example_crash_recovery()
    time.sleep(1)
    
    # Run async example
    asyncio.run(example_async_monitoring())
    
    example_api_integration()
    
    print("\n=== All examples completed ===")
    print("Check ./memory/context/jarvis/ for persisted data")