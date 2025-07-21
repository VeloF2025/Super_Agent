#!/usr/bin/env python3
"""
Safety Monitoring and Emergency Stop System
Monitors all agent operations and can halt the system if issues detected
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum
import logging
import psutil
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """System threat levels"""
    SAFE = 1
    CAUTION = 2
    WARNING = 3
    DANGER = 4
    CRITICAL = 5


class SafetyViolationType(Enum):
    """Types of safety violations"""
    HIGH_ERROR_RATE = "high_error_rate"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_CORRUPTION = "data_corruption"
    INFINITE_LOOP = "infinite_loop"
    CASCADE_FAILURE = "cascade_failure"
    SECURITY_BREACH = "security_breach"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    UNRESPONSIVE_AGENT = "unresponsive_agent"
    RAPID_STATE_CHANGES = "rapid_state_changes"


@dataclass
class SafetyIncident:
    """Record of a safety incident"""
    incident_id: str
    timestamp: datetime
    violation_type: SafetyViolationType
    threat_level: ThreatLevel
    affected_agents: List[str]
    description: str
    metrics: Dict[str, float]
    auto_resolved: bool
    resolution: Optional[str]


class JarvisSafetyMonitor:
    """Comprehensive safety monitoring system"""
    
    def __init__(self, heartbeat_dir: str = "./shared/heartbeats",
                 log_dir: str = "./memory/context/jarvis/safety"):
        self.heartbeat_dir = heartbeat_dir
        self.log_dir = log_dir
        self.emergency_stop_active = False
        self.monitoring_active = True
        self.safety_thresholds = self._load_safety_thresholds()
        self.incidents = []
        self.agent_states = {}
        self.performance_metrics = {}
        self.blocked_operations = set()
        
        # Create directories
        os.makedirs(log_dir, exist_ok=True)
        
        # Start monitoring
        self._start_monitoring_threads()
    
    def _load_safety_thresholds(self) -> Dict[str, Any]:
        """Load safety threshold configurations"""
        return {
            "max_error_rate": 0.3,  # 30% error rate triggers warning
            "max_cpu_usage": 90,    # 90% CPU usage
            "max_memory_usage": 85,  # 85% memory usage
            "max_response_time": 30,  # 30 seconds
            "heartbeat_timeout": 120,  # 2 minutes without heartbeat
            "cascade_threshold": 3,  # 3 related failures
            "rapid_change_window": 60,  # 1 minute window
            "rapid_change_count": 10,  # 10 state changes in window
        }
    
    def check_system_safety(self) -> Tuple[ThreatLevel, List[str]]:
        """Perform comprehensive safety check"""
        threat_level = ThreatLevel.SAFE
        issues = []
        
        # Check heartbeats
        heartbeat_issues = self._check_heartbeats()
        if heartbeat_issues:
            threat_level = max(threat_level, ThreatLevel.WARNING)
            issues.extend(heartbeat_issues)
        
        # Check resource usage
        resource_issues = self._check_resource_usage()
        if resource_issues:
            threat_level = max(threat_level, ThreatLevel.CAUTION)
            issues.extend(resource_issues)
        
        # Check error rates
        error_issues = self._check_error_rates()
        if error_issues:
            threat_level = max(threat_level, ThreatLevel.WARNING)
            issues.extend(error_issues)
        
        # Check for cascade failures
        cascade_issues = self._check_cascade_failures()
        if cascade_issues:
            threat_level = max(threat_level, ThreatLevel.DANGER)
            issues.extend(cascade_issues)
        
        # Check for rapid state changes
        rapid_changes = self._check_rapid_state_changes()
        if rapid_changes:
            threat_level = max(threat_level, ThreatLevel.WARNING)
            issues.extend(rapid_changes)
        
        # Determine if emergency stop needed
        if threat_level.value >= ThreatLevel.DANGER.value:
            self._evaluate_emergency_stop(threat_level, issues)
        
        return threat_level, issues
    
    def _check_heartbeats(self) -> List[str]:
        """Check agent heartbeats for issues"""
        issues = []
        current_time = datetime.now()
        timeout = self.safety_thresholds["heartbeat_timeout"]
        
        try:
            for filename in os.listdir(self.heartbeat_dir):
                if filename.endswith('.heartbeat'):
                    filepath = os.path.join(self.heartbeat_dir, filename)
                    
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        
                        # Check timestamp
                        heartbeat_time = datetime.fromisoformat(data['timestamp'])
                        time_diff = (current_time - heartbeat_time).total_seconds()
                        
                        if time_diff > timeout:
                            agent_id = data.get('agent_id', filename)
                            issues.append(f"Agent {agent_id} heartbeat timeout ({time_diff:.0f}s)")
                            self._record_incident(
                                SafetyViolationType.UNRESPONSIVE_AGENT,
                                ThreatLevel.WARNING,
                                [agent_id],
                                f"No heartbeat for {time_diff:.0f} seconds"
                            )
                        
                        # Update agent state
                        self.agent_states[data['agent_id']] = {
                            'last_heartbeat': heartbeat_time,
                            'status': data.get('status', 'unknown'),
                            'pid': data.get('pid')
                        }
                    
                    except Exception as e:
                        issues.append(f"Error reading heartbeat {filename}: {e}")
        
        except Exception as e:
            issues.append(f"Error checking heartbeats: {e}")
        
        return issues
    
    def _check_resource_usage(self) -> List[str]:
        """Check system resource usage"""
        issues = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.safety_thresholds["max_cpu_usage"]:
                issues.append(f"High CPU usage: {cpu_percent}%")
                self._record_incident(
                    SafetyViolationType.RESOURCE_EXHAUSTION,
                    ThreatLevel.WARNING,
                    ["system"],
                    f"CPU usage at {cpu_percent}%"
                )
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.safety_thresholds["max_memory_usage"]:
                issues.append(f"High memory usage: {memory.percent}%")
                self._record_incident(
                    SafetyViolationType.RESOURCE_EXHAUSTION,
                    ThreatLevel.WARNING,
                    ["system"],
                    f"Memory usage at {memory.percent}%"
                )
            
            # Check individual agent processes
            for agent_id, state in self.agent_states.items():
                if 'pid' in state and state['pid']:
                    try:
                        process = psutil.Process(state['pid'])
                        agent_cpu = process.cpu_percent(interval=0.1)
                        agent_memory = process.memory_percent()
                        
                        if agent_cpu > 50:  # Single agent using >50% CPU
                            issues.append(f"Agent {agent_id} high CPU: {agent_cpu}%")
                        
                        if agent_memory > 10:  # Single agent using >10% memory
                            issues.append(f"Agent {agent_id} high memory: {agent_memory}%")
                    
                    except psutil.NoSuchProcess:
                        pass
        
        except Exception as e:
            issues.append(f"Error checking resources: {e}")
        
        return issues
    
    def _check_error_rates(self) -> List[str]:
        """Check error rates from logs and metrics"""
        issues = []
        
        # This would integrate with the decision logger to check failure rates
        # For now, using placeholder logic
        if hasattr(self, 'decision_logger'):
            recent_stats = self.decision_logger.get_decision_report(1)  # Last hour
            
            if recent_stats['total_decisions'] > 0:
                failure_rate = recent_stats['failed_decisions'] / recent_stats['total_decisions']
                
                if failure_rate > self.safety_thresholds["max_error_rate"]:
                    issues.append(f"High failure rate: {failure_rate:.1%}")
                    self._record_incident(
                        SafetyViolationType.HIGH_ERROR_RATE,
                        ThreatLevel.DANGER,
                        ["system"],
                        f"Decision failure rate at {failure_rate:.1%}"
                    )
        
        return issues
    
    def _check_cascade_failures(self) -> List[str]:
        """Check for cascade failure patterns"""
        issues = []
        
        # Look for multiple related failures in recent incidents
        recent_window = datetime.now() - timedelta(minutes=15)
        recent_incidents = [i for i in self.incidents if i.timestamp > recent_window]
        
        # Group by affected agents
        agent_incident_count = {}
        for incident in recent_incidents:
            for agent in incident.affected_agents:
                agent_incident_count[agent] = agent_incident_count.get(agent, 0) + 1
        
        # Check for cascade pattern
        cascade_agents = [agent for agent, count in agent_incident_count.items() 
                         if count >= self.safety_thresholds["cascade_threshold"]]
        
        if cascade_agents:
            issues.append(f"Potential cascade failure: {cascade_agents}")
            self._record_incident(
                SafetyViolationType.CASCADE_FAILURE,
                ThreatLevel.DANGER,
                cascade_agents,
                "Multiple related failures detected"
            )
        
        return issues
    
    def _check_rapid_state_changes(self) -> List[str]:
        """Check for rapid state changes indicating instability"""
        issues = []
        
        # Track state changes per agent
        window_start = datetime.now() - timedelta(seconds=self.safety_thresholds["rapid_change_window"])
        
        for agent_id, changes in self.performance_metrics.get('state_changes', {}).items():
            recent_changes = [c for c in changes if c['timestamp'] > window_start]
            
            if len(recent_changes) > self.safety_thresholds["rapid_change_count"]:
                issues.append(f"Agent {agent_id} rapid state changes: {len(recent_changes)}")
                self._record_incident(
                    SafetyViolationType.RAPID_STATE_CHANGES,
                    ThreatLevel.WARNING,
                    [agent_id],
                    f"{len(recent_changes)} state changes in {self.safety_thresholds['rapid_change_window']}s"
                )
        
        return issues
    
    def trigger_emergency_stop(self, reason: str, affected_agents: Optional[List[str]] = None):
        """Trigger emergency stop of system or specific agents"""
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")
        self.emergency_stop_active = True
        
        timestamp = datetime.now()
        
        # Log emergency stop
        emergency_log = {
            "timestamp": timestamp.isoformat(),
            "reason": reason,
            "affected_agents": affected_agents or ["all"],
            "system_state": self._capture_system_state()
        }
        
        log_file = os.path.join(self.log_dir, f"emergency_stop_{timestamp.strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w') as f:
            json.dump(emergency_log, f, indent=2)
        
        # Stop affected agents
        if affected_agents:
            for agent_id in affected_agents:
                self._stop_agent(agent_id)
        else:
            # Stop all agents
            self._stop_all_agents()
        
        # Block operations
        self.blocked_operations = {
            "auto_acceptance",
            "task_assignment",
            "resource_allocation",
            "system_modification"
        }
        
        logger.critical(f"Emergency stop log: {log_file}")
        logger.critical("Manual intervention required to resume operations")
    
    def resume_operations(self, admin_token: str) -> bool:
        """Resume operations after emergency stop"""
        # Verify admin token (implement proper authentication)
        if not self._verify_admin_token(admin_token):
            logger.error("Invalid admin token for resume operations")
            return False
        
        logger.info("Resuming operations after emergency stop")
        
        # Clear emergency stop
        self.emergency_stop_active = False
        self.blocked_operations.clear()
        
        # Log resume
        resume_log = {
            "timestamp": datetime.now().isoformat(),
            "admin_token": admin_token[:8] + "...",  # Partial token for audit
            "pre_resume_check": self.check_system_safety()
        }
        
        log_file = os.path.join(self.log_dir, f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w') as f:
            json.dump(resume_log, f, indent=2)
        
        return True
    
    def is_operation_allowed(self, operation_type: str) -> bool:
        """Check if an operation is allowed given current safety state"""
        if self.emergency_stop_active:
            return False
        
        if operation_type in self.blocked_operations:
            return False
        
        # Check current threat level
        threat_level, _ = self.check_system_safety()
        
        # Block high-risk operations at high threat levels
        if threat_level.value >= ThreatLevel.DANGER.value:
            high_risk_ops = {"system_modification", "resource_allocation", "auto_acceptance"}
            if operation_type in high_risk_ops:
                return False
        
        return True
    
    def _record_incident(self, violation_type: SafetyViolationType, 
                        threat_level: ThreatLevel, affected_agents: List[str],
                        description: str, auto_resolved: bool = False):
        """Record a safety incident"""
        import uuid
        
        incident = SafetyIncident(
            incident_id=f"INC-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(),
            violation_type=violation_type,
            threat_level=threat_level,
            affected_agents=affected_agents,
            description=description,
            metrics=self._gather_incident_metrics(),
            auto_resolved=auto_resolved,
            resolution=None
        )
        
        self.incidents.append(incident)
        
        # Log incident
        incident_file = os.path.join(self.log_dir, "incidents.jsonl")
        with open(incident_file, 'a') as f:
            f.write(json.dumps(asdict(incident), default=str) + "\n")
    
    def _evaluate_emergency_stop(self, threat_level: ThreatLevel, issues: List[str]):
        """Evaluate whether emergency stop should be triggered"""
        # Count critical issues
        critical_count = sum(1 for issue in issues if "critical" in issue.lower())
        danger_count = sum(1 for issue in issues if any(word in issue.lower() 
                          for word in ["danger", "cascade", "breach"]))
        
        # Trigger conditions
        if threat_level == ThreatLevel.CRITICAL:
            self.trigger_emergency_stop("Critical threat level reached")
        elif critical_count >= 2:
            self.trigger_emergency_stop(f"Multiple critical issues: {critical_count}")
        elif danger_count >= 3:
            self.trigger_emergency_stop(f"Multiple danger conditions: {danger_count}")
        elif threat_level == ThreatLevel.DANGER and len(issues) > 5:
            self.trigger_emergency_stop(f"Danger level with {len(issues)} issues")
    
    def _stop_agent(self, agent_id: str):
        """Stop a specific agent"""
        logger.warning(f"Stopping agent: {agent_id}")
        
        if agent_id in self.agent_states and 'pid' in self.agent_states[agent_id]:
            pid = self.agent_states[agent_id]['pid']
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to agent {agent_id} (PID: {pid})")
            except Exception as e:
                logger.error(f"Failed to stop agent {agent_id}: {e}")
    
    def _stop_all_agents(self):
        """Stop all agents"""
        logger.warning("Stopping all agents")
        
        for agent_id in self.agent_states:
            self._stop_agent(agent_id)
    
    def _capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state for emergency log"""
        return {
            "active_agents": list(self.agent_states.keys()),
            "threat_level": self.check_system_safety()[0].name,
            "recent_incidents": len([i for i in self.incidents 
                                   if i.timestamp > datetime.now() - timedelta(hours=1)]),
            "resource_usage": {
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent
            }
        }
    
    def _gather_incident_metrics(self) -> Dict[str, float]:
        """Gather metrics for incident recording"""
        return {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "active_agents": len(self.agent_states),
            "incident_count_1h": len([i for i in self.incidents 
                                    if i.timestamp > datetime.now() - timedelta(hours=1)])
        }
    
    def _verify_admin_token(self, token: str) -> bool:
        """Verify admin token for emergency operations"""
        # Implement proper authentication
        # For now, using simple check
        return len(token) > 20 and token.startswith("ADMIN_")
    
    def _start_monitoring_threads(self):
        """Start background monitoring threads"""
        def safety_monitor_loop():
            while self.monitoring_active:
                try:
                    threat_level, issues = self.check_system_safety()
                    
                    if issues:
                        logger.info(f"Safety check - Threat: {threat_level.name}, Issues: {len(issues)}")
                    
                    time.sleep(30)  # Check every 30 seconds
                
                except Exception as e:
                    logger.error(f"Safety monitor error: {e}")
                    time.sleep(60)
        
        def performance_tracker_loop():
            while self.monitoring_active:
                try:
                    # Track performance metrics
                    self._update_performance_metrics()
                    time.sleep(10)  # Update every 10 seconds
                
                except Exception as e:
                    logger.error(f"Performance tracker error: {e}")
                    time.sleep(30)
        
        # Start threads
        safety_thread = threading.Thread(target=safety_monitor_loop, daemon=True)
        safety_thread.start()
        
        perf_thread = threading.Thread(target=performance_tracker_loop, daemon=True)
        perf_thread.start()
    
    def _update_performance_metrics(self):
        """Update performance tracking metrics"""
        # This would integrate with various monitoring systems
        # Placeholder for now
        pass
    
    def get_safety_report(self) -> Dict[str, Any]:
        """Generate comprehensive safety report"""
        current_threat, current_issues = self.check_system_safety()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "emergency_stop_active": self.emergency_stop_active,
            "current_threat_level": current_threat.name,
            "current_issues": current_issues,
            "blocked_operations": list(self.blocked_operations),
            "active_agents": len(self.agent_states),
            "recent_incidents": [
                {
                    "incident_id": i.incident_id,
                    "type": i.violation_type.value,
                    "threat_level": i.threat_level.name,
                    "timestamp": i.timestamp.isoformat(),
                    "affected_agents": i.affected_agents
                }
                for i in self.incidents[-10:]  # Last 10 incidents
            ],
            "system_resources": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
        }


# Example usage
if __name__ == "__main__":
    monitor = JarvisSafetyMonitor()
    
    # Check system safety
    threat_level, issues = monitor.check_system_safety()
    print(f"Current threat level: {threat_level.name}")
    print(f"Issues found: {len(issues)}")
    
    # Check if operation allowed
    if monitor.is_operation_allowed("auto_acceptance"):
        print("Auto-acceptance is allowed")
    else:
        print("Auto-acceptance is blocked")
    
    # Get safety report
    report = monitor.get_safety_report()
    print(f"\nSafety Report:")
    print(f"Active agents: {report['active_agents']}")
    print(f"Emergency stop: {report['emergency_stop_active']}")
    print(f"Recent incidents: {len(report['recent_incidents'])}")