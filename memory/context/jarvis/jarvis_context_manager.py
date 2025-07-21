#!/usr/bin/env python3
"""
JarvisContextManager - Robust context persistence and crash recovery system for Jarvis orchestrator.
Ensures zero context loss with automatic checkpointing and multi-layer recovery mechanisms.
"""

import sqlite3
import pickle
import json
import threading
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager
import traceback
import os
import signal
import atexit

logger = logging.getLogger(__name__)


class JarvisContextManager:
    """Manages persistent context and crash recovery for Jarvis orchestrator."""
    
    def __init__(self, base_path: str = "./memory/context/jarvis"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Database paths
        self.db_path = self.base_path / "jarvis_context.db"
        self.checkpoint_dir = self.base_path / "checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # Crash detection
        self.crash_marker = self.base_path / "CRASH_DETECTED"
        self.pid_file = self.base_path / "jarvis.pid"
        
        # Active context structure
        self.active_context = {
            'current_task': {
                'id': None,
                'description': None,
                'status': 'idle',
                'assigned_agents': []
            },
            'task_progress': {},  # task_id -> progress_data
            'agent_states': {},   # agent_id -> state_data
            'conversation_history': deque(maxlen=100),
            'decision_log': deque(maxlen=50),
            'error_recovery': {},
            'workflow_state': {
                'current_workflow_id': None,
                'phase': None,
                'completed_phases': []
            }
        }
        
        # Threading
        self._checkpoint_thread = None
        self._stop_checkpoint = threading.Event()
        self._context_lock = threading.RLock()
        
        # Initialize database
        self._init_database()
        
        # Check for crash on startup
        self._check_crash_on_startup()
        
        # Register cleanup handlers
        atexit.register(self._cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Start auto-checkpoint thread
        self._start_checkpoint_thread()
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        with self._get_db_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    hash TEXT UNIQUE,
                    context_data BLOB,
                    is_recovery_point BOOLEAN DEFAULT 0,
                    recovery_reason TEXT
                );
                
                CREATE TABLE IF NOT EXISTS task_progress (
                    task_id TEXT PRIMARY KEY,
                    description TEXT,
                    status TEXT,
                    percentage INTEGER DEFAULT 0,
                    completed_subtasks TEXT,
                    blockers TEXT,
                    last_update DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS agent_coordination (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    from_agent TEXT,
                    to_agent TEXT,
                    message_type TEXT,
                    message_content TEXT,
                    response TEXT
                );
                
                CREATE TABLE IF NOT EXISTS decision_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    decision_type TEXT,
                    context TEXT,
                    decision TEXT,
                    reasoning TEXT,
                    outcome TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON context_snapshots(timestamp);
                CREATE INDEX IF NOT EXISTS idx_snapshots_recovery ON context_snapshots(is_recovery_point);
                CREATE INDEX IF NOT EXISTS idx_agent_messages_timestamp ON agent_coordination(timestamp);
                CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decision_log(timestamp);
            """)
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _check_crash_on_startup(self):
        """Check if system crashed previously and recover if needed."""
        if self.crash_marker.exists():
            logger.warning("Crash detected! Initiating recovery...")
            self.recover_from_crash()
            self.crash_marker.unlink()
        
        # Update PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def _start_checkpoint_thread(self):
        """Start background thread for automatic checkpointing."""
        def checkpoint_loop():
            while not self._stop_checkpoint.is_set():
                try:
                    self.save_context(recovery_point=False)
                    logger.debug("Auto-checkpoint completed")
                except Exception as e:
                    logger.error(f"Auto-checkpoint failed: {e}")
                
                # Wait 30 seconds or until stop signal
                self._stop_checkpoint.wait(30)
        
        self._checkpoint_thread = threading.Thread(target=checkpoint_loop, daemon=True)
        self._checkpoint_thread.start()
        logger.info("Auto-checkpoint thread started")
    
    def save_context(self, recovery_point: bool = False, reason: str = None) -> bool:
        """Save current context with deduplication."""
        with self._context_lock:
            try:
                # Create crash marker before save
                self.crash_marker.touch()
                
                # Serialize context
                context_data = pickle.dumps(self.active_context)
                context_hash = hashlib.sha256(context_data).hexdigest()
                
                # Check if context changed
                with self._get_db_connection() as conn:
                    existing = conn.execute(
                        "SELECT id FROM context_snapshots WHERE hash = ?",
                        (context_hash,)
                    ).fetchone()
                    
                    if not existing:
                        conn.execute(
                            """INSERT INTO context_snapshots 
                               (hash, context_data, is_recovery_point, recovery_reason)
                               VALUES (?, ?, ?, ?)""",
                            (context_hash, context_data, recovery_point, reason)
                        )
                        logger.info(f"Context saved (hash: {context_hash[:8]}...)")
                    
                    # Update task progress table
                    for task_id, progress in self.active_context['task_progress'].items():
                        conn.execute(
                            """INSERT OR REPLACE INTO task_progress
                               (task_id, description, status, percentage, 
                                completed_subtasks, blockers)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (task_id, progress.get('description'),
                             progress.get('status'), progress.get('percentage', 0),
                             json.dumps(progress.get('completed_subtasks', [])),
                             json.dumps(progress.get('blockers', [])))
                        )
                
                # Emergency backup to pickle file
                if recovery_point:
                    checkpoint_file = self.checkpoint_dir / f"recovery_{int(time.time())}.pkl"
                    with open(checkpoint_file, 'wb') as f:
                        pickle.dump(self.active_context, f)
                
                # Remove crash marker after successful save
                if self.crash_marker.exists():
                    self.crash_marker.unlink()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save context: {e}")
                self._emergency_save()
                return False
    
    def _emergency_save(self):
        """Emergency save to JSON when database fails."""
        try:
            emergency_file = self.base_path / f"emergency_{int(time.time())}.json"
            with open(emergency_file, 'w') as f:
                # Convert deques to lists for JSON serialization
                context_copy = self.active_context.copy()
                context_copy['conversation_history'] = list(context_copy['conversation_history'])
                context_copy['decision_log'] = list(context_copy['decision_log'])
                json.dump(context_copy, f, indent=2, default=str)
            logger.warning(f"Emergency save completed: {emergency_file}")
        except Exception as e:
            logger.critical(f"Emergency save failed: {e}")
    
    def restore_context(self, timestamp: Optional[datetime] = None) -> bool:
        """Restore context from checkpoint or database."""
        with self._context_lock:
            try:
                with self._get_db_connection() as conn:
                    if timestamp:
                        snapshot = conn.execute(
                            """SELECT context_data FROM context_snapshots
                               WHERE timestamp <= ? ORDER BY timestamp DESC LIMIT 1""",
                            (timestamp,)
                        ).fetchone()
                    else:
                        snapshot = conn.execute(
                            """SELECT context_data FROM context_snapshots
                               ORDER BY timestamp DESC LIMIT 1"""
                        ).fetchone()
                    
                    if snapshot:
                        self.active_context = pickle.loads(snapshot['context_data'])
                        logger.info("Context restored from database")
                        return True
                
                # Fallback to checkpoint files
                checkpoint_files = sorted(self.checkpoint_dir.glob("recovery_*.pkl"))
                if checkpoint_files:
                    with open(checkpoint_files[-1], 'rb') as f:
                        self.active_context = pickle.load(f)
                    logger.info(f"Context restored from checkpoint: {checkpoint_files[-1]}")
                    return True
                
                # Fallback to emergency JSON
                emergency_files = sorted(self.base_path.glob("emergency_*.json"))
                if emergency_files:
                    with open(emergency_files[-1], 'r') as f:
                        context = json.load(f)
                        # Restore deques
                        context['conversation_history'] = deque(
                            context['conversation_history'], maxlen=100
                        )
                        context['decision_log'] = deque(
                            context['decision_log'], maxlen=50
                        )
                        self.active_context = context
                    logger.info(f"Context restored from emergency file: {emergency_files[-1]}")
                    return True
                
                logger.warning("No context found to restore")
                return False
                
            except Exception as e:
                logger.error(f"Failed to restore context: {e}")
                return False
    
    def update_task_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """Update task progress tracking."""
        with self._context_lock:
            self.active_context['task_progress'][task_id] = {
                **progress_data,
                'last_update': datetime.now().isoformat()
            }
            
            # Log significant progress changes
            if progress_data.get('percentage', 0) % 25 == 0:
                self.mark_recovery_point(f"Task {task_id} at {progress_data.get('percentage')}%")
    
    def log_decision(self, decision_type: str, context: str, 
                    decision: str, reasoning: str, outcome: str = None):
        """Log orchestration decisions for audit trail."""
        with self._context_lock:
            decision_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': decision_type,
                'context': context,
                'decision': decision,
                'reasoning': reasoning,
                'outcome': outcome
            }
            
            self.active_context['decision_log'].append(decision_entry)
            
            # Persist to database
            try:
                with self._get_db_connection() as conn:
                    conn.execute(
                        """INSERT INTO decision_log 
                           (decision_type, context, decision, reasoning, outcome)
                           VALUES (?, ?, ?, ?, ?)""",
                        (decision_type, context, decision, reasoning, outcome)
                    )
            except Exception as e:
                logger.error(f"Failed to log decision: {e}")
    
    def mark_recovery_point(self, reason: str):
        """Create manual recovery checkpoint."""
        logger.info(f"Creating recovery point: {reason}")
        self.save_context(recovery_point=True, reason=reason)
    
    def recover_from_crash(self):
        """Full crash recovery procedure."""
        logger.info("Starting crash recovery...")
        
        # Generate recovery report
        report = {
            'timestamp': datetime.now().isoformat(),
            'recovery_steps': [],
            'recovered_context': None,
            'stale_agents': [],
            'incomplete_tasks': []
        }
        
        # Step 1: Restore context
        if self.restore_context():
            report['recovery_steps'].append("Context restored successfully")
            report['recovered_context'] = {
                'current_task': self.active_context['current_task'],
                'workflow_state': self.active_context['workflow_state']
            }
        else:
            report['recovery_steps'].append("Failed to restore context - starting fresh")
        
        # Step 2: Check agent health
        stale_threshold = datetime.now() - timedelta(minutes=5)
        for agent_id, state in self.active_context['agent_states'].items():
            last_update = datetime.fromisoformat(state.get('last_update', '1970-01-01'))
            if last_update < stale_threshold:
                report['stale_agents'].append({
                    'agent_id': agent_id,
                    'last_seen': state.get('last_update'),
                    'last_task': state.get('current_task')
                })
        
        # Step 3: Identify incomplete tasks
        for task_id, progress in self.active_context['task_progress'].items():
            if progress.get('status') not in ['completed', 'failed']:
                report['incomplete_tasks'].append({
                    'task_id': task_id,
                    'progress': progress.get('percentage', 0),
                    'blockers': progress.get('blockers', [])
                })
        
        # Save recovery report
        report_file = self.base_path / f"recovery_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Recovery complete. Report saved to: {report_file}")
        return report
    
    def get_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """Get current state of an agent."""
        with self._context_lock:
            return self.active_context['agent_states'].get(agent_id, {})
    
    def update_agent_state(self, agent_id: str, state: Dict[str, Any]):
        """Update agent state."""
        with self._context_lock:
            self.active_context['agent_states'][agent_id] = {
                **state,
                'last_update': datetime.now().isoformat()
            }
    
    def log_agent_message(self, from_agent: str, to_agent: str, 
                         message_type: str, content: str, response: str = None):
        """Log inter-agent communication."""
        with self._context_lock:
            try:
                with self._get_db_connection() as conn:
                    conn.execute(
                        """INSERT INTO agent_coordination
                           (from_agent, to_agent, message_type, message_content, response)
                           VALUES (?, ?, ?, ?, ?)""",
                        (from_agent, to_agent, message_type, content, response)
                    )
            except Exception as e:
                logger.error(f"Failed to log agent message: {e}")
    
    def get_context_status(self) -> Dict[str, Any]:
        """Get current context status for monitoring."""
        with self._context_lock:
            return {
                'current_task': self.active_context['current_task'],
                'active_agents': len(self.active_context['agent_states']),
                'task_count': len(self.active_context['task_progress']),
                'conversation_size': len(self.active_context['conversation_history']),
                'decision_count': len(self.active_context['decision_log']),
                'workflow_phase': self.active_context['workflow_state']['phase']
            }
    
    def _cleanup(self):
        """Cleanup on shutdown."""
        logger.info("Shutting down JarvisContextManager...")
        self._stop_checkpoint.set()
        if self._checkpoint_thread:
            self._checkpoint_thread.join(timeout=5)
        
        # Final save
        self.save_context(recovery_point=True, reason="Graceful shutdown")
        
        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        logger.info(f"Received signal {signum}")
        self._cleanup()
        exit(0)