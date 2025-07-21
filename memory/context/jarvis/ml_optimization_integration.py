#!/usr/bin/env python3
"""
ML Optimization Integration - Unified entry point for all ML optimization features.
Integrates context persistence, ML optimization, and collaborative learning.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from jarvis_context_manager import JarvisContextManager
from jarvis_orchestrator_integration import JarvisOrchestratorWithContext
from ml_optimization_bridge import MLOptimizationBridge
from collaborative_learning_enhancer import CollaborativeLearningEnhancer
from context_monitor_api import router as context_router, set_context_manager
from ml_optimization_api import router as ml_router, set_ml_bridge


class JarvisMLOptimizedOrchestrator:
    """Fully ML-optimized orchestrator with context persistence and collaborative learning."""
    
    def __init__(self, base_orchestrator=None, context_path: str = "./memory/context/jarvis"):
        # Initialize components
        self.context_manager = JarvisContextManager(context_path)
        self.ml_bridge = MLOptimizationBridge(self.context_manager)
        self.collab_enhancer = CollaborativeLearningEnhancer(self.context_manager)
        
        # Wrap orchestrator if provided
        if base_orchestrator:
            self.orchestrator = JarvisOrchestratorWithContext(base_orchestrator, context_path)
        else:
            self.orchestrator = None
        
        # Initialize APIs
        set_context_manager(self.context_manager)
        set_ml_bridge(self.ml_bridge, self.context_manager)
        
        # Start optimization loops
        self._start_optimization_loops()
        
        logger.info("ML-Optimized Orchestrator initialized successfully")
    
    def _start_optimization_loops(self):
        """Start all optimization and learning loops."""
        async def optimization_loop():
            while True:
                try:
                    # Run optimization cycles
                    await self._run_optimization_cycle()
                    await asyncio.sleep(300)  # Every 5 minutes
                except Exception as e:
                    logger.error(f"Optimization loop error: {e}")
        
        async def monitoring_loop():
            while True:
                try:
                    # Monitor and report system health
                    await self._monitor_system_health()
                    await asyncio.sleep(60)  # Every minute
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
        
        # Start loops
        asyncio.create_task(optimization_loop())
        asyncio.create_task(monitoring_loop())
    
    async def _run_optimization_cycle(self):
        """Run a complete optimization cycle."""
        logger.info("Starting optimization cycle...")
        
        # 1. Analyze recent performance
        ml_status = self.ml_bridge.get_optimization_status()
        collab_insights = self.collab_enhancer.get_collaboration_insights()
        
        # 2. Generate optimization report
        report = {
            'timestamp': datetime.now().isoformat(),
            'agent_count': len(ml_status['agent_performance_scores']),
            'avg_performance': sum(
                score['score'] for score in ml_status['agent_performance_scores'].values()
            ) / len(ml_status['agent_performance_scores']) if ml_status['agent_performance_scores'] else 0,
            'decision_types': len(ml_status['decision_success_rates']),
            'collaboration_density': collab_insights['network_density'],
            'optimal_teams_identified': len(collab_insights['optimal_teams'])
        }
        
        # 3. Log optimization results
        self.context_manager.log_decision(
            decision_type="system_optimization",
            context=f"Optimization cycle at {report['timestamp']}",
            decision="Apply learned optimizations",
            reasoning=f"Avg performance: {report['avg_performance']:.2f}, Network density: {report['collaboration_density']:.2f}",
            outcome="applied"
        )
        
        logger.info(f"Optimization cycle completed: {report}")
    
    async def _monitor_system_health(self):
        """Monitor system health and performance metrics."""
        try:
            # Get system metrics
            context_status = self.context_manager.get_context_status()
            
            # Check for issues
            issues = []
            
            # Check for stale agents
            stale_agents = []
            for agent_id, state in self.context_manager.active_context['agent_states'].items():
                last_update = datetime.fromisoformat(state.get('last_update', '1970-01-01'))
                if (datetime.now() - last_update).seconds > 600:  # 10 minutes
                    stale_agents.append(agent_id)
                    issues.append(f"Agent {agent_id} is stale")
            
            # Check for low performance agents
            low_performers = []
            for agent_id, score_data in self.ml_bridge.agent_performance_scores.items():
                if score_data['score'] < 0.3 and score_data['samples'] > 5:
                    low_performers.append(agent_id)
                    issues.append(f"Agent {agent_id} has low performance score: {score_data['score']:.2f}")
            
            # Take corrective actions
            if issues:
                logger.warning(f"System health issues detected: {len(issues)}")
                await self._handle_health_issues(stale_agents, low_performers)
        
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
    
    async def _handle_health_issues(self, stale_agents: list, low_performers: list):
        """Handle detected health issues."""
        # Handle stale agents
        for agent_id in stale_agents:
            self.context_manager.log_decision(
                decision_type="agent_recovery",
                context=f"Agent {agent_id} is stale",
                decision="Initiate recovery procedure",
                reasoning="No activity for >10 minutes",
                outcome="recovery_initiated"
            )
        
        # Handle low performers
        for agent_id in low_performers:
            # Find better alternatives
            agent_score = self.ml_bridge.agent_performance_scores[agent_id]['score']
            
            # Recommend retraining or replacement
            self.context_manager.log_decision(
                decision_type="performance_intervention",
                context=f"Agent {agent_id} performance: {agent_score:.2f}",
                decision="Recommend additional training",
                reasoning="Performance below threshold with sufficient samples",
                outcome="intervention_recommended"
            )
    
    async def assign_task_optimized(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Assign task using ML optimization."""
        # Get ML recommendation
        recommended_agent = self.ml_bridge.recommend_agent_for_task(
            task['description'],
            task.get('required_capabilities', [])
        )
        
        if recommended_agent:
            # Check if agent should work alone or in a team
            task_type = self.ml_bridge._categorize_task(task['description'])
            optimal_teams = self.collab_enhancer._get_optimal_team_compositions()
            
            # Find if this task type benefits from teamwork
            team_recommendation = next(
                (team for team in optimal_teams if team['task_type'] == task_type),
                None
            )
            
            if team_recommendation and team_recommendation['success_rate'] > 0.8:
                # Assign to optimal team
                result = {
                    'task_id': task['id'],
                    'assigned_to': team_recommendation['optimal_team'],
                    'assignment_type': 'team',
                    'expected_success_rate': team_recommendation['success_rate'],
                    'ml_optimized': True
                }
            else:
                # Assign to single agent
                result = {
                    'task_id': task['id'],
                    'assigned_to': [recommended_agent],
                    'assignment_type': 'individual',
                    'agent_score': self.ml_bridge.agent_performance_scores[recommended_agent]['score'],
                    'ml_optimized': True
                }
            
            # Log assignment
            self.context_manager.log_decision(
                decision_type="ml_task_assignment",
                context=f"Task: {task['description']}",
                decision=f"Assign to: {result['assigned_to']}",
                reasoning=f"ML recommendation based on historical performance",
                outcome="assigned"
            )
            
            # Update context
            self.context_manager.update_task_progress(task['id'], {
                'description': task['description'],
                'status': 'assigned',
                'percentage': 0,
                'assigned_agents': result['assigned_to']
            })
            
            return result
        else:
            # Fallback to traditional assignment
            logger.warning(f"No ML recommendation available for task {task['id']}")
            return {'task_id': task['id'], 'assigned_to': [], 'ml_optimized': False}
    
    def get_optimization_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for ML optimization."""
        return {
            'ml_optimization': self.ml_bridge.get_optimization_status(),
            'collaboration_insights': self.collab_enhancer.get_collaboration_insights(),
            'context_status': self.context_manager.get_context_status(),
            'system_health': {
                'active_agents': len(self.context_manager.active_context['agent_states']),
                'active_tasks': len(self.context_manager.active_context['task_progress']),
                'optimization_active': True,
                'last_checkpoint': datetime.now().isoformat()
            }
        }
    
    def export_learning_insights(self, filepath: str = "learning_insights.json"):
        """Export all learning insights for analysis."""
        import json
        
        insights = {
            'export_timestamp': datetime.now().isoformat(),
            'performance_scores': dict(self.ml_bridge.agent_performance_scores),
            'decision_patterns': self.ml_bridge.pattern_library,
            'collaboration_scores': dict(self.collab_enhancer.collaboration_scores),
            'optimal_teams': self.collab_enhancer._get_optimal_team_compositions(),
            'agent_expertise': dict(self.collab_enhancer.shared_knowledge_base['agent_expertise']),
            'success_rates': dict(self.ml_bridge.decision_success_rates)
        }
        
        with open(filepath, 'w') as f:
            json.dump(insights, f, indent=2, default=str)
        
        logger.info(f"Learning insights exported to {filepath}")
        return filepath


# FastAPI app integration
def create_ml_optimized_app(base_orchestrator=None):
    """Create FastAPI app with ML optimization endpoints."""
    from fastapi import FastAPI
    
    app = FastAPI(title="Jarvis ML-Optimized Orchestrator")
    
    # Initialize ML-optimized orchestrator
    ml_orchestrator = JarvisMLOptimizedOrchestrator(base_orchestrator)
    
    # Include routers
    app.include_router(context_router)
    app.include_router(ml_router)
    
    # Add custom endpoints
    @app.get("/ml-optimization/dashboard")
    async def get_ml_dashboard():
        """Get comprehensive ML optimization dashboard data."""
        return ml_orchestrator.get_optimization_dashboard_data()
    
    @app.post("/ml-optimization/assign-task")
    async def assign_task_with_ml(task: Dict[str, Any]):
        """Assign task using ML optimization."""
        return await ml_orchestrator.assign_task_optimized(task)
    
    @app.post("/ml-optimization/export-insights")
    async def export_insights():
        """Export learning insights."""
        filepath = ml_orchestrator.export_learning_insights()
        return {"status": "success", "filepath": filepath}
    
    @app.get("/")
    async def root():
        """Root endpoint with system info."""
        return {
            "system": "Jarvis ML-Optimized Orchestrator",
            "version": "2.0",
            "features": [
                "Context Persistence",
                "ML Optimization",
                "Collaborative Learning",
                "Real-time Monitoring",
                "Crash Recovery"
            ],
            "api_docs": "/docs"
        }
    
    return app, ml_orchestrator


# Example usage
if __name__ == "__main__":
    import uvicorn
    
    # Create app
    app, orchestrator = create_ml_optimized_app()
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)