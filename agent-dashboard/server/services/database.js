import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class DatabaseService {
  constructor() {
    const dataDir = path.join(__dirname, '../../data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    
    const dbPath = path.join(dataDir, 'dashboard.db');
    this.db = new Database(dbPath);
    this.initializeSchema();
  }

  initializeSchema() {
    // Agents table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT DEFAULT 'offline',
        capabilities TEXT,
        location TEXT,
        project TEXT,
        path TEXT,
        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Activities table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        activity_type TEXT NOT NULL,
        description TEXT,
        status TEXT,
        priority TEXT,
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        duration_ms INTEGER,
        result TEXT,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
      )
    `);

    // Metrics table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        metric_type TEXT NOT NULL,
        agent_id TEXT,
        value REAL,
        metadata TEXT
      )
    `);

    // Communication logs table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS communications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_agent TEXT,
        to_agent TEXT,
        message_type TEXT,
        priority TEXT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'sent'
      )
    `);

    // Projects table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        path TEXT,
        status TEXT DEFAULT 'active',
        agent_assignments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create indexes
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_activities_agent ON activities(agent_id);
      CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(started_at);
      CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
      CREATE INDEX IF NOT EXISTS idx_communications_timestamp ON communications(timestamp);
    `);
  }

  // Agent operations
  upsertAgent(agent) {
    const stmt = this.db.prepare(`
      INSERT INTO agents (id, name, type, status, capabilities, location, project, path, last_seen)
      VALUES (@id, @name, @type, @status, @capabilities, @location, @project, @path, @last_seen)
      ON CONFLICT(id) DO UPDATE SET
        status = @status,
        location = @location,
        project = @project,
        path = @path,
        last_seen = @last_seen
    `);
    
    return stmt.run({
      id: agent.id,
      name: agent.name,
      type: agent.type,
      status: agent.status || 'offline',
      capabilities: JSON.stringify(agent.capabilities || []),
      location: agent.location || null,
      project: agent.project || null,
      path: agent.path || null,
      last_seen: new Date().toISOString()
    });
  }

  getAgents() {
    return this.db.prepare('SELECT * FROM agents ORDER BY name').all();
  }

  // Activity operations
  recordActivity(activity) {
    const stmt = this.db.prepare(`
      INSERT INTO activities (agent_id, activity_type, description, status, priority)
      VALUES (@agent_id, @activity_type, @description, @status, @priority)
    `);
    
    return stmt.run(activity);
  }

  completeActivity(activityId, result, duration) {
    const stmt = this.db.prepare(`
      UPDATE activities 
      SET status = 'completed', 
          completed_at = CURRENT_TIMESTAMP,
          duration_ms = @duration,
          result = @result
      WHERE id = @id
    `);
    
    return stmt.run({ id: activityId, result, duration });
  }

  getRecentActivities(limit = 100) {
    return this.db.prepare(`
      SELECT a.*, ag.name as agent_name 
      FROM activities a
      LEFT JOIN agents ag ON a.agent_id = ag.id
      ORDER BY a.started_at DESC
      LIMIT ?
    `).all(limit);
  }

  // Metrics operations
  recordMetric(metric) {
    const stmt = this.db.prepare(`
      INSERT INTO metrics (metric_type, agent_id, value, metadata)
      VALUES (@metric_type, @agent_id, @value, @metadata)
    `);
    
    return stmt.run({
      metric_type: metric.type,
      agent_id: metric.agentId,
      value: metric.value,
      metadata: JSON.stringify(metric.metadata || {})
    });
  }

  getMetrics(since, agentId = null) {
    let query = 'SELECT * FROM metrics WHERE timestamp >= @since';
    const params = { since };
    
    if (agentId) {
      query += ' AND agent_id = @agent_id';
      params.agent_id = agentId;
    }
    
    query += ' ORDER BY timestamp DESC';
    
    return this.db.prepare(query).all(params);
  }

  // Communication operations
  recordCommunication(comm) {
    const stmt = this.db.prepare(`
      INSERT INTO communications (from_agent, to_agent, message_type, priority, content)
      VALUES (@from_agent, @to_agent, @message_type, @priority, @content)
    `);
    
    return stmt.run(comm);
  }

  getRecentCommunications(limit = 50) {
    return this.db.prepare(`
      SELECT * FROM communications
      ORDER BY timestamp DESC
      LIMIT ?
    `).all(limit);
  }

  // Analytics queries
  getAgentPerformanceStats() {
    return this.db.prepare(`
      SELECT 
        a.id,
        a.name,
        COUNT(act.id) as total_activities,
        SUM(CASE WHEN act.status = 'completed' THEN 1 ELSE 0 END) as completed_activities,
        AVG(act.duration_ms) as avg_duration_ms,
        MAX(act.started_at) as last_activity
      FROM agents a
      LEFT JOIN activities act ON a.id = act.agent_id
      GROUP BY a.id, a.name
    `).all();
  }

  getActivityDistribution() {
    return this.db.prepare(`
      SELECT 
        activity_type,
        COUNT(*) as count,
        AVG(duration_ms) as avg_duration
      FROM activities
      WHERE started_at >= datetime('now', '-24 hours')
      GROUP BY activity_type
    `).all();
  }

  close() {
    this.db.close();
  }
}