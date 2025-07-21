# 🤖 Jarvis Orchestration Agent

## Overview

Jarvis is the primary orchestration agent in the Super Agent system. When the system is properly initialized and you ask "Hey Jarvis" or "Jarvis?", it will confirm its identity and operational status.

## How It Works

### Recognition Patterns

Jarvis responds to the following queries:
- `Jarvis?`
- `Hey Jarvis`
- `jarvis` (case insensitive)
- `Are you there Jarvis?`
- `Is Jarvis online?`

### Response Examples

When called, Jarvis will respond with one of these greetings:
- "Yes, I'm here. Jarvis at your service."
- "Jarvis online and operational. How may I assist you?"
- "Indeed, it's Jarvis. All systems functioning within normal parameters."
- "Jarvis here. Ready to orchestrate your agents."
- "You called? Jarvis is fully operational and ready."
- "Jarvis responding. All agent systems are under my supervision."
- "Present and accounted for. This is Jarvis, your orchestration agent."

## API Endpoints

### 1. Direct Jarvis Query
```http
GET /api/jarvis
```

Returns Jarvis's current status and a greeting message.

**Response:**
```json
{
  "message": "Jarvis online and operational. How may I assist you?",
  "status": "operational",
  "agent": "jarvis-orchestrator",
  "details": {
    "uptime": "2h 15m 30s",
    "initialized": true,
    "version": "2.0.0",
    "capabilities": [
      "agent-coordination",
      "task-delegation",
      "system-monitoring",
      "context-persistence"
    ]
  }
}
```

### 2. Query Recognition Check
```http
POST /api/jarvis/query
Content-Type: application/json

{
  "message": "Hey Jarvis"
}
```

Checks if a message is asking for Jarvis and returns appropriate response.

**Response:**
```json
{
  "isJarvisQuery": true,
  "response": {
    "message": "Jarvis here. Ready to orchestrate your agents.",
    "status": "operational",
    "agent": "jarvis-orchestrator"
  }
}
```

### 3. Jarvis Commands
```http
POST /api/jarvis/command
Content-Type: application/json

{
  "command": "status"
}
```

Send commands to Jarvis for execution.

### 4. System Status
```http
GET /api/jarvis/status
```

Get comprehensive system status from Jarvis's perspective.

**Response:**
```json
{
  "orchestrator": "Jarvis",
  "status": "operational",
  "systemHealth": {
    "totalAgents": 5,
    "activeAgents": 5,
    "recentActivities": 42,
    "uptime": "2h 15m 30s"
  },
  "message": "All systems nominal. Jarvis is monitoring all agents."
}
```

## WebSocket Integration

Jarvis also responds through WebSocket connections for real-time interaction:

```javascript
// Send a query through WebSocket
ws.send(JSON.stringify({
  type: 'jarvis-query',
  message: 'Hey Jarvis'
}));

// Receive response
{
  "type": "jarvis-response",
  "data": {
    "message": "Jarvis at your service.",
    "status": "operational",
    "agent": "jarvis-orchestrator"
  }
}
```

## Dashboard Integration

The dashboard includes a Jarvis Status component that:
- Shows real-time Jarvis operational status
- Displays system health metrics
- Provides quick test buttons for Jarvis queries
- Shows Jarvis responses in a popup

## Testing Jarvis

### Using the Test Script

```bash
# Install dependencies (if needed)
cd agent-dashboard
npm install node-fetch

# Run the test script
node ../test-jarvis.js
```

The test script will:
1. Test the direct Jarvis endpoint
2. Test various query patterns
3. Test command execution
4. Enter interactive mode for manual testing

### Manual Testing with cURL

```bash
# Direct query
curl http://localhost:3010/api/jarvis

# Check if message is for Jarvis
curl -X POST http://localhost:3010/api/jarvis/query \
  -H "Content-Type: application/json" \
  -d '{"message": "Hey Jarvis"}'

# Get system status
curl http://localhost:3010/api/jarvis/status
```

## Implementation Details

### Service Location
- Main service: `agent-dashboard/server/services/jarvis.js`
- API routes: `agent-dashboard/server/routes/api.js`
- Client component: `agent-dashboard/client/src/components/JarvisStatus.tsx`

### Database Registration
Jarvis registers itself in the database as:
- ID: `jarvis-orchestrator`
- Type: `orchestrator`
- Capabilities: agent-coordination, task-delegation, system-monitoring, context-persistence

### Event System
Jarvis emits the following events:
- `initialized` - When Jarvis comes online
- `shutdown` - When Jarvis is shutting down

These events are broadcast to all connected WebSocket clients.

## Future Enhancements

Planned improvements for Jarvis:
1. Natural language command processing
2. Voice recognition integration
3. Advanced workflow automation
4. Predictive task assignment
5. Learning from user preferences
6. Multi-language support

## Troubleshooting

### Jarvis Not Responding
1. Check if the dashboard server is running
2. Verify Jarvis service initialized successfully
3. Check logs for any errors
4. Ensure database is accessible

### Jarvis Shows "Initializing"
- Wait a few seconds for initialization to complete
- Check for any system component failures
- Verify all required directories exist

### WebSocket Not Receiving Responses
1. Ensure WebSocket connection is established
2. Check browser console for errors
3. Verify message format is correct