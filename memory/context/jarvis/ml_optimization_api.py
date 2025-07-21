#!/usr/bin/env python3
"""
ML Optimization API endpoints for agent improvement insights.
Provides access to learning metrics, performance analysis, and recommendations.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ml_optimization_bridge import MLOptimizationBridge
from jarvis_context_manager import JarvisContextManager

router = APIRouter(prefix="/api/jarvis/ml-optimization", tags=["ml-optimization"])

# Global ML optimization bridge (initialized by main app)
ml_bridge: Optional[MLOptimizationBridge] = None
context_manager: Optional[JarvisContextManager] = None


def set_ml_bridge(bridge: MLOptimizationBridge, cm: JarvisContextManager):
    """Set the ML optimization bridge and context manager."""
    global ml_bridge, context_manager
    ml_bridge = bridge
    context_manager = cm


@router.get("/status")
async def get_optimization_status() -> Dict[str, Any]:
    """Get current ML optimization status and metrics."""
    if not ml_bridge:
        raise HTTPException(status_code=503, detail="ML optimization not initialized")
    
    status = ml_bridge.get_optimization_status()
    
    # Add context persistence metrics
    context_status = context_manager.get_context_status() if context_manager else {}
    
    return {
        "optimization": status,
        "context": context_status,
        "learning_insights": {
            "total_agents_tracked": len(status['agent_performance_scores']),
            "decision_types_analyzed": len(status['decision_success_rates']),
            "pattern_categories": len(status['pattern_library_size'])
        }
    }


@router.get("/agent-performance")
async def get_agent_performance_scores() -> Dict[str, Any]:
    """Get detailed agent performance scores and trends."""
    if not ml_bridge:
        raise HTTPException(status_code=503, detail="ML optimization not initialized")
    
    scores = ml_bridge.agent_performance_scores
    
    # Calculate rankings
    ranked_agents = sorted(
        [(agent_id, data['score']) for agent_id, data in scores.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    return {
        "performance_scores": dict(scores),
        "rankings": [
            {"rank": i+1, "agent_id": agent_id, "score": score}
            for i, (agent_id, score) in enumerate(ranked_agents)
        ],
        "average_score": sum(data['score'] for data in scores.values()) / len(scores) if scores else 0
    }


@router.get("/decision-analytics")
async def get_decision_analytics() -> Dict[str, Any]:
    """Get analytics on decision-making patterns and success rates."""
    if not ml_bridge:
        raise HTTPException(status_code=503, detail="ML optimization not initialized")
    
    success_rates = ml_bridge.decision_success_rates
    patterns = ml_bridge.pattern_library
    
    # Calculate insights
    analytics = {
        "success_rates_by_type": dict(success_rates),
        "overall_success_rate": sum(success_rates.values()) / len(success_rates) if success_rates else 0,
        "pattern_insights": {}
    }
    
    # Extract top patterns for each decision type
    for decision_type, pattern_data in patterns.items():
        if 'reasoning_keywords' in pattern_data:
            top_keywords = sorted(
                pattern_data['reasoning_keywords'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            analytics['pattern_insights'][decision_type] = {
                "total_patterns": len(pattern_data.get('successful_strategies', [])),
                "top_reasoning_keywords": dict(top_keywords),
                "common_contexts": list(pattern_data.get('common_contexts', {}).keys())[:5]
            }
    
    return analytics


@router.post("/recommend-agent")
async def recommend_agent_for_task(
    task_description: str,
    required_capabilities: List[str] = []
) -> Dict[str, Any]:
    """Get ML-based agent recommendation for a specific task."""
    if not ml_bridge:
        raise HTTPException(status_code=503, detail="ML optimization not initialized")
    
    recommended_agent = ml_bridge.recommend_agent_for_task(
        task_description,
        required_capabilities
    )
    
    if not recommended_agent:
        return {
            "status": "no_recommendation",
            "reason": "No agents match the required capabilities"
        }
    
    # Get performance data for recommended agent
    agent_score = ml_bridge.agent_performance_scores.get(recommended_agent, {})
    
    return {
        "status": "success",
        "recommended_agent": recommended_agent,
        "performance_score": agent_score.get('score', 0.5),
        "confidence": min(agent_score.get('samples', 0) / 10, 1.0),  # Confidence based on sample size
        "reasoning": {
            "task_category": ml_bridge._categorize_task(task_description),
            "capability_match": True,
            "historical_performance": "strong" if agent_score.get('score', 0.5) > 0.7 else "moderate"
        }
    }


@router.get("/learning-patterns")
async def get_learning_patterns(decision_type: Optional[str] = None) -> Dict[str, Any]:
    """Get discovered learning patterns and successful strategies."""
    if not ml_bridge:
        raise HTTPException(status_code=503, detail="ML optimization not initialized")
    
    if decision_type:
        patterns = ml_bridge.pattern_library.get(decision_type, {})
        return {
            "decision_type": decision_type,
            "patterns": patterns
        }
    else:
        # Return summary of all patterns
        pattern_summary = {}
        for dt, patterns in ml_bridge.pattern_library.items():
            pattern_summary[dt] = {
                "strategy_count": len(patterns.get('successful_strategies', [])),
                "top_keywords": list(patterns.get('reasoning_keywords', {}).keys())[:3]
            }
        
        return {
            "pattern_summary": pattern_summary,
            "total_decision_types": len(ml_bridge.pattern_library)
        }


@router.get("/improvement-trends")
async def get_improvement_trends(days: int = 7) -> Dict[str, Any]:
    """Get agent improvement trends over time."""
    if not ml_bridge or not context_manager:
        raise HTTPException(status_code=503, detail="ML optimization not initialized")
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with context_manager._get_db_connection() as conn:
            # Get task completion trends
            completion_trends = conn.execute("""
                SELECT 
                    DATE(last_update) as date,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(*) as total,
                    AVG(percentage) as avg_progress
                FROM task_progress
                WHERE last_update > ?
                GROUP BY DATE(last_update)
                ORDER BY date
            """, (cutoff_date,)).fetchall()
            
            # Get decision success trends
            decision_trends = conn.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(CASE WHEN outcome = 'success' THEN 1 END) as successful,
                    COUNT(*) as total
                FROM decision_log
                WHERE timestamp > ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (cutoff_date,)).fetchall()
        
        return {
            "task_completion_trends": [
                {
                    "date": row['date'],
                    "completion_rate": row['completed'] / row['total'] if row['total'] > 0 else 0,
                    "avg_progress": row['avg_progress'],
                    "total_tasks": row['total']
                }
                for row in completion_trends
            ],
            "decision_success_trends": [
                {
                    "date": row['date'],
                    "success_rate": row['successful'] / row['total'] if row['total'] > 0 else 0,
                    "total_decisions": row['total']
                }
                for row in decision_trends
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-learning-cycle")
async def trigger_learning_cycle() -> Dict[str, Any]:
    """Manually trigger a learning cycle."""
    if not ml_bridge:
        raise HTTPException(status_code=503, detail="ML optimization not initialized")
    
    try:
        # Run all learning tasks
        await ml_bridge.analyze_decision_outcomes()
        await ml_bridge.update_agent_performance_models()
        await ml_bridge.extract_successful_patterns()
        await ml_bridge.propagate_learning_insights()
        
        return {
            "status": "success",
            "message": "Learning cycle completed",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-evolution/{agent_id}")
async def get_agent_evolution(agent_id: str, days: int = 30) -> Dict[str, Any]:
    """Track evolution of a specific agent's performance over time."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with context_manager._get_db_connection() as conn:
            # Get agent's task history
            task_history = conn.execute("""
                SELECT 
                    DATE(ac.timestamp) as date,
                    COUNT(DISTINCT tp.task_id) as tasks_handled,
                    AVG(tp.percentage) as avg_completion,
                    COUNT(CASE WHEN tp.status = 'completed' THEN 1 END) as tasks_completed
                FROM agent_coordination ac
                JOIN task_progress tp ON ac.message_content LIKE '%' || tp.task_id || '%'
                WHERE ac.from_agent = ? AND ac.timestamp > ?
                GROUP BY DATE(ac.timestamp)
                ORDER BY date
            """, (agent_id, cutoff_date)).fetchall()
            
            # Get decision involvement
            decision_involvement = conn.execute("""
                SELECT 
                    COUNT(*) as total_decisions,
                    COUNT(CASE WHEN outcome = 'success' THEN 1 END) as successful_decisions
                FROM decision_log
                WHERE context LIKE '%' || ? || '%' AND timestamp > ?
            """, (agent_id, cutoff_date)).fetchone()
        
        # Get current performance score
        current_score = ml_bridge.agent_performance_scores.get(agent_id, {}) if ml_bridge else {}
        
        return {
            "agent_id": agent_id,
            "current_performance_score": current_score.get('score', 0.5),
            "performance_samples": current_score.get('samples', 0),
            "task_history": [
                {
                    "date": row['date'],
                    "tasks_handled": row['tasks_handled'],
                    "completion_rate": row['tasks_completed'] / row['tasks_handled'] if row['tasks_handled'] > 0 else 0,
                    "avg_completion_percentage": row['avg_completion']
                }
                for row in task_history
            ],
            "decision_metrics": {
                "total_decisions_involved": decision_involvement['total_decisions'],
                "successful_decisions": decision_involvement['successful_decisions'],
                "success_rate": decision_involvement['successful_decisions'] / decision_involvement['total_decisions'] 
                               if decision_involvement['total_decisions'] > 0 else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))