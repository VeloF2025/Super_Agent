# Claude Context Management System - Complete Guide

## Overview

This enhanced context management system provides:
- **Crash Prevention**: Monitor and manage multiple Claude instances
- **Privacy Separation**: Keep personal data out of public repositories
- **Context Optimization**: Cache and route contexts efficiently
- **Agent Coordination**: Smooth handoffs between specialized agents

## Quick Start

```bash
cd "C:\Jarvis\AI Workspace\Super Agent"

# Run setup
.claude\setup.bat

# Check status
python .claude\claude-helper.py status

# Initialize environment
python .claude\claude-helper.py init

# Enhance existing files (dry run)
python .claude\claude-helper.py enhance --check

# Apply enhancements
python .claude\claude-helper.py enhance --apply
```

## Tools Overview

### 1. **claude-helper.py** - Main CLI Tool
All-in-one tool for context management:
```bash
# Show comprehensive status
python .claude\claude-helper.py status

# Run diagnostics and auto-fix
python .claude\claude-helper.py doctor

# Clean cache and temp files
python .claude\claude-helper.py clean

# Switch agent context
python .claude\claude-helper.py switch orchestrator
```

### 2. **context-monitor.py** - Performance Monitor
Prevents crashes by monitoring resources:
```bash
# Real-time monitoring
python .claude\context-monitor.py monitor --duration 300

# Check system status
python .claude\context-monitor.py status

# Clean old cache
python .claude\context-monitor.py clean

# Create/release instance locks
python .claude\context-monitor.py lock --agent orchestrator --instance vscode-1
```

### 3. **context-router.py** - Context Switching
Manages context hierarchy and routing:
```bash
# Show current context
python .claude\context-router.py status

# List available agents
python .claude\context-router.py list

# Route task to best agent
python .claude\context-router.py route --task "implement user auth"

# Validate all contexts
python .claude\context-router.py validate
```

### 4. **enhance-context.py** - File Enhancement
Improves existing CLAUDE.md files:
```bash
# Check what would change
python .claude\enhance-context.py check

# Enhance single file
python .claude\enhance-context.py enhance --file agents\agent-orchestrator\CLAUDE.md

# Batch enhance all files
python .claude\enhance-context.py batch --apply
```

## Preventing Multiple Instance Crashes

### 1. Use Different Instance IDs
In VSCode `.claude\config.local.json`:
```json
{
  "instance": {
    "id": "vscode-main",
    "cache_dir": ".claude/cache/vscode/"
  }
}
```

In Cursor `.claude\config.local.json`:
```json
{
  "instance": {
    "id": "cursor-dev",
    "cache_dir": ".claude/cache/cursor/"
  }
}
```

### 2. Monitor Resources
```bash
# Check before starting new instance
python .claude\context-monitor.py status

# Monitor in real-time
python .claude\context-monitor.py monitor
```

### 3. Use Instance Locks
```bash
# Before starting work
python .claude\context-monitor.py lock --agent development --instance vscode-1

# When done
python .claude\context-monitor.py unlock --agent development --instance vscode-1
```

## Context Hierarchy

```
1. Root Context (C:\Jarvis\CLAUDE.md)
   ↓ inherits
2. Workspace Base (.claude\contexts\base.md)
   ↓ inherits
3. Agent Context (agents\[agent-name]\CLAUDE.md)
   ↓ extends with
4. Private Context (.claude\contexts\private\[agent].md)
```

## Privacy Best Practices

### What Goes Where

**Public (CLAUDE.md)**:
- Agent roles and responsibilities
- General procedures
- Public integration points
- Shareable configurations

**Private (.claude\contexts\private\)**:
- Instance IDs (agent-orchestrator-001)
- Absolute paths (C:\Jarvis\...)
- API keys and credentials
- Personal performance metrics
- Local development notes

### GitHub Publishing Checklist

1. **Run privacy validation**:
   ```bash
   python shared\tools\context-manager.py validate --all
   ```

2. **Check .gitignore**:
   - Ensure all private patterns are listed
   - Verify `.claude/config.local.json` is ignored

3. **Review enhanced files**:
   - Check that private data shows `[See private context]`
   - Verify no absolute paths remain

4. **Test with clean clone**:
   ```bash
   git clone [your-repo] test-clone
   cd test-clone
   python .claude\claude-helper.py doctor
   ```

## Troubleshooting

### "Claude keeps crashing"
1. Check system resources: `python .claude\context-monitor.py status`
2. Clean cache: `python .claude\context-monitor.py clean`
3. Use different instance IDs per IDE
4. Reduce context file sizes

### "Context not loading"
1. Validate hierarchy: `python .claude\context-router.py validate`
2. Check current context: `python .claude\context-router.py status`
3. Run doctor: `python .claude\claude-helper.py doctor`

### "Private data in public files"
1. Run enhancement: `python .claude\enhance-context.py batch --apply`
2. Check results: `python shared\tools\context-manager.py validate`
3. Review .gitignore patterns

## Advanced Usage

### Custom Agent Templates
Create `.claude\contexts\templates\[type].md` for new agent types

### Performance Tuning
Edit `.claude\config.local.json`:
```json
{
  "overrides": {
    "context_length_max": 10000,
    "cache_size_mb": 200,
    "quality_threshold": 0.95
  }
}
```

### Multi-Project Setup
```bash
# Create project-specific context
mkdir projects\my-project\.claude
echo "# Project Context" > projects\my-project\.claude\context.md
```

## Next Steps

1. **Set up your environment**: Run `setup.bat`
2. **Enhance existing files**: Use `claude-helper.py enhance`
3. **Configure local settings**: Edit `config.local.json`
4. **Monitor performance**: Use real-time monitoring
5. **Validate before publishing**: Check privacy compliance

Remember: The goal is to maintain powerful local development while keeping your GitHub repository clean and shareable!