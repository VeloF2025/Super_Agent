#!/usr/bin/env python3
"""
Integration layer for JarvisContextManager with existing orchestrator systems.
Provides seamless context persistence without modifying core orchestrator code.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from jarvis_context_manager import JarvisContextManager

logger = logging.getLogger(__name__)


class JarvisOrchestratorWithContext:
    """Wrapper class that adds context persistence to any orchestrator."""
    
    def __init__(self, orchestrator_instance: Any, context_path: str = "./memory/context/jarvis"):
        self.orchestrator = orchestrator_instance
        self.context_manager = JarvisContextManager(context_path)
        self._setup_hooks()
        
        # Restore previous context if available
        if self.context_manager.restore_context():
            logger.info("Previous context restored successfully")
            self._resume_from_context()
    
    def _setup_hooks(self):
        """Setup method interceptors for context tracking."""
        # Intercept key orchestrator methods
        self._wrap_method('assign_task', self._before_assign_task, self._after_assign_task)
        self._wrap_method('receive_message', self._before_receive_message, self._after_receive_message)
        self._wrap_method('make_decision', self._before_decision, self._after_decision)
        self._wrap_method('handle_error', self._before_error, self._after_error)
    
    def _wrap_method(self, method_name: str, before_hook: Callable = None, after_hook: Callable = None):
        """Wrap orchestrator method with context hooks."""
        if hasattr(self.orchestrator, method_name):
            original_method = getattr(self.orchestrator, method_name)
            
            @wraps(original_method)
            def wrapped(*args, **kwargs):
                # Before hook
                if before_hook:
                    before_hook(method_name, args, kwargs)
                
                # Call original method
                result = original_method(*args, **kwargs)
                
                # After hook
                if after_hook:
                    after_hook(method_name, result, args, kwargs)
                
                return result
            
            setattr(self.orchestrator, method_name, wrapped)
    
    def _before_assign_task(self, method_name: str, args: tuple, kwargs: dict):
        """Called before task assignment."""
        task_data = args[0] if args else kwargs.get('task')
        if task_data:
            self.context_manager.active_context['current_task'] = {
                'id': task_data.get('id'),
                'description': task_data.get('description'),
                'status': 'assigning',
                'assigned_agents': []
            }
            self.context_manager.mark_recovery_point(f"Assigning task: {task_data.get('id')}")
    
    def _after_assign_task(self, method_name: str, result: Any, args: tuple, kwargs: dict):
        """Called after task assignment."""
        if result and 'assigned_to' in result:
            self.context_manager.active_context['current_task']['assigned_agents'] = result['assigned_to']
            self.context_manager.active_context['current_task']['status'] = 'assigned'
            
            # Initialize task progress
            task_id = self.context_manager.active_context['current_task']['id']
            self.context_manager.update_task_progress(task_id, {
                'description': self.context_manager.active_context['current_task']['description'],
                'status': 'in_progress',
                'percentage': 0,
                'completed_subtasks': [],
                'blockers': []
            })
    
    def _before_receive_message(self, method_name: str, args: tuple, kwargs: dict):
        """Called before receiving message from agent."""
        message = args[0] if args else kwargs.get('message')
        if message:
            self.context_manager.active_context['conversation_history'].append({
                'timestamp': datetime.now().isoformat(),
                'from': message.get('from_agent'),
                'type': message.get('type'),
                'content': message.get('content')[:500]  # Truncate for storage
            })
    
    def _after_receive_message(self, method_name: str, result: Any, args: tuple, kwargs: dict):
        """Called after processing agent message."""
        message = args[0] if args else kwargs.get('message')
        if message and result:
            # Update agent state
            agent_id = message.get('from_agent')
            if agent_id:
                self.context_manager.update_agent_state(agent_id, {
                    'status': message.get('status', 'active'),
                    'current_task': message.get('task_id'),
                    'capabilities': message.get('capabilities', [])
                })
            
            # Log inter-agent communication
            if 'response_to' in message:
                self.context_manager.log_agent_message(
                    from_agent=agent_id,
                    to_agent=message.get('response_to'),
                    message_type=message.get('type'),
                    content=str(message.get('content'))[:1000],
                    response=str(result)[:1000]
                )
    
    def _before_decision(self, method_name: str, args: tuple, kwargs: dict):
        """Called before making orchestration decision."""
        context = kwargs.get('context', {})
        self.context_manager.active_context['workflow_state']['phase'] = 'decision_making'
    
    def _after_decision(self, method_name: str, result: Any, args: tuple, kwargs: dict):
        """Called after making orchestration decision."""
        if result:
            self.context_manager.log_decision(
                decision_type=kwargs.get('decision_type', 'general'),
                context=str(kwargs.get('context', {}))[:500],
                decision=str(result.get('decision', ''))[:500],
                reasoning=str(result.get('reasoning', ''))[:500],
                outcome=str(result.get('outcome', 'pending'))[:500]
            )
    
    def _before_error(self, method_name: str, args: tuple, kwargs: dict):
        """Called before error handling."""
        error = args[0] if args else kwargs.get('error')
        if error:
            self.context_manager.active_context['error_recovery'] = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.now().isoformat(),
                'recovery_attempts': 0
            }
    
    def _after_error(self, method_name: str, result: Any, args: tuple, kwargs: dict):
        """Called after error handling."""
        if result and result.get('recovered'):
            self.context_manager.active_context['error_recovery']['recovered'] = True
            self.context_manager.mark_recovery_point("Error recovered")
    
    def _resume_from_context(self):
        """Resume operations from restored context."""
        context = self.context_manager.active_context
        
        # Resume current task if any
        if context['current_task']['id'] and context['current_task']['status'] != 'completed':
            logger.info(f"Resuming task: {context['current_task']['id']}")
            # Notify orchestrator to resume task
            if hasattr(self.orchestrator, 'resume_task'):
                self.orchestrator.resume_task(context['current_task'])
        
        # Check for stale agents
        for agent_id, state in context['agent_states'].items():
            last_update = datetime.fromisoformat(state['last_update'])
            if (datetime.now() - last_update).seconds > 300:  # 5 minutes
                logger.warning(f"Agent {agent_id} is stale, sending recovery ping")
                if hasattr(self.orchestrator, 'ping_agent'):
                    self.orchestrator.ping_agent(agent_id)
    
    def get_context_status(self) -> Dict[str, Any]:
        """Get current context status."""
        return self.context_manager.get_context_status()
    
    def manual_checkpoint(self, reason: str):
        """Create manual checkpoint."""
        self.context_manager.mark_recovery_point(reason)
    
    def __getattr__(self, name):
        """Proxy all other attributes to wrapped orchestrator."""
        return getattr(self.orchestrator, name)


class AsyncJarvisOrchestratorWithContext(JarvisOrchestratorWithContext):
    """Async version of the orchestrator wrapper."""
    
    def _wrap_method(self, method_name: str, before_hook: Callable = None, after_hook: Callable = None):
        """Wrap async orchestrator method with context hooks."""
        if hasattr(self.orchestrator, method_name):
            original_method = getattr(self.orchestrator, method_name)
            
            @wraps(original_method)
            async def wrapped(*args, **kwargs):
                # Before hook
                if before_hook:
                    before_hook(method_name, args, kwargs)
                
                # Call original method
                result = await original_method(*args, **kwargs)
                
                # After hook  
                if after_hook:
                    after_hook(method_name, result, args, kwargs)
                
                return result
            
            setattr(self.orchestrator, method_name, wrapped)


def integrate_context_manager(orchestrator_class):
    """Decorator to add context management to any orchestrator class."""
    class ContextAwareOrchestrator(orchestrator_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._context_wrapper = JarvisOrchestratorWithContext(self)
        
        def get_context_status(self):
            return self._context_wrapper.get_context_status()
        
        def manual_checkpoint(self, reason: str):
            self._context_wrapper.manual_checkpoint(reason)
    
    return ContextAwareOrchestrator


# Example usage patterns
"""
# Method 1: Wrap existing orchestrator instance
orchestrator = YourExistingOrchestrator()
jarvis = JarvisOrchestratorWithContext(orchestrator)

# Method 2: Use decorator on orchestrator class
@integrate_context_manager
class YourOrchestrator:
    def assign_task(self, task):
        # Your implementation
        pass

# Method 3: For async orchestrators
async_orchestrator = YourAsyncOrchestrator()
jarvis = AsyncJarvisOrchestratorWithContext(async_orchestrator)
"""