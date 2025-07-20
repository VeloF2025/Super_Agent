# Multi-Agent Development Workflow

## Initial Setup (One Time)

1. **Position yourself in Cursor**
   ```bash
   cd ~/workspace/agents
   ```

2. **Make the agent manager executable**
   ```bash
   chmod +x agent-manager.py
   ```

## Creating a New Project

1. **From Cursor, tell the Orchestrator Agent:**
   ```
   Create a new SaaS application called "task-tracker" with user authentication, 
   real-time updates, and a modern UI
   ```

2. **Or use the command line:**
   ```bash
   ./agent-manager.py create task-tracker --type fullstack --agents 4
   ```

3. **Deploy agents to the project:**
   ```bash
   ./agent-manager.py deploy task-tracker
   ```

## Working on Features

1. **Coordinate a complex task:**
   ```bash
   ./agent-manager.py task task-tracker "Implement user authentication with email verification"
   ```

2. **The system will:**
   - Create the project structure
   - Deploy specialized agents
   - Distribute subtasks
   - Coordinate development

3. **Monitor progress:**
   ```bash
   ./agent-manager.py status --project task-tracker
   ```

## Project Structure Created

```
workspace/
└── projects/
    └── task-tracker/
        ├── agent-workspace/        # Not deployed
        │   ├── agents/
        │   │   ├── agent-frontend-001/
        │   │   ├── agent-backend-001/
        │   │   ├── agent-database-001/
        │   │   └── agent-testing-001/
        │   ├── communication/
        │   ├── logs/
        │   ├── docs/
        │   └── project.json
        │
        └── app/                    # Deployed
            ├── src/
            │   ├── components/
            │   ├── pages/
            │   ├── api/
            │   └── utils/
            ├── public/
            ├── tests/
            ├── package.json
            └── README.md
```

## Agent Communication Flow

1. **Orchestrator → Agents**
   ```json
   {
     "to": "agent-backend-001",
     "type": "task",
     "payload": {
       "description": "Create authentication API",
       "requirements": ["JWT", "Email verification"]
     }
   }
   ```

2. **Agent → Orchestrator**
   ```json
   {
     "from": "agent-backend-001",
     "type": "task_complete",
     "payload": {
       "files_created": ["src/api/auth.js"],
       "tests_passed": true
     }
   }
   ```

3. **Agent → Agent**
   ```json
   {
     "from": "agent-backend-001",
     "to": "agent-frontend-001",
     "type": "api_ready",
     "payload": {
       "endpoints": ["/api/auth/login", "/api/auth/register"],
       "documentation": "src/api/auth.md"
     }
   }
   ```

## Best Practices

### 1. **Clear Separation**
- Agent workspace: Development environment, logs, communication
- App folder: Only production-ready, deployable code

### 2. **Git Strategy**
- Main branch: Contains both folders
- Agent branches: Individual agent work
- Feature branches: Merged completed features

### 3. **Communication**
- Use the shared communication directory
- JSON messages for clarity
- Event-driven coordination

### 4. **Documentation**
- Technical docs in agent-workspace/docs/
- User docs in app/README.md
- API docs auto-generated

### 5. **Testing**
- Testing agent validates all code
- Tests go in app/tests/
- CI/CD ready structure

## Deployment

When ready to deploy, you only need the `app/` folder:

```bash
cd projects/task-tracker/app
npm install
npm run build
# Deploy to your platform
```

The agent-workspace remains on your development machine as a powerful development accelerator.