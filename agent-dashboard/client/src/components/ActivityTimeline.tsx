import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, Activity, CheckCircle, AlertCircle, Play, Pause, MoreVertical } from 'lucide-react'
import { Activity as ActivityType, Agent } from '../types'
import clsx from 'clsx'

interface ActivityTimelineProps {
  activities: ActivityType[]
  agents: Agent[]
  showAgentFilter?: boolean
}

export default function ActivityTimeline({ activities, agents, showAgentFilter = true }: ActivityTimelineProps) {
  const [selectedAgent, setSelectedAgent] = useState<string>('all')
  const [expandedActivities, setExpandedActivities] = useState<Set<string | number>>(new Set())

  // Group activities by time intervals
  const groupedActivities = useMemo(() => {
    const filtered = selectedAgent === 'all' 
      ? activities 
      : activities.filter(a => a.agent_id === selectedAgent)
    
    const sorted = [...filtered].sort((a, b) => 
      new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
    )

    const groups: { [key: string]: ActivityType[] } = {}
    const now = new Date()
    
    sorted.forEach(activity => {
      const startTime = new Date(activity.started_at)
      const diffHours = (now.getTime() - startTime.getTime()) / (1000 * 60 * 60)
      
      let groupKey: string
      if (diffHours < 1) groupKey = 'Last Hour'
      else if (diffHours < 24) groupKey = 'Today'
      else if (diffHours < 48) groupKey = 'Yesterday'
      else if (diffHours < 168) groupKey = 'This Week'
      else groupKey = 'Older'
      
      if (!groups[groupKey]) groups[groupKey] = []
      groups[groupKey].push(activity)
    })
    
    return groups
  }, [activities, selectedAgent])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return CheckCircle
      case 'in_progress':
        return Play
      case 'failed':
        return AlertCircle
      default:
        return Activity
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-500'
      case 'in_progress':
        return 'text-blue-500'
      case 'failed':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  const toggleExpanded = (activityId: string | number) => {
    setExpandedActivities(prev => {
      const newSet = new Set(prev)
      if (newSet.has(activityId)) {
        newSet.delete(activityId)
      } else {
        newSet.add(activityId)
      }
      return newSet
    })
  }

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A'
    const seconds = Math.floor(ms / 1000)
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ${seconds % 60}s`
    const hours = Math.floor(minutes / 60)
    return `${hours}h ${minutes % 60}m`
  }

  return (
    <div className="space-y-6">
      {/* Filter */}
      {showAgentFilter && (
        <div className="flex items-center space-x-4">
          <label className="text-sm text-gray-400">Filter by Agent:</label>
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-neon-blue"
          >
            <option value="all">All Agents</option>
            {agents.map(agent => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-800"></div>

        {Object.entries(groupedActivities).map(([groupName, groupActivities]) => (
          <div key={groupName} className="mb-8">
            <h3 className="text-sm font-semibold text-gray-400 mb-4 pl-16">{groupName}</h3>
            
            <div className="space-y-4">
              {groupActivities.map((activity, index) => {
                const StatusIcon = getStatusIcon(activity.status)
                const isExpanded = expandedActivities.has(activity.id)
                const agent = agents.find(a => a.id === activity.agent_id)
                
                return (
                  <motion.div
                    key={activity.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="relative flex items-start"
                  >
                    {/* Timeline dot */}
                    <div className="absolute left-6 w-4 h-4 bg-gray-900 border-2 border-gray-700 rounded-full z-10"></div>
                    
                    {/* Content */}
                    <div className="ml-16 flex-1 bg-gray-900/50 backdrop-blur-md rounded-lg border border-gray-800 p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <StatusIcon className={clsx('h-5 w-5', getStatusColor(activity.status))} />
                            <h4 className="font-medium text-gray-200">{activity.activity_type}</h4>
                            <span className={clsx(
                              'px-2 py-0.5 rounded text-xs font-medium',
                              activity.priority === 'critical' && 'bg-red-500/20 text-red-400',
                              activity.priority === 'high' && 'bg-orange-500/20 text-orange-400',
                              activity.priority === 'medium' && 'bg-yellow-500/20 text-yellow-400',
                              activity.priority === 'low' && 'bg-green-500/20 text-green-400'
                            )}>
                              {activity.priority}
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-400 mt-1">{activity.description}</p>
                          
                          <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                            <span>{agent?.name || activity.agent_name || 'Unknown Agent'}</span>
                            <span>•</span>
                            <span>{new Date(activity.started_at).toLocaleTimeString()}</span>
                            {activity.duration_ms && (
                              <>
                                <span>•</span>
                                <span className="flex items-center space-x-1">
                                  <Clock className="h-3 w-3" />
                                  <span>{formatDuration(activity.duration_ms)}</span>
                                </span>
                              </>
                            )}
                          </div>

                          {/* Expanded content */}
                          <AnimatePresence>
                            {isExpanded && activity.result && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.2 }}
                                className="mt-3 pt-3 border-t border-gray-800"
                              >
                                <p className="text-xs font-medium text-gray-400 mb-1">Result:</p>
                                <pre className="text-xs text-gray-500 bg-gray-900/50 rounded p-2 overflow-x-auto">
                                  {typeof activity.result === 'string' 
                                    ? activity.result 
                                    : JSON.stringify(activity.result, null, 2)}
                                </pre>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                        
                        {activity.result && (
                          <button
                            onClick={() => toggleExpanded(activity.id)}
                            className="ml-4 p-1 rounded hover:bg-gray-800 transition-colors"
                          >
                            <MoreVertical className="h-4 w-4 text-gray-500" />
                          </button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        ))}

        {Object.keys(groupedActivities).length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No activities to display</p>
          </div>
        )}
      </div>
    </div>
  )
}