#!/usr/bin/env python3
"""
Agent Learning Adapter - Automatic integration for all Super Agent types
Provides seamless learning integration without modifying existing agent code
"""

import json
import logging
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from context_integration_wrapper import ContextLearningWrapper

logger = logging.getLogger(__name__)

class AgentLearningAdapter:
    """
    Automatic learning adapter that monitors agent activities and learns from them
    Integrates with existing Super Agent architecture without code changes
    """
    
    def __init__(self, base_path: str = "./memory/context/jarvis"):
        self.wrapper = ContextLearningWrapper(base_path)
        self.active_agents = {}  # agent_id -> agent_info
        self.learning_active = True
        self._monitor_thread = None
        
        # Agent type configurations
        self.agent_configs = {
            'development_agent': {
                'learning_priority': ['typescript_error', 'import_resolution', 'build_configuration'],
                'knowledge_sharing': ['devops_agent', 'testing_agent'],
                'auto_recommend': True
            },
            'devops_agent': {
                'learning_priority': ['workflow_optimization', 'api_integration'],
                'knowledge_sharing': ['development_agent'],
                'auto_recommend': True
            },
            'quality_agent': {
                'learning_priority': ['security_vulnerability', 'workflow_optimization'],
                'knowledge_sharing': ['development_agent', 'devops_agent'],
                'auto_recommend': True
            },
            'research_agent': {
                'learning_priority': ['workflow_optimization'],
                'knowledge_sharing': ['development_agent'],
                'auto_recommend': False
            },
            'housekeeper_agent': {
                'learning_priority': ['workflow_optimization'],
                'knowledge_sharing': [],
                'auto_recommend': False
            }
        }
        
        self._start_monitoring()
        
        # Register learning hooks
        self.wrapper.register_action_hook(self._on_action_completed)
        
        logger.info("Agent Learning Adapter initialized")
    
    def register_agent(self, agent_id: str, agent_type: str, metadata: Dict[str, Any] = None):
        """Register an agent for learning monitoring"""
        self.active_agents[agent_id] = {
            'agent_type': agent_type,
            'registered_at': datetime.now(),
            'metadata': metadata or {},
            'action_count': 0,
            'learning_patterns': 0,
            'last_activity': datetime.now()
        }
        
        # Share existing knowledge if configured
        self._share_relevant_knowledge(agent_id, agent_type)
        
        logger.info(f"Registered agent {agent_id} of type {agent_type}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            logger.info(f"Unregistered agent {agent_id}")
    
    def monitor_agent_action(self, 
                           agent_id: str, 
                           action_type: str,
                           context: Dict[str, Any],
                           result: Any = None,
                           error: Exception = None):
        """
        Monitor and learn from an agent action
        This can be called manually or automatically via monitoring
        """
        
        if not self.learning_active or agent_id not in self.active_agents:
            return
        
        # Update agent activity
        self.active_agents[agent_id]['last_activity'] = datetime.now()
        self.active_agents[agent_id]['action_count'] += 1
        
        # Determine outcome
        outcome = 'success' if error is None else 'failure'
        
        # Prepare learning context
        learning_context = {
            **context,
            'agent_type': self.active_agents[agent_id]['agent_type'],
            'action_sequence_id': self._generate_sequence_id(agent_id),
            'session_context': self._get_session_context(agent_id)
        }
        
        # Prepare solution/error context
        if error:
            solution_context = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'action_type': action_type,
                'attempted_solution': context.get('attempted_solution', 'unknown')
            }
        else:
            solution_context = {
                'action_type': action_type,
                'result_summary': str(result)[:200] if result else None,
                'success_factors': context.get('success_factors', [])
            }
        
        # Learn from the action
        try:
            pattern_id = self.wrapper.learning_system.learn_from_action(
                action_context=learning_context,
                solution=solution_context,
                outcome=outcome,
                agent_id=agent_id
            )
            
            self.active_agents[agent_id]['learning_patterns'] += 1
            
            # Auto-share knowledge if configured
            self._auto_share_knowledge(agent_id, pattern_id)
            
        except Exception as e:
            logger.error(f"Failed to learn from action: {e}")
    
    def get_agent_recommendations(self, 
                                agent_id: str, 
                                planned_action: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations for an agent before performing an action"""
        
        if agent_id not in self.active_agents:
            return {'recommendations': [], 'warnings': []}
        
        agent_type = self.active_agents[agent_id]['agent_type']
        config = self.agent_configs.get(agent_type, {})
        
        if not config.get('auto_recommend', False):
            return {'recommendations': [], 'warnings': []}
        
        # Enhance context with agent-specific information
        enhanced_context = {
            **planned_action,
            'agent_type': agent_type,
            'agent_experience': self.active_agents[agent_id]['action_count'],
            'session_context': self._get_session_context(agent_id)
        }
        
        return self.wrapper.get_action_recommendations(agent_id, enhanced_context)
    
    def _share_relevant_knowledge(self, agent_id: str, agent_type: str):
        """Share relevant existing knowledge with a new agent"""
        config = self.agent_configs.get(agent_type, {})
        sharing_targets = config.get('knowledge_sharing', [])
        
        # Find agents to share knowledge from
        source_agents = [
            aid for aid, info in self.active_agents.items()
            if info['agent_type'] in sharing_targets and info['learning_patterns'] > 0
        ]
        
        total_transferred = 0
        for source_agent in source_agents:
            try:
                transfer_count = self.wrapper.share_knowledge_between_agents(
                    from_agent=source_agent,
                    to_agent=agent_id,
                    knowledge_types=config.get('learning_priority')
                )
                total_transferred += transfer_count
            except Exception as e:
                logger.error(f"Failed to transfer knowledge from {source_agent} to {agent_id}: {e}")
        
        if total_transferred > 0:
            logger.info(f"Transferred {total_transferred} patterns to new agent {agent_id}")
    
    def _auto_share_knowledge(self, agent_id: str, pattern_id: str):
        """Automatically share new knowledge with relevant agents"""
        if agent_id not in self.active_agents:
            return
        
        agent_type = self.active_agents[agent_id]['agent_type']
        config = self.agent_configs.get(agent_type, {})
        sharing_targets = config.get('knowledge_sharing', [])
        
        # Find target agents
        target_agents = [
            aid for aid, info in self.active_agents.items()
            if info['agent_type'] in sharing_targets and aid != agent_id
        ]
        
        # Share with each target
        for target_agent in target_agents:
            try:
                self.wrapper.share_knowledge_between_agents(
                    from_agent=agent_id,
                    to_agent=target_agent
                )
            except Exception as e:
                logger.error(f"Failed to auto-share knowledge: {e}")
    
    def _generate_sequence_id(self, agent_id: str) -> str:
        """Generate a sequence ID for tracking related actions"""
        timestamp = int(time.time())
        action_count = self.active_agents[agent_id]['action_count']
        return f"{agent_id}_{timestamp}_{action_count}"
    
    def _get_session_context(self, agent_id: str) -> Dict[str, Any]:
        """Get current session context for an agent"""
        if agent_id not in self.active_agents:
            return {}
        
        agent_info = self.active_agents[agent_id]
        return {
            'session_duration_minutes': (datetime.now() - agent_info['registered_at']).total_seconds() / 60,
            'actions_performed': agent_info['action_count'],
            'patterns_learned': agent_info['learning_patterns'],
            'agent_type': agent_info['agent_type']
        }
    
    def _on_action_completed(self, hook_data: Dict[str, Any]):
        """Hook called when any action is completed"""
        agent_id = hook_data['agent_id']
        
        # Update statistics
        if agent_id in self.active_agents:
            self.active_agents[agent_id]['last_activity'] = datetime.now()
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        def monitor_loop():
            while self.learning_active:
                try:
                    self._perform_periodic_maintenance()
                    time.sleep(300)  # 5 minutes
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _perform_periodic_maintenance(self):
        """Perform periodic maintenance tasks"""
        current_time = datetime.now()
        
        # Remove inactive agents
        inactive_agents = [
            agent_id for agent_id, info in self.active_agents.items()
            if (current_time - info['last_activity']).total_seconds() > 3600  # 1 hour
        ]
        
        for agent_id in inactive_agents:
            logger.info(f"Removing inactive agent {agent_id}")
            del self.active_agents[agent_id]
        
        # Trigger knowledge consolidation
        try:
            # This would trigger consolidation in the learning system if needed
            pass
        except Exception as e:
            logger.error(f"Consolidation failed: {e}")
    
    def get_learning_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive learning dashboard data"""
        system_status = self.wrapper.get_unified_status()
        
        # Agent-specific statistics
        agent_stats = {}
        for agent_id, info in self.active_agents.items():
            agent_stats[agent_id] = {
                'type': info['agent_type'],
                'actions_performed': info['action_count'],
                'patterns_learned': info['learning_patterns'],
                'active_duration_minutes': (datetime.now() - info['registered_at']).total_seconds() / 60,
                'last_activity': info['last_activity'].isoformat()
            }
        
        # Learning effectiveness by agent type
        type_effectiveness = {}
        for agent_type in set(info['agent_type'] for info in self.active_agents.values()):
            type_agents = [aid for aid, info in self.active_agents.items() if info['agent_type'] == agent_type]
            if type_agents:
                type_effectiveness[agent_type] = {
                    'active_agents': len(type_agents),
                    'total_actions': sum(self.active_agents[aid]['action_count'] for aid in type_agents),
                    'total_patterns': sum(self.active_agents[aid]['learning_patterns'] for aid in type_agents)
                }
        
        return {
            'system_status': system_status,
            'active_agents': len(self.active_agents),
            'agent_statistics': agent_stats,
            'learning_by_agent_type': type_effectiveness,
            'learning_active': self.learning_active,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_learning_data(self, output_path: str):
        """Export learning data for analysis or backup"""
        dashboard_data = self.get_learning_dashboard()
        learning_report = self.wrapper.learning_system.get_learning_report()
        
        export_data = {
            'dashboard': dashboard_data,
            'learning_report': learning_report,
            'export_timestamp': datetime.now().isoformat(),
            'export_version': '1.0'
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Learning data exported to {output_path}")
    
    def shutdown(self):
        """Shutdown the learning adapter"""
        self.learning_active = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        # Save all learning data
        self.wrapper.cleanup_and_save()
        
        logger.info("Agent Learning Adapter shutdown complete")


# Global adapter instance for easy access
_global_adapter: Optional[AgentLearningAdapter] = None

def get_learning_adapter(base_path: str = None) -> AgentLearningAdapter:
    """Get or create global learning adapter instance"""
    global _global_adapter
    
    if _global_adapter is None:
        _global_adapter = AgentLearningAdapter(base_path or "./memory/context/jarvis")
    
    return _global_adapter

def register_agent(agent_id: str, agent_type: str, metadata: Dict[str, Any] = None):
    """Convenience function to register an agent"""
    adapter = get_learning_adapter()
    adapter.register_agent(agent_id, agent_type, metadata)

def monitor_action(agent_id: str, action_type: str, context: Dict[str, Any], 
                  result: Any = None, error: Exception = None):
    """Convenience function to monitor an action"""
    adapter = get_learning_adapter()
    adapter.monitor_agent_action(agent_id, action_type, context, result, error)

def get_recommendations(agent_id: str, planned_action: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to get action recommendations"""
    adapter = get_learning_adapter()
    return adapter.get_agent_recommendations(agent_id, planned_action)


if __name__ == "__main__":
    # Example usage
    adapter = AgentLearningAdapter()
    
    # Register some agents
    adapter.register_agent('dev_agent_01', 'development_agent', {'version': '1.0'})
    adapter.register_agent('devops_agent_01', 'devops_agent', {'version': '1.0'})
    
    # Simulate some actions
    adapter.monitor_agent_action(
        'dev_agent_01',
        'typescript_compilation',
        {'file': 'src/component.tsx', 'issue': 'type error'},
        result='compilation successful'
    )
    
    # Get recommendations
    recommendations = adapter.get_agent_recommendations(
        'dev_agent_01',
        {'action': 'edit_file', 'file_type': 'typescript'}
    )
    
    print(f"Recommendations: {json.dumps(recommendations, indent=2)}")
    
    # Get dashboard
    dashboard = adapter.get_learning_dashboard()
    print(f"Learning Dashboard: {json.dumps(dashboard, indent=2, default=str)}")
    
    # Export data
    adapter.export_learning_data('./learning_export.json')
    
    # Shutdown
    adapter.shutdown()