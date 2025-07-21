import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import AgentDetails from './components/AgentDetails'
import CommunicationPanel from './components/CommunicationPanel'
import ProjectsView from './components/ProjectsView'
import useWebSocket from './hooks/useWebSocket'
import { DashboardData, Agent } from './types'

function App() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [selectedView, setSelectedView] = useState<'dashboard' | 'agents' | 'communications' | 'projects'>('dashboard')
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Temporarily disable WebSocket and use polling instead
  const isConnected = true // Mock as connected for now
  
  // Poll for updates every 5 seconds
  useEffect(() => {
    const fetchData = () => {
      fetch('/api/dashboard')
        .then(res => res.json())
        .then(data => {
          setData(data)
          setLoading(false)
        })
        .catch(err => {
          console.error('Failed to fetch dashboard data:', err)
        })
    }

    // Fetch immediately
    fetchData()
    
    // Then poll every 5 seconds
    const interval = setInterval(fetchData, 5000)
    
    return () => clearInterval(interval)
  }, [])


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
                  <AgentDetails agent={selectedAgent} activities={data?.activities || []} />
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
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}

export default App