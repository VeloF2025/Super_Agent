#!/usr/bin/env python3
"""
Collaborative Learning Enhancer - Extends collaborative intelligence with context-based learning.
Enables agents to learn from each other's experiences through the context persistence system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import json
import numpy as np
from pathlib import Path
import sys

# Add shared tools to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "shared/tools/analyzers"))

from jarvis_context_manager import JarvisContextManager
from collaborative_intelligence import CollaborativeIntelligence

logger = logging.getLogger(__name__)


class CollaborativeLearningEnhancer:
    """Enhances collaborative intelligence with context-based learning."""
    
    def __init__(self, context_manager: JarvisContextManager):
        self.context_manager = context_manager
        self.collab_intelligence = CollaborativeIntelligence()
        
        # Learning structures
        self.shared_knowledge_base = {
            'successful_patterns': defaultdict(list),
            'failure_patterns': defaultdict(list),
            'agent_expertise': defaultdict(set),
            'cross_agent_insights': []
        }
        
        # Agent collaboration metrics
        self.collaboration_scores = defaultdict(lambda: defaultdict(float))
        self.knowledge_propagation_map = defaultdict(set)
        
        # Start collaborative learning loop
        self._start_collaborative_learning()
    
    def _start_collaborative_learning(self):
        """Start background thread for collaborative learning."""
        async def learning_loop():
            while True:
                try:
                    await self.analyze_agent_interactions()
                    await self.extract_collaborative_patterns()
                    await self.propagate_collective_knowledge()
                    await self.optimize_agent_teams()
                except Exception as e:
                    logger.error(f"Collaborative learning error: {e}")
                
                await asyncio.sleep(600)  # Run every 10 minutes
        
        asyncio.create_task(learning_loop())
    
    async def analyze_agent_interactions(self):
        """Analyze how agents work together and learn from each other."""
        try:
            with self.context_manager._get_db_connection() as conn:
                # Get recent agent interactions
                interactions = conn.execute("""
                    SELECT from_agent, to_agent, message_type, message_content, response, timestamp
                    FROM agent_coordination
                    WHERE timestamp > datetime('now', '-1 day')
                    ORDER BY timestamp
                """).fetchall()
                
                # Build interaction graph
                interaction_graph = defaultdict(lambda: defaultdict(int))
                successful_collaborations = []
                
                for interaction in interactions:
                    from_agent = interaction['from_agent']
                    to_agent = interaction['to_agent']
                    
                    # Track interaction frequency
                    interaction_graph[from_agent][to_agent] += 1
                    
                    # Identify successful collaborations
                    if interaction['response'] and 'success' in str(interaction['response']).lower():
                        successful_collaborations.append({
                            'agents': [from_agent, to_agent],
                            'type': interaction['message_type'],
                            'timestamp': interaction['timestamp']
                        })
                
                # Update collaboration scores
                for collab in successful_collaborations:
                    agent1, agent2 = collab['agents']
                    self.collaboration_scores[agent1][agent2] += 0.1
                    self.collaboration_scores[agent2][agent1] += 0.1
                
                # Identify knowledge sharing patterns
                await self._analyze_knowledge_transfer(interactions)
                
        except Exception as e:
            logger.error(f"Agent interaction analysis error: {e}")
    
    async def _analyze_knowledge_transfer(self, interactions: List[Dict]):
        """Analyze how knowledge transfers between agents."""
        knowledge_transfers = []
        
        for interaction in interactions:
            content = str(interaction['message_content']).lower()
            
            # Identify knowledge transfer indicators
            if any(indicator in content for indicator in ['learned', 'discovered', 'found that', 'insight', 'pattern']):
                knowledge_transfers.append({
                    'from': interaction['from_agent'],
                    'to': interaction['to_agent'],
                    'knowledge_type': self._categorize_knowledge(content),
                    'timestamp': interaction['timestamp']
                })
        
        # Update knowledge propagation map
        for transfer in knowledge_transfers:
            self.knowledge_propagation_map[transfer['from']].add(transfer['to'])
            
            # Track expertise areas
            self.shared_knowledge_base['agent_expertise'][transfer['from']].add(transfer['knowledge_type'])
    
    def _categorize_knowledge(self, content: str) -> str:
        """Categorize the type of knowledge being shared."""
        categories = {
            'optimization': ['optimize', 'improve', 'enhance', 'performance'],
            'error_handling': ['error', 'exception', 'fix', 'resolve', 'bug'],
            'pattern_recognition': ['pattern', 'trend', 'recurring', 'common'],
            'workflow': ['workflow', 'process', 'pipeline', 'sequence'],
            'integration': ['integrate', 'connect', 'api', 'interface']
        }
        
        for category, keywords in categories.items():
            if any(keyword in content for keyword in keywords):
                return category
        
        return 'general'
    
    async def extract_collaborative_patterns(self):
        """Extract patterns from successful agent collaborations."""
        try:
            # Analyze task completions involving multiple agents
            with self.context_manager._get_db_connection() as conn:
                # Get tasks with multiple agents
                multi_agent_tasks = conn.execute("""
                    SELECT tp.task_id, tp.description, tp.status, tp.percentage,
                           GROUP_CONCAT(DISTINCT ac.from_agent) as involved_agents
                    FROM task_progress tp
                    JOIN agent_coordination ac ON ac.message_content LIKE '%' || tp.task_id || '%'
                    WHERE tp.last_update > datetime('now', '-7 days')
                    GROUP BY tp.task_id
                    HAVING COUNT(DISTINCT ac.from_agent) > 1
                """).fetchall()
                
                for task in multi_agent_tasks:
                    agents = task['involved_agents'].split(',')
                    
                    if task['status'] == 'completed' and task['percentage'] == 100:
                        # Successful collaboration pattern
                        pattern = {
                            'task_type': self._categorize_task(task['description']),
                            'agent_team': agents,
                            'team_size': len(agents),
                            'outcome': 'success'
                        }
                        self.shared_knowledge_base['successful_patterns'][pattern['task_type']].append(pattern)
                        
                        # Update collaboration scores for successful teams
                        for i, agent1 in enumerate(agents):
                            for agent2 in agents[i+1:]:
                                self.collaboration_scores[agent1][agent2] += 0.2
                                self.collaboration_scores[agent2][agent1] += 0.2
                    
                    elif task['status'] == 'failed' or task['percentage'] < 50:
                        # Failed collaboration pattern
                        pattern = {
                            'task_type': self._categorize_task(task['description']),
                            'agent_team': agents,
                            'team_size': len(agents),
                            'outcome': 'failure',
                            'completion': task['percentage']
                        }
                        self.shared_knowledge_base['failure_patterns'][pattern['task_type']].append(pattern)
            
            # Extract cross-agent insights
            await self._extract_cross_agent_insights()
            
        except Exception as e:
            logger.error(f"Pattern extraction error: {e}")
    
    def _categorize_task(self, description: str) -> str:
        """Categorize task type from description."""
        description_lower = description.lower()
        
        categories = {
            'complex_analysis': ['analyze', 'research', 'investigate', 'study'],
            'system_integration': ['integrate', 'connect', 'merge', 'combine'],
            'optimization': ['optimize', 'improve', 'enhance', 'refactor'],
            'development': ['build', 'create', 'implement', 'develop'],
            'quality_assurance': ['test', 'validate', 'verify', 'check']
        }
        
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return 'general'
    
    async def _extract_cross_agent_insights(self):
        """Extract insights from cross-agent collaboration."""
        insights = []
        
        # Find agent pairs with high collaboration scores
        high_performing_pairs = []
        for agent1, collaborators in self.collaboration_scores.items():
            for agent2, score in collaborators.items():
                if score > 0.7:  # High collaboration score
                    high_performing_pairs.append((agent1, agent2, score))
        
        # Analyze what makes these pairs successful
        for agent1, agent2, score in high_performing_pairs:
            # Get their shared expertise
            shared_expertise = (
                self.shared_knowledge_base['agent_expertise'][agent1] &
                self.shared_knowledge_base['agent_expertise'][agent2]
            )
            
            complementary_expertise = (
                self.shared_knowledge_base['agent_expertise'][agent1] ^
                self.shared_knowledge_base['agent_expertise'][agent2]
            )
            
            insight = {
                'type': 'high_performing_pair',
                'agents': [agent1, agent2],
                'collaboration_score': score,
                'shared_expertise': list(shared_expertise),
                'complementary_expertise': list(complementary_expertise),
                'timestamp': datetime.now().isoformat()
            }
            
            insights.append(insight)
            self.shared_knowledge_base['cross_agent_insights'].append(insight)
        
        # Share insights with collaborative intelligence
        for insight in insights:
            self.collab_intelligence.add_knowledge_entry({
                'type': 'collaboration_insight',
                'data': insight
            })
    
    async def propagate_collective_knowledge(self):
        """Propagate successful patterns and insights across all agents."""
        # Prepare knowledge package
        knowledge_package = {
            'timestamp': datetime.now().isoformat(),
            'successful_team_compositions': self._get_optimal_team_compositions(),
            'expertise_map': dict(self.shared_knowledge_base['agent_expertise']),
            'collaboration_recommendations': self._generate_collaboration_recommendations(),
            'learning_insights': self._summarize_learning_insights()
        }
        
        # Log propagation
        self.context_manager.log_decision(
            decision_type="knowledge_propagation",
            context=f"Propagating to {len(self.context_manager.active_context['agent_states'])} agents",
            decision="Share collective knowledge",
            reasoning="Regular collaborative learning cycle",
            outcome="propagated"
        )
        
        logger.info(f"Propagated collective knowledge: {len(knowledge_package['successful_team_compositions'])} team patterns")
    
    def _get_optimal_team_compositions(self) -> List[Dict[str, Any]]:
        """Get optimal team compositions for different task types."""
        optimal_teams = []
        
        for task_type, patterns in self.shared_knowledge_base['successful_patterns'].items():
            if patterns:
                # Find most successful team composition
                team_success_rates = defaultdict(lambda: {'success': 0, 'total': 0})
                
                for pattern in patterns:
                    team_key = tuple(sorted(pattern['agent_team']))
                    team_success_rates[team_key]['success'] += 1
                    team_success_rates[team_key]['total'] += 1
                
                # Add failure data
                for pattern in self.shared_knowledge_base['failure_patterns'].get(task_type, []):
                    team_key = tuple(sorted(pattern['agent_team']))
                    team_success_rates[team_key]['total'] += 1
                
                # Find best team
                best_team = max(
                    team_success_rates.items(),
                    key=lambda x: x[1]['success'] / x[1]['total'] if x[1]['total'] > 0 else 0
                )
                
                if best_team[1]['total'] > 0:
                    optimal_teams.append({
                        'task_type': task_type,
                        'optimal_team': list(best_team[0]),
                        'success_rate': best_team[1]['success'] / best_team[1]['total'],
                        'sample_size': best_team[1]['total']
                    })
        
        return optimal_teams
    
    def _generate_collaboration_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for agent collaboration."""
        recommendations = []
        
        # Recommend new collaborations based on complementary skills
        all_agents = list(self.shared_knowledge_base['agent_expertise'].keys())
        
        for i, agent1 in enumerate(all_agents):
            for agent2 in all_agents[i+1:]:
                # Check if they haven't collaborated much
                current_score = self.collaboration_scores[agent1].get(agent2, 0)
                
                if current_score < 0.3:  # Low collaboration
                    # Check for complementary skills
                    skills1 = self.shared_knowledge_base['agent_expertise'][agent1]
                    skills2 = self.shared_knowledge_base['agent_expertise'][agent2]
                    
                    if skills1 and skills2 and skills1 != skills2:
                        recommendations.append({
                            'type': 'new_collaboration',
                            'agents': [agent1, agent2],
                            'reason': 'complementary_skills',
                            'potential_expertise': list(skills1 | skills2)
                        })
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _summarize_learning_insights(self) -> Dict[str, Any]:
        """Summarize key learning insights."""
        return {
            'total_knowledge_transfers': sum(len(agents) for agents in self.knowledge_propagation_map.values()),
            'most_knowledgeable_agents': [
                agent for agent, expertise in self.shared_knowledge_base['agent_expertise'].items()
                if len(expertise) > 3
            ],
            'collaboration_network_density': self._calculate_network_density(),
            'emerging_patterns': len(self.shared_knowledge_base['cross_agent_insights'])
        }
    
    def _calculate_network_density(self) -> float:
        """Calculate the density of the collaboration network."""
        all_agents = set()
        connection_count = 0
        
        for agent1, collaborators in self.collaboration_scores.items():
            all_agents.add(agent1)
            for agent2, score in collaborators.items():
                all_agents.add(agent2)
                if score > 0:
                    connection_count += 1
        
        n = len(all_agents)
        if n > 1:
            max_connections = n * (n - 1) / 2
            return connection_count / max_connections if max_connections > 0 else 0
        return 0
    
    async def optimize_agent_teams(self):
        """Optimize agent team compositions based on learning."""
        try:
            # Get current task workload
            active_tasks = [
                task for task_id, task in self.context_manager.active_context['task_progress'].items()
                if task.get('status') == 'in_progress'
            ]
            
            for task in active_tasks:
                task_type = self._categorize_task(task.get('description', ''))
                
                # Find optimal team for this task type
                optimal_teams = [
                    team for team in self._get_optimal_team_compositions()
                    if team['task_type'] == task_type
                ]
                
                if optimal_teams:
                    best_team = optimal_teams[0]
                    
                    # Log team optimization recommendation
                    self.context_manager.log_decision(
                        decision_type="team_optimization",
                        context=f"Task type: {task_type}",
                        decision=f"Recommend team: {best_team['optimal_team']}",
                        reasoning=f"Historical success rate: {best_team['success_rate']:.2%}",
                        outcome="recommended"
                    )
        
        except Exception as e:
            logger.error(f"Team optimization error: {e}")
    
    def get_collaboration_insights(self) -> Dict[str, Any]:
        """Get current collaboration insights."""
        return {
            'collaboration_scores': {
                agent1: dict(scores) for agent1, scores in self.collaboration_scores.items()
            },
            'knowledge_propagation': {
                agent: list(recipients) for agent, recipients in self.knowledge_propagation_map.items()
            },
            'agent_expertise': {
                agent: list(expertise) for agent, expertise in self.shared_knowledge_base['agent_expertise'].items()
            },
            'optimal_teams': self._get_optimal_team_compositions(),
            'network_density': self._calculate_network_density()
        }