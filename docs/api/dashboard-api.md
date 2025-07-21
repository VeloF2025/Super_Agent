# Dashboard API Documentation

## Overview
The Dashboard API provides real-time access to agent status, system metrics, and project information.

## Base URL
```
http://localhost:3001/api
```

## Endpoints

### GET /dashboard
Get complete dashboard data including all agents, activities, and metrics.

**Response:**
```json
{
  "agents": [...],
  "activities": [...],
  "metrics": {...},
  "system_status": "healthy"
}
```

### GET /agents
List all registered agents.

**Response:**
```json
[
  {
    "id": "agent-frontend",
    "name": "Frontend Agent",
    "status": "active",
    "last_heartbeat": "2025-01-21T10:30:00Z",
    "current_task": "Implementing component library"
  }
]
```

### GET /agents/:id
Get detailed information for a specific agent.

**Parameters:**
- `id` - Agent identifier

**Response:**
```json
{
  "id": "agent-frontend",
  "name": "Frontend Agent",
  "status": "active",
  "workspace_path": "../agents/agent-frontend",
  "metrics": {...},
  "recent_activities": [...]
}
```

### GET /agents/:id/metrics
Get performance metrics for a specific agent.

**Parameters:**
- `id` - Agent identifier

**Response:**
```json
{
  "agent_id": "agent-frontend",
  "efficiency_score": 85,
  "tasks_completed": 12,
  "hours_active": 6.5,
  "commits_today": 8
}
```

### GET /activities
Get recent system activities.

**Query Parameters:**
- `limit` - Number of activities to return (default: 50)
- `agent_id` - Filter by specific agent

**Response:**
```json
[
  {
    "id": 1,
    "agent_id": "agent-frontend",
    "type": "task_completion",
    "description": "Completed component implementation",
    "status": "completed",
    "created_at": "2025-01-21T10:30:00Z"
  }
]
```

### POST /activities
Record a new activity.

**Request Body:**
```json
{
  "agent_id": "agent-frontend",
  "type": "task_start",
  "description": "Starting new feature implementation"
}
```

### PUT /activities/:id/complete
Mark an activity as completed.

**Parameters:**
- `id` - Activity identifier

### GET /communications
Get recent inter-agent communications.

**Query Parameters:**
- `limit` - Number of messages to return (default: 100)
- `from_agent` - Filter by sender
- `to_agent` - Filter by recipient

**Response:**
```json
[
  {
    "id": "msg-12345",
    "from_agent": "agent-frontend",
    "to_agent": "agent-backend",
    "message_type": "api_request",
    "priority": "high",
    "timestamp": "2025-01-21T10:30:00Z",
    "processed": true
  }
]
```

### GET /projects
Get active project information.

**Response:**
```json
[
  {
    "id": "proj-123",
    "name": "E-commerce Platform",
    "status": "in_progress",
    "agents_assigned": ["agent-frontend", "agent-backend"],
    "progress": 65,
    "created_at": "2025-01-20T09:00:00Z"
  }
]
```

## WebSocket Connection

### Connection Endpoint
```
ws://localhost:3001/ws
```

### Message Format
```json
{
  "type": "agent_status_update",
  "data": {
    "agent_id": "agent-frontend",
    "status": "active",
    "current_task": "New task description"
  },
  "timestamp": "2025-01-21T10:30:00Z"
}
```

### Event Types
- `agent_status_update` - Agent status changes
- `new_activity` - New activities logged
- `system_metric_update` - System performance updates
- `communication_event` - New inter-agent messages

## Error Responses

All endpoints return standard HTTP status codes and error messages:

```json
{
  "error": "Agent not found",
  "status": 404,
  "timestamp": "2025-01-21T10:30:00Z"
}
```

## Rate Limiting
- Default: 100 requests per minute per IP
- WebSocket: 1 connection per client
- No authentication required for local development

## Examples

### Get Agent Status
```bash
curl http://localhost:3001/api/agents/agent-frontend
```

### Record New Activity
```bash
curl -X POST http://localhost:3001/api/activities   -H "Content-Type: application/json"   -d '{"agent_id":"agent-frontend","type":"task_start","description":"Starting new feature"}'
```

### WebSocket Connection (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:3001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```
