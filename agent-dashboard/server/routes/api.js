import express from 'express';

export default function createApiRoutes(agentMonitor, db, metricsCollector, jarvisService) {
  const router = express.Router();

  // Jarvis identity confirmation endpoint
  router.get('/jarvis', (req, res) => {
    const response = jarvisService.getJarvisResponse();
    res.json(response);
  });

  // Jarvis query endpoint - for checking if message is asking for Jarvis
  router.post('/jarvis/query', (req, res) => {
    const { message } = req.body;
    
    if (jarvisService.isJarvisQuery(message)) {
      const response = jarvisService.getJarvisResponse();
      res.json({
        isJarvisQuery: true,
        response: response
      });
    } else {
      res.json({
        isJarvisQuery: false
      });
    }
  });

  // Jarvis command endpoint
  router.post('/jarvis/command', async (req, res) => {
    const { command, context } = req.body;
    const result = await jarvisService.handleCommand(command, context);
    res.json(result);
  });

  // Jarvis system status
  router.get('/jarvis/status', (req, res) => {
    const status = jarvisService.getSystemStatus();
    res.json(status);
  });

  // Dashboard overview
  router.get('/dashboard', async (req, res) => {
    try {
      const agents = agentMonitor.getAgents() || [];
      const activities = await db.getRecentActivities(50) || [];
      const metrics = metricsCollector.getCurrentMetrics() || {
        timestamp: new Date(),
        agents: { total: 0, online: 0, working: 0, idle: 0, error: 0 },
        activities: { recent: 0, total: 0, successRate: 100 },
        queues: { incoming: 0, processing: 0, completed: 0 },
        performance: { avgResponseTime: 0, throughput: 0 }
      };
      const projects = agentMonitor.getProjects() || [];
      const communications = await db.getRecentCommunications(20) || [];
      const performance = await db.getAgentPerformanceStats() || [];

      res.json({
        agents,
        activities,
        metrics,
        projects,
        communications,
        performance,
        orchestrator: jarvisService.getSystemStatus() // Include Jarvis status
      });
    } catch (error) {
      console.error('Dashboard API error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  // Agents endpoints
  router.get('/agents', (req, res) => {
    const agents = agentMonitor.getAgents();
    res.json(agents);
  });

  router.get('/agents/:id', (req, res) => {
    const agent = agentMonitor.getAgent(req.params.id);
    if (!agent) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    res.json(agent);
  });

  router.get('/agents/:id/metrics', async (req, res) => {
    const hours = parseInt(req.query.hours) || 24;
    const metrics = await metricsCollector.getAgentMetrics(req.params.id, hours);
    res.json(metrics);
  });

  // Activities endpoints
  router.get('/activities', async (req, res) => {
    const limit = parseInt(req.query.limit) || 100;
    const activities = await db.getRecentActivities(limit);
    res.json(activities);
  });

  router.post('/activities', (req, res) => {
    const { agentId, activity } = req.body;
    const activityId = agentMonitor.startActivity(agentId, activity);
    res.json({ activityId });
  });

  router.put('/activities/:id/complete', (req, res) => {
    const { result } = req.body;
    agentMonitor.completeActivity(req.params.id, result);
    res.json({ success: true });
  });

  // Metrics endpoints
  router.get('/metrics', async (req, res) => {
    const hours = parseInt(req.query.hours) || 24;
    const metrics = await metricsCollector.getHistoricalMetrics(hours);
    res.json(metrics);
  });

  router.get('/metrics/current', (req, res) => {
    const metrics = metricsCollector.getCurrentMetrics();
    res.json(metrics);
  });

  router.get('/metrics/distribution', async (req, res) => {
    const distribution = await db.getActivityDistribution();
    res.json(distribution);
  });

  // Communications endpoints
  router.get('/communications', async (req, res) => {
    const limit = parseInt(req.query.limit) || 50;
    const communications = await db.getRecentCommunications(limit);
    res.json(communications);
  });

  router.post('/communications', async (req, res) => {
    const comm = req.body;
    await db.recordCommunication(comm);
    res.json({ success: true });
  });

  // Projects endpoints
  router.get('/projects', (req, res) => {
    const projects = agentMonitor.getProjects();
    res.json(projects);
  });

  // Health check
  router.get('/health', (req, res) => {
    res.json({ 
      status: 'healthy', 
      timestamp: new Date(),
      uptime: process.uptime(),
      jarvis: jarvisService.isInitialized ? 'operational' : 'initializing'
    });
  });

  return router;
}