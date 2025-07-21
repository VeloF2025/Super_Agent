/**
 * Database Service Tests
 * Comprehensive testing for database operations
 */

import { jest } from '@jest/globals';
import { DatabaseService } from '../../server/services/database.js';

describe('DatabaseService', () => {
  let db;

  beforeEach(() => {
    // Use in-memory database for tests
    db = new DatabaseService(':memory:');
  });

  afterEach(() => {
    if (db) {
      db.close();
    }
  });

  describe('Initialization', () => {
    test('should create all required tables', () => {
      const tables = db.db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
      const tableNames = tables.map(t => t.name);

      expect(tableNames).toContain('agents');
      expect(tableNames).toContain('activities');
      expect(tableNames).toContain('metrics');
      expect(tableNames).toContain('communications');
      expect(tableNames).toContain('projects');
    });

    test('should create all required indexes', () => {
      const indexes = db.db.prepare("SELECT name FROM sqlite_master WHERE type='index'").all();
      const indexNames = indexes.map(i => i.name);

      expect(indexNames).toContain('idx_activities_agent');
      expect(indexNames).toContain('idx_activities_timestamp');
      expect(indexNames).toContain('idx_metrics_timestamp');
      expect(indexNames).toContain('idx_communications_timestamp');
    });
  });

  describe('Agent Operations', () => {
    test('should insert new agent', () => {
      const agent = global.testUtils.createTestAgent();
      const result = db.upsertAgent(agent);

      expect(result.changes).toBe(1);
      
      const saved = db.db.prepare('SELECT * FROM agents WHERE id = ?').get(agent.id);
      expect(saved).toBeDefined();
      expect(saved.name).toBe(agent.name);
      expect(saved.type).toBe(agent.type);
      expect(JSON.parse(saved.capabilities)).toEqual(agent.capabilities);
    });

    test('should update existing agent', () => {
      const agent = global.testUtils.createTestAgent();
      
      // Insert agent
      db.upsertAgent(agent);
      
      // Update agent
      agent.status = 'offline';
      agent.location = '/new/location';
      const result = db.upsertAgent(agent);

      expect(result.changes).toBe(1);
      
      const updated = db.db.prepare('SELECT * FROM agents WHERE id = ?').get(agent.id);
      expect(updated.status).toBe('offline');
      expect(updated.location).toBe('/new/location');
    });

    test('should retrieve all agents', () => {
      const agent1 = global.testUtils.createTestAgent({ id: 'agent-1', name: 'Agent One' });
      const agent2 = global.testUtils.createTestAgent({ id: 'agent-2', name: 'Agent Two' });
      
      db.upsertAgent(agent1);
      db.upsertAgent(agent2);
      
      const agents = db.getAgents();
      
      expect(agents).toHaveLength(2);
      expect(agents[0].name).toBe('Agent One');
      expect(agents[1].name).toBe('Agent Two');
    });

    test('should handle invalid agent data', () => {
      expect(() => {
        db.upsertAgent(null);
      }).toThrow();

      expect(() => {
        db.upsertAgent({ invalid: 'data' });
      }).toThrow();
    });
  });

  describe('Activity Operations', () => {
    beforeEach(() => {
      // Create test agent first
      const agent = global.testUtils.createTestAgent();
      db.upsertAgent(agent);
    });

    test('should record new activity', () => {
      const activity = global.testUtils.createTestActivity();
      const result = db.recordActivity(activity);

      expect(result.changes).toBe(1);
      expect(result.lastInsertRowid).toBeDefined();
    });

    test('should complete activity', () => {
      const activity = global.testUtils.createTestActivity();
      const { lastInsertRowid } = db.recordActivity(activity);
      
      const result = db.completeActivity(lastInsertRowid, 'Success', 1000);
      
      expect(result.changes).toBe(1);
      
      const completed = db.db.prepare('SELECT * FROM activities WHERE id = ?').get(lastInsertRowid);
      expect(completed.status).toBe('completed');
      expect(completed.result).toBe('Success');
      expect(completed.duration_ms).toBe(1000);
      expect(completed.completed_at).toBeDefined();
    });

    test('should retrieve recent activities with agent names', () => {
      const activity1 = global.testUtils.createTestActivity({ description: 'Activity 1' });
      const activity2 = global.testUtils.createTestActivity({ description: 'Activity 2' });
      
      db.recordActivity(activity1);
      db.recordActivity(activity2);
      
      const activities = db.getRecentActivities(10);
      
      expect(activities).toHaveLength(2);
      expect(activities[0].agent_name).toBe('Test Agent');
      expect(activities[0].description).toBe('Activity 2'); // Most recent first
    });
  });

  describe('Metrics Operations', () => {
    test('should record metric', () => {
      const metric = {
        type: 'cpu_usage',
        agentId: 'test-agent-1',
        value: 75.5,
        metadata: { unit: 'percent' }
      };
      
      const result = db.recordMetric(metric);
      
      expect(result.changes).toBe(1);
      
      const saved = db.db.prepare('SELECT * FROM metrics WHERE id = ?').get(result.lastInsertRowid);
      expect(saved.metric_type).toBe('cpu_usage');
      expect(saved.value).toBe(75.5);
      expect(JSON.parse(saved.metadata)).toEqual({ unit: 'percent' });
    });

    test('should retrieve metrics by time range', () => {
      const now = new Date();
      const hourAgo = new Date(now - 60 * 60 * 1000);
      const twoHoursAgo = new Date(now - 2 * 60 * 60 * 1000);
      
      // Record metrics at different times
      db.recordMetric({ type: 'memory', value: 50, agentId: 'agent-1' });
      
      // Manually update timestamp for testing
      db.db.prepare('UPDATE metrics SET timestamp = ? WHERE id = 1').run(twoHoursAgo.toISOString());
      
      db.recordMetric({ type: 'memory', value: 60, agentId: 'agent-1' });
      
      const metrics = db.getMetrics(hourAgo.toISOString());
      
      expect(metrics).toHaveLength(1);
      expect(metrics[0].value).toBe(60);
    });

    test('should filter metrics by agent', () => {
      db.recordMetric({ type: 'cpu', value: 50, agentId: 'agent-1' });
      db.recordMetric({ type: 'cpu', value: 60, agentId: 'agent-2' });
      db.recordMetric({ type: 'cpu', value: 70, agentId: 'agent-1' });
      
      const metrics = db.getMetrics(new Date(0).toISOString(), 'agent-1');
      
      expect(metrics).toHaveLength(2);
      expect(metrics.every(m => m.agent_id === 'agent-1')).toBe(true);
    });
  });

  describe('Communication Operations', () => {
    test('should record communication', () => {
      const comm = {
        from_agent: 'agent-1',
        to_agent: 'agent-2',
        message_type: 'task_assignment',
        priority: 'high',
        content: 'Test message content'
      };
      
      const result = db.recordCommunication(comm);
      
      expect(result.changes).toBe(1);
      
      const saved = db.db.prepare('SELECT * FROM communications WHERE id = ?').get(result.lastInsertRowid);
      expect(saved.from_agent).toBe('agent-1');
      expect(saved.to_agent).toBe('agent-2');
      expect(saved.status).toBe('sent');
    });

    test('should retrieve recent communications', () => {
      for (let i = 0; i < 10; i++) {
        db.recordCommunication({
          from_agent: `agent-${i % 2}`,
          to_agent: `agent-${(i + 1) % 2}`,
          message_type: 'test',
          priority: 'medium',
          content: `Message ${i}`
        });
      }
      
      const comms = db.getRecentCommunications(5);
      
      expect(comms).toHaveLength(5);
      expect(comms[0].content).toBe('Message 9'); // Most recent first
    });
  });

  describe('Analytics Queries', () => {
    beforeEach(() => {
      // Set up test data
      const agent1 = global.testUtils.createTestAgent({ id: 'agent-1', name: 'Agent One' });
      const agent2 = global.testUtils.createTestAgent({ id: 'agent-2', name: 'Agent Two' });
      
      db.upsertAgent(agent1);
      db.upsertAgent(agent2);
      
      // Add activities
      const act1 = db.recordActivity({ agent_id: 'agent-1', activity_type: 'coding', status: 'pending' });
      const act2 = db.recordActivity({ agent_id: 'agent-1', activity_type: 'testing', status: 'pending' });
      const act3 = db.recordActivity({ agent_id: 'agent-2', activity_type: 'review', status: 'pending' });
      
      // Complete some activities
      db.completeActivity(act1.lastInsertRowid, 'Success', 1000);
      db.completeActivity(act2.lastInsertRowid, 'Success', 2000);
    });

    test('should get agent performance stats', () => {
      const stats = db.getAgentPerformanceStats();
      
      expect(stats).toHaveLength(2);
      
      const agent1Stats = stats.find(s => s.id === 'agent-1');
      expect(agent1Stats.total_activities).toBe(2);
      expect(agent1Stats.completed_activities).toBe(2);
      expect(agent1Stats.avg_duration_ms).toBe(1500);
      
      const agent2Stats = stats.find(s => s.id === 'agent-2');
      expect(agent2Stats.total_activities).toBe(1);
      expect(agent2Stats.completed_activities).toBe(0);
    });

    test('should get activity distribution', () => {
      const distribution = db.getActivityDistribution();
      
      expect(distribution).toHaveLength(3);
      
      const codingStats = distribution.find(d => d.activity_type === 'coding');
      expect(codingStats.count).toBe(1);
      expect(codingStats.avg_duration).toBe(1000);
    });
  });

  describe('Error Handling', () => {
    test('should handle database errors gracefully', () => {
      // Close database to simulate error
      db.close();
      
      expect(() => {
        db.getAgents();
      }).toThrow();
    });

    test('should validate data types', () => {
      const metric = {
        type: 'test',
        value: 'not-a-number', // Should be numeric
        agentId: 'test'
      };
      
      // This should not throw due to SQLite's flexible typing,
      // but the value should be stored as string
      const result = db.recordMetric(metric);
      expect(result.changes).toBe(1);
      
      const saved = db.db.prepare('SELECT * FROM metrics WHERE id = ?').get(result.lastInsertRowid);
      expect(typeof saved.value).toBe('string');
    });
  });

  describe('Transaction Safety', () => {
    test('should rollback on error', () => {
      const agent = global.testUtils.createTestAgent();
      
      // Start transaction
      const insertAgent = db.db.prepare('INSERT INTO agents (id, name, type) VALUES (?, ?, ?)');
      const insertActivity = db.db.prepare('INSERT INTO activities (agent_id, activity_type) VALUES (?, ?)');
      
      const transaction = db.db.transaction(() => {
        insertAgent.run(agent.id, agent.name, agent.type);
        // This should fail due to foreign key constraint
        insertActivity.run('non-existent-agent', 'test');
      });
      
      expect(() => transaction()).toThrow();
      
      // Verify agent was not inserted due to rollback
      const agents = db.getAgents();
      expect(agents).toHaveLength(0);
    });
  });
});