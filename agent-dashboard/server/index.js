import express from 'express';
import { WebSocketServer } from 'ws';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { AgentMonitor } from './services/agentMonitor.js';
import { FileSystemWatcher } from './services/fileSystemWatcher.js';
import { DatabaseService } from './services/database.js';
import { MetricsCollector } from './services/metricsCollector.js';
import { HeartbeatMonitor } from './services/heartbeatMonitor.js';
import { JarvisService } from './services/jarvis.js';
import apiRoutes from './routes/api.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3010;

// Initialize services
const db = new DatabaseService();
const agentMonitor = new AgentMonitor(db);
const fileWatcher = new FileSystemWatcher(agentMonitor);
const metricsCollector = new MetricsCollector(db, agentMonitor);
const heartbeatMonitor = new HeartbeatMonitor(agentMonitor);
const jarvisService = new JarvisService(db);

// Middleware
app.use(cors());
app.use(express.json());

// Serve static files in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/dist')));
}

// API routes
app.use('/api', apiRoutes(agentMonitor, db, metricsCollector, jarvisService));

// Create HTTP server
const server = app.listen(PORT, () => {
  console.log(`🚀 Dashboard server running on http://localhost:${PORT}`);
});

// WebSocket server attached directly to HTTP server
const wss = new WebSocketServer({ server });

// Broadcast function
const broadcast = (data) => {
  const message = JSON.stringify(data);
  wss.clients.forEach((client) => {
    if (client.readyState === 1) {
      client.send(message);
    }
  });
};

// WebSocket connections
wss.on('connection', (ws, req) => {
  console.log('New WebSocket client connected from:', req.headers.origin || 'unknown');
  
  // Send initial data
  try {
    const initialData = {
      type: 'initial',
      data: {
        agents: agentMonitor.getAgents(),
        activities: agentMonitor.getRecentActivities(),
        metrics: metricsCollector.getCurrentMetrics(),
        projects: agentMonitor.getProjects(),
        jarvis: jarvisService.getSystemStatus()
      }
    };
    ws.send(JSON.stringify(initialData));
    console.log('Sent initial data to client');
  } catch (error) {
    console.error('Error sending initial data:', error);
  }

  // Handle messages from client
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      
      // Check if it's a Jarvis query
      if (data.type === 'jarvis-query' && data.message) {
        if (jarvisService.isJarvisQuery(data.message)) {
          const response = jarvisService.getJarvisResponse();
          ws.send(JSON.stringify({
            type: 'jarvis-response',
            data: response
          }));
        }
      }
    } catch (error) {
      console.error('WebSocket message error:', error);
    }
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });

  ws.on('close', () => {
    console.log('WebSocket client disconnected');
  });
});

// Set up event listeners for real-time updates
agentMonitor.on('update', (data) => {
  broadcast({ type: 'agent-update', data });
});

fileWatcher.on('file-change', (data) => {
  broadcast({ type: 'file-change', data });
});

metricsCollector.on('metrics-update', (data) => {
  broadcast({ type: 'metrics-update', data });
});

// Start monitoring
fileWatcher.startWatching();
metricsCollector.startCollecting();
heartbeatMonitor.initialize();

// Set up Jarvis event listeners
jarvisService.on('initialized', (data) => {
  broadcast({ type: 'jarvis-initialized', data });
});

jarvisService.on('shutdown', () => {
  broadcast({ type: 'jarvis-shutdown', data: { message: 'Jarvis is shutting down' } });
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('Shutting down gracefully...');
  await jarvisService.shutdown();
  fileWatcher.stopWatching();
  metricsCollector.stopCollecting();
  db.close();
  server.close(() => {
    process.exit(0);
  });
});