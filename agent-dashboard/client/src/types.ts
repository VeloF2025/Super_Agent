export interface Agent {
  id: string
  name: string
  type: string
  status: 'online' | 'idle' | 'working' | 'error' | 'offline'
  capabilities: string[]
  last_seen: string
  currentActivity?: string
  location?: string
  project?: string
  path?: string
}

export interface Activity {
  id: string | number
  agent_id: string
  agent_name?: string
  activity_type: string
  description: string
  status: 'in_progress' | 'completed' | 'failed'
  priority: 'low' | 'medium' | 'high' | 'critical'
  started_at: string
  completed_at?: string
  duration_ms?: number
  result?: string
}

export interface Metrics {
  timestamp: string
  agents: {
    total: number
    online: number
    working: number
    idle: number
    error: number
  }
  activities: {
    recent: number
    total: number
    successRate: number
  }
  queues: {
    incoming: number
    processing: number
    completed: number
  }
  performance: {
    avgResponseTime: number
    throughput: number
  }
}

export interface Communication {
  id: number
  from_agent: string
  to_agent: string
  message_type: string
  priority: string
  content: string
  timestamp: string
  status: string
}

export interface Project {
  id: string
  name: string
  path: string
  status: string
  agents: string[]
  created_at: string
  updated_at: string
}

export interface AgentPerformance {
  id: string
  name: string
  total_activities: number
  completed_activities: number
  avg_duration_ms: number
  last_activity: string
}

export interface DashboardData {
  agents: Agent[]
  activities: Activity[]
  metrics: Metrics
  projects: Project[]
  communications: Communication[]
  performance: AgentPerformance[]
}