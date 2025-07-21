# Claude Context Management Implementation Guide

## Quick Start

### 1. Check Current State
```bash
cd "C:\Jarvis\AI Workspace\Super Agent"
python .claude\enhance-context.py check
```

### 2. Enhance Existing CLAUDE.md Files
```bash
# Dry run first
python .claude\enhance-context.py batch

# Apply changes
python .claude\enhance-context.py batch --apply
```

### 3. Set Up Local Development
```bash
# Copy local config template
copy .claude\config.local.example.json .claude\config.local.json

# Edit with your settings
notepad .claude\config.local.json
```

## Architecture Overview

```
.claude/                        # All Claude configs in one place
├── config.json                 # Public configuration (git-tracked)
├── config.local.json          # Your private settings (git-ignored)
├── contexts/
│   ├── base.md                # Shared base context for all agents
│   ├── private/               # Private contexts (git-ignored)
│   │   ├── orchestrator.md    # Private data for orchestrator
│   │   └── [agent].md         # Private data per agent
│   └── templates/             # Templates for new agents
├── enhance-context.py         # Tool to improve existing files
└── IMPLEMENTATION_GUIDE.md    # This file
```

## Key Benefits

1. **Clean Separation**: Public vs private configs clearly separated
2. **GitHub Ready**: Private data automatically excluded from git
3. **Backwards Compatible**: Enhances existing CLAUDE.md files
4. **Multiple IDEs**: Each can have its own local config
5. **Context Hierarchy**: Clear inheritance from root → workspace → agent

## Usage Patterns

### For Development
- Your personal settings in `.claude/config.local.json`
- Agent work logs in `.claude/contexts/private/`
- Debug with enhanced logging

### For Production/GitHub
- Only public files are committed
- Clean, shareable configurations
- No personal paths or IDs exposed

## Preventing Crashes

1. **Separate Instances**: Use different agent IDs in each IDE
2. **Resource Management**: Configure memory limits in local config
3. **Session Isolation**: Each IDE uses its own cache directory

Example config.local.json for multiple IDEs:
```json
{
  "instance": {
    "id": "vscode-instance-1",
    "cache_dir": ".claude/cache/vscode/"
  }
}
```

## Next Steps

1. Run the enhancement check to see what would change
2. Back up your current CLAUDE.md files
3. Apply enhancements with `--apply` flag
4. Configure your local settings
5. Test with one agent before rolling out to all

## Troubleshooting

- **File not found**: Use absolute paths or cd to workspace first
- **Permission denied**: Run as administrator or check file permissions
- **Import errors**: Ensure Python 3.8+ is installed

For issues, check:
- `.claude/logs/` for error details
- Original files are backed up as `.bak`
- Private contexts in `.claude/contexts/private/`