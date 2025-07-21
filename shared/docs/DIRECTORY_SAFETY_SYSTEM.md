# Directory Safety System for Multi-Agent Environment

## Overview

The Directory Safety System prevents agents from accidentally working in wrong directories or making unauthorized changes. It ensures agents stay within their designated working areas and request confirmation for sensitive operations.

## Components

### 1. Directory Context Safety (`directory_context_safety.py`)
- Validates agent operations across directory boundaries
- Tracks agent working contexts
- Provides risk assessment for operations
- Maintains history of known safe directories per agent

### 2. Agent Directory Configuration (`agent_directory_config.py`)
- Defines allowed/restricted paths per agent type
- Manages confirmation requirements
- Handles read-only directory protection
- Provides safe fallback directories

### 3. Directory-Aware Agent Base (`directory_aware_agent.py`)
- Base class for all agents with built-in safety
- Decorators for automatic permission checking
- Safe file operation methods
- Directory change tracking and history

### 4. Auto-Acceptance Integration
- Directory checks integrated into auto-acceptance workflow
- High-risk directory operations automatically blocked
- Cross-boundary operations require confirmation

## Configuration

Each agent type has specific permissions defined in `agent_directory_rules.json`:

```json
{
  "agent-orchestrator": {
    "allowed_paths": [...],
    "restricted_paths": [...],
    "require_confirmation": [...],
    "read_only_paths": [...]
  }
}
```

## Usage

### For Agent Developers

```python
from shared.tools.directory_aware_agent import DirectoryAwareAgent

class MyAgent(DirectoryAwareAgent):
    def __init__(self):
        super().__init__("my-agent-001", "MyAgent")
    
    def process_file(self, file_path):
        # Automatic safety checks
        content = self.read_file(file_path)
        # Process content...
        self.write_file(output_path, result)
```

### Risk Levels

- **LOW**: Operations within agent's designated directories
- **MEDIUM**: Cross-directory operations, unknown directories
- **HIGH**: System directories, sensitive paths, configuration files

### Confirmation Requirements

Operations requiring confirmation:
1. Writing to configuration directories
2. Deleting files outside designated areas
3. Modifying system-critical paths
4. First-time access to new directories

## Safety Features

1. **Automatic Blocking**
   - Windows system directories
   - Program Files
   - Git internals
   - Node modules

2. **Read-Only Protection**
   - Prevents modification of critical files
   - Protects configuration integrity
   - Safeguards version control

3. **Context Tracking**
   - Remembers safe directories per agent
   - Builds trust over time
   - Reduces confirmation prompts

4. **Emergency Stop**
   - Triggered by repeated failures
   - Blocks all auto-acceptance
   - Requires manual intervention

## Best Practices

1. Always use DirectoryAwareAgent as base class
2. Use provided safe methods for file operations
3. Check permissions before batch operations
4. Handle PermissionError gracefully
5. Log directory changes for audit trail

## Troubleshooting

### "Directory safety check failed"
- Agent trying to access restricted path
- Check agent_directory_rules.json
- Add path to allowed_paths if legitimate

### "High risk operation blocked"
- Operation deemed dangerous
- Review operation necessity
- Request manual approval if needed

### "Target directory does not exist"
- For new files, parent must exist
- Create parent directory first
- Use safe_path methods

## Integration Points

- Auto-acceptance system checks directory safety
- Decision logger records directory operations
- Safety monitor tracks cross-boundary attempts
- Dashboard shows directory access patterns