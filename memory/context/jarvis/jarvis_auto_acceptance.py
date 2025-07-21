#!/usr/bin/env python3
"""
Jarvis Auto-Acceptance System with Confidence Building
Learns from past decisions to safely auto-accept routine operations
"""

import json
import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from shared.tools.directory_context_safety import DirectoryContextSafety, DirectorySafetyIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of requests that can be auto-accepted"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    CODE_ANALYSIS = "code_analysis"
    DEPENDENCY_INSTALL = "dependency_install"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    CONFIG_UPDATE = "config_update"
    LOG_ANALYSIS = "log_analysis"
    HEALTH_CHECK = "health_check"
    REPORT_GENERATION = "report_generation"
    CONTEXT_SAVE = "context_save"
    AGENT_COMMUNICATION = "agent_communication"
    DATA_PROCESSING = "data_processing"
    CACHE_CLEAR = "cache_clear"
    BACKUP_CREATE = "backup_create"
    MONITORING_CHECK = "monitoring_check"


class RiskLevel(Enum):
    """Risk levels for operations"""
    MINIMAL = 1    # Safe operations like reading logs
    LOW = 2        # Minor modifications like config updates
    MEDIUM = 3     # Operations that could affect functionality
    HIGH = 4       # Operations that could break systems
    CRITICAL = 5   # Operations that could cause data loss


class DecisionOutcome(Enum):
    """Outcomes of auto-accepted decisions"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ROLLED_BACK = "rolled_back"
    MANUAL_OVERRIDE = "manual_override"


@dataclass
class AutoAcceptanceDecision:
    """Record of an auto-acceptance decision"""
    decision_id: str
    timestamp: datetime
    request_type: RequestType
    request_details: Dict[str, Any]
    risk_level: RiskLevel
    confidence_score: float
    auto_accepted: bool
    reasoning: List[str]
    outcome: Optional[DecisionOutcome]
    error_details: Optional[str]
    rollback_performed: bool = False


@dataclass
class OperationPattern:
    """Pattern of operations that have been successful"""
    pattern_hash: str
    request_type: RequestType
    key_attributes: Dict[str, Any]
    success_count: int
    failure_count: int
    last_success: datetime
    average_duration: float
    confidence_score: float


class JarvisAutoAcceptance:
    """Main auto-acceptance system with confidence building"""
    
    def __init__(self, db_path: str = "./memory/context/jarvis/auto_acceptance.db"):
        self.db_path = db_path
        self.confidence_threshold = 0.8  # Start conservative
        self.emergency_stop = False
        self.learning_enabled = True
        self.decision_cache = {}
        self.directory_safety = DirectoryContextSafety()
        self.safety_integration = DirectorySafetyIntegration()
        self._init_database()
        self._load_sop_rules()
        
        # Start monitoring thread
        self._start_monitoring()
    
    def _init_database(self):
        """Initialize decision history database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Decision history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_history (
                decision_id TEXT PRIMARY KEY,
                timestamp TEXT,
                request_type TEXT,
                request_details TEXT,
                risk_level INTEGER,
                confidence_score REAL,
                auto_accepted BOOLEAN,
                reasoning TEXT,
                outcome TEXT,
                error_details TEXT,
                rollback_performed BOOLEAN
            )
        """)
        
        # Operation patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_patterns (
                pattern_hash TEXT PRIMARY KEY,
                request_type TEXT,
                key_attributes TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_success TEXT,
                average_duration REAL,
                confidence_score REAL
            )
        """)
        
        # SOP rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sop_rules (
                rule_id TEXT PRIMARY KEY,
                request_type TEXT,
                conditions TEXT,
                required_confidence REAL,
                max_risk_level INTEGER,
                requires_verification BOOLEAN,
                enabled BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Emergency stop log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_stops (
                timestamp TEXT,
                triggered_by TEXT,
                reason TEXT,
                decisions_affected INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def evaluate_request(self, request_type: RequestType, request_details: Dict[str, Any]) -> Tuple[bool, AutoAcceptanceDecision]:
        """Evaluate whether a request should be auto-accepted"""
        if self.emergency_stop:
            logger.warning("Emergency stop active - manual approval required")
            return False, self._create_decision(request_type, request_details, False, ["Emergency stop active"])
        
        # Calculate risk level
        risk_level = self._assess_risk(request_type, request_details)
        
        # Get historical confidence
        pattern_hash = self._generate_pattern_hash(request_type, request_details)
        confidence = self._calculate_confidence(pattern_hash, request_type)
        
        # Check SOP rules
        sop_approved, sop_reasons = self._check_sop_rules(request_type, request_details, risk_level, confidence)
        
        # Make decision
        auto_accept = False
        reasoning = []
        
        if risk_level.value <= RiskLevel.LOW.value and confidence >= self.confidence_threshold:
            auto_accept = True
            reasoning.append(f"Low risk operation with {confidence:.2%} confidence")
        
        if sop_approved:
            auto_accept = True
            reasoning.extend(sop_reasons)
        else:
            auto_accept = False
            reasoning.extend(sop_reasons)
        
        # Additional safety checks
        if auto_accept:
            safety_passed, safety_reasons = self._safety_checks(request_type, request_details)
            if not safety_passed:
                auto_accept = False
                reasoning.extend(safety_reasons)
        
        # Create decision record
        decision = self._create_decision(
            request_type, request_details, auto_accept, reasoning,
            risk_level=risk_level, confidence=confidence
        )
        
        # Log decision
        self._log_decision(decision)
        
        return auto_accept, decision
    
    def _assess_risk(self, request_type: RequestType, details: Dict[str, Any]) -> RiskLevel:
        """Assess risk level of operation"""
        # Base risk levels by type
        risk_map = {
            RequestType.FILE_READ: RiskLevel.MINIMAL,
            RequestType.LOG_ANALYSIS: RiskLevel.MINIMAL,
            RequestType.HEALTH_CHECK: RiskLevel.MINIMAL,
            RequestType.MONITORING_CHECK: RiskLevel.MINIMAL,
            RequestType.CODE_ANALYSIS: RiskLevel.LOW,
            RequestType.REPORT_GENERATION: RiskLevel.LOW,
            RequestType.CONTEXT_SAVE: RiskLevel.LOW,
            RequestType.AGENT_COMMUNICATION: RiskLevel.LOW,
            RequestType.CACHE_CLEAR: RiskLevel.LOW,
            RequestType.FILE_WRITE: RiskLevel.MEDIUM,
            RequestType.CONFIG_UPDATE: RiskLevel.MEDIUM,
            RequestType.BACKUP_CREATE: RiskLevel.MEDIUM,
            RequestType.DATA_PROCESSING: RiskLevel.MEDIUM,
            RequestType.SERVICE_START: RiskLevel.HIGH,
            RequestType.SERVICE_STOP: RiskLevel.HIGH,
            RequestType.DEPENDENCY_INSTALL: RiskLevel.HIGH,
            RequestType.FILE_DELETE: RiskLevel.CRITICAL,
        }
        
        base_risk = risk_map.get(request_type, RiskLevel.HIGH)
        
        # Adjust based on specific details
        if request_type == RequestType.FILE_WRITE:
            if 'backup' in details.get('file_path', '').lower():
                return RiskLevel.LOW
            if 'config' in details.get('file_path', '').lower():
                return RiskLevel.HIGH
        
        if request_type == RequestType.FILE_DELETE:
            if 'temp' in details.get('file_path', '').lower():
                return RiskLevel.MEDIUM
            if 'log' in details.get('file_path', '').lower():
                return RiskLevel.MEDIUM
        
        return base_risk
    
    def _calculate_confidence(self, pattern_hash: str, request_type: RequestType) -> float:
        """Calculate confidence based on historical success"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get pattern statistics
        cursor.execute("""
            SELECT success_count, failure_count, confidence_score
            FROM operation_patterns
            WHERE pattern_hash = ?
        """, (pattern_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # No history - start with low confidence
            return 0.3
        
        success_count, failure_count, stored_confidence = result
        total = success_count + failure_count
        
        if total < 5:
            # Not enough data - use cautious confidence
            return min(0.5, success_count / 5)
        
        # Calculate confidence based on success rate and volume
        success_rate = success_count / total
        volume_factor = min(1.0, total / 100)  # More operations = more confidence
        
        confidence = success_rate * 0.7 + volume_factor * 0.3
        
        # Factor in time decay
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT last_success FROM operation_patterns
            WHERE pattern_hash = ?
        """, (pattern_hash,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            last_success = datetime.fromisoformat(result[0])
            days_ago = (datetime.now() - last_success).days
            if days_ago > 30:
                confidence *= 0.8  # Reduce confidence for old patterns
        
        return confidence
    
    def _check_sop_rules(self, request_type: RequestType, details: Dict[str, Any], 
                        risk_level: RiskLevel, confidence: float) -> Tuple[bool, List[str]]:
        """Check standard operating procedure rules"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rule_id, conditions, required_confidence, max_risk_level, requires_verification
            FROM sop_rules
            WHERE request_type = ? AND enabled = TRUE
        """, (request_type.value,))
        
        rules = cursor.fetchall()
        conn.close()
        
        reasons = []
        approved = True
        
        for rule_id, conditions_json, req_confidence, max_risk, requires_verify in rules:
            conditions = json.loads(conditions_json)
            
            # Check risk level
            if risk_level.value > max_risk:
                approved = False
                reasons.append(f"Rule {rule_id}: Risk level {risk_level.value} exceeds maximum {max_risk}")
                continue
            
            # Check confidence
            if confidence < req_confidence:
                approved = False
                reasons.append(f"Rule {rule_id}: Confidence {confidence:.2%} below required {req_confidence:.2%}")
                continue
            
            # Check specific conditions
            condition_met = self._evaluate_conditions(conditions, details)
            if not condition_met:
                approved = False
                reasons.append(f"Rule {rule_id}: Conditions not met")
                continue
            
            if requires_verify:
                reasons.append(f"Rule {rule_id}: Requires verification (not auto-approved)")
                approved = False
            else:
                reasons.append(f"Rule {rule_id}: All conditions met")
        
        return approved, reasons
    
    def _safety_checks(self, request_type: RequestType, details: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Perform final safety checks"""
        reasons = []
        safe = True
        
        # Check for dangerous patterns
        if request_type in [RequestType.FILE_DELETE, RequestType.FILE_WRITE, RequestType.FILE_READ]:
            path = details.get('file_path', '')
            dangerous_paths = ['/system', '/boot', 'C:\\Windows', 'C:\\Program Files']
            for danger in dangerous_paths:
                if danger in path:
                    safe = False
                    reasons.append(f"Dangerous path detected: {danger}")
            
            # Directory context safety check
            agent_id = details.get('agent_id', 'unknown-agent')
            current_dir = os.getcwd()
            target_dir = os.path.dirname(path) if path else current_dir
            
            dir_safe, risk_level, warnings = self.directory_safety.validate_directory_context(
                agent_id, current_dir, target_dir
            )
            
            if risk_level == "high":
                safe = False
                reasons.append(f"Directory safety check failed: {', '.join(warnings)}")
            elif risk_level == "medium" and len(warnings) > 1:
                safe = False
                reasons.append(f"Multiple directory warnings: {', '.join(warnings)}")
        
        # Check for cross-directory operations
        if request_type == RequestType.FILE_WRITE:
            agent_id = details.get('agent_id', 'unknown-agent')
            file_path = details.get('file_path', '')
            if file_path:
                file_safe, reason = self.directory_safety.check_file_operation(
                    agent_id, file_path, 'write'
                )
                if not file_safe:
                    safe = False
                    reasons.append(reason)
        
        # Check recent failure rate
        failure_rate = self._get_recent_failure_rate()
        if failure_rate > 0.2:  # More than 20% failures recently
            safe = False
            reasons.append(f"High recent failure rate: {failure_rate:.2%}")
        
        # Check for ongoing issues
        if self._has_ongoing_issues():
            safe = False
            reasons.append("System has ongoing issues - manual review required")
        
        return safe, reasons
    
    def record_outcome(self, decision_id: str, outcome: DecisionOutcome, error_details: Optional[str] = None):
        """Record the outcome of an auto-accepted decision"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update decision record
        cursor.execute("""
            UPDATE decision_history
            SET outcome = ?, error_details = ?
            WHERE decision_id = ?
        """, (outcome.value, error_details, decision_id))
        
        # Get decision details for pattern learning
        cursor.execute("""
            SELECT request_type, request_details, confidence_score
            FROM decision_history
            WHERE decision_id = ?
        """, (decision_id,))
        
        result = cursor.fetchone()
        if result:
            request_type, details_json, confidence = result
            details = json.loads(details_json)
            pattern_hash = self._generate_pattern_hash(RequestType(request_type), details)
            
            # Update pattern statistics
            if outcome == DecisionOutcome.SUCCESS:
                self._update_pattern_success(pattern_hash, RequestType(request_type), details)
            else:
                self._update_pattern_failure(pattern_hash, RequestType(request_type), details)
                
                # Check if we need emergency stop
                if outcome == DecisionOutcome.FAILURE:
                    self._check_emergency_conditions()
        
        conn.commit()
        conn.close()
    
    def _update_pattern_success(self, pattern_hash: str, request_type: RequestType, details: Dict[str, Any]):
        """Update pattern statistics for successful operation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO operation_patterns 
            (pattern_hash, request_type, key_attributes, success_count, failure_count, 
             last_success, average_duration, confidence_score)
            VALUES (?, ?, ?, 1, 0, ?, 0, 0.5)
            ON CONFLICT(pattern_hash) DO UPDATE SET
                success_count = success_count + 1,
                last_success = ?,
                confidence_score = (success_count + 1.0) / (success_count + failure_count + 1.0)
        """, (pattern_hash, request_type.value, json.dumps(self._extract_key_attributes(details)),
              datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def _update_pattern_failure(self, pattern_hash: str, request_type: RequestType, details: Dict[str, Any]):
        """Update pattern statistics for failed operation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO operation_patterns 
            (pattern_hash, request_type, key_attributes, success_count, failure_count, 
             last_success, average_duration, confidence_score)
            VALUES (?, ?, ?, 0, 1, NULL, 0, 0.0)
            ON CONFLICT(pattern_hash) DO UPDATE SET
                failure_count = failure_count + 1,
                confidence_score = success_count / (success_count + failure_count + 1.0)
        """, (pattern_hash, request_type.value, json.dumps(self._extract_key_attributes(details))))
        
        conn.commit()
        conn.close()
    
    def trigger_emergency_stop(self, reason: str):
        """Trigger emergency stop - all operations require manual approval"""
        self.emergency_stop = True
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count affected decisions
        cursor.execute("""
            SELECT COUNT(*) FROM decision_history
            WHERE outcome IS NULL AND auto_accepted = TRUE
        """)
        affected = cursor.fetchone()[0]
        
        # Log emergency stop
        cursor.execute("""
            INSERT INTO emergency_stops (timestamp, triggered_by, reason, decisions_affected)
            VALUES (?, ?, ?, ?)
        """, (datetime.now().isoformat(), "system", reason, affected))
        
        conn.commit()
        conn.close()
        
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")
        logger.critical(f"Affected decisions: {affected}")
    
    def reset_emergency_stop(self):
        """Reset emergency stop after manual review"""
        self.emergency_stop = False
        logger.info("Emergency stop reset - auto-acceptance resumed")
    
    def _check_emergency_conditions(self):
        """Check if emergency stop should be triggered"""
        # Get recent failure stats
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check failures in last hour
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM decision_history
            WHERE timestamp > ? AND outcome = ? AND auto_accepted = TRUE
        """, (one_hour_ago, DecisionOutcome.FAILURE.value))
        
        recent_failures = cursor.fetchone()[0]
        
        # Check total in last hour
        cursor.execute("""
            SELECT COUNT(*) FROM decision_history
            WHERE timestamp > ? AND auto_accepted = TRUE
        """, (one_hour_ago,))
        
        recent_total = cursor.fetchone()[0]
        conn.close()
        
        # Trigger emergency stop conditions
        if recent_failures >= 5:
            self.trigger_emergency_stop(f"{recent_failures} failures in last hour")
        elif recent_total > 0 and recent_failures / recent_total > 0.3:
            self.trigger_emergency_stop(f"Failure rate {recent_failures/recent_total:.1%} exceeds 30%")
    
    def _generate_pattern_hash(self, request_type: RequestType, details: Dict[str, Any]) -> str:
        """Generate hash for operation pattern"""
        key_attrs = self._extract_key_attributes(details)
        pattern_str = f"{request_type.value}:{json.dumps(key_attrs, sort_keys=True)}"
        return hashlib.sha256(pattern_str.encode()).hexdigest()[:16]
    
    def _extract_key_attributes(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key attributes that define a pattern"""
        # Extract only the important attributes that define the pattern
        key_attrs = {}
        
        if 'file_path' in details:
            # Use directory and extension, not full path
            path = Path(details['file_path'])
            key_attrs['directory'] = str(path.parent)
            key_attrs['extension'] = path.suffix
        
        if 'service_name' in details:
            key_attrs['service_name'] = details['service_name']
        
        if 'operation_type' in details:
            key_attrs['operation_type'] = details['operation_type']
        
        return key_attrs
    
    def _create_decision(self, request_type: RequestType, details: Dict[str, Any], 
                        auto_accepted: bool, reasoning: List[str], 
                        risk_level: RiskLevel = None, confidence: float = 0.0) -> AutoAcceptanceDecision:
        """Create decision record"""
        import uuid
        
        return AutoAcceptanceDecision(
            decision_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            request_type=request_type,
            request_details=details,
            risk_level=risk_level or RiskLevel.MEDIUM,
            confidence_score=confidence,
            auto_accepted=auto_accepted,
            reasoning=reasoning,
            outcome=None,
            error_details=None
        )
    
    def _log_decision(self, decision: AutoAcceptanceDecision):
        """Log decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO decision_history 
            (decision_id, timestamp, request_type, request_details, risk_level, 
             confidence_score, auto_accepted, reasoning, outcome, error_details, rollback_performed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.decision_id,
            decision.timestamp.isoformat(),
            decision.request_type.value,
            json.dumps(decision.request_details),
            decision.risk_level.value,
            decision.confidence_score,
            decision.auto_accepted,
            json.dumps(decision.reasoning),
            decision.outcome.value if decision.outcome else None,
            decision.error_details,
            decision.rollback_performed
        ))
        
        conn.commit()
        conn.close()
    
    def _get_recent_failure_rate(self) -> float:
        """Get failure rate for recent auto-accepted decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN outcome = ? THEN 1 END) as failures,
                COUNT(*) as total
            FROM decision_history
            WHERE timestamp > ? AND auto_accepted = TRUE AND outcome IS NOT NULL
        """, (DecisionOutcome.FAILURE.value, one_hour_ago))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[1] > 0:
            return result[0] / result[1]
        return 0.0
    
    def _has_ongoing_issues(self) -> bool:
        """Check if system has ongoing issues"""
        # Check recent error patterns
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        cursor.execute("""
            SELECT COUNT(*) FROM decision_history
            WHERE timestamp > ? AND outcome = ? AND auto_accepted = TRUE
        """, (five_min_ago, DecisionOutcome.FAILURE.value))
        
        recent_failures = cursor.fetchone()[0]
        conn.close()
        
        return recent_failures >= 3
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], details: Dict[str, Any]) -> bool:
        """Evaluate rule conditions against request details"""
        for key, expected in conditions.items():
            if key not in details:
                return False
            
            if isinstance(expected, list):
                if details[key] not in expected:
                    return False
            elif details[key] != expected:
                return False
        
        return True
    
    def _load_sop_rules(self):
        """Load standard operating procedure rules"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Default SOP rules
        default_rules = [
            # Safe read operations
            ("read_logs", RequestType.LOG_ANALYSIS.value, {}, 0.5, RiskLevel.MINIMAL.value, False),
            ("read_files", RequestType.FILE_READ.value, {}, 0.6, RiskLevel.MINIMAL.value, False),
            ("health_checks", RequestType.HEALTH_CHECK.value, {}, 0.5, RiskLevel.MINIMAL.value, False),
            
            # Context operations
            ("save_context", RequestType.CONTEXT_SAVE.value, {}, 0.7, RiskLevel.LOW.value, False),
            
            # Safe write operations
            ("write_logs", RequestType.FILE_WRITE.value, {"file_type": "log"}, 0.8, RiskLevel.LOW.value, False),
            ("write_reports", RequestType.REPORT_GENERATION.value, {}, 0.7, RiskLevel.LOW.value, False),
            
            # Higher risk operations
            ("service_ops", RequestType.SERVICE_START.value, {}, 0.9, RiskLevel.HIGH.value, True),
            ("delete_ops", RequestType.FILE_DELETE.value, {}, 0.95, RiskLevel.CRITICAL.value, True),
        ]
        
        for rule_id, req_type, conditions, confidence, max_risk, verify in default_rules:
            cursor.execute("""
                INSERT OR IGNORE INTO sop_rules 
                (rule_id, request_type, conditions, required_confidence, max_risk_level, requires_verification)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rule_id, req_type, json.dumps(conditions), confidence, max_risk, verify))
        
        conn.commit()
        conn.close()
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        def monitor_loop():
            while True:
                try:
                    # Periodic health check
                    self._check_system_health()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _check_system_health(self):
        """Periodic system health check"""
        # Clean old decisions
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute("""
            DELETE FROM decision_history
            WHERE timestamp < ? AND outcome IS NOT NULL
        """, (thirty_days_ago,))
        
        conn.commit()
        conn.close()
    
    def get_decision_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate report of recent decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # Get statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN auto_accepted = TRUE THEN 1 END) as auto_accepted,
                COUNT(CASE WHEN outcome = ? THEN 1 END) as successful,
                COUNT(CASE WHEN outcome = ? THEN 1 END) as failed,
                AVG(confidence_score) as avg_confidence
            FROM decision_history
            WHERE timestamp > ?
        """, (DecisionOutcome.SUCCESS.value, DecisionOutcome.FAILURE.value, since))
        
        stats = cursor.fetchone()
        
        # Get breakdown by type
        cursor.execute("""
            SELECT request_type, COUNT(*) as count,
                   COUNT(CASE WHEN auto_accepted = TRUE THEN 1 END) as auto_accepted,
                   AVG(confidence_score) as avg_confidence
            FROM decision_history
            WHERE timestamp > ?
            GROUP BY request_type
        """, (since,))
        
        by_type = cursor.fetchall()
        
        conn.close()
        
        return {
            "period_hours": hours,
            "total_decisions": stats[0],
            "auto_accepted": stats[1],
            "successful": stats[2],
            "failed": stats[3],
            "average_confidence": stats[4],
            "acceptance_rate": stats[1] / stats[0] if stats[0] > 0 else 0,
            "success_rate": stats[2] / stats[1] if stats[1] > 0 else 0,
            "breakdown_by_type": [
                {
                    "type": row[0],
                    "count": row[1],
                    "auto_accepted": row[2],
                    "avg_confidence": row[3]
                }
                for row in by_type
            ],
            "emergency_stop_active": self.emergency_stop
        }


# Example usage and integration
if __name__ == "__main__":
    # Initialize system
    auto_accept = JarvisAutoAcceptance()
    
    # Example: Evaluate a file read request
    request = {
        "file_path": "/var/log/application.log",
        "purpose": "error_analysis"
    }
    
    approved, decision = auto_accept.evaluate_request(RequestType.FILE_READ, request)
    print(f"Auto-approved: {approved}")
    print(f"Reasoning: {decision.reasoning}")
    
    # Simulate outcome
    if approved:
        # Perform operation...
        # Then record outcome
        auto_accept.record_outcome(decision.decision_id, DecisionOutcome.SUCCESS)
    
    # Get report
    report = auto_accept.get_decision_report(24)
    print(f"\nLast 24 hours: {report['auto_accepted']}/{report['total_decisions']} auto-accepted")
    print(f"Success rate: {report['success_rate']:.1%}")