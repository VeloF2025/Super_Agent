import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Activity, AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react'
import { Agent, AgentPerformance } from '../types'

interface AgentHealthScoreProps {
  agent: Agent
  performance?: AgentPerformance
  activities?: any[]
}

export default function AgentHealthScore({ agent, performance, activities = [] }: AgentHealthScoreProps) {
  const healthScore = useMemo(() => {
    let score = 100
    let factors = []

    // Status factor (40% weight)
    if (agent.status === 'offline') {
      score -= 40
      factors.push({ name: 'Status', value: 0, weight: 40, reason: 'Agent is offline' })
    } else if (agent.status === 'error') {
      score -= 30
      factors.push({ name: 'Status', value: 10, weight: 40, reason: 'Agent has errors' })
    } else if (agent.status === 'idle') {
      factors.push({ name: 'Status', value: 30, weight: 40, reason: 'Agent is idle' })
    } else {
      factors.push({ name: 'Status', value: 40, weight: 40, reason: 'Agent is active' })
    }

    // Performance factor (30% weight)
    if (performance) {
      const successRate = performance.total_activities > 0
        ? (performance.completed_activities / performance.total_activities) * 100
        : 100
      
      const performanceScore = (successRate / 100) * 30
      score = score - 30 + performanceScore
      factors.push({ 
        name: 'Success Rate', 
        value: performanceScore, 
        weight: 30, 
        reason: `${successRate.toFixed(1)}% success rate` 
      })
    } else {
      factors.push({ name: 'Success Rate', value: 30, weight: 30, reason: 'No data available' })
    }

    // Response time factor (20% weight)
    if (performance && performance.avg_duration_ms) {
      const avgMs = performance.avg_duration_ms
      let responseScore = 20
      
      if (avgMs > 5000) responseScore = 5
      else if (avgMs > 2000) responseScore = 10
      else if (avgMs > 1000) responseScore = 15
      
      score = score - 20 + responseScore
      factors.push({ 
        name: 'Response Time', 
        value: responseScore, 
        weight: 20, 
        reason: `${(avgMs / 1000).toFixed(1)}s average` 
      })
    } else {
      factors.push({ name: 'Response Time', value: 20, weight: 20, reason: 'No data available' })
    }

    // Recent activity factor (10% weight)
    const recentActivities = activities.filter(a => 
      a.agent_id === agent.id && 
      new Date(a.started_at) > new Date(Date.now() - 60 * 60 * 1000) // Last hour
    )
    
    const activityScore = recentActivities.length > 0 ? 10 : 0
    score = score - 10 + activityScore
    factors.push({ 
      name: 'Recent Activity', 
      value: activityScore, 
      weight: 10, 
      reason: `${recentActivities.length} activities in last hour` 
    })

    return { score: Math.max(0, Math.min(100, score)), factors }
  }, [agent, performance, activities])

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    if (score >= 40) return 'text-orange-500'
    return 'text-red-500'
  }

  const getHealthIcon = (score: number) => {
    if (score >= 80) return CheckCircle
    if (score >= 60) return Clock
    if (score >= 40) return AlertCircle
    return AlertCircle
  }

  const HealthIcon = getHealthIcon(healthScore.score)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-900/50 backdrop-blur-md rounded-xl border border-gray-800 p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-200">Health Score</h3>
        <div className={`flex items-center space-x-2 ${getHealthColor(healthScore.score)}`}>
          <HealthIcon className="h-5 w-5" />
          <span className="text-2xl font-bold">{healthScore.score}</span>
          <span className="text-sm text-gray-400">/ 100</span>
        </div>
      </div>

      {/* Score breakdown */}
      <div className="space-y-3">
        {healthScore.factors.map((factor, index) => (
          <div key={factor.name}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-400">{factor.name}</span>
              <span className="text-gray-500 text-xs">{factor.reason}</span>
            </div>
            <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(factor.value / factor.weight) * 100}%` }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className={`absolute top-0 left-0 h-full rounded-full ${
                  factor.value / factor.weight >= 0.8 ? 'bg-green-500' :
                  factor.value / factor.weight >= 0.6 ? 'bg-yellow-500' :
                  factor.value / factor.weight >= 0.4 ? 'bg-orange-500' :
                  'bg-red-500'
                }`}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Health status */}
      <div className="mt-4 pt-4 border-t border-gray-800">
        <p className="text-sm text-gray-400">
          Overall Status: 
          <span className={`ml-2 font-medium ${getHealthColor(healthScore.score)}`}>
            {healthScore.score >= 80 ? 'Excellent' :
             healthScore.score >= 60 ? 'Good' :
             healthScore.score >= 40 ? 'Fair' :
             'Poor'}
          </span>
        </p>
      </div>
    </motion.div>
  )
}