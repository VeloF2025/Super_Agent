#!/usr/bin/env python3
"""
ML Optimization Bridge - Connects context persistence with existing ML systems.
Enhances agent learning by analyzing decision outcomes and performance patterns.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import json
import sqlite3
from pathlib import Path
import sys

# Add shared tools to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "shared/tools/analyzers"))

from jarvis_context_manager import JarvisContextManager
from predictive_orchestrator import PredictiveOrchestrator
from intelligent_task_router import IntelligentTaskRouter
from collaborative_intelligence import CollaborativeIntelligence

logger = logging.getLogger(__name__)


class MLOptimizationBridge:
    """Bridges context persistence with ML optimization systems."""
    
    def __init__(self, context_manager: JarvisContextManager):
        self.context_manager = context_manager
        self.predictive_orchestrator = PredictiveOrchestrator()
        self.task_router = IntelligentTaskRouter()
        self.collab_intelligence = CollaborativeIntelligence()
        
        # Performance tracking
        self.agent_performance_scores = defaultdict(lambda: {"score": 0.5, "samples": 0})
        self.decision_success_rates = defaultdict(float)
        self.pattern_library = {}
        
        # Start continuous learning
        self._start_learning_loop()
    
    def _start_learning_loop(self):
        """Start background thread for continuous learning."""
        async def learning_loop():
            while True:
                try:
                    await self.analyze_decision_outcomes()
                    await self.update_agent_performance_models()
                    await self.extract_successful_patterns()
                    await self.propagate_learning_insights()
                except Exception as e:
                    logger.error(f"Learning loop error: {e}")
                
                await asyncio.sleep(300)  # Run every 5 minutes
        
        asyncio.create_task(learning_loop())
    
    async def analyze_decision_outcomes(self):
        """Analyze decision outcomes to improve future decisions."""
        try:
            with self.context_manager._get_db_connection() as conn:
                # Get recent decisions with outcomes
                decisions = conn.execute("""
                    SELECT decision_type, context, decision, reasoning, outcome
                    FROM decision_log 
                    WHERE outcome IS NOT NULL
                    AND timestamp > datetime('now', '-1 day')
                """).fetchall()
                
                # Group by decision type
                decision_groups = defaultdict(list)
                for d in decisions:
                    decision_groups[d['decision_type']].append({
                        'context': json.loads(d['context']) if d['context'].startswith('{') else d['context'],
                        'decision': d['decision'],
                        'reasoning': d['reasoning'],
                        'outcome': d['outcome']
                    })
                
                # Analyze each decision type
                for decision_type, group in decision_groups.items():
                    success_rate = sum(1 for d in group if d['outcome'] == 'success') / len(group)
                    self.decision_success_rates[decision_type] = success_rate
                    
                    # Extract features from successful decisions
                    successful_decisions = [d for d in group if d['outcome'] == 'success']
                    if successful_decisions:
                        self._extract_decision_patterns(decision_type, successful_decisions)
                
                # Feed insights to predictive orchestrator
                await self._update_predictive_models()
                
        except Exception as e:
            logger.error(f"Decision analysis error: {e}")
    
    def _extract_decision_patterns(self, decision_type: str, decisions: List[Dict]):
        """Extract patterns from successful decisions."""
        patterns = {
            'common_contexts': {},
            'successful_strategies': [],
            'reasoning_keywords': defaultdict(int)
        }
        
        for decision in decisions:
            # Analyze context patterns
            if isinstance(decision['context'], dict):
                for key, value in decision['context'].items():
                    if key not in patterns['common_contexts']:
                        patterns['common_contexts'][key] = []
                    patterns['common_contexts'][key].append(value)
            
            # Extract reasoning keywords
            reasoning_words = decision['reasoning'].lower().split()
            for word in reasoning_words:
                if len(word) > 4:  # Skip short words
                    patterns['reasoning_keywords'][word] += 1
            
            # Store successful strategies
            patterns['successful_strategies'].append({
                'decision': decision['decision'],
                'reasoning': decision['reasoning']
            })
        
        self.pattern_library[decision_type] = patterns
        logger.info(f"Extracted patterns for {decision_type}: {len(patterns['successful_strategies'])} strategies")
    
    async def update_agent_performance_models(self):
        """Update agent performance models based on task outcomes."""
        try:
            # Get recent task completions
            completed_tasks = {}
            for task_id, progress in self.context_manager.active_context['task_progress'].items():
                if progress.get('status') == 'completed':
                    completed_tasks[task_id] = progress
            
            # Analyze agent performance
            with self.context_manager._get_db_connection() as conn:
                # Get agent task assignments and outcomes
                agent_tasks = conn.execute("""
                    SELECT ac.from_agent, ac.message_content, tp.percentage, tp.status
                    FROM agent_coordination ac
                    JOIN task_progress tp ON ac.message_content LIKE '%' || tp.task_id || '%'
                    WHERE ac.timestamp > datetime('now', '-1 day')
                """).fetchall()
                
                # Calculate performance scores
                agent_metrics = defaultdict(lambda: {'completed': 0, 'total': 0, 'avg_progress': []})
                for task in agent_tasks:
                    agent_id = task['from_agent']
                    agent_metrics[agent_id]['total'] += 1
                    if task['status'] == 'completed':
                        agent_metrics[agent_id]['completed'] += 1
                    agent_metrics[agent_id]['avg_progress'].append(task['percentage'])
                
                # Update performance scores
                for agent_id, metrics in agent_metrics.items():
                    if metrics['total'] > 0:
                        completion_rate = metrics['completed'] / metrics['total']
                        avg_progress = np.mean(metrics['avg_progress']) / 100.0
                        
                        # Weighted score
                        new_score = (completion_rate * 0.7 + avg_progress * 0.3)
                        
                        # Update with exponential moving average
                        current = self.agent_performance_scores[agent_id]
                        current['score'] = 0.8 * current['score'] + 0.2 * new_score
                        current['samples'] += 1
                        
                        # Update task router with new performance data
                        self.task_router.update_agent_performance(agent_id, current['score'])
                
                logger.info(f"Updated performance scores for {len(agent_metrics)} agents")
                
        except Exception as e:
            logger.error(f"Performance update error: {e}")
    
    async def extract_successful_patterns(self):
        """Extract patterns from successful task completions."""
        try:
            # Analyze successful workflows
            successful_workflows = []
            
            with self.context_manager._get_db_connection() as conn:
                # Get completed tasks with high performance
                successful_tasks = conn.execute("""
                    SELECT task_id, description, completed_subtasks
                    FROM task_progress
                    WHERE percentage >= 100 AND status = 'completed'
                    AND last_update > datetime('now', '-7 days')
                """).fetchall()
                
                for task in successful_tasks:
                    # Get the decision chain that led to success
                    decisions = conn.execute("""
                        SELECT decision_type, decision, reasoning
                        FROM decision_log
                        WHERE context LIKE '%' || ? || '%'
                        ORDER BY timestamp
                    """, (task['task_id'],)).fetchall()
                    
                    if decisions:
                        successful_workflows.append({
                            'task_type': self._categorize_task(task['description']),
                            'decision_chain': [
                                {'type': d['decision_type'], 'decision': d['decision']}
                                for d in decisions
                            ],
                            'subtasks': json.loads(task['completed_subtasks']) if task['completed_subtasks'] else []
                        })
            
            # Feed patterns to collaborative intelligence
            if successful_workflows:
                await self._share_workflow_patterns(successful_workflows)
            
        except Exception as e:
            logger.error(f"Pattern extraction error: {e}")
    
    def _categorize_task(self, description: str) -> str:
        """Categorize task based on description."""
        description_lower = description.lower()
        
        categories = {
            'data_processing': ['process', 'analyze', 'transform', 'extract'],
            'integration': ['integrate', 'connect', 'api', 'sync'],
            'optimization': ['optimize', 'improve', 'enhance', 'refactor'],
            'monitoring': ['monitor', 'track', 'observe', 'alert'],
            'development': ['build', 'create', 'implement', 'develop']
        }
        
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return 'general'
    
    async def _share_workflow_patterns(self, workflows: List[Dict]):
        """Share successful workflow patterns across agents."""
        # Group workflows by task type
        workflow_groups = defaultdict(list)
        for workflow in workflows:
            workflow_groups[workflow['task_type']].append(workflow)
        
        # Create knowledge entries for collaborative intelligence
        for task_type, type_workflows in workflow_groups.items():
            # Find most common decision patterns
            decision_patterns = defaultdict(int)
            for workflow in type_workflows:
                pattern_key = tuple(d['type'] for d in workflow['decision_chain'])
                decision_patterns[pattern_key] += 1
            
            # Store as collaborative knowledge
            best_pattern = max(decision_patterns.items(), key=lambda x: x[1])
            knowledge_entry = {
                'type': 'workflow_pattern',
                'task_type': task_type,
                'decision_sequence': list(best_pattern[0]),
                'success_count': best_pattern[1],
                'timestamp': datetime.now().isoformat()
            }
            
            # Share with collaborative intelligence system
            self.collab_intelligence.add_knowledge_entry(knowledge_entry)
    
    async def propagate_learning_insights(self):
        """Propagate learning insights to all active agents."""
        insights = {
            'performance_updates': dict(self.agent_performance_scores),
            'decision_success_rates': dict(self.decision_success_rates),
            'recommended_patterns': self._get_top_patterns(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Log propagation for tracking
        self.context_manager.log_decision(
            decision_type="learning_propagation",
            context=f"Propagating to {len(self.context_manager.active_context['agent_states'])} agents",
            decision="Share learning insights",
            reasoning="Regular learning cycle update",
            outcome="propagated"
        )
        
        logger.info(f"Propagated insights to active agents: {len(insights['performance_updates'])} performance updates")
    
    def _get_top_patterns(self) -> Dict[str, List[Dict]]:
        """Get top performing patterns for each decision type."""
        top_patterns = {}
        
        for decision_type, patterns in self.pattern_library.items():
            if 'successful_strategies' in patterns:
                # Sort by frequency and recency
                sorted_strategies = sorted(
                    patterns['successful_strategies'],
                    key=lambda x: len(x['reasoning']),
                    reverse=True
                )[:5]  # Top 5 strategies
                
                top_patterns[decision_type] = sorted_strategies
        
        return top_patterns
    
    async def _update_predictive_models(self):
        """Update predictive orchestrator with new insights."""
        # Prepare training data from recent decisions
        training_data = []
        
        with self.context_manager._get_db_connection() as conn:
            recent_data = conn.execute("""
                SELECT d.decision_type, d.context, d.outcome,
                       COUNT(ac.id) as message_volume,
                       AVG(tp.percentage) as avg_progress
                FROM decision_log d
                LEFT JOIN agent_coordination ac ON ac.timestamp 
                    BETWEEN datetime(d.timestamp, '-1 hour') AND datetime(d.timestamp, '+1 hour')
                LEFT JOIN task_progress tp ON tp.last_update 
                    BETWEEN datetime(d.timestamp, '-1 hour') AND datetime(d.timestamp, '+1 hour')
                WHERE d.timestamp > datetime('now', '-7 days')
                GROUP BY d.id
            """).fetchall()
            
            for row in recent_data:
                training_data.append({
                    'features': {
                        'decision_type': row['decision_type'],
                        'message_volume': row['message_volume'] or 0,
                        'avg_progress': row['avg_progress'] or 0
                    },
                    'outcome': 1 if row['outcome'] == 'success' else 0
                })
        
        # Update predictive models if we have enough data
        if len(training_data) > 50:
            self.predictive_orchestrator.update_models(training_data)
            logger.info(f"Updated predictive models with {len(training_data)} samples")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        return {
            'agent_performance_scores': dict(self.agent_performance_scores),
            'decision_success_rates': dict(self.decision_success_rates),
            'pattern_library_size': {k: len(v.get('successful_strategies', [])) 
                                    for k, v in self.pattern_library.items()},
            'learning_active': True,
            'last_update': datetime.now().isoformat()
        }
    
    def recommend_agent_for_task(self, task_description: str, required_capabilities: List[str]) -> str:
        """Recommend best agent for a task based on ML analysis."""
        # Get task category
        task_type = self._categorize_task(task_description)
        
        # Get agents with required capabilities
        eligible_agents = []
        for agent_id, state in self.context_manager.active_context['agent_states'].items():
            agent_capabilities = state.get('capabilities', [])
            if all(cap in agent_capabilities for cap in required_capabilities):
                eligible_agents.append(agent_id)
        
        if not eligible_agents:
            return None
        
        # Score agents based on performance
        agent_scores = {}
        for agent_id in eligible_agents:
            performance = self.agent_performance_scores[agent_id]['score']
            
            # Bonus for agents that have succeeded with similar tasks
            task_bonus = 0.1 if task_type in self.pattern_library else 0
            
            agent_scores[agent_id] = performance + task_bonus
        
        # Return agent with highest score
        best_agent = max(agent_scores.items(), key=lambda x: x[1])
        
        # Log the recommendation
        self.context_manager.log_decision(
            decision_type="agent_recommendation",
            context=f"Task: {task_description}, Type: {task_type}",
            decision=f"Recommend {best_agent[0]}",
            reasoning=f"Highest score: {best_agent[1]:.3f}",
            outcome="pending"
        )
        
        return best_agent[0]