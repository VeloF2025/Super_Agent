#!/usr/bin/env python3
"""
Context Integration Wrapper - Seamless integration between existing context system and enhanced learning
Provides unified interface for all Super Agents to learn from actions and prevent repeated mistakes
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path

from jarvis_context_manager import JarvisContextManager
from enhanced_learning_system import EnhancedLearningSystem

logger = logging.getLogger(__name__)

class ContextLearningWrapper:
    """
    Unified wrapper that integrates:
    - Existing JarvisContextManager (crash recovery, task tracking)  
    - New EnhancedLearningSystem (mistake prevention, pattern learning)
    - Cross-agent knowledge sharing
    """
    
    def __init__(self, base_path: str = "./memory/context/jarvis"):
        self.base_path = Path(base_path)
        
        # Initialize both systems
        self.context_manager = JarvisContextManager(str(base_path))
        self.learning_system = EnhancedLearningSystem(str(base_path))
        
        # Agent action hooks
        self._action_hooks: List[Callable] = []
        
        logger.info("Context Learning Wrapper initialized")
    
    def register_action_hook(self, hook_func: Callable):
        """Register a function to be called on every agent action"""
        self._action_hooks.append(hook_func)
    
    def execute_with_learning(self, 
                            agent_id: str,
                            action_type: str,
                            action_context: Dict[str, Any],
                            action_func: Callable,
                            *args, **kwargs) -> Any:
        """
        Execute an action with automatic learning integration
        
        Args:
            agent_id: ID of the agent performing the action
            action_type: Type of action being performed
            action_context: Context information about the action
            action_func: The function to execute
            *args, **kwargs: Arguments for the action function
        
        Returns:
            Result of the action function
        """
        
        start_time = datetime.now()
        
        # Get preventive guidance before action
        guidance = self.learning_system.get_preventive_guidance(action_context, agent_id)
        
        # Log the action start
        self.context_manager.log_decision(
            decision_type='action_start',
            context=json.dumps(action_context),
            decision=f"Executing {action_type}",
            reasoning=f"Agent {agent_id} starting {action_type} with guidance: {len(guidance.get('recommendations', []))} recommendations"
        )
        
        success = False
        result = None
        error = None
        
        try:
            # Execute the actual action
            result = action_func(*args, **kwargs)
            success = True
            
            # Learn from successful action
            solution_context = {
                'action_type': action_type,
                'result': str(result)[:500] if result else None,  # Truncate large results
                'execution_time_ms': (datetime.now() - start_time).total_seconds() * 1000,
                'guidance_used': len(guidance.get('recommendations', []))
            }
            
            pattern_id = self.learning_system.learn_from_action(
                action_context=action_context,
                solution=solution_context,
                outcome='success',
                agent_id=agent_id,
                pattern_type=self._map_action_to_pattern_type(action_type)
            )
            
            # Update context manager
            self.context_manager.log_decision(
                decision_type='action_success',
                context=json.dumps(action_context),
                decision=f"Successfully completed {action_type}",
                reasoning=f"Learned pattern {pattern_id}",
                outcome='success'
            )
            
        except Exception as e:
            error = str(e)
            
            # Learn from failed action
            error_context = {
                'action_type': action_type,
                'error': error,
                'execution_time_ms': (datetime.now() - start_time).total_seconds() * 1000,
                'guidance_ignored': len(guidance.get('warnings', []))
            }
            
            pattern_id = self.learning_system.learn_from_action(
                action_context=action_context,
                solution=error_context,
                outcome='failure', 
                agent_id=agent_id,
                pattern_type=self._map_action_to_pattern_type(action_type)
            )
            
            # Update context manager
            self.context_manager.log_decision(
                decision_type='action_failure',
                context=json.dumps(action_context),
                decision=f"Failed to complete {action_type}",
                reasoning=f"Error: {error}, Learned pattern {pattern_id}",
                outcome='failure'
            )
            
            # Re-raise the exception
            raise
        
        finally:
            # Call registered hooks
            hook_data = {
                'agent_id': agent_id,
                'action_type': action_type,
                'action_context': action_context,
                'success': success,
                'result': result,
                'error': error,
                'guidance': guidance,
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
            
            for hook in self._action_hooks:
                try:
                    hook(hook_data)
                except Exception as e:
                    logger.error(f"Action hook failed: {e}")
        
        return result
    
    def _map_action_to_pattern_type(self, action_type: str) -> str:
        """Map action types to learning pattern types"""
        mapping = {
            'file_edit': 'typescript_error',
            'api_call': 'api_integration', 
            'build_process': 'build_configuration',
            'test_execution': 'workflow_optimization',
            'deployment': 'workflow_optimization',
            'error_resolution': 'workflow_optimization'
        }
        
        return mapping.get(action_type, 'workflow_optimization')
    
    def get_action_recommendations(self, 
                                 agent_id: str, 
                                 action_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations before performing an action"""
        return self.learning_system.get_preventive_guidance(action_context, agent_id)
    
    def share_knowledge_between_agents(self, 
                                     from_agent: str, 
                                     to_agent: str, 
                                     knowledge_types: List[str] = None):
        """Share learned patterns between agents"""
        transfer_count = self.learning_system.transfer_knowledge(
            from_agent, to_agent, knowledge_types
        )
        
        # Log the knowledge transfer
        self.context_manager.log_agent_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type='knowledge_transfer',
            content=f"Transferred {transfer_count} patterns",
            response='acknowledged'
        )
        
        return transfer_count
    
    def get_unified_status(self) -> Dict[str, Any]:
        """Get unified status of both context and learning systems"""
        context_status = self.context_manager.get_context_status()
        learning_report = self.learning_system.get_learning_report()
        
        return {
            'context_system': context_status,
            'learning_system': {
                'total_patterns': learning_report['total_patterns'],
                'learning_effectiveness': learning_report['learning_effectiveness'],
                'recent_transfers': len(learning_report['recent_knowledge_transfers'])
            },
            'integration_status': 'active',
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup_and_save(self):
        """Perform cleanup and save both systems"""
        # Save context manager state
        self.context_manager.save_context(recovery_point=True, reason="Integration cleanup")
        
        # The learning system auto-saves to database, but we can trigger consolidation
        # if needed in the future
        
        logger.info("Context and learning systems saved")


# Convenience decorators for easy integration

def learn_from_action(agent_id: str, action_type: str, context_wrapper: ContextLearningWrapper):
    """
    Decorator to automatically learn from function execution
    
    Usage:
    @learn_from_action('dev_agent', 'file_edit', wrapper)
    def edit_typescript_file(file_path, changes):
        # Function implementation
        pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract context from function arguments
            action_context = {
                'function_name': func.__name__,
                'args': str(args)[:200],  # Truncate long args
                'kwargs': {k: str(v)[:100] for k, v in kwargs.items()},  # Truncate values
                'timestamp': datetime.now().isoformat()
            }
            
            return context_wrapper.execute_with_learning(
                agent_id=agent_id,
                action_type=action_type,
                action_context=action_context,
                action_func=func,
                *args, **kwargs
            )
        return wrapper
    return decorator

def with_recommendations(agent_id: str, context_wrapper: ContextLearningWrapper):
    """
    Decorator to get recommendations before function execution
    
    Usage:
    @with_recommendations('dev_agent', wrapper) 
    def complex_operation(data):
        # Function will receive recommendations in kwargs['_recommendations']
        pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate context for recommendations
            action_context = {
                'function_name': func.__name__,
                'args_summary': str(args)[:200]
            }
            
            recommendations = context_wrapper.get_action_recommendations(agent_id, action_context)
            
            # Add recommendations to kwargs
            kwargs['_recommendations'] = recommendations
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage
    wrapper = ContextLearningWrapper()
    
    # Example: Decorated function with automatic learning
    @learn_from_action('test_agent', 'file_edit', wrapper)
    def edit_file(file_path: str, content: str):
        """Example function that edits a file"""
        print(f"Editing {file_path} with content: {content[:50]}...")
        # Simulate file editing
        return f"Successfully edited {file_path}"
    
    # Test the decorated function
    try:
        result = edit_file("/path/to/file.ts", "const x: string = 'hello';")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Get unified status
    status = wrapper.get_unified_status()
    print(f"System status: {json.dumps(status, indent=2)}")