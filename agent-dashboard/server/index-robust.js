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
import apiRoutes from './routes/api.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class RobustDashboardServer {
  constructor() {
    this.app = express();
    this.PORT = process.env.PORT || 3001;
    this.server = null;
    this.wss = null;
    this.services = {};
    this.isShuttingDown = false;
    this.restartCount = 0;
    this.maxRestarts = 5;
    
    this.setupErrorHandling();
    this.initializeServices();
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupErrorHandling() {
    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      this.handleError(error, 'uncaughtException');
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled Rejection at:', promise, 'reason:', reason);
      this.handleError(reason, 'unhandledRejection');
    });

    // Handle SIGTERM (graceful shutdown)
    process.on('SIGTERM', () => {
      console.log('SIGTERM received, shutting down gracefully...');
      this.gracefulShutdown();
    });

    // Handle SIGINT (Ctrl+C)
    process.on('SIGINT', () => {
      console.log('SIGINT received, shutting down gracefully...');
      this.gracefulShutdown();
    });
  }

  async initializeServices() {
    try {
      console.log('Initializing services...');
      
      // Initialize database with retry logic
      this.services.db = new DatabaseService();
      await this.retryOperation(() => this.services.db.initialize?.(), 'Database');
      
      // Initialize other services
      this.services.agentMonitor = new AgentMonitor(this.services.db);
      this.services.fileWatcher = new FileSystemWatcher(this.services.agentMonitor);
      this.services.metricsCollector = new MetricsCollector(this.services.db, this.services.agentMonitor);
      this.services.heartbeatMonitor = new HeartbeatMonitor(this.services.agentMonitor);
      
      console.log('✓ All services initialized');
    } catch (error) {
      console.error('Failed to initialize services:', error);
      throw error;
    }
  }

  async retryOperation(operation, name, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        if (operation) {
          await operation();
        }
        console.log(`✓ ${name} initialized`);
        return;
      } catch (error) {
        console.error(`Attempt ${i + 1} failed for ${name}:`, error.message);
        if (i === maxRetries - 1) throw error;
        await this.delay(1000 * (i + 1)); // Exponential backoff
      }
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  setupMiddleware() {
    // Request timeout middleware
    this.app.use((req, res, next) => {
      res.setTimeout(30000, () => {
        console.error(`Request timeout: ${req.method} ${req.url}`);
        if (!res.headersSent) {
          res.status(408).json({ error: 'Request timeout' });
        }
      });
      next();
    });

    // CORS with proper error handling
    this.app.use(cors({
      origin: true,
      credentials: true,
      optionsSuccessStatus: 200
    }));

    // JSON parsing with size limit and error handling
    this.app.use(express.json({ 
      limit: '10mb',
      strict: true
    }));

    // Global error handler for JSON parsing
    this.app.use((error, req, res, next) => {
      if (error instanceof SyntaxError && error.status === 400 && 'body' in error) {
        console.error('Bad JSON:', error.message);
        return res.status(400).json({ error: 'Invalid JSON format' });
      }
      next(error);
    });

    // Request logging
    this.app.use((req, res, next) => {
      const start = Date.now();
      res.on('finish', () => {
        const duration = Date.now() - start;
        if (duration > 5000) { // Log slow requests
          console.warn(`Slow request: ${req.method} ${req.url} - ${duration}ms`);
        }
      });
      next();
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        restartCount: this.restartCount
      });
    });

    // API routes with error handling
    this.app.use('/api', (req, res, next) => {
      try {
        apiRoutes(this.services.agentMonitor, this.services.db, this.services.metricsCollector)(req, res, next);
      } catch (error) {
        console.error('API route error:', error);
        if (!res.headersSent) {
          res.status(500).json({ error: 'Internal server error' });
        }
      }
    });

    // Serve static files in production
    if (process.env.NODE_ENV === 'production') {
      this.app.use(express.static(path.join(__dirname, '../client/dist')));
      
      this.app.get('*', (req, res) => {
        res.sendFile(path.join(__dirname, '../client/dist/index.html'));
      });
    }

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({ error: 'Endpoint not found' });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      console.error('Global error handler:', error);
      
      if (!res.headersSent) {
        res.status(500).json({ 
          error: 'Internal server error',
          timestamp: new Date().toISOString()
        });
      }
    });
  }

  async startServer() {
    return new Promise((resolve, reject) => {
      try {
        this.server = this.app.listen(this.PORT, () => {
          console.log(`🚀 Robust Dashboard server running on http://localhost:${this.PORT}`);
          this.setupWebSocket();
          this.startServices();
          resolve();
        });

        this.server.on('error', (error) => {
          if (error.code === 'EADDRINUSE') {
            console.error(`Port ${this.PORT} is already in use`);
            reject(new Error(`Port ${this.PORT} is already in use`));
          } else {
            console.error('Server error:', error);
            reject(error);
          }
        });

        // Set server timeouts
        this.server.timeout = 30000; // 30 seconds
        this.server.keepAliveTimeout = 5000;
        this.server.headersTimeout = 6000;

      } catch (error) {
        reject(error);
      }
    });
  }

  setupWebSocket() {
    this.wss = new WebSocketServer({ 
      server: this.server,
      perMessageDeflate: false // Disable compression for stability
    });

    this.wss.on('connection', (ws, req) => {
      console.log('WebSocket client connected from:', req.headers.origin || 'unknown');
      
      // Send initial data with error handling
      try {
        const initialData = {
          type: 'initial',
          data: {
            agents: this.services.agentMonitor.getAgents() || [],
            activities: [],
            metrics: this.services.metricsCollector.getCurrentMetrics() || {},
            projects: this.services.agentMonitor.getProjects() || []
          }
        };
        ws.send(JSON.stringify(initialData));
      } catch (error) {
        console.error('Error sending initial WebSocket data:', error);
      }

      ws.on('error', (error) => {
        console.error('WebSocket error:', error);
      });

      ws.on('close', () => {
        console.log('WebSocket client disconnected');
      });

      // Ping/pong for connection health
      const pingInterval = setInterval(() => {
        if (ws.readyState === ws.OPEN) {
          ws.ping();
        } else {
          clearInterval(pingInterval);
        }
      }, 30000);
    });

    // Setup event listeners for real-time updates
    this.setupEventListeners();
  }

  setupEventListeners() {
    const broadcast = (data) => {
      if (!this.wss) return;
      
      const message = JSON.stringify(data);
      this.wss.clients.forEach((client) => {
        if (client.readyState === 1) {
          try {
            client.send(message);
          } catch (error) {
            console.error('WebSocket broadcast error:', error);
          }
        }
      });
    };

    // Set up event listeners with error handling
    if (this.services.agentMonitor) {
      this.services.agentMonitor.on('update', (data) => {
        try {
          broadcast({ type: 'agent-update', data });
        } catch (error) {
          console.error('Agent update broadcast error:', error);
        }
      });
    }

    if (this.services.fileWatcher) {
      this.services.fileWatcher.on('file-change', (data) => {
        try {
          broadcast({ type: 'file-change', data });
        } catch (error) {
          console.error('File change broadcast error:', error);
        }
      });
    }

    if (this.services.metricsCollector) {
      this.services.metricsCollector.on('metrics-update', (data) => {
        try {
          broadcast({ type: 'metrics-update', data });
        } catch (error) {
          console.error('Metrics update broadcast error:', error);
        }
      });
    }
  }

  startServices() {
    try {
      if (this.services.fileWatcher) {
        this.services.fileWatcher.startWatching();
      }
      if (this.services.metricsCollector) {
        this.services.metricsCollector.startCollecting();
      }
      if (this.services.heartbeatMonitor) {
        this.services.heartbeatMonitor.initialize();
      }
      console.log('✓ All services started');
    } catch (error) {
      console.error('Error starting services:', error);
    }
  }

  handleError(error, source) {
    console.error(`Error from ${source}:`, error);
    
    // Don't restart for certain types of errors
    if (this.isShuttingDown) return;
    
    // Increment restart count
    this.restartCount++;
    
    if (this.restartCount >= this.maxRestarts) {
      console.error(`Max restarts (${this.maxRestarts}) reached. Shutting down.`);
      process.exit(1);
    }
    
    // For critical errors, attempt graceful restart
    if (source === 'uncaughtException') {
      console.log('Attempting graceful restart...');
      setTimeout(() => {
        this.gracefulShutdown();
      }, 1000);
    }
  }

  async gracefulShutdown() {
    if (this.isShuttingDown) return;
    this.isShuttingDown = true;
    
    console.log('Starting graceful shutdown...');
    
    try {
      // Stop services
      if (this.services.fileWatcher) {
        this.services.fileWatcher.stopWatching();
      }
      if (this.services.metricsCollector) {
        this.services.metricsCollector.stopCollecting();
      }
      
      // Close WebSocket server
      if (this.wss) {
        this.wss.close();
      }
      
      // Close database
      if (this.services.db) {
        this.services.db.close();
      }
      
      // Close HTTP server
      if (this.server) {
        this.server.close(() => {
          console.log('Server closed gracefully');
          process.exit(0);
        });
        
        // Force close after 10 seconds
        setTimeout(() => {
          console.log('Force closing server');
          process.exit(1);
        }, 10000);
      } else {
        process.exit(0);
      }
    } catch (error) {
      console.error('Error during shutdown:', error);
      process.exit(1);
    }
  }
}

// Start the robust server
async function main() {
  const server = new RobustDashboardServer();
  
  try {
    await server.startServer();
    console.log('✓ Robust dashboard server started successfully');
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Handle module being run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export default RobustDashboardServer;