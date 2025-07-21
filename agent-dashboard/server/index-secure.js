/**
 * Secure Dashboard Server
 * Enhanced with authentication, HTTPS, and comprehensive security
 */

import express from 'express';
import { WebSocketServer } from 'ws';
import cors from 'cors';
import helmet from 'helmet';
import path from 'path';
import https from 'https';
import http from 'http';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Import services
import { AgentMonitor } from './services/agentMonitor.js';
import { FileSystemWatcher } from './services/fileSystemWatcher.js';
import { DatabaseService } from './services/database.js';
import { MetricsCollector } from './services/metricsCollector.js';
import { HeartbeatMonitor } from './services/heartbeatMonitor.js';
import { AuthService } from './services/auth.js';
import { JarvisService } from './services/jarvis.js';

// Import middleware and routes
import SecurityMiddleware from './middleware/security.js';
import apiRoutes from './routes/api.js';
import authRoutes from './routes/auth.js';

// Import configuration
import config from '../../config/environment.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = config.server.port;

// Initialize services
const db = new DatabaseService();
const securityMiddleware = new SecurityMiddleware(config);
const authService = new AuthService(db, securityMiddleware);
const agentMonitor = new AgentMonitor(db);
const fileWatcher = new FileSystemWatcher(agentMonitor);
const metricsCollector = new MetricsCollector(db, agentMonitor);
const heartbeatMonitor = new HeartbeatMonitor(agentMonitor);
const jarvisService = new JarvisService(db);

// Apply security middleware
app.use(helmet(securityMiddleware.helmetOptions));
app.use(securityMiddleware.securityHeaders);
app.use(securityMiddleware.auditLog);
app.use(securityMiddleware.createRateLimiter());

// CORS configuration
app.use(cors(securityMiddleware.corsOptions));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Serve static files in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/dist')));
}

// Health check endpoint (no auth required)
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    services: {
      database: 'connected',
      monitoring: 'active',
      authentication: 'enabled'
    }
  });
});

// Authentication routes (no auth middleware)
app.use('/api/auth', authRoutes(authService, securityMiddleware));

// Protected API routes
app.use('/api', 
  securityMiddleware.authenticate,
  apiRoutes(agentMonitor, db, metricsCollector, jarvisService)
);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  
  if (err.name === 'ValidationError') {
    return res.status(400).json({
      error: 'Validation error',
      details: err.message
    });
  }
  
  if (err.name === 'UnauthorizedError') {
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Authentication required'
    });
  }
  
  res.status(500).json({
    error: 'Internal server error',
    message: config.isDevelopment() ? err.message : 'An error occurred'
  });
});

// Create server (HTTPS in production, HTTP in development)
let server;

if (config.server.enableHttps) {
  // HTTPS configuration
  const sslOptions = {
    cert: fs.readFileSync(config.ssl.certPath),
    key: fs.readFileSync(config.ssl.keyPath),
    secureProtocol: 'TLSv1_2_method',
    ciphers: [
      'ECDHE-RSA-AES128-GCM-SHA256',
      'ECDHE-RSA-AES256-GCM-SHA384',
      'ECDHE-RSA-AES128-SHA256',
      'ECDHE-RSA-AES256-SHA384'
    ].join(':'),
    honorCipherOrder: true
  };
  
  server = https.createServer(sslOptions, app);
  console.log('🔒 HTTPS enabled');
} else {
  server = http.createServer(app);
  if (config.isProduction()) {
    console.warn('⚠️  WARNING: Running in production without HTTPS!');
  }
}

// Start server
server.listen(PORT, config.server.host, () => {
  const protocol = config.server.enableHttps ? 'https' : 'http';
  console.log(`🚀 Secure Dashboard server running on ${protocol}://${config.server.host}:${PORT}`);
  console.log(`🔐 Authentication: ENABLED`);
  console.log(`🛡️  Security headers: ENABLED`);
  console.log(`⚡ Rate limiting: ${config.rateLimiting.maxRequests} requests per ${config.rateLimiting.windowMs/1000/60} minutes`);
  
  if (config.isDevelopment()) {
    console.log(`\n📝 Default admin credentials are in: ADMIN_CREDENTIALS.txt`);
  }
});

// WebSocket server with authentication
const wss = new WebSocketServer({
  server,
  verifyClient: securityMiddleware.authenticateWebSocket
});

// Broadcast function with error handling
const broadcast = (data) => {
  const message = JSON.stringify(data);
  let sent = 0;
  
  wss.clients.forEach((client) => {
    if (client.readyState === 1) {
      try {
        client.send(message);
        sent++;
      } catch (error) {
        console.error('WebSocket broadcast error:', error);
      }
    }
  });
  
  if (config.isDebugMode()) {
    console.log(`Broadcast sent to ${sent} clients`);
  }
};

// WebSocket connections with authentication
wss.on('connection', (ws, req) => {
  const user = req.user;
  console.log(`New WebSocket client connected: ${user.username} from ${req.headers.origin || 'unknown'}`);
  
  // Send initial data
  try {
    const initialData = {
      type: 'initial',
      data: {
        agents: agentMonitor.getAgents(),
        activities: agentMonitor.getRecentActivities(),
        metrics: metricsCollector.getCurrentMetrics(),
        projects: agentMonitor.getProjects(),
        user: {
          username: user.username,
          role: user.role
        }
      }
    };
    ws.send(JSON.stringify(initialData));
  } catch (error) {
    console.error('Error sending initial data:', error);
  }
  
  // Handle client messages
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      
      // Handle different message types
      switch (data.type) {
        case 'ping':
          ws.send(JSON.stringify({ type: 'pong' }));
          break;
        case 'subscribe':
          // Handle subscription to specific events
          ws.subscriptions = data.topics || [];
          break;
        default:
          console.log('Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('WebSocket message error:', error);
    }
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });

  ws.on('close', () => {
    console.log(`WebSocket client disconnected: ${user.username}`);
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

// Start monitoring services
fileWatcher.startWatching();
metricsCollector.startCollecting();
heartbeatMonitor.initialize();

// Session cleanup job
setInterval(() => {
  authService.cleanupExpiredSessions();
}, 60 * 60 * 1000); // Every hour

// Graceful shutdown
const shutdown = () => {
  console.log('\nShutting down gracefully...');
  
  // Stop accepting new connections
  server.close(() => {
    console.log('HTTP server closed');
  });
  
  // Close WebSocket connections
  wss.clients.forEach((client) => {
    client.close(1000, 'Server shutting down');
  });
  
  // Stop services
  fileWatcher.stopWatching();
  metricsCollector.stopCollecting();
  heartbeatMonitor.stop();
  
  // Close database
  db.close();
  
  console.log('Shutdown complete');
  process.exit(0);
};

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  authService.logAudit(null, 'server_error', 'system', null, null, false, error.message);
  shutdown();
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  authService.logAudit(null, 'server_error', 'system', null, null, false, String(reason));
});

export default app;