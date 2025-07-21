# CLAUDE.md Template for Super Agent System

## Configuration Layers

### Public Layer (Git-tracked)
```markdown
# Agent: [Agent Name] ([Agent Type])

## Core Identity
- **Agent Type**: [e.g., orchestrator, developer, researcher]
- **Role**: [Public role description]
- **Authority Level**: [Standard/Executive/Specialist]

## Core Responsibilities
[List public responsibilities]

## Integration Points
@import ../../shared/standards/[relevant-standards].md
@import ./sop/[public-procedures].md

## Commands
[Public command documentation]
```

### Private Layer (.claude-private.md - Git-ignored)
```markdown
# Private Configuration for [Agent Name]

## Instance Details
- **Agent ID**: [personal-instance-id]
- **Working Directory**: [local paths]
- **API Keys**: [encrypted references]
- **Performance Metrics**: [personal tracking]

## Active Projects
- **Current Focus**: [private project details]
- **Local Dependencies**: [system-specific paths]
```

## Recommended File Structure

```
AI Workspace/
├── .gitignore                    # Ignore private files
├── CLAUDE.md                     # Public orchestrator context
├── .claude-private.md            # Private config (ignored)
├── .env.example                  # Template for env vars
├── .env                          # Actual env vars (ignored)
├── config/
│   ├── public/                   # Git-tracked configs
│   │   └── agent-defaults.json
│   └── private/                  # Git-ignored configs
│       └── local-overrides.json
└── agents/
    └── [agent-name]/
        ├── CLAUDE.md             # Public agent context
        ├── .claude-private.md    # Private instance config
        └── .claude-dev.md        # Development notes
```

## Context Loading Strategy

```python
# Pseudo-code for loading contexts
def load_agent_context(agent_path):
    contexts = []
    
    # 1. Load public CLAUDE.md (always exists)
    contexts.append(load_file(f"{agent_path}/CLAUDE.md"))
    
    # 2. Load private config if exists (dev environment)
    if exists(f"{agent_path}/.claude-private.md"):
        contexts.append(load_file(f"{agent_path}/.claude-private.md"))
    
    # 3. Load dev notes if in development mode
    if ENV == "development" and exists(f"{agent_path}/.claude-dev.md"):
        contexts.append(load_file(f"{agent_path}/.claude-dev.md"))
    
    return merge_contexts(contexts)
```

## .gitignore Patterns

```gitignore
# Private Claude configurations
.claude-private.md
.claude-dev.md
**/private/
**/.env
**/.env.local

# Personal data
**/logs/
**/metrics/
**/temp/
**/recycle-bin/

# Instance-specific
agent-*-[0-9][0-9][0-9]/
**/project.local.json

# Development artifacts
**/agent-workspace/
**/.cache/
```

## Environment Variables Strategy

```bash
# .env.example (git-tracked)
AGENT_MODE=production
WORKSPACE_ROOT=./
LOG_LEVEL=info

# .env (git-ignored)
AGENT_MODE=development
WORKSPACE_ROOT=C:/Jarvis/AI Workspace
LOG_LEVEL=debug
PERSONAL_AGENT_ID=agent-orchestrator-001-personal
API_KEY_OPENAI=sk-...
```

## Migration Commands

### /separate-contexts
Splits existing CLAUDE.md into public/private layers

### /validate-privacy
Checks for personal information in public files

### /init-dev-environment
Sets up local development with private configs