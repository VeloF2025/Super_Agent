# OA Agent Dashboard - Command Center

A high-tech, real-time monitoring dashboard for the OA (Office Assistant) and all agents in the Super Agent system. Features a cyberpunk-inspired UI with comprehensive monitoring, communication tracking, and project management capabilities.

## Features

- **Real-time Agent Monitoring**: Track status, activities, and performance of all agents
- **Communication Visualization**: View message flow between agents with priority routing
- **Project Management**: Monitor active projects and agent assignments
- **Performance Analytics**: Charts and metrics for agent performance and system health
- **Local Storage**: SQLite database for persistent data storage
- **WebSocket Updates**: Real-time data synchronization
- **File System Monitoring**: Watches agent logs, communication queues, and project files

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Node.js + Express + WebSocket
- **Database**: SQLite (better-sqlite3)
- **UI Components**: Framer Motion, Recharts, Lucide Icons
- **File Monitoring**: Chokidar

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Windows/Linux/macOS

## Installation

1. Navigate to the dashboard directory:
```bash
cd "C:\Jarvis\AI Workspace\Super Agent\agent-dashboard"
```

2. Install dependencies:
```bash
npm run setup
```

This will install dependencies for both server and client.

## Running the Dashboard

### Development Mode

Start both frontend and backend in development mode:
```bash
npm run dev
```

This will:
- Start the backend server on http://localhost:3001
- Start the frontend dev server on http://localhost:3000
- Enable hot module replacement for frontend
- Enable auto-restart for backend changes

### Production Mode

1. Build the frontend:
```bash
npm run build
```

2. Start the production server:
```bash
npm start
```

Access the dashboard at http://localhost:3001

## Architecture

### Backend Services

- **AgentMonitor**: Tracks agent status, activities, and health
- **FileSystemWatcher**: Monitors file changes in agent directories
- **DatabaseService**: SQLite operations for persistent storage
- **MetricsCollector**: Collects and aggregates performance metrics

### Frontend Components

- **Dashboard**: Main overview with charts and metrics
- **AgentDetails**: Detailed view of individual agent performance
- **CommunicationPanel**: Real-time message flow visualization
- **ProjectsView**: Active project management interface

### Data Flow

1. File system changes trigger events in FileSystemWatcher
2. AgentMonitor processes events and updates agent states
3. MetricsCollector aggregates performance data
4. WebSocket broadcasts updates to connected clients
5. React frontend updates UI in real-time

## API Endpoints

- `GET /api/dashboard` - Complete dashboard data
- `GET /api/agents` - List all agents
- `GET /api/agents/:id` - Get specific agent details
- `GET /api/agents/:id/metrics` - Agent performance metrics
- `GET /api/activities` - Recent activities
- `POST /api/activities` - Record new activity
- `PUT /api/activities/:id/complete` - Mark activity complete
- `GET /api/metrics` - Historical metrics
- `GET /api/communications` - Recent communications
- `GET /api/projects` - Active projects
- `WebSocket /ws` - Real-time updates

## Database Schema

### Tables
- **agents**: Agent registry and status
- **activities**: Task execution history
- **metrics**: Performance metrics time series
- **communications**: Inter-agent message logs
- **projects**: Project management data

## Customization

### UI Theme

Modify `tailwind.config.js` and `src/index.css` for theme customization. The dashboard uses a cyberpunk-inspired color scheme with neon accents.

### Monitoring Paths

Update paths in `server/services/agentMonitor.js` and `server/services/fileSystemWatcher.js` to match your agent directory structure.

## Troubleshooting

### Dashboard not loading
- Check if both servers are running (port 3000 and 3001)
- Verify WebSocket connection in browser console
- Check for CORS errors

### Agents not appearing
- Verify agent directory structure matches expected format
- Check file permissions for reading agent directories
- Look for errors in server console

### Database errors
- Ensure write permissions in data directory
- Check if SQLite is properly installed
- Delete `data/dashboard.db` to reset database

## Future Enhancements

- Authentication and multi-user support
- Historical data visualization
- Alert system for critical events
- Agent command interface
- Export functionality for reports
- Dark/light theme toggle
- Mobile responsive design improvements