import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import AgentDetails from './components/AgentDetails'
import CommunicationPanel from './components/CommunicationPanel'
import ProjectsView from './components/ProjectsView'
import useWebSocket from './hooks/useWebSocket'
import { DashboardData, Agent } from './types'

// Error boundary component
class ErrorBoundary extends React.Component {
  constructor(props: any) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: any) {
    return { hasError: true, error }
  }

  componentDidCatch(error: any, errorInfo: any) {
    console.error('React Error Boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-950 flex items-center justify-center">
          <div className="text-center text-white">
            <h1 className="text-2xl font-bold mb-4">Something went wrong</h1>
            <p className="text-gray-400 mb-4">The dashboard encountered an error</p>
            <button 
              onClick={() => window.location.reload()} 
              className="bg-neon-blue text-black px-4 py-2 rounded hover:bg-blue-400"
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Connection status component
function ConnectionStatus({ isConnected, isRetrying, lastError }: {
  isConnected: boolean
  isRetrying: boolean
  lastError: string | null
}) {
  if (isConnected) return null

  return (
    <div className="fixed top-0 left-0 right-0 bg-red-600 text-white p-2 text-center text-sm z-50">
      {isRetrying ? (
        <div className="flex items-center justify-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
          <span>Reconnecting to dashboard...</span>
        </div>
      ) : (
        <div>
          ⚠️ Dashboard connection lost {lastError && `(${lastError})`}
          <button 
            onClick={() => window.location.reload()} 
            className="ml-2 underline hover:no-underline"
          >
            Reload
          </button>
        </div>
      )}
    </div>
  )
}

// Offline fallback data
const FALLBACK_DATA: DashboardData = {
  agents: [],
  activities: [],
  metrics: {
    timestamp: new Date(),
    agents: { total: 0, online: 0, working: 0, idle: 0, error: 0 },
    activities: { recent: 0, total: 0, successRate: 100 },
    queues: { incoming: 0, processing: 0, completed: 0 },
    performance: { avgResponseTime: 0, throughput: 0 }
  },
  projects: [],
  communications: [],
  performance: []
}

function App() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [selectedView, setSelectedView] = useState<'dashboard' | 'agents' | 'communications' | 'projects'>('dashboard')
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(true)
  const [isRetrying, setIsRetrying] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [lastSuccessfulFetch, setLastSuccessfulFetch] = useState<Date | null>(null)

  const maxRetries = 5
  const baseRetryDelay = 1000 // 1 second

  const fetchData = useCallback(async (isRetry = false) => {
    try {
      setIsRetrying(isRetry)
      
      // Add timeout to fetch request
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const response = await fetch('/api/dashboard', {
        signal: controller.signal,
        headers: {
          'Cache-Control': 'no-cache',
          'Accept': 'application/json'
        }
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      // Check if response has content
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Invalid response format: Expected JSON')
      }
      
      const text = await response.text()
      if (!text.trim()) {
        throw new Error('Empty response from server')
      }
      
      let dashboardData
      try {
        dashboardData = JSON.parse(text)
      } catch (parseError) {
        throw new Error(`Invalid JSON: ${parseError.message}`)
      }
      
      // Validate data structure
      if (!dashboardData || typeof dashboardData !== 'object') {
        throw new Error('Invalid data structure received')
      }
      
      // Success - update state
      setData(dashboardData)
      setError(null)
      setIsConnected(true)
      setIsRetrying(false)
      setRetryCount(0)
      setLastSuccessfulFetch(new Date())
      
      if (loading) {
        setLoading(false)
      }
      
    } catch (err: any) {
      console.error('Failed to fetch dashboard data:', err)
      
      const errorMessage = err.name === 'AbortError' 
        ? 'Request timeout'
        : err.message || 'Unknown error'
      
      setError(errorMessage)
      setIsConnected(false)
      
      // Only set fallback data if we have no data at all
      if (!data) {
        setData(FALLBACK_DATA)
        setLoading(false)
      }
      
      // Implement exponential backoff for retries
      if (isRetry && retryCount < maxRetries) {
        const delay = baseRetryDelay * Math.pow(2, retryCount)
        console.log(`Retrying in ${delay}ms... (attempt ${retryCount + 1}/${maxRetries})`)
        
        setTimeout(() => {
          setRetryCount(prev => prev + 1)
          fetchData(true)
        }, delay)
      } else {
        setIsRetrying(false)
        
        // Auto-retry after 30 seconds if we haven't exceeded max retries
        if (retryCount < maxRetries) {
          setTimeout(() => {
            console.log('Auto-retry after 30 seconds...')
            setRetryCount(0)
            fetchData(true)
          }, 30000)
        }
      }
    }
  }, [data, loading, retryCount])

  // Manual retry function
  const handleRetry = useCallback(() => {
    setRetryCount(0)
    setError(null)
    fetchData(true)
  }, [fetchData])

  // Initial fetch and polling
  useEffect(() => {
    fetchData()
    
    // Poll every 5 seconds when connected, 15 seconds when disconnected
    const pollInterval = isConnected ? 5000 : 15000
    const interval = setInterval(() => {
      if (!isRetrying) {
        fetchData()
      }
    }, pollInterval)
    
    return () => clearInterval(interval)
  }, [fetchData, isConnected, isRetrying])

  // Show loading screen
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-neon-blue"></div>
          <p className="text-white mt-4">Loading Dashboard...</p>
          {error && (
            <div className="mt-4 text-red-400">
              <p>Connection issue: {error}</p>
              <button 
                onClick={handleRetry}
                className="mt-2 bg-neon-blue text-black px-4 py-2 rounded hover:bg-blue-400"
              >
                Retry Connection
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Show error state if no data available
  if (!data) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center text-white">
          <h1 className="text-2xl font-bold mb-4">Dashboard Unavailable</h1>
          <p className="text-gray-400 mb-4">
            Unable to connect to the dashboard server
          </p>
          <div className="text-sm text-red-400 mb-4">
            Error: {error}
          </div>
          <div className="space-x-4">
            <button 
              onClick={handleRetry}
              disabled={isRetrying}
              className="bg-neon-blue text-black px-4 py-2 rounded hover:bg-blue-400 disabled:opacity-50"
            >
              {isRetrying ? 'Retrying...' : 'Retry Connection'}
            </button>
            <button 
              onClick={() => window.location.reload()}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-500"
            >
              Reload Page
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-950 text-white">
        <ConnectionStatus 
          isConnected={isConnected} 
          isRetrying={isRetrying}
          lastError={error}
        />
        
        <Header />
        
        <div className="flex">
          <Sidebar 
            selectedView={selectedView} 
            onViewChange={setSelectedView}
            connectionStatus={{
              isConnected,
              lastUpdate: lastSuccessfulFetch,
              retryCount
            }}
          />
          
          <main className={`flex-1 transition-all duration-300 ${!isConnected ? 'opacity-75' : ''}`}>
            <AnimatePresence mode="wait">
              {selectedView === 'dashboard' && (
                <motion.div
                  key="dashboard"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <Dashboard 
                    data={data} 
                    onAgentSelect={setSelectedAgent}
                    connectionStatus={{ isConnected, error }}
                  />
                </motion.div>
              )}
              
              {selectedView === 'agents' && (
                <motion.div
                  key="agents"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  {selectedAgent ? (
                    <AgentDetails 
                      agent={selectedAgent} 
                      onBack={() => setSelectedAgent(null)}
                      connectionStatus={{ isConnected, error }}
                    />
                  ) : (
                    <Dashboard 
                      data={data} 
                      onAgentSelect={setSelectedAgent}
                      focusMode="agents"
                      connectionStatus={{ isConnected, error }}
                    />
                  )}
                </motion.div>
              )}
              
              {selectedView === 'communications' && (
                <motion.div
                  key="communications"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <CommunicationPanel 
                    communications={data.communications}
                    agents={data.agents}
                    connectionStatus={{ isConnected, error }}
                  />
                </motion.div>
              )}
              
              {selectedView === 'projects' && (
                <motion.div
                  key="projects"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <ProjectsView 
                    projects={data.projects}
                    agents={data.agents}
                    connectionStatus={{ isConnected, error }}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </main>
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default App