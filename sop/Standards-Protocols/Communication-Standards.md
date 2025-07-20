# Communication Standards & Protocols

## Overview

This document establishes the mandatory communication standards for all agents in the Super Agent Team. These protocols ensure efficient coordination, maintain quality standards, and provide clear audit trails.

## Message Format Standards

### Standard Message Structure

```json
{
  "message_id": "uuid-v4",
  "timestamp": "2025-07-20T10:30:00.000Z",
  "from": "agent_id",
  "to": "target_agent_or_team",
  "message_type": "task|result|error|status|escalation|info",
  "priority": "critical|high|medium|low",
  "security_level": "public|internal|confidential|restricted",
  "thread_id": "uuid-v4",
  "parent_message_id": "uuid-v4",
  "payload": {
    "subject": "brief_description",
    "content": "detailed_message_content",
    "attachments": [],
    "context": {},
    "evidence": [],
    "validation_required": true,
    "confidence_score": 0.95,
    "estimated_effort": "1h",
    "deadline": "2025-07-20T18:00:00.000Z"
  },
  "routing": {
    "retry_count": 0,
    "max_retries": 3,
    "timeout_ms": 30000,
    "fallback_agents": ["backup_agent_id"],
    "notification_required": false
  },
  "metadata": {
    "source_task_id": "uuid-v4",
    "business_context": "project_name",
    "cost_center": "development",
    "compliance_tags": ["gdpr", "security_review"]
  }
}
```

### Message Types & Requirements

#### **Task Assignment (task)**
```json
{
  "message_type": "task",
  "priority": "high|medium|low",
  "payload": {
    "task_id": "uuid-v4",
    "task_title": "Clear, descriptive title",
    "task_description": "Detailed requirements and context",
    "acceptance_criteria": ["criterion_1", "criterion_2"],
    "dependencies": ["task_id_1", "task_id_2"],
    "estimated_effort": "4h",
    "deadline": "ISO-8601 timestamp",
    "resources": ["links", "files", "documentation"],
    "success_metrics": "How to measure completion"
  },
  "validation_required": true
}
```

#### **Result Delivery (result)**
```json
{
  "message_type": "result",
  "payload": {
    "task_id": "uuid-v4",
    "status": "completed|partial|failed",
    "deliverables": ["file_paths", "urls", "outputs"],
    "summary": "Brief description of what was accomplished",
    "evidence": ["supporting_documentation", "test_results"],
    "quality_metrics": {
      "validation_score": 0.95,
      "confidence_level": "high",
      "review_status": "passed"
    },
    "next_steps": "What should happen next",
    "lessons_learned": "Insights for future tasks"
  }
}
```

#### **Error Report (error)**
```json
{
  "message_type": "error",
  "priority": "critical|high",
  "payload": {
    "error_type": "technical|process|communication|resource",
    "error_description": "Clear description of what went wrong",
    "affected_tasks": ["task_id_1", "task_id_2"],
    "impact_assessment": "Description of business/technical impact",
    "immediate_actions": "What was done to contain the issue",
    "recommended_resolution": "Suggested fix or next steps",
    "escalation_required": true
  }
}
```

#### **Status Update (status)**
```json
{
  "message_type": "status",
  "payload": {
    "current_tasks": [
      {
        "task_id": "uuid-v4",
        "progress_percentage": 75,
        "status": "in_progress|blocked|review",
        "estimated_completion": "ISO-8601 timestamp",
        "blockers": ["Description of any impediments"]
      }
    ],
    "capacity_status": "available|busy|overloaded",
    "next_availability": "ISO-8601 timestamp",
    "alerts": ["Any issues or concerns to report"]
  }
}
```

## Communication Channels

### File-Based Messaging (Primary)

#### **Directory Structure**
```
communication/
├── queue/                   # Pending messages by priority
│   ├── critical/           # Immediate attention required
│   ├── high/               # Process within 1 hour
│   ├── medium/             # Process within 4 hours
│   └── low/                # Process within 24 hours
├── processing/             # Currently being handled
├── completed/              # Successfully processed
├── failed/                 # Processing failures
├── archive/                # Historical messages
│   ├── daily/
│   ├── weekly/
│   └── monthly/
└── broadcasts/             # Team-wide announcements
```

#### **File Naming Convention**
```
{timestamp}_{priority}_{from_agent}_{to_agent}_{message_type}_{uuid}.json

Example:
20250720_103000_high_OA001_DEV001_task_a1b2c3d4.json
```

#### **Atomic Operations Protocol**
```python
def send_message(message):
    # 1. Create temporary file
    temp_file = f"{message.id}.tmp"
    
    # 2. Write message content
    with open(temp_file, 'w') as f:
        json.dump(message, f, indent=2)
    
    # 3. Atomic rename to final location
    final_file = f"queue/{message.priority}/{generate_filename(message)}"
    os.rename(temp_file, final_file)
    
    # 4. Optional: Create notification
    if message.routing.notification_required:
        create_notification(message)
```

### Event-Driven Coordination (Secondary)

#### **Event Types**
```json
{
  "system_events": [
    "agent_started",
    "agent_stopped", 
    "task_assigned",
    "task_completed",
    "error_occurred",
    "escalation_triggered"
  ],
  "business_events": [
    "milestone_reached",
    "deadline_approaching",
    "quality_threshold_exceeded",
    "resource_constraint_detected"
  ]
}
```

#### **Event Publishing**
```python
def publish_event(event_type, data, source_agent):
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "source": source_agent,
        "data": data,
        "version": "1.0"
    }
    
    # Write to event stream
    with open(f"events/{event_type}_{event.event_id}.json", 'w') as f:
        json.dump(event, f)
    
    # Notify subscribers
    notify_subscribers(event_type, event)
```

## Response Time Standards

### Priority-Based Response Times

| Priority | Acknowledgment | Response | Resolution |
|----------|---------------|----------|------------|
| CRITICAL | Immediate | 5 minutes | 1 hour |
| HIGH | 15 minutes | 30 minutes | 4 hours |
| MEDIUM | 1 hour | 2 hours | 24 hours |
| LOW | 4 hours | 24 hours | 72 hours |

### Response Requirements

#### **Acknowledgment**
All agents must acknowledge receipt of messages:
```json
{
  "message_type": "acknowledgment",
  "payload": {
    "original_message_id": "uuid-v4",
    "received_timestamp": "ISO-8601",
    "estimated_response_time": "30m",
    "current_workload_impact": "none|minor|moderate|significant"
  }
}
```

#### **Status Updates**
For tasks taking longer than estimated:
```json
{
  "message_type": "status",
  "payload": {
    "task_id": "uuid-v4",
    "progress_update": "Detailed description of current progress",
    "revised_estimate": "New completion estimate",
    "reason_for_delay": "Explanation if behind schedule",
    "assistance_needed": "Any help required to complete"
  }
}
```

## Quality Standards

### Evidence Requirements

All technical claims and recommendations must include:

#### **Technical Evidence**
```json
{
  "evidence_type": "technical",
  "sources": [
    {
      "type": "documentation",
      "url": "https://docs.example.com/api",
      "relevant_section": "Section 4.2 - Authentication"
    },
    {
      "type": "code_example", 
      "file_path": "/path/to/example.js",
      "line_numbers": "15-25"
    },
    {
      "type": "test_result",
      "test_suite": "integration_tests",
      "result": "passed",
      "confidence": 0.95
    }
  ]
}
```

#### **Performance Evidence**
```json
{
  "evidence_type": "performance",
  "metrics": {
    "response_time": "150ms",
    "throughput": "1000 req/sec",
    "error_rate": "0.1%",
    "resource_usage": "40% CPU, 2GB RAM"
  },
  "benchmark_comparison": {
    "baseline": "200ms response time",
    "improvement": "25% faster"
  },
  "measurement_method": "Load testing with 100 concurrent users"
}
```

### Validation Framework

#### **Message Validation**
```python
def validate_message(message):
    validation_results = []
    
    # 1. Structure validation
    if not validate_message_structure(message):
        validation_results.append("Invalid message structure")
    
    # 2. Content validation
    if not validate_content_quality(message):
        validation_results.append("Content quality issues")
    
    # 3. Evidence validation
    if message.validation_required and not validate_evidence(message):
        validation_results.append("Insufficient evidence")
    
    # 4. Security validation
    if not validate_security_requirements(message):
        validation_results.append("Security validation failed")
    
    return ValidationResult(
        passed=len(validation_results) == 0,
        issues=validation_results
    )
```

## Escalation Protocols

### Escalation Triggers

#### **Automatic Escalation**
- Response time exceeded by >100%
- Critical errors affecting multiple agents
- Security violations or concerns
- Resource constraints preventing task completion
- Conflicts between agents requiring mediation

#### **Manual Escalation**
- Complex decisions requiring higher authority
- Scope changes or requirement clarifications
- Quality issues requiring management attention
- Customer or stakeholder concerns

### Escalation Process

#### **Step 1: Internal Escalation**
```json
{
  "message_type": "escalation",
  "priority": "high",
  "payload": {
    "escalation_type": "internal",
    "issue_description": "Clear description of the problem",
    "attempted_resolutions": ["What has been tried"],
    "business_impact": "How this affects project goals",
    "recommended_action": "Suggested next steps",
    "timeline_urgency": "How quickly this needs resolution"
  }
}
```

#### **Step 2: Human Escalation**
```json
{
  "message_type": "escalation",
  "priority": "critical",
  "payload": {
    "escalation_type": "human_required",
    "severity": "critical|high|medium",
    "issue_summary": "Executive summary of the issue",
    "context_package": "Complete situation analysis",
    "decision_required": "What decision needs to be made",
    "options_analysis": ["Option 1: pros/cons", "Option 2: pros/cons"],
    "recommendation": "Preferred course of action",
    "timeline_impact": "Effect on project timeline"
  }
}
```

## Security Protocols

### Information Classification

#### **Security Levels**
- **PUBLIC**: No restrictions on access or sharing
- **INTERNAL**: Restricted to team members only
- **CONFIDENTIAL**: Restricted access, audit trail required
- **RESTRICTED**: Highest security, minimal access, full logging

#### **Handling Requirements**
```json
{
  "security_requirements": {
    "public": {
      "access_control": "none",
      "audit_logging": false,
      "encryption": "optional"
    },
    "internal": {
      "access_control": "team_members_only",
      "audit_logging": true,
      "encryption": "in_transit"
    },
    "confidential": {
      "access_control": "role_based",
      "audit_logging": true,
      "encryption": "end_to_end"
    },
    "restricted": {
      "access_control": "explicit_authorization",
      "audit_logging": "full_trail",
      "encryption": "military_grade"
    }
  }
}
```

### Access Control

#### **Agent Permissions**
```json
{
  "agent_permissions": {
    "OA-001": {
      "read": ["all"],
      "write": ["all"],
      "approve": ["all"],
      "escalate": ["human_required"]
    },
    "team_leads": {
      "read": ["team_specific", "shared"],
      "write": ["team_specific"],
      "approve": ["team_tasks"],
      "escalate": ["to_OA"]
    },
    "specialists": {
      "read": ["assigned_tasks", "public"],
      "write": ["task_outputs"],
      "approve": ["own_work"],
      "escalate": ["to_team_lead"]
    }
  }
}
```

## Monitoring & Compliance

### Audit Requirements

#### **Message Logging**
```json
{
  "audit_log_entry": {
    "timestamp": "ISO-8601",
    "message_id": "uuid-v4",
    "from_agent": "agent_id",
    "to_agent": "agent_id",
    "action": "sent|received|processed|failed",
    "security_level": "public|internal|confidential|restricted",
    "business_context": "project_name",
    "compliance_flags": ["gdpr", "security_review"]
  }
}
```

#### **Performance Tracking**
```json
{
  "performance_metrics": {
    "message_volume": "messages_per_hour",
    "response_times": "average_response_time_by_priority",
    "error_rates": "percentage_failed_messages",
    "escalation_frequency": "escalations_per_day",
    "quality_scores": "average_validation_score"
  }
}
```

### Compliance Checks

#### **Daily Compliance Review**
- All critical messages acknowledged within required timeframes
- Evidence requirements met for technical deliverables
- Security protocols followed for sensitive information
- Escalation procedures executed correctly
- Audit trails complete and accessible

#### **Weekly Quality Assessment**
- Communication effectiveness analysis
- Response time performance review
- Error pattern identification
- Process improvement recommendations
- Training needs assessment

---

**Implementation Note**: All agents must implement these communication standards before becoming operational. Regular audits will ensure compliance and identify opportunities for improvement.