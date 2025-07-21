# CLAUDE.md - Jarvis Super Agent System

This file provides guidance to Claude Code when working with the Jarvis Super Agent System.

## System Overview

The Jarvis Super Agent System is a sophisticated multi-agent orchestration platform designed for enterprise-scale AI operations. It features robust context persistence, crash recovery, and real-time monitoring capabilities.

## Context Persistence Protocol

### Overview
Jarvis implements a zero-context-loss architecture with automatic checkpointing every 30 seconds and comprehensive crash recovery. All orchestration decisions, agent states, and task progress are persisted to ensure perfect continuity across sessions.

### Memory Hierarchy
```
1. Active Memory (In-Process)
   - Current task and workflow state
   - Recent conversation history (100 messages)
   - Decision log (50 entries)
   - Real-time agent states

2. Persistent Storage (SQLite + Pickle)
   - Context snapshots with deduplication
   - Task progress tracking
   - Agent coordination logs
   - Decision audit trail

3. Emergency Fallback (JSON)
   - Automatic failover when database fails
   - Human-readable format for manual recovery
```

### Recovery Commands

#### Check Context Status
```python
from memory.context.jarvis.jarvis_context_manager import JarvisContextManager
cm = JarvisContextManager()
status = cm.get_context_status()
```

#### Manual Checkpoint
```python
cm.mark_recovery_point("Critical operation completed")
```

#### Trigger Recovery
```python
report = cm.recover_from_crash()
```

### Critical Decision Logging

All orchestration decisions must be logged with proper context:
```python
context_manager.log_decision(
    decision_type="task_assignment",  # or "agent_selection", "error_handling", etc.
    context="Current system state and constraints",
    decision="Assign task X to agent Y",
    reasoning="Agent Y has required capabilities and lowest workload",
    outcome="pending"  # Updated after execution
)
```

### Integration Pattern

For new orchestrator implementations:
```python
from memory.context.jarvis.jarvis_orchestrator_integration import integrate_context_manager

@integrate_context_manager
class YourOrchestrator:
    def assign_task(self, task):
        # Your implementation
        pass
```

For existing orchestrators:
```python
from memory.context.jarvis.jarvis_orchestrator_integration import JarvisOrchestratorWithContext

orchestrator = YourExistingOrchestrator()
jarvis = JarvisOrchestratorWithContext(orchestrator)
```

## File Structure

```
memory/context/jarvis/
├── jarvis_context.db              # Primary SQLite database
├── checkpoints/                   # Recovery checkpoint files
│   └── recovery_*.pkl            # Binary snapshots
├── emergency_*.json              # Emergency JSON backups
├── recovery_report_*.json        # Crash recovery reports
└── CRASH_DETECTED                # Crash marker (temporary)
```

## Monitoring Integration

The context persistence system integrates with the agent dashboard through REST APIs:

- `/api/jarvis/context/status` - Real-time context status
- `/api/jarvis/context/agent-states` - Current agent health
- `/api/jarvis/context/task-progress` - Task completion tracking
- `/api/jarvis/context/recovery-reports` - Historical recovery data
- `/api/jarvis/context/metrics` - Persistence performance metrics

## Development Guidelines

### When to Create Checkpoints
1. Before critical operations
2. After completing major workflow phases
3. When switching between tasks
4. Before risky operations that might fail

### Context Size Management
- Conversation history: Limited to 100 messages
- Decision log: Limited to 50 entries  
- Old data automatically cleaned after 7 days
- Recovery points preserved indefinitely

### Error Handling
```python
try:
    # Critical operation
    context_manager.mark_recovery_point("Before critical op")
    result = perform_critical_operation()
    context_manager.update_task_progress(task_id, {"percentage": 100})
except Exception as e:
    context_manager.active_context['error_recovery'] = {
        'error': str(e),
        'recovery_attempted': True
    }
    raise
```

## Testing Recovery

To test crash recovery:
1. Create a `CRASH_DETECTED` file in the context directory
2. Restart the orchestrator
3. Verify recovery report is generated
4. Check that incomplete tasks resume

## Performance Considerations

- Checkpoints are non-blocking (separate thread)
- Database writes use WAL mode for concurrency
- Context deduplication prevents redundant saves
- Average checkpoint time: <100ms
- Database growth: ~10MB/day typical usage

## Security Notes

- All context data is stored locally
- No sensitive credentials in context
- Audit trail for compliance
- Atomic file operations prevent corruption

This context persistence system ensures Jarvis maintains perfect continuity even through unexpected shutdowns, making it suitable for mission-critical enterprise deployments.