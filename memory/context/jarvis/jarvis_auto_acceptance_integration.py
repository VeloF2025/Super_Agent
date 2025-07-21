#!/usr/bin/env python3
"""
Integration module to connect auto-acceptance system with orchestrator
Provides seamless integration without modifying existing code
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps

from jarvis_auto_acceptance import JarvisAutoAcceptance, RequestType, DecisionOutcome
from jarvis_decision_logger import JarvisDecisionLogger, DecisionType, DecisionImpact
from jarvis_safety_monitor import JarvisSafetyMonitor

logger = logging.getLogger(__name__)


class JarvisAutoAcceptanceIntegration:
    """Integrates auto-acceptance capabilities into Jarvis orchestrator"""
    
    def __init__(self, orchestrator_instance: Any = None):
        self.orchestrator = orchestrator_instance
        self.auto_acceptance = JarvisAutoAcceptance()
        self.decision_logger = JarvisDecisionLogger()
        self.safety_monitor = JarvisSafetyMonitor()
        
        # Link components
        self.auto_acceptance.decision_logger = self.decision_logger
        self.safety_monitor.decision_logger = self.decision_logger
        
        # Setup interceptors if orchestrator provided
        if orchestrator_instance:
            self._setup_interceptors()
        
        logger.info("Jarvis Auto-Acceptance System initialized")
    
    def _setup_interceptors(self):
        """Setup method interceptors for auto-acceptance"""
        # Common orchestrator methods to intercept
        methods_to_intercept = [
            ('process_request', self._intercept_request),
            ('execute_task', self._intercept_task),
            ('handle_message', self._intercept_message),
            ('assign_agent', self._intercept_assignment),
            ('access_resource', self._intercept_resource)
        ]
        
        for method_name, interceptor in methods_to_intercept:
            if hasattr(self.orchestrator, method_name):
                self._wrap_method(method_name, interceptor)
    
    def _wrap_method(self, method_name: str, interceptor: Callable):
        """Wrap orchestrator method with auto-acceptance logic"""
        original_method = getattr(self.orchestrator, method_name)
        
        @wraps(original_method)
        def wrapped(*args, **kwargs):
            # Check if operation is allowed
            if not self.safety_monitor.is_operation_allowed(method_name):
                logger.warning(f"Operation {method_name} blocked by safety monitor")
                raise PermissionError(f"Operation {method_name} is currently blocked")
            
            # Intercept for auto-acceptance
            should_proceed, decision_context = interceptor(method_name, args, kwargs)
            
            if should_proceed:
                try:
                    # Execute original method
                    result = original_method(*args, **kwargs)
                    
                    # Record success
                    if decision_context:
                        self._record_success(decision_context, result)
                    
                    return result
                
                except Exception as e:
                    # Record failure
                    if decision_context:
                        self._record_failure(decision_context, str(e))
                    raise
            else:
                raise PermissionError(f"Operation {method_name} requires manual approval")
        
        setattr(self.orchestrator, method_name, wrapped)
    
    def _intercept_request(self, method_name: str, args: tuple, kwargs: dict) -> tuple:
        """Intercept general request processing"""
        request = args[0] if args else kwargs.get('request', {})
        
        # Map to request type
        request_type = self._map_request_type(request)
        if not request_type:
            return True, None  # Unknown type, allow but don't track
        
        # Evaluate for auto-acceptance
        approved, decision = self.auto_acceptance.evaluate_request(
            request_type=request_type,
            request_details=request
        )
        
        # Log decision
        decision_id = self.decision_logger.log_decision(
            agent_id=getattr(self.orchestrator, 'agent_id', 'orchestrator'),
            decision_type=DecisionType.AUTO_ACCEPTANCE,
            description=f"Auto-acceptance evaluation for {request_type.value}",
            context=request,
            alternatives=[
                {"choice": "auto_accept", "confidence": decision.confidence_score},
                {"choice": "manual_review", "confidence": 1 - decision.confidence_score}
            ],
            chosen={"choice": "auto_accept" if approved else "manual_review"},
            reasoning=" | ".join(decision.reasoning),
            impact=DecisionImpact.LOW if approved else DecisionImpact.MEDIUM,
            reversible=True
        )
        
        decision_context = {
            'decision_id': decision.decision_id,
            'logger_id': decision_id,
            'request_type': request_type
        }
        
        return approved, decision_context
    
    def _intercept_task(self, method_name: str, args: tuple, kwargs: dict) -> tuple:
        """Intercept task execution"""
        task = args[0] if args else kwargs.get('task', {})
        
        # Check task risk
        if self._is_high_risk_task(task):
            return False, None  # Require manual approval
        
        # Standard task evaluation
        return self._intercept_request(method_name, args, kwargs)
    
    def _intercept_message(self, method_name: str, args: tuple, kwargs: dict) -> tuple:
        """Intercept message handling"""
        # Agent communication is generally low risk
        message = args[0] if args else kwargs.get('message', {})
        
        request_details = {
            'message_type': message.get('type'),
            'from_agent': message.get('from'),
            'to_agent': message.get('to'),
            'content_type': type(message.get('content')).__name__
        }
        
        approved, decision = self.auto_acceptance.evaluate_request(
            request_type=RequestType.AGENT_COMMUNICATION,
            request_details=request_details
        )
        
        return approved, {'decision_id': decision.decision_id}
    
    def _intercept_assignment(self, method_name: str, args: tuple, kwargs: dict) -> tuple:
        """Intercept agent assignment"""
        # Agent assignments need careful evaluation
        assignment = args[0] if args else kwargs.get('assignment', {})
        
        request_details = {
            'task_type': assignment.get('task_type'),
            'agent_id': assignment.get('agent_id'),
            'priority': assignment.get('priority'),
            'estimated_duration': assignment.get('duration')
        }
        
        approved, decision = self.auto_acceptance.evaluate_request(
            request_type=RequestType.RESOURCE_ALLOCATION,
            request_details=request_details
        )
        
        return approved, {'decision_id': decision.decision_id}
    
    def _intercept_resource(self, method_name: str, args: tuple, kwargs: dict) -> tuple:
        """Intercept resource access"""
        resource = args[0] if args else kwargs.get('resource', {})
        
        # Map resource access to appropriate request type
        if 'file' in str(resource).lower():
            if kwargs.get('mode') == 'r':
                request_type = RequestType.FILE_READ
            elif kwargs.get('mode') == 'w':
                request_type = RequestType.FILE_WRITE
            elif kwargs.get('mode') == 'd':
                request_type = RequestType.FILE_DELETE
            else:
                request_type = RequestType.FILE_READ
        else:
            return True, None  # Unknown resource type
        
        request_details = {
            'resource': str(resource),
            'mode': kwargs.get('mode', 'r'),
            'purpose': kwargs.get('purpose', 'unknown')
        }
        
        approved, decision = self.auto_acceptance.evaluate_request(
            request_type=request_type,
            request_details=request_details
        )
        
        return approved, {'decision_id': decision.decision_id}
    
    def _map_request_type(self, request: Dict[str, Any]) -> Optional[RequestType]:
        """Map generic request to specific request type"""
        request_str = json.dumps(request).lower()
        
        # Pattern matching for request types
        patterns = {
            RequestType.FILE_READ: ['read', 'open', 'load', 'fetch'],
            RequestType.FILE_WRITE: ['write', 'save', 'update', 'modify'],
            RequestType.FILE_DELETE: ['delete', 'remove', 'unlink'],
            RequestType.CODE_ANALYSIS: ['analyze', 'inspect', 'review'],
            RequestType.LOG_ANALYSIS: ['log', 'trace', 'debug'],
            RequestType.SERVICE_START: ['start', 'launch', 'initialize'],
            RequestType.SERVICE_STOP: ['stop', 'halt', 'terminate'],
            RequestType.CONFIG_UPDATE: ['config', 'setting', 'preference'],
            RequestType.HEALTH_CHECK: ['health', 'status', 'ping'],
            RequestType.REPORT_GENERATION: ['report', 'summary', 'export'],
            RequestType.BACKUP_CREATE: ['backup', 'snapshot', 'archive'],
            RequestType.CACHE_CLEAR: ['cache', 'clear', 'flush'],
            RequestType.DATA_PROCESSING: ['process', 'transform', 'compute']
        }
        
        for request_type, keywords in patterns.items():
            if any(keyword in request_str for keyword in keywords):
                return request_type
        
        return None
    
    def _is_high_risk_task(self, task: Dict[str, Any]) -> bool:
        """Check if task is high risk requiring manual approval"""
        high_risk_indicators = [
            'production', 'delete', 'security', 'credential',
            'password', 'token', 'key', 'critical', 'emergency'
        ]
        
        task_str = json.dumps(task).lower()
        return any(indicator in task_str for indicator in high_risk_indicators)
    
    def _record_success(self, decision_context: Dict[str, Any], result: Any):
        """Record successful operation"""
        if 'decision_id' in decision_context:
            self.auto_acceptance.record_outcome(
                decision_context['decision_id'],
                DecisionOutcome.SUCCESS
            )
        
        if 'logger_id' in decision_context:
            self.decision_logger.update_outcome(
                decision_context['logger_id'],
                f"Operation completed successfully",
                DecisionImpact.LOW,
                metrics={
                    'execution_time_ms': 0,  # Would calculate actual time
                    'error_count': 0
                }
            )
    
    def _record_failure(self, decision_context: Dict[str, Any], error: str):
        """Record failed operation"""
        if 'decision_id' in decision_context:
            self.auto_acceptance.record_outcome(
                decision_context['decision_id'],
                DecisionOutcome.FAILURE,
                error_details=error
            )
        
        if 'logger_id' in decision_context:
            self.decision_logger.update_outcome(
                decision_context['logger_id'],
                f"Operation failed: {error}",
                DecisionImpact.HIGH,
                metrics={
                    'error_count': 1,
                    'error_type': type(error).__name__
                }
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of auto-acceptance system"""
        acceptance_report = self.auto_acceptance.get_decision_report(24)
        safety_report = self.safety_monitor.get_safety_report()
        decision_report = self.decision_logger.generate_decision_report(24)
        
        return {
            "auto_acceptance": {
                "enabled": not self.safety_monitor.emergency_stop_active,
                "total_evaluated": acceptance_report['total_decisions'],
                "auto_accepted": acceptance_report['auto_accepted'],
                "success_rate": acceptance_report['success_rate'],
                "confidence_threshold": self.auto_acceptance.confidence_threshold
            },
            "safety": {
                "threat_level": safety_report['current_threat_level'],
                "emergency_stop": safety_report['emergency_stop_active'],
                "active_issues": len(safety_report['current_issues']),
                "blocked_operations": safety_report['blocked_operations']
            },
            "decisions": {
                "total_logged": decision_report['total_decisions'],
                "critical_decisions": decision_report['critical_decisions'],
                "rollback_rate": decision_report['rollback_rate']
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def manual_override(self, admin_token: str, operation: str) -> bool:
        """Allow manual override for specific operation"""
        if self.safety_monitor._verify_admin_token(admin_token):
            # Temporarily allow operation
            logger.warning(f"Manual override activated for {operation}")
            return True
        return False
    
    def adjust_confidence_threshold(self, new_threshold: float):
        """Adjust confidence threshold for auto-acceptance"""
        if 0.5 <= new_threshold <= 0.95:
            self.auto_acceptance.confidence_threshold = new_threshold
            logger.info(f"Confidence threshold adjusted to {new_threshold}")
        else:
            raise ValueError("Threshold must be between 0.5 and 0.95")


# Standalone functions for easy integration

def enable_auto_acceptance(orchestrator: Any) -> JarvisAutoAcceptanceIntegration:
    """Enable auto-acceptance for an orchestrator instance"""
    integration = JarvisAutoAcceptanceIntegration(orchestrator)
    logger.info("Auto-acceptance enabled for orchestrator")
    return integration


def check_auto_acceptance_status() -> Dict[str, Any]:
    """Check status without orchestrator instance"""
    integration = JarvisAutoAcceptanceIntegration()
    return integration.get_status()


# Example usage patterns
"""
# Method 1: Enable for existing orchestrator
orchestrator = YourOrchestrator()
auto_accept = enable_auto_acceptance(orchestrator)

# Method 2: Standalone usage
integration = JarvisAutoAcceptanceIntegration()

# Evaluate specific request
approved, decision = integration.auto_acceptance.evaluate_request(
    RequestType.FILE_READ,
    {"file_path": "/logs/app.log"}
)

# Check system status
status = integration.get_status()
print(f"Auto-acceptance enabled: {status['auto_acceptance']['enabled']}")
print(f"Current threat level: {status['safety']['threat_level']}")

# Manual override if needed
if integration.manual_override("ADMIN_TOKEN_HERE", "critical_operation"):
    # Perform critical operation
    pass
"""

if __name__ == "__main__":
    # Test integration
    integration = JarvisAutoAcceptanceIntegration()
    
    # Simulate some requests
    test_requests = [
        (RequestType.FILE_READ, {"file_path": "/logs/test.log"}),
        (RequestType.HEALTH_CHECK, {"service": "agent-001"}),
        (RequestType.CACHE_CLEAR, {"cache_type": "temporary"})
    ]
    
    for req_type, details in test_requests:
        approved, decision = integration.auto_acceptance.evaluate_request(req_type, details)
        print(f"{req_type.value}: {'Approved' if approved else 'Manual Review Required'}")
        
        if approved:
            # Simulate execution
            integration.auto_acceptance.record_outcome(
                decision.decision_id,
                DecisionOutcome.SUCCESS
            )
    
    # Get status
    status = integration.get_status()
    print(f"\nSystem Status:")
    print(f"Auto-accepted: {status['auto_acceptance']['auto_accepted']}/{status['auto_acceptance']['total_evaluated']}")
    print(f"Safety Level: {status['safety']['threat_level']}")