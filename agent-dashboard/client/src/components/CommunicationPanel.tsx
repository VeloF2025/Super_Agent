import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { Communication } from '../types'
import { MessageSquare, Send, ArrowRight, AlertCircle, Info, Zap } from 'lucide-react'
import clsx from 'clsx'

interface CommunicationPanelProps {
  communications: Communication[]
}

export default function CommunicationPanel({ communications }: CommunicationPanelProps) {
  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-400" />
      case 'high':
        return <Zap className="w-4 h-4 text-orange-400" />
      default:
        return <Info className="w-4 h-4 text-blue-400" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'border-red-500/30 bg-red-500/5'
      case 'high':
        return 'border-orange-500/30 bg-orange-500/5'
      case 'medium':
        return 'border-yellow-500/30 bg-yellow-500/5'
      default:
        return 'border-gray-700 bg-gray-800/30'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-neon-blue to-neon-purple mb-2">
          Agent Communications
        </h2>
        <p className="text-gray-400">Real-time message flow between agents</p>
      </div>

      <div className="space-y-4">
        {communications.length > 0 ? (
          communications.map((comm, index) => (
            <motion.div
              key={comm.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={clsx(
                'bg-gray-900/50 backdrop-blur-md rounded-xl border p-6',
                getPriorityColor(comm.priority)
              )}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <MessageSquare className="w-5 h-5 text-gray-400" />
                  <div className="flex items-center space-x-2 text-sm">
                    <span className="font-medium text-gray-200">{comm.from_agent}</span>
                    <ArrowRight className="w-4 h-4 text-gray-600" />
                    <span className="font-medium text-gray-200">{comm.to_agent}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  {getPriorityIcon(comm.priority)}
                  <span className="text-xs text-gray-500">
                    {format(new Date(comm.timestamp), 'HH:mm:ss')}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-medium text-gray-400">Type:</span>
                  <span className="text-xs px-2 py-1 rounded bg-gray-800/50 text-gray-300">
                    {comm.message_type}
                  </span>
                  <span className="text-xs font-medium text-gray-400 ml-4">Status:</span>
                  <span className={clsx(
                    'text-xs px-2 py-1 rounded',
                    comm.status === 'sent' ? 'bg-green-400/10 text-green-400' : 'bg-gray-400/10 text-gray-400'
                  )}>
                    {comm.status}
                  </span>
                </div>
                
                {comm.content && (
                  <div className="mt-3 p-3 rounded-lg bg-gray-800/30">
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">
                      {typeof comm.content === 'string' 
                        ? comm.content 
                        : JSON.stringify(comm.content, null, 2)
                      }
                    </pre>
                  </div>
                )}
              </div>
            </motion.div>
          ))
        ) : (
          <div className="text-center py-12">
            <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500">No communications recorded yet</p>
          </div>
        )}
      </div>
    </div>
  )
}