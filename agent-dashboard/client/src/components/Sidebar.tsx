import { motion } from 'framer-motion'
import { LayoutDashboard, Bot, MessageSquare, FolderOpen, ChevronRight, Brain } from 'lucide-react'
import { Agent } from '../types'
import clsx from 'clsx'

interface SidebarProps {
  selectedView: string
  onViewChange: (view: 'dashboard' | 'agents' | 'communications' | 'projects' | 'ml-optimization') => void
  agents: Agent[]
  onAgentSelect: (agent: Agent) => void
}

export default function Sidebar({ selectedView, onViewChange, agents, onAgentSelect }: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'agents', label: 'Agents', icon: Bot },
    { id: 'communications', label: 'Communications', icon: MessageSquare },
    { id: 'projects', label: 'Projects', icon: FolderOpen },
    { id: 'ml-optimization', label: 'ML Optimization', icon: Brain },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
      case 'idle':
        return 'bg-green-500'
      case 'working':
        return 'bg-blue-500'
      case 'error':
        return 'bg-red-500'
      case 'offline':
        return 'bg-gray-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <aside className="w-64 bg-gray-900/50 backdrop-blur-md border-r border-gray-800 h-[calc(100vh-73px)]">
      <nav className="p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onViewChange(item.id as any)}
                className={clsx(
                  'w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all',
                  selectedView === item.id
                    ? 'bg-gradient-to-r from-cyber-700/20 to-cyber-600/20 text-neon-blue border border-cyber-600/30'
                    : 'hover:bg-gray-800/50 text-gray-400 hover:text-gray-200'
                )}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
                {selectedView === item.id && (
                  <ChevronRight className="ml-auto" size={16} />
                )}
              </button>
            </li>
          ))}
        </ul>
        
        {selectedView === 'agents' && agents.length > 0 && (
          <div className="mt-6 max-h-[calc(100vh-200px)] overflow-y-auto">
            <h3 className="text-xs uppercase text-gray-500 font-semibold mb-2 px-4">All Agents</h3>
            
            {/* Group agents by project/location */}
            {(() => {
              const groupedAgents = agents.reduce((groups, agent) => {
                const key = agent.project || agent.location || 'Ungrouped';
                if (!groups[key]) groups[key] = [];
                groups[key].push(agent);
                return groups;
              }, {} as Record<string, Agent[]>);
              
              // Sort groups to put Super Agent System first
              const sortedGroups = Object.entries(groupedAgents).sort(([a], [b]) => {
                if (a === 'Super Agent System') return -1;
                if (b === 'Super Agent System') return 1;
                return a.localeCompare(b);
              });
              
              return sortedGroups.map(([groupName, groupAgents]) => (
                <div key={groupName} className="mb-4">
                  <h4 className="text-xs text-gray-500 font-medium mb-1 px-4">{groupName}</h4>
                  <ul className="space-y-1">
                    {groupAgents
                      .sort((a, b) => {
                        // OA (Orchestrator) always comes first within Super Agent System
                        if (groupName === 'Super Agent System' || groupName === 'Super Agent') {
                          if (a.id.includes('orchestrator')) return -1;
                          if (b.id.includes('orchestrator')) return 1;
                        }
                        return a.name.localeCompare(b.name);
                      })
                      .map((agent) => (
                        <li key={agent.id}>
                          <button
                            onClick={() => onAgentSelect(agent)}
                            className="w-full flex items-center space-x-2 px-4 py-2 rounded-lg hover:bg-gray-800/50 text-left"
                          >
                            <div className={clsx('w-2 h-2 rounded-full', getStatusColor(agent.status))} />
                            <span className="text-sm text-gray-300 truncate">
                              {agent.id.includes('orchestrator') ? 'OA (Orchestrator)' : agent.name}
                            </span>
                          </button>
                        </li>
                      ))}
                  </ul>
                </div>
              ));
            })()}
          </div>
        )}
      </nav>
    </aside>
  )
}