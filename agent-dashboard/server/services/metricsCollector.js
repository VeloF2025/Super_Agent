import { EventEmitter } from 'events';
import cron from 'node-cron';

export class MetricsCollector extends EventEmitter {
  constructor(db, agentMonitor) {
    super();
    this.db = db;
    this.agentMonitor = agentMonitor;
    this.metrics = {
      timestamp: new Date(),
      agents: {
        total: 0,
        online: 0,
        working: 0,
        idle: 0,
        error: 0
      },
      activities: {
        recent: 0,
        total: 0,
        successRate: 100
      },
      queues: {
        incoming: 0,
        processing: 0,
        completed: 0
      },
      performance: {
        avgResponseTime: 0,
        throughput: 0
      }
    };
    this.collectInterval = null;
  }

  startCollecting() {
    // Collect metrics every 5 seconds
    this.collectInterval = setInterval(() => {
      this.collectMetrics();
    }, 5000);

    // Collect detailed metrics every minute
    cron.schedule('* * * * *', () => {
      this.collectDetailedMetrics();
    });

    // Initial collection
    this.collectMetrics();
  }

  async collectMetrics() {
    const timestamp = new Date();
    
    // Agent metrics
    const agents = this.agentMonitor.getAgents();
    const agentStats = {
      total: agents.length,
      online: agents.filter(a => a.status !== 'offline').length,
      working: agents.filter(a => a.status === 'working').length,
      idle: agents.filter(a => a.status === 'idle').length,
      error: agents.filter(a => a.status === 'error').length
    };

    // Activity metrics
    const recentActivities = await this.db.getRecentActivities(100);
    const last5Minutes = new Date(Date.now() - 5 * 60 * 1000);
    const recentCount = recentActivities.filter(a => 
      new Date(a.started_at) > last5Minutes
    ).length;

    // Calculate success rate
    const completedActivities = recentActivities.filter(a => a.status === 'completed');
    const successRate = completedActivities.length > 0
      ? (completedActivities.filter(a => {
          try {
            const result = JSON.parse(a.result || '{}');
            return result.success !== false;
          } catch {
            return true;
          }
        }).length / completedActivities.length) * 100
      : 100;

    // Queue metrics (simulated for now)
    const queueStats = {
      incoming: Math.floor(Math.random() * 10),
      processing: agents.filter(a => a.status === 'working').length,
      completed: Math.floor(Math.random() * 50)
    };

    // Performance metrics
    const avgResponseTime = completedActivities.length > 0
      ? completedActivities.reduce((acc, a) => acc + (a.duration_ms || 0), 0) / completedActivities.length
      : 0;

    this.metrics = {
      timestamp,
      agents: agentStats,
      activities: {
        recent: recentCount,
        total: recentActivities.length,
        successRate: Math.round(successRate)
      },
      queues: queueStats,
      performance: {
        avgResponseTime: Math.round(avgResponseTime),
        throughput: recentCount / 5 // activities per minute
      }
    };

    // Store in database
    this.db.recordMetric({
      type: 'system_overview',
      value: JSON.stringify(this.metrics),
      metadata: { source: 'collector' }
    });

    // Emit update
    this.emit('metrics-update', this.metrics);
  }

  async collectDetailedMetrics() {
    // Collect per-agent metrics
    const agentPerformance = await this.db.getAgentPerformanceStats();
    
    for (const stats of agentPerformance) {
      // Success rate
      const successRate = stats.total_activities > 0
        ? (stats.completed_activities / stats.total_activities) * 100
        : 0;
      
      this.db.recordMetric({
        type: 'agent_success_rate',
        agentId: stats.id,
        value: successRate,
        metadata: {
          total: stats.total_activities,
          completed: stats.completed_activities
        }
      });

      // Average response time
      if (stats.avg_duration_ms) {
        this.db.recordMetric({
          type: 'agent_response_time',
          agentId: stats.id,
          value: stats.avg_duration_ms,
          metadata: { unit: 'ms' }
        });
      }
    }

    // Activity distribution
    const distribution = await this.db.getActivityDistribution();
    this.db.recordMetric({
      type: 'activity_distribution',
      value: JSON.stringify(distribution),
      metadata: { period: '24h' }
    });
  }

  getCurrentMetrics() {
    return this.metrics;
  }

  async getHistoricalMetrics(hours = 24) {
    const since = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
    return this.db.getMetrics(since);
  }

  async getAgentMetrics(agentId, hours = 24) {
    const since = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
    return this.db.getMetrics(since, agentId);
  }

  stopCollecting() {
    if (this.collectInterval) {
      clearInterval(this.collectInterval);
      this.collectInterval = null;
    }
  }
}