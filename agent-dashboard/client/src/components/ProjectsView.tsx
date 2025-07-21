import { motion } from 'framer-motion'
import { Project, Agent } from '../types'
import { FolderOpen, Users, Clock, GitBranch, ChevronRight } from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'

interface ProjectsViewProps {
  projects: Project[]
  agents: Agent[]
}

export default function ProjectsView({ projects, agents }: ProjectsViewProps) {
  const getAgentInfo = (agentId: string) => {
    return agents.find(a => a.id === agentId) || null
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-400 bg-green-400/10'
      case 'completed':
        return 'text-blue-400 bg-blue-400/10'
      case 'paused':
        return 'text-yellow-400 bg-yellow-400/10'
      default:
        return 'text-gray-400 bg-gray-400/10'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-neon-blue to-neon-purple mb-2">
          Active Projects
        </h2>
        <p className="text-gray-400">Projects being managed by the agent system</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {projects.map((project, index) => (
          <motion.div
            key={project.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            className="bg-gray-900/50 backdrop-blur-md rounded-xl border border-gray-800 p-6 hover:border-gray-700 transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30">
                  <FolderOpen className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-100">{project.name}</h3>
                  <p className="text-xs text-gray-500 mt-1 font-mono">{project.path}</p>
                </div>
              </div>
              <span className={clsx(
                'px-2 py-1 rounded text-xs font-medium',
                getStatusColor(project.status)
              )}>
                {project.status.toUpperCase()}
              </span>
            </div>

            <div className="space-y-3">
              {/* Assigned Agents */}
              {project.agents.length > 0 && (
                <div>
                  <div className="flex items-center space-x-2 text-sm text-gray-400 mb-2">
                    <Users className="w-4 h-4" />
                    <span>Assigned Agents</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {project.agents.map((agentId) => {
                      const agent = getAgentInfo(agentId)
                      return (
                        <div
                          key={agentId}
                          className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-gray-800/50 border border-gray-700"
                        >
                          <div className={clsx(
                            'w-2 h-2 rounded-full',
                            agent?.status === 'online' || agent?.status === 'idle' ? 'bg-green-400' :
                            agent?.status === 'working' ? 'bg-blue-400' :
                            'bg-gray-400'
                          )} />
                          <span className="text-xs text-gray-300">
                            {agent?.name || agentId}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Project Metadata */}
              <div className="grid grid-cols-2 gap-4 pt-3 border-t border-gray-800">
                <div className="flex items-center space-x-2 text-xs text-gray-400">
                  <Clock className="w-4 h-4" />
                  <span>Created: {format(new Date(project.created_at), 'MMM d, yyyy')}</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-400">
                  <GitBranch className="w-4 h-4" />
                  <span>Updated: {format(new Date(project.updated_at), 'MMM d, yyyy')}</span>
                </div>
              </div>
            </div>

            {/* View Details Button */}
            <button className="mt-4 w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 text-gray-300 hover:text-gray-100 transition-all">
              <span className="text-sm">View Details</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </motion.div>
        ))}
      </div>

      {projects.length === 0 && (
        <div className="text-center py-12">
          <FolderOpen className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-500">No active projects found</p>
        </div>
      )}
    </div>
  )
}