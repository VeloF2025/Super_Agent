import { useState } from 'react'
import { motion } from 'framer-motion'
import { AreaChart, Area, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Activity, Bot, CheckCircle, AlertCircle, Clock, Zap } from 'lucide-react'
import { DashboardData } from '../types'
import MetricCard from './MetricCard'
import ActivityFeed from './ActivityFeed'
import ProjectFilter from './ProjectFilter'
import ActivityTimeline from './ActivityTimeline'

interface DashboardProps {
  data: DashboardData | null
}

export default function Dashboard({ data }: DashboardProps) {
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'feed' | 'timeline'>('feed')
  
  if (!data) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-neon-blue mx-auto"></div>
        <p className="mt-4 text-gray-400">Loading dashboard data...</p>
      </div>
    </div>
  )

  const { metrics, agents, activities, performance = [] } = data
  
  // Filter agents by selected project
  const filteredAgents = selectedProject 
    ? agents.filter(agent => agent.project === selectedProject || agent.location === selectedProject)
    : agents
    
  // Get unique projects
  const allProjects = [...new Set(agents.map(a => a.project || a.location).filter(Boolean))] as string[]

  // Prepare chart data
  const agentStatusData = metrics ? [
    { name: 'Online', value: metrics.agents.online, color: '#10b981' },
    { name: 'Working', value: metrics.agents.working, color: '#3b82f6' },
    { name: 'Idle', value: metrics.agents.idle, color: '#f59e0b' },
    { name: 'Error', value: metrics.agents.error, color: '#ef4444' },
  ].filter(d => d.value > 0) : []

  const performanceData = performance.map(p => ({
    name: p.name.split(' ')[0],
    activities: p.total_activities,
    avgTime: Math.round(p.avg_duration_ms / 1000),
  }))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-neon-blue to-neon-purple mb-2">
          System Overview
        </h2>
        <p className="text-gray-400">Real-time monitoring of OA and all agent activities</p>
      </div>
      
      {/* Project Filter */}
      {allProjects.length > 0 && (
        <ProjectFilter 
          projects={allProjects}
          selectedProject={selectedProject}
          onProjectSelect={setSelectedProject}
        />
      )}

      {/* Metrics Grid */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title={selectedProject ? `${selectedProject} Agents` : "Total Agents"}
            value={filteredAgents.length}
            icon={Bot}
            trend={`${filteredAgents.filter(a => a.status !== 'offline').length} online`}
            color="blue"
          />
          <MetricCard
            title="Active Tasks"
            value={metrics.activities.recent}
            icon={Activity}
            trend={`${metrics.activities.successRate}% success`}
            color="green"
          />
          <MetricCard
            title="Queue Size"
            value={metrics.queues.incoming + metrics.queues.processing}
            icon={Clock}
            trend={`${metrics.queues.processing} processing`}
            color="yellow"
          />
          <MetricCard
            title="Avg Response"
            value={`${metrics.performance.avgResponseTime}ms`}
            icon={Zap}
            trend={`${metrics.performance.throughput}/min`}
            color="purple"
          />
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gray-900/50 backdrop-blur-md rounded-xl border border-gray-800 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Agent Status</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={agentStatusData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {agentStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(17, 24, 39, 0.9)', 
                  border: '1px solid rgba(75, 85, 99, 0.3)',
                  borderRadius: '8px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {agentStatusData.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-gray-400">{item.name}</span>
                </div>
                <span className="text-gray-300">{item.value}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Performance Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gray-900/50 backdrop-blur-md rounded-xl border border-gray-800 p-6 lg:col-span-2"
        >
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Agent Performance</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(75, 85, 99, 0.3)" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(17, 24, 39, 0.9)', 
                  border: '1px solid rgba(75, 85, 99, 0.3)',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="activities" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              <Bar dataKey="avgTime" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Activity Feed */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gray-900/50 backdrop-blur-md rounded-xl border border-gray-800 p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-200">Recent Activities</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('feed')}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'feed' 
                  ? 'bg-neon-blue/20 text-neon-blue border border-neon-blue/30' 
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Feed
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'timeline' 
                  ? 'bg-neon-blue/20 text-neon-blue border border-neon-blue/30' 
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Timeline
            </button>
          </div>
        </div>
        
        {viewMode === 'feed' ? (
          <ActivityFeed activities={activities.slice(0, 10)} />
        ) : (
          <ActivityTimeline 
            activities={activities} 
            agents={filteredAgents}
            showAgentFilter={!selectedProject}
          />
        )}
      </motion.div>
    </div>
  )
}