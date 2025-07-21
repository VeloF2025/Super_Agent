import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import AgentDetails from './components/AgentDetails'
import CommunicationPanel from './components/CommunicationPanel'
import ProjectsView from './components/ProjectsView'
import { MLOptimizationPanel } from './components/MLOptimizationPanel'
import useWebSocket from './hooks/useWebSocket'
import { DashboardData, Agent } from './types'

function App() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [selectedView, setSelectedView] = useState<'dashboard' | 'agents' | 'communications' | 'projects' | 'ml-optimization'>('dashboard')
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // WebSocket connection
  const wsUrl = `ws://${window.location.hostname}:3010`
  const { isConnected, lastMessage } = useWebSocket(wsUrl, {
    onMessage: (message) => {
      if (message.type === 'initial') {
        setData(message.data)
        setLoading(false)
      } else if (message.type === 'agent-update') {
        setData(prev => {
          if (!prev) return prev
          const updatedAgents = prev.agents.map(agent => 
            agent.id === message.data.agent.id ? message.data.agent : agent
          )
          return { ...prev, agents: updatedAgents }
        })
      } else if (message.type === 'metrics-update') {
        setData(prev => prev ? { ...prev, metrics: message.data } : prev)
      } else if (message.type === 'activity-start' || message.type === 'activity-complete') {
        // Fetch updated activities
        fetch('/api/activities')
          .then(res => res.json())
          .then(activities => {
            setData(prev => prev ? { ...prev, activities } : prev)
          })
      }
    },
    onError: () => setError('WebSocket connection error'),
    onClose: () => console.log('WebSocket disconnected')
  })

  // Fallback: fetch initial data if WebSocket fails
  useEffect(() => {
    if (!isConnected) {
      const timer = setTimeout(() => {
        if (loading) {
          fetch('/api/dashboard')
            .then(res => res.json())
            .then(data => {
              setData(data)
              setLoading(false)
            })
            .catch(err => {
              console.error('Failed to fetch dashboard data:', err)
              setError('Failed to load dashboard')
            })
        }
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [isConnected, loading])


  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-neon-blue"></div>
          <p className="mt-4 text-neon-blue animate-pulse">Initializing Command Center...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center text-red-500">
          <p className="text-2xl mb-2">System Error</p>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 cyber-grid">
      <Header isConnected={isConnected} />
      
      <div className="flex">
        <Sidebar 
          selectedView={selectedView} 
          onViewChange={setSelectedView}
          agents={data?.agents || []}
          onAgentSelect={setSelectedAgent}
        />
        
        <main className="flex-1 p-6">
          <AnimatePresence mode="wait">
            {selectedView === 'dashboard' && (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <Dashboard data={data} />
              </motion.div>
            )}
            
            {selectedView === 'agents' && (
              <motion.div
                key="agents"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                {selectedAgent ? (
                  <AgentDetails 
                    agent={selectedAgent} 
                    activities={data?.activities || []} 
                    performance={data?.performance?.find(p => p.id === selectedAgent.id)}
                  />
                ) : (
                  <div className="text-center text-gray-500 mt-20">
                    <p>Select an agent from the sidebar to view details</p>
                  </div>
                )}
              </motion.div>
            )}
            
            {selectedView === 'communications' && (
              <motion.div
                key="communications"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <CommunicationPanel communications={data?.communications || []} />
              </motion.div>
            )}
            
            {selectedView === 'projects' && (
              <motion.div
                key="projects"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <ProjectsView projects={data?.projects || []} agents={data?.agents || []} />
              </motion.div>
            )}
            
            {selectedView === 'ml-optimization' && (
              <motion.div
                key="ml-optimization"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <MLOptimizationPanel />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}

export default App