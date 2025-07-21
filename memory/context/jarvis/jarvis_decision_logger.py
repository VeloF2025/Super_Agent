#!/usr/bin/env python3
"""
Decision Logging System with Complete Audit Trail
Tracks all decisions made by Jarvis and agents for accountability
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
import threading
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of decisions that can be logged"""
    TASK_ASSIGNMENT = "task_assignment"
    RESOURCE_ALLOCATION = "resource_allocation"
    AGENT_SELECTION = "agent_selection"
    AUTO_ACCEPTANCE = "auto_acceptance"
    ERROR_HANDLING = "error_handling"
    WORKFLOW_MODIFICATION = "workflow_modification"
    SYSTEM_CONFIGURATION = "system_configuration"
    DATA_PROCESSING = "data_processing"
    SECURITY_ACTION = "security_action"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class DecisionImpact(Enum):
    """Impact level of decisions"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Decision:
    """Complete decision record"""
    decision_id: str
    timestamp: datetime
    agent_id: str
    decision_type: DecisionType
    description: str
    context: Dict[str, Any]
    alternatives_considered: List[Dict[str, Any]]
    chosen_option: Dict[str, Any]
    reasoning: str
    expected_impact: DecisionImpact
    actual_impact: Optional[DecisionImpact]
    outcome: Optional[str]
    reversible: bool
    rollback_plan: Optional[str]
    related_decisions: List[str]
    tags: List[str]


class JarvisDecisionLogger:
    """Comprehensive decision logging system"""
    
    def __init__(self, db_path: str = "./memory/context/jarvis/decision_log.db",
                 json_backup: str = "./memory/context/jarvis/decision_backup.json"):
        self.db_path = db_path
        self.json_backup = json_backup
        self.active_decisions = {}
        self.lock = threading.Lock()
        self._init_database()
        self._init_audit_file()
    
    def _init_database(self):
        """Initialize decision logging database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main decision log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_log (
                decision_id TEXT PRIMARY KEY,
                timestamp TEXT,
                agent_id TEXT,
                decision_type TEXT,
                description TEXT,
                context TEXT,
                alternatives_considered TEXT,
                chosen_option TEXT,
                reasoning TEXT,
                expected_impact TEXT,
                actual_impact TEXT,
                outcome TEXT,
                reversible BOOLEAN,
                rollback_plan TEXT,
                related_decisions TEXT,
                tags TEXT,
                INDEX idx_timestamp (timestamp),
                INDEX idx_agent (agent_id),
                INDEX idx_type (decision_type)
            )
        """)
        
        # Decision metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_metrics (
                decision_id TEXT PRIMARY KEY,
                execution_time_ms REAL,
                resources_used TEXT,
                affected_agents TEXT,
                performance_impact REAL,
                error_count INTEGER,
                rollback_triggered BOOLEAN,
                FOREIGN KEY (decision_id) REFERENCES decision_log(decision_id)
            )
        """)
        
        # Audit trail table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                decision_id TEXT,
                event_type TEXT,
                details TEXT,
                agent_id TEXT,
                INDEX idx_audit_decision (decision_id),
                INDEX idx_audit_time (timestamp)
            )
        """)
        
        # Decision dependencies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_dependencies (
                parent_decision TEXT,
                child_decision TEXT,
                dependency_type TEXT,
                created_at TEXT,
                PRIMARY KEY (parent_decision, child_decision)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _init_audit_file(self):
        """Initialize real-time audit file"""
        audit_dir = os.path.dirname(self.json_backup)
        if not os.path.exists(audit_dir):
            os.makedirs(audit_dir)
        
        # Create audit header if file doesn't exist
        audit_file = self.json_backup.replace('.json', '_audit.jsonl')
        if not os.path.exists(audit_file):
            with open(audit_file, 'w') as f:
                header = {
                    "audit_log_created": datetime.now().isoformat(),
                    "version": "1.0",
                    "description": "Real-time decision audit trail"
                }
                f.write(json.dumps(header) + "\n")
    
    def log_decision(self, agent_id: str, decision_type: DecisionType,
                    description: str, context: Dict[str, Any],
                    alternatives: List[Dict[str, Any]], chosen: Dict[str, Any],
                    reasoning: str, impact: DecisionImpact,
                    reversible: bool = True, rollback_plan: Optional[str] = None,
                    tags: Optional[List[str]] = None) -> str:
        """Log a new decision"""
        import uuid
        
        decision_id = f"DEC-{uuid.uuid4().hex[:8]}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        decision = Decision(
            decision_id=decision_id,
            timestamp=datetime.now(),
            agent_id=agent_id,
            decision_type=decision_type,
            description=description,
            context=context,
            alternatives_considered=alternatives,
            chosen_option=chosen,
            reasoning=reasoning,
            expected_impact=impact,
            actual_impact=None,
            outcome=None,
            reversible=reversible,
            rollback_plan=rollback_plan,
            related_decisions=[],
            tags=tags or []
        )
        
        with self.lock:
            # Store in active decisions
            self.active_decisions[decision_id] = decision
            
            # Log to database
            self._log_to_database(decision)
            
            # Log to audit file
            self._log_to_audit_file(decision_id, "DECISION_CREATED", {
                "agent": agent_id,
                "type": decision_type.value,
                "description": description
            })
            
            # Trigger real-time monitoring
            self._monitor_decision(decision_id)
        
        logger.info(f"Decision logged: {decision_id} - {description}")
        return decision_id
    
    def update_outcome(self, decision_id: str, outcome: str, 
                      actual_impact: DecisionImpact, metrics: Optional[Dict[str, Any]] = None):
        """Update decision outcome after execution"""
        with self.lock:
            if decision_id in self.active_decisions:
                decision = self.active_decisions[decision_id]
                decision.outcome = outcome
                decision.actual_impact = actual_impact
                
                # Update database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE decision_log
                    SET outcome = ?, actual_impact = ?
                    WHERE decision_id = ?
                """, (outcome, actual_impact.value, decision_id))
                
                # Log metrics if provided
                if metrics:
                    cursor.execute("""
                        INSERT OR REPLACE INTO decision_metrics
                        (decision_id, execution_time_ms, resources_used, 
                         affected_agents, performance_impact, error_count, rollback_triggered)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        decision_id,
                        metrics.get('execution_time_ms', 0),
                        json.dumps(metrics.get('resources_used', {})),
                        json.dumps(metrics.get('affected_agents', [])),
                        metrics.get('performance_impact', 0),
                        metrics.get('error_count', 0),
                        metrics.get('rollback_triggered', False)
                    ))
                
                conn.commit()
                conn.close()
                
                # Log to audit
                self._log_to_audit_file(decision_id, "OUTCOME_UPDATED", {
                    "outcome": outcome,
                    "impact": actual_impact.value,
                    "metrics": metrics
                })
                
                # Check if emergency action needed
                if actual_impact == DecisionImpact.CRITICAL and "failure" in outcome.lower():
                    self._trigger_emergency_review(decision_id, outcome)
    
    def link_decisions(self, parent_id: str, child_id: str, dependency_type: str = "caused_by"):
        """Link related decisions for traceability"""
        with self.lock:
            # Update parent's related decisions
            if parent_id in self.active_decisions:
                self.active_decisions[parent_id].related_decisions.append(child_id)
            
            # Update child's related decisions
            if child_id in self.active_decisions:
                self.active_decisions[child_id].related_decisions.append(parent_id)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO decision_dependencies
                (parent_decision, child_decision, dependency_type, created_at)
                VALUES (?, ?, ?, ?)
            """, (parent_id, child_id, dependency_type, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
    
    def trigger_rollback(self, decision_id: str, reason: str) -> bool:
        """Trigger rollback for a reversible decision"""
        with self.lock:
            if decision_id not in self.active_decisions:
                logger.error(f"Decision {decision_id} not found for rollback")
                return False
            
            decision = self.active_decisions[decision_id]
            
            if not decision.reversible:
                logger.error(f"Decision {decision_id} is not reversible")
                return False
            
            if not decision.rollback_plan:
                logger.error(f"Decision {decision_id} has no rollback plan")
                return False
            
            # Log rollback initiation
            self._log_to_audit_file(decision_id, "ROLLBACK_INITIATED", {
                "reason": reason,
                "rollback_plan": decision.rollback_plan
            })
            
            # Update metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE decision_metrics
                SET rollback_triggered = TRUE
                WHERE decision_id = ?
            """, (decision_id,))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"Rollback triggered for decision {decision_id}: {reason}")
            return True
    
    def get_decision_chain(self, decision_id: str) -> List[Dict[str, Any]]:
        """Get full decision chain (parents and children)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all related decisions recursively
        chain = []
        visited = set()
        to_visit = [decision_id]
        
        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            
            # Get decision details
            cursor.execute("""
                SELECT * FROM decision_log WHERE decision_id = ?
            """, (current,))
            
            result = cursor.fetchone()
            if result:
                chain.append(self._row_to_dict(cursor.description, result))
            
            # Get dependencies
            cursor.execute("""
                SELECT child_decision FROM decision_dependencies WHERE parent_decision = ?
                UNION
                SELECT parent_decision FROM decision_dependencies WHERE child_decision = ?
            """, (current, current))
            
            for (related,) in cursor.fetchall():
                if related not in visited:
                    to_visit.append(related)
        
        conn.close()
        return chain
    
    def search_decisions(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search decisions with filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM decision_log WHERE 1=1"
        params = []
        
        if 'agent_id' in filters:
            query += " AND agent_id = ?"
            params.append(filters['agent_id'])
        
        if 'decision_type' in filters:
            query += " AND decision_type = ?"
            params.append(filters['decision_type'])
        
        if 'start_date' in filters:
            query += " AND timestamp >= ?"
            params.append(filters['start_date'])
        
        if 'end_date' in filters:
            query += " AND timestamp <= ?"
            params.append(filters['end_date'])
        
        if 'impact' in filters:
            query += " AND (expected_impact = ? OR actual_impact = ?)"
            params.extend([filters['impact'], filters['impact']])
        
        if 'tags' in filters:
            for tag in filters['tags']:
                query += " AND tags LIKE ?"
                params.append(f"%{tag}%")
        
        query += " ORDER BY timestamp DESC"
        
        if 'limit' in filters:
            query += " LIMIT ?"
            params.append(filters['limit'])
        
        cursor.execute(query, params)
        results = []
        
        for row in cursor.fetchall():
            results.append(self._row_to_dict(cursor.description, row))
        
        conn.close()
        return results
    
    def generate_decision_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive decision report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now().timestamp() - (hours * 3600)
        since_str = datetime.fromtimestamp(since).isoformat()
        
        # Get decision statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN actual_impact = 'critical' THEN 1 END) as critical_decisions,
                COUNT(CASE WHEN actual_impact = 'high' THEN 1 END) as high_impact,
                COUNT(CASE WHEN outcome LIKE '%fail%' THEN 1 END) as failed_decisions,
                COUNT(CASE WHEN reversible = TRUE THEN 1 END) as reversible_decisions
            FROM decision_log
            WHERE timestamp > ?
        """, (since_str,))
        
        stats = cursor.fetchone()
        
        # Get breakdown by type
        cursor.execute("""
            SELECT decision_type, COUNT(*) as count,
                   AVG(CASE WHEN actual_impact IN ('high', 'critical') THEN 1 ELSE 0 END) as high_impact_rate
            FROM decision_log
            WHERE timestamp > ?
            GROUP BY decision_type
        """, (since_str,))
        
        by_type = cursor.fetchall()
        
        # Get rollback statistics
        cursor.execute("""
            SELECT COUNT(*) as rollback_count
            FROM decision_metrics
            WHERE rollback_triggered = TRUE
            AND decision_id IN (
                SELECT decision_id FROM decision_log WHERE timestamp > ?
            )
        """, (since_str,))
        
        rollbacks = cursor.fetchone()[0]
        
        # Get top agents by decision count
        cursor.execute("""
            SELECT agent_id, COUNT(*) as decision_count,
                   AVG(CASE WHEN outcome LIKE '%success%' THEN 1 ELSE 0 END) as success_rate
            FROM decision_log
            WHERE timestamp > ?
            GROUP BY agent_id
            ORDER BY decision_count DESC
            LIMIT 10
        """, (since_str,))
        
        top_agents = cursor.fetchall()
        
        conn.close()
        
        return {
            "period_hours": hours,
            "total_decisions": stats[0],
            "critical_decisions": stats[1],
            "high_impact_decisions": stats[2],
            "failed_decisions": stats[3],
            "reversible_decisions": stats[4],
            "rollback_count": rollbacks,
            "rollback_rate": rollbacks / stats[0] if stats[0] > 0 else 0,
            "breakdown_by_type": [
                {
                    "type": row[0],
                    "count": row[1],
                    "high_impact_rate": row[2]
                }
                for row in by_type
            ],
            "top_decision_makers": [
                {
                    "agent_id": row[0],
                    "decision_count": row[1],
                    "success_rate": row[2]
                }
                for row in top_agents
            ],
            "report_generated": datetime.now().isoformat()
        }
    
    def _log_to_database(self, decision: Decision):
        """Log decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO decision_log
            (decision_id, timestamp, agent_id, decision_type, description,
             context, alternatives_considered, chosen_option, reasoning,
             expected_impact, actual_impact, outcome, reversible,
             rollback_plan, related_decisions, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.decision_id,
            decision.timestamp.isoformat(),
            decision.agent_id,
            decision.decision_type.value,
            decision.description,
            json.dumps(decision.context),
            json.dumps(decision.alternatives_considered),
            json.dumps(decision.chosen_option),
            decision.reasoning,
            decision.expected_impact.value,
            decision.actual_impact.value if decision.actual_impact else None,
            decision.outcome,
            decision.reversible,
            decision.rollback_plan,
            json.dumps(decision.related_decisions),
            json.dumps(decision.tags)
        ))
        
        # Log initial audit entry
        cursor.execute("""
            INSERT INTO audit_trail
            (timestamp, decision_id, event_type, details, agent_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            decision.decision_id,
            "DECISION_CREATED",
            json.dumps({"description": decision.description}),
            decision.agent_id
        ))
        
        conn.commit()
        conn.close()
    
    def _log_to_audit_file(self, decision_id: str, event_type: str, details: Dict[str, Any]):
        """Log to real-time audit file"""
        audit_file = self.json_backup.replace('.json', '_audit.jsonl')
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "decision_id": decision_id,
            "event_type": event_type,
            "details": details
        }
        
        with open(audit_file, 'a') as f:
            f.write(json.dumps(audit_entry) + "\n")
    
    def _monitor_decision(self, decision_id: str):
        """Start monitoring a decision for anomalies"""
        # This could trigger alerts based on decision patterns
        pass
    
    def _trigger_emergency_review(self, decision_id: str, outcome: str):
        """Trigger emergency review for critical failures"""
        logger.critical(f"EMERGENCY REVIEW REQUIRED: Decision {decision_id} had critical failure")
        logger.critical(f"Outcome: {outcome}")
        
        # Log emergency event
        self._log_to_audit_file(decision_id, "EMERGENCY_REVIEW_TRIGGERED", {
            "outcome": outcome,
            "severity": "critical"
        })
    
    def _row_to_dict(self, description, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        result = {}
        for i, col in enumerate(description):
            value = row[i]
            # Parse JSON fields
            if col[0] in ['context', 'alternatives_considered', 'chosen_option', 
                         'related_decisions', 'tags', 'resources_used', 'affected_agents']:
                try:
                    value = json.loads(value) if value else None
                except:
                    pass
            result[col[0]] = value
        return result
    
    def export_audit_trail(self, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> str:
        """Export audit trail for compliance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_trail WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        
        export_file = f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_path = os.path.join(os.path.dirname(self.json_backup), export_file)
        
        with open(export_path, 'w') as f:
            audit_data = {
                "export_date": datetime.now().isoformat(),
                "start_date": start_date,
                "end_date": end_date,
                "entries": []
            }
            
            for row in cursor.fetchall():
                audit_data["entries"].append(self._row_to_dict(cursor.description, row))
            
            json.dump(audit_data, f, indent=2)
        
        conn.close()
        return export_path


# Example usage
if __name__ == "__main__":
    logger = JarvisDecisionLogger()
    
    # Log a decision
    decision_id = logger.log_decision(
        agent_id="agent-orchestrator-001",
        decision_type=DecisionType.TASK_ASSIGNMENT,
        description="Assign code review task to quality agent",
        context={"task_id": "TASK-123", "priority": "high"},
        alternatives=[
            {"agent": "agent-quality-001", "score": 0.9},
            {"agent": "agent-development-001", "score": 0.7}
        ],
        chosen={"agent": "agent-quality-001", "score": 0.9},
        reasoning="Quality agent has highest availability and expertise",
        impact=DecisionImpact.MEDIUM,
        reversible=True,
        rollback_plan="Reassign task to development agent",
        tags=["code_review", "quality_assurance"]
    )
    
    print(f"Decision logged: {decision_id}")
    
    # Update outcome
    logger.update_outcome(
        decision_id=decision_id,
        outcome="Task completed successfully in 45 minutes",
        actual_impact=DecisionImpact.LOW,
        metrics={
            "execution_time_ms": 2700000,
            "affected_agents": ["agent-quality-001"],
            "performance_impact": 0.1
        }
    )
    
    # Generate report
    report = logger.generate_decision_report(24)
    print(f"\nDecision Report (Last 24 hours):")
    print(f"Total decisions: {report['total_decisions']}")
    print(f"Critical decisions: {report['critical_decisions']}")
    print(f"Rollback rate: {report['rollback_rate']:.1%}")