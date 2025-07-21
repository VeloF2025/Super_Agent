# Claude Configuration Directory

This directory contains all Claude-specific configurations for the Super Agent system.

## Structure

```
.claude/
├── README.md           # This file
├── config.json         # Main configuration (public)
├── config.local.json   # Local overrides (git-ignored)
├── contexts/           # Context inheritance system
│   ├── base.md         # Base context for all agents
│   ├── templates/      # Templates for new agents
│   └── private/        # Private contexts (git-ignored)
├── cache/              # Context cache (git-ignored)
└── logs/               # Claude session logs (git-ignored)
```

## Usage

### Public Configuration (config.json)
- Tracked in git
- Contains default settings
- Defines agent hierarchy
- Sets quality standards

### Private Configuration (config.local.json)
- Git-ignored
- Personal settings
- API keys
- Local paths
- Instance IDs

### Context Loading Order
1. Root CLAUDE.md (C:\Jarvis\)
2. Workspace base context (.claude/contexts/base.md)
3. Agent-specific CLAUDE.md 
4. Private overrides (.claude/contexts/private/[agent].md)

## Commands

```bash
# Validate privacy settings
python shared/tools/context-manager.py validate

# Initialize development environment
python shared/tools/context-manager.py init

# Show context hierarchy
python shared/tools/context-manager.py hierarchy
```