import { motion } from 'framer-motion'
import { Agent, Activity } from '../types'
import { Bot, Cpu, Clock, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react'
import ActivityFeed from './ActivityFeed'
import clsx from 'clsx'

interface AgentDetailsProps {
  agent: Agent
  activities: Activity[]
}

export default function AgentDetails({ agent, activities }: AgentDetailsProps) {
  const agentActivities = activities.filter(a => a.agent_id === agent.id)
  const completedActivities = agentActivities.filter(a => a.status === 'completed')
  const successRate = completedActivities.length > 0
    ? Math.round((completedActivities.filter(a => {
        try {
          const result = JSON.parse(a.result || '{}')
          return result.success !== false
        } catch {
          return true
        }
      }).length / completedActivities.length) * 100)
    : 100

  const avgDuration = completedActivities.length > 0
    ? Math.round(completedActivities.reduce((acc, a) => acc + (a.duration_ms || 0), 0) / completedActivities.length / 1000)
    : 0

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
      case 'idle':
        return 'text-green-400 bg-green-400/10'
      case 'working':
        return 'text-blue-400 bg-blue-400/10'
      case 'error':
        return 'text-red-400 bg-red-400/10'
      case 'offline':
        return 'text-gray-400 bg-gray-400/10'
      default:
        return 'text-gray-400 bg-gray-400/10'
    }
  }

  return (
    <div className="space-y-6">
      {/* Agent Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-900/50 backdrop-blur-md rounded-xl border border-gray-800 p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 rounded-lg bg-gradient-to-br from-neon-blue/20 to-neon-purple/20 border border-neon-blue/30">
              <Bot className="w-8 h-8 text-neon-blue" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-100">
                {agent.id.includes('orchestrator') ? 'OA (Orchestrator)' : agent.name}
              </h2>
              <p className="text-gray-400">
                Type: {agent.type}
                {agent.id.includes('orchestrator') && ' - Master Coordinator'}
              </p>
              {(agent.project || agent.location) && (
                <p className="text-sm text-gray-500 mt-1">
                  Project: {agent.project || agent.location}
                </p>
              )}
            </div>
          </div>
          <span className={clsx(
            'px-3 py-1 rounded-lg text-sm font-medium',
            getStatusColor(agent.status)
          )}>
            {agent.status.toUpperCase()}
          </span>
        </div>

        {/* Agent Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800/30 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Total Tasks</span>
              <Cpu className="w-4 h-4 text-gray-500" />
            </div>
            <p className="text-2xl font-bold text-gray-100">{agentActivities.length}</p>
          </div>
          
          <div className="bg-gray-800/30 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Success Rate</span>
              <CheckCircle className="w-4 h-4 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-gray-100">{successRate}%</p>
          </div>
          
          <div className="bg-gray-800/30 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Avg Duration</span>
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <p className="text-2xl font-bold text-gray-100">{avgDuration}s</p>
          </div>
          
          <div className="bg-gray-800/30 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Last Seen</span>
              <TrendingUp className="w-4 h-4 text-purple-500" />
            </div>
            <p className="text-sm font-medium text-gray-100">
              {new Date(agent.last_seen).toLocaleTimeString()}
            </p>
          </div>
        </div>

        {/* Capabilities */}
        {agent.capabilities.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Capabilities</h3>
            <div className="flex flex-wrap gap-2">
              {agent.capabilities.map((cap, index) => (
                <span
                  key={index}
                  className="px-3 py-1 rounded-full text-xs bg-gray-800/50 text-gray-300 border border-gray-700"
                >
                  {cap}
                </span>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      {/* Recent Activities */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-gray-900/50 backdrop-blur-md rounded-xl border border-gray-800 p-6"
      >
        <h3 className="text-lg font-semibold text-gray-200 mb-4">Recent Activities</h3>
        {agentActivities.length > 0 ? (
          <ActivityFeed activities={agentActivities.slice(0, 20)} />
        ) : (
          <p className="text-center text-gray-500 py-8">No activities recorded yet</p>
        )}
      </motion.div>
    </div>
  )
}