import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { Activity } from '../types'
import clsx from 'clsx'
import { CheckCircle, Clock, AlertCircle, ArrowRight } from 'lucide-react'

interface ActivityFeedProps {
  activities: Activity[]
}

export default function ActivityFeed({ activities }: ActivityFeedProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'in_progress':
        return <Clock className="w-4 h-4 text-blue-400 animate-pulse" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />
      default:
        return null
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'text-red-400 bg-red-400/10'
      case 'high':
        return 'text-orange-400 bg-orange-400/10'
      case 'medium':
        return 'text-yellow-400 bg-yellow-400/10'
      case 'low':
        return 'text-gray-400 bg-gray-400/10'
      default:
        return 'text-gray-400 bg-gray-400/10'
    }
  }

  return (
    <div className="space-y-3">
      {activities.map((activity, index) => (
        <motion.div
          key={activity.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
          className="flex items-center space-x-4 p-3 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 transition-colors"
        >
          <div className="flex-shrink-0">
            {getStatusIcon(activity.status)}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-200 truncate">
                {activity.agent_name || activity.agent_id}
              </span>
              <ArrowRight className="w-3 h-3 text-gray-600" />
              <span className="text-sm text-gray-400 truncate">
                {activity.description}
              </span>
            </div>
            <div className="flex items-center space-x-3 mt-1">
              <span className={clsx(
                'text-xs px-2 py-0.5 rounded',
                getPriorityColor(activity.priority)
              )}>
                {activity.priority}
              </span>
              <span className="text-xs text-gray-500">
                {activity.activity_type}
              </span>
              {activity.duration_ms && (
                <span className="text-xs text-gray-500">
                  {Math.round(activity.duration_ms / 1000)}s
                </span>
              )}
            </div>
          </div>
          
          <div className="flex-shrink-0 text-xs text-gray-500">
            {format(new Date(activity.started_at), 'HH:mm:ss')}
          </div>
        </motion.div>
      ))}
    </div>
  )
}