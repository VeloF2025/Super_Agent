# Getting Started with Jarvis Super Agent System

This guide will walk you through setting up and using the Jarvis Super Agent System for the first time.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18 or higher** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **A modern text editor** - VS Code, Cursor, or Windsurf recommended

### Verify Installation

```bash
# Check Python version
python --version

# Check Node.js version
node --version

# Check Git version
git --version
```

## Installation

### Step 1: Clone or Set Up the Repository

If you're starting fresh:
```bash
# Create the workspace directory
mkdir -p "C:\Jarvis\AI Workspace\Super Agent"
cd "C:\Jarvis\AI Workspace\Super Agent"

# Initialize git repository
git init
```

If you're cloning an existing repository:
```bash
git clone <your-repo-url> "C:\Jarvis\AI Workspace\Super Agent"
cd "C:\Jarvis\AI Workspace\Super Agent"
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies for the system
pip install schedule watchdog

# Install Node.js dependencies for the dashboard
cd agent-dashboard
npm install
cd ..
```

### Step 3: Initial System Setup

```bash
# Make sure you're in the Super Agent directory
cd "C:\Jarvis\AI Workspace\Super Agent"

# Run the system startup script
daily-ops\start-daily-ops.bat
```

This will:
- Start the Agent Dashboard (http://localhost:3000)
- Initialize the Housekeeper service
- Start the Context Monitor
- Begin the automated scheduler

## First Project Setup

### Method 1: Using Templates (Recommended)

1. **Choose a project template:**
   ```bash
   # Copy a template to start
   copy context-inbox\templates\quick-project-template.md context-inbox\new-projects\my-first-project.md
   ```

2. **Edit the template:**
   Open `context-inbox\new-projects\my-first-project.md` and fill in your project details:
   
   ```markdown
   # Quick Project Context Template

   ## Project Information
   **Project Name**: My Task Manager App
   **Type**: Full-Stack Web App
   **Primary Goal**: Create a simple task management application

   ## Technical Requirements
   **Frontend**: React
   **Backend**: Node.js
   **Database**: SQLite
   **Special Requirements**: User authentication

   ## Core Features (MVP)
   1. User registration and login
   2. Create and manage tasks
   3. Mark tasks as complete

   ## Constraints
   **Timeline**: 2 weeks
   **Team Size**: Auto-assign agents
   ```

3. **Wait for processing:**
   The system will automatically detect and process your project file within 30 seconds.

### Method 2: Drop Existing Requirements

If you have existing project documentation:

1. **Place files in the inbox:**
   ```bash
   # Copy any existing requirements
   copy your-requirements.pdf context-inbox\new-projects\
   copy project-spec.md context-inbox\new-projects\
   ```

2. **The system will process automatically** and generate agent contexts.

## Understanding the Dashboard

Once the system is running, visit http://localhost:3000 to see:

### Main Dashboard View
- **System Status** - Overall health and active agents
- **Agent Activity** - Real-time view of what each agent is doing
- **Project Progress** - Current workflows and completion status
- **Performance Metrics** - System efficiency and usage statistics

### Agent Details
Click on any agent to see:
- Current tasks and status
- Work history and accomplishments
- Performance metrics
- Communication logs

### Communication Panel
View real-time message flow between agents:
- Message priority and routing
- Response times
- Communication patterns

## Daily Workflow

### Morning Routine (Automatic at 9:00 AM)

The system automatically runs a morning standup that:
1. **Reviews yesterday's progress** from shutdown summary
2. **Checks system health** and agent status
3. **Identifies incomplete tasks** from previous day
4. **Sets today's priorities** based on context
5. **Initializes agents** with daily context

**Manual trigger:**
```bash
cd daily-ops
python jarvis-scheduler.py morning
```

### During the Day

- **Monitor progress** via the dashboard
- **Add new projects** by dropping files in `context-inbox/new-projects/`
- **Check agent status** and communication
- **Review metrics** and performance

### Evening Routine (Automatic at 6:00 PM)

The system automatically runs an evening shutdown that:
1. **Collects accomplishments** from all agents
2. **Archives daily data** for preservation
3. **Identifies issues** and blockers
4. **Plans tomorrow's priorities** based on today's work
5. **Generates summary reports** for review

**Manual trigger:**
```bash
cd daily-ops
python jarvis-scheduler.py evening
```

## Working with Agents

### Understanding Agent Roles

| Agent | When to Use | Example Tasks |
|-------|-------------|---------------|
| **Frontend** | UI/UX work needed | Creating React components, styling, responsive design |
| **Backend** | Server-side logic needed | APIs, databases, authentication, business logic |
| **Quality** | Testing and validation | Unit tests, integration tests, code quality checks |
| **Research** | Investigation needed | Technology evaluation, best practices, architecture |
| **Development** | General coding tasks | Bug fixes, refactoring, feature implementation |

### Agent Communication

Agents communicate automatically, but you can monitor their interactions:

1. **View in Dashboard** - Real-time communication panel
2. **Check queue files** - `communication/queue/` for pending messages
3. **Review logs** - `logs/` directory for detailed activity

### Working with Git Worktrees

Each agent operates in its own git worktree:

```bash
# View all worktrees
git worktree list

# Access agent workspace
cd ..\agents\agent-frontend

# Each agent can work independently
git status
git add .
git commit -m "Implement new feature"
```

## Common Tasks

### Adding a New Project

1. **Drop requirements** in `context-inbox/new-projects/`
2. **Monitor processing** in dashboard
3. **Review agent assignments** once processed
4. **Track progress** through the workflow

### Taking Over an Existing Project

1. **Create takeover request:**
   ```bash
   copy context-inbox\templates\takeover-template.md context-inbox\existing-projects\legacy-app-takeover.md
   ```

2. **Fill in project details:**
   - Repository URL
   - Current challenges
   - Takeover goals

3. **Let agents analyze** the codebase and generate context

### Monitoring System Health

1. **Dashboard overview** - System status indicators
2. **Housekeeper status** - Check cleanup operations
3. **Agent heartbeats** - Verify all agents are responsive
4. **Performance metrics** - Monitor efficiency trends

### Troubleshooting

#### Dashboard Not Loading
```bash
# Check if services are running
netstat -an | findstr 3000
netstat -an | findstr 3001

# Restart the dashboard
cd agent-dashboard
npm run dev
```

#### Agents Not Responding
```bash
# Check agent directories
dir ..\agents\

# Review communication queue
dir communication\queue\

# Check system logs
type logs\system\jarvis-*.log
```

#### Context Processing Issues
```bash
# Check context monitor
cd context-inbox
python oa-monitor.py

# Manually process contexts
python context-processor.py
```

## Best Practices

### Project Organization
- **Use descriptive filenames** for context requests
- **Include comprehensive requirements** for better agent understanding
- **Organize by priority** - critical features first

### Agent Collaboration
- **Let agents communicate naturally** - minimal manual intervention needed
- **Monitor for conflicts** via dashboard
- **Review daily summaries** for insights

### System Maintenance
- **Daily routines run automatically** - manual triggers only when needed
- **Monitor disk usage** - housekeeper maintains optimal storage
- **Regular git commits** - agents commit work automatically

### Performance Optimization
- **Review metrics regularly** - identify efficiency patterns
- **Adjust agent allocation** based on project needs
- **Monitor resource usage** - scale as needed

## Next Steps

Once you're comfortable with the basics:

1. **Explore advanced features** - Custom templates, agent configuration
2. **Integrate with your tools** - IDE extensions, CI/CD pipelines
3. **Customize workflows** - Tailor the system to your specific needs
4. **Scale the system** - Add more agents or integrate with external tools

## Getting Help

- **Documentation** - Check the `docs/` directory for detailed guides
- **Dashboard logs** - Built-in logging and error reporting
- **System status** - Real-time health monitoring
- **Community** - GitHub issues and discussions

The Jarvis Super Agent System is designed to be intuitive and self-managing. Start with simple projects and gradually explore more advanced features as you become comfortable with the system.