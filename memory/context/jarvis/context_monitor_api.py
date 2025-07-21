#!/usr/bin/env python3
"""
API endpoints for Jarvis context monitoring integration with agent dashboard.
Provides real-time context status, recovery reports, and persistence metrics.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
from jarvis_context_manager import JarvisContextManager

router = APIRouter(prefix="/api/jarvis/context", tags=["jarvis-context"])

# Global context manager instance (should be initialized by main app)
context_manager: Optional[JarvisContextManager] = None


def set_context_manager(cm: JarvisContextManager):
    """Set the context manager instance."""
    global context_manager
    context_manager = cm


@router.get("/status")
async def get_context_status() -> Dict[str, Any]:
    """Get current context status and metrics."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    status = context_manager.get_context_status()
    
    # Add persistence metrics
    try:
        with context_manager._get_db_connection() as conn:
            # Get snapshot count
            snapshot_count = conn.execute(
                "SELECT COUNT(*) as count FROM context_snapshots"
            ).fetchone()
            
            # Get recovery point count
            recovery_count = conn.execute(
                "SELECT COUNT(*) as count FROM context_snapshots WHERE is_recovery_point = 1"
            ).fetchone()
            
            # Get recent decisions
            recent_decisions = conn.execute(
                """SELECT decision_type, timestamp FROM decision_log 
                   ORDER BY timestamp DESC LIMIT 5"""
            ).fetchall()
            
            # Get database size
            db_size = Path(context_manager.db_path).stat().st_size / 1024 / 1024  # MB
    except Exception as e:
        snapshot_count = recovery_count = {"count": 0}
        recent_decisions = []
        db_size = 0
    
    return {
        "status": "healthy",
        "context": status,
        "persistence": {
            "total_snapshots": snapshot_count["count"],
            "recovery_points": recovery_count["count"],
            "database_size_mb": round(db_size, 2),
            "auto_checkpoint": "active",
            "last_checkpoint": datetime.now().isoformat()
        },
        "recent_decisions": [
            {"type": d["decision_type"], "timestamp": d["timestamp"]}
            for d in recent_decisions
        ]
    }


@router.get("/recovery-reports")
async def get_recovery_reports() -> List[Dict[str, Any]]:
    """Get list of recovery reports."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    reports = []
    report_files = sorted(context_manager.base_path.glob("recovery_report_*.json"))
    
    for report_file in report_files[-10:]:  # Last 10 reports
        try:
            with open(report_file, 'r') as f:
                report = json.load(f)
                report['filename'] = report_file.name
                reports.append(report)
        except Exception as e:
            continue
    
    return reports


@router.get("/agent-states")
async def get_agent_states() -> Dict[str, Any]:
    """Get current state of all agents."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    agent_states = context_manager.active_context['agent_states']
    
    # Add health status
    for agent_id, state in agent_states.items():
        last_update = datetime.fromisoformat(state.get('last_update', '1970-01-01'))
        time_since_update = (datetime.now() - last_update).seconds
        
        if time_since_update < 60:
            health = "healthy"
        elif time_since_update < 300:
            health = "warning"
        else:
            health = "stale"
        
        state['health'] = health
        state['seconds_since_update'] = time_since_update
    
    return agent_states


@router.get("/task-progress")
async def get_task_progress() -> Dict[str, Any]:
    """Get progress of all tasks."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    return context_manager.active_context['task_progress']


@router.post("/checkpoint")
async def create_checkpoint(reason: str) -> Dict[str, Any]:
    """Manually create a recovery checkpoint."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    context_manager.mark_recovery_point(reason)
    return {"status": "success", "message": f"Checkpoint created: {reason}"}


@router.post("/recover")
async def trigger_recovery() -> Dict[str, Any]:
    """Manually trigger crash recovery."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    report = context_manager.recover_from_crash()
    return {"status": "success", "report": report}


@router.get("/conversation-history")
async def get_conversation_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent conversation history."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    history = list(context_manager.active_context['conversation_history'])
    return history[-limit:]


@router.get("/decision-log")
async def get_decision_log(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent orchestration decisions."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    decisions = list(context_manager.active_context['decision_log'])
    return decisions[-limit:]


@router.get("/metrics")
async def get_persistence_metrics() -> Dict[str, Any]:
    """Get detailed persistence metrics."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    try:
        with context_manager._get_db_connection() as conn:
            # Hourly snapshot rate
            hourly_snapshots = conn.execute(
                """SELECT COUNT(*) as count FROM context_snapshots 
                   WHERE timestamp > datetime('now', '-1 hour')"""
            ).fetchone()
            
            # Daily snapshot rate
            daily_snapshots = conn.execute(
                """SELECT COUNT(*) as count FROM context_snapshots 
                   WHERE timestamp > datetime('now', '-1 day')"""
            ).fetchone()
            
            # Agent message volume
            message_volume = conn.execute(
                """SELECT COUNT(*) as count FROM agent_coordination 
                   WHERE timestamp > datetime('now', '-1 hour')"""
            ).fetchone()
            
            # Decision rate
            decision_rate = conn.execute(
                """SELECT COUNT(*) as count FROM decision_log 
                   WHERE timestamp > datetime('now', '-1 hour')"""
            ).fetchone()
            
            # Storage growth
            first_snapshot = conn.execute(
                "SELECT timestamp FROM context_snapshots ORDER BY timestamp ASC LIMIT 1"
            ).fetchone()
            
            if first_snapshot:
                days_active = (datetime.now() - datetime.fromisoformat(first_snapshot['timestamp'])).days
                growth_rate = (Path(context_manager.db_path).stat().st_size / 1024 / 1024) / max(days_active, 1)
            else:
                growth_rate = 0
    
    except Exception as e:
        return {"error": str(e)}
    
    return {
        "snapshot_rates": {
            "hourly": hourly_snapshots["count"],
            "daily": daily_snapshots["count"]
        },
        "activity": {
            "messages_per_hour": message_volume["count"],
            "decisions_per_hour": decision_rate["count"]
        },
        "storage": {
            "growth_rate_mb_per_day": round(growth_rate, 2),
            "checkpoint_count": len(list(context_manager.checkpoint_dir.glob("*.pkl")))
        }
    }


@router.delete("/cleanup")
async def cleanup_old_data(days: int = 7) -> Dict[str, Any]:
    """Clean up old context data."""
    if not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        with context_manager._get_db_connection() as conn:
            # Delete old snapshots (keep recovery points)
            deleted_snapshots = conn.execute(
                """DELETE FROM context_snapshots 
                   WHERE timestamp < ? AND is_recovery_point = 0""",
                (cutoff_date,)
            ).rowcount
            
            # Delete old agent messages
            deleted_messages = conn.execute(
                "DELETE FROM agent_coordination WHERE timestamp < ?",
                (cutoff_date,)
            ).rowcount
            
            # Delete old decisions
            deleted_decisions = conn.execute(
                "DELETE FROM decision_log WHERE timestamp < ?",
                (cutoff_date,)
            ).rowcount
        
        # Clean old checkpoint files
        deleted_files = 0
        for checkpoint in context_manager.checkpoint_dir.glob("*.pkl"):
            if datetime.fromtimestamp(checkpoint.stat().st_mtime) < cutoff_date:
                checkpoint.unlink()
                deleted_files += 1
        
        return {
            "status": "success",
            "deleted": {
                "snapshots": deleted_snapshots,
                "messages": deleted_messages,
                "decisions": deleted_decisions,
                "checkpoint_files": deleted_files
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time monitoring (to be implemented with your WebSocket server)
async def context_status_websocket(websocket):
    """Stream real-time context updates via WebSocket."""
    while True:
        if context_manager:
            status = context_manager.get_context_status()
            await websocket.send_json({
                "type": "context_update",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
        await asyncio.sleep(5)  # Update every 5 seconds