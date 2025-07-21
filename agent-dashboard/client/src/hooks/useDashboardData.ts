import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { DashboardData, Agent } from '../types';

interface UseDashboardDataOptions {
  refreshInterval?: number;
  autoRefresh?: boolean;
  enableWebSocket?: boolean;
  retryAttempts?: number;
  batchUpdates?: boolean;
}

interface DashboardMetrics {
  totalAgents: number;
  onlineAgents: number;
  activeAgents: number;
  systemLoad: number;
  avgResponseTime: number;
  tasksCompleted: number;
  successRate: number;
  lastUpdate: Date;
}

export const useDashboardData = (options: UseDashboardDataOptions = {}) => {
  const {
    refreshInterval = 5000,
    autoRefresh = true,
    enableWebSocket = true,
    retryAttempts = 3,
    batchUpdates = true
  } = options;

  // State management
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);

  // Refs for performance optimization
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const pendingUpdatesRef = useRef<Partial<DashboardData>[]>([]);
  const batchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Memoized computed values
  const computedMetrics = useMemo((): DashboardMetrics | null => {
    if (!data) return null;

    const agents = data.agents || [];
    const activities = data.activities || [];
    const onlineAgents = agents.filter(a => a.status !== 'offline');
    const activeAgents = agents.filter(a => a.status === 'working');
    
    return {
      totalAgents: agents.length,
      onlineAgents: onlineAgents.length,
      activeAgents: activeAgents.length,
      systemLoad: Math.round((activeAgents.length / Math.max(onlineAgents.length, 1)) * 100),
      avgResponseTime: data.metrics?.performance?.avgResponseTime || 0,
      tasksCompleted: activities.filter(a => a.type === 'task-complete').length,
      successRate: data.metrics?.activities?.successRate || 0,
      lastUpdate: new Date()
    };
  }, [data]);

  // Update metrics when computed values change
  useEffect(() => {
    setMetrics(computedMetrics);
  }, [computedMetrics]);

  // Batch update handler for better performance
  const processBatchedUpdates = useCallback(() => {
    if (pendingUpdatesRef.current.length === 0) return;

    const updates = pendingUpdatesRef.current;
    pendingUpdatesRef.current = [];

    // Merge all pending updates
    const mergedUpdate = updates.reduce((acc, update) => {
      return { ...acc, ...update };
    }, {} as Partial<DashboardData>);

    setData(prevData => {
      if (!prevData) return prevData;
      return { ...prevData, ...mergedUpdate };
    });
  }, []);

  // Add update to batch
  const addToBatch = useCallback((update: Partial<DashboardData>) => {
    if (!batchUpdates) {
      setData(prevData => prevData ? { ...prevData, ...update } : null);
      return;
    }

    pendingUpdatesRef.current.push(update);

    if (batchTimeoutRef.current) {
      clearTimeout(batchTimeoutRef.current);
    }

    batchTimeoutRef.current = setTimeout(processBatchedUpdates, 100);
  }, [batchUpdates, processBatchedUpdates]);

  // Fetch initial data
  const fetchData = useCallback(async (signal?: AbortSignal) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/dashboard', {
        signal,
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const dashboardData = await response.json();
      setData(dashboardData);
      setConnectionStatus('connected');
      retryCountRef.current = 0;
      
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      
      console.error('Dashboard data fetch error:', err);
      setError(err.message);
      
      // Implement exponential backoff for retries
      if (retryCountRef.current < retryAttempts) {
        retryCountRef.current++;
        const delay = Math.pow(2, retryCountRef.current) * 1000;
        
        setTimeout(() => {
          if (!signal?.aborted) {
            fetchData(signal);
          }
        }, delay);
      } else {
        setConnectionStatus('disconnected');
      }
    } finally {
      setLoading(false);
    }
  }, [retryAttempts]);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket) return;

    const wsUrl = `ws://${window.location.hostname}:${window.location.port.replace('3000', '3010')}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Dashboard WebSocket connected');
      setConnectionStatus('connected');
      retryCountRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'initial':
            setData(message.data);
            break;
            
          case 'agent-update':
            addToBatch({
              agents: data?.agents.map(a => 
                a.id === message.data.agent.id ? message.data.agent : a
              ) || []
            });
            break;
            
          case 'metrics-update':
            addToBatch({ metrics: message.data });
            break;
            
          case 'activity-start':
          case 'activity-complete':
            // Fetch updated activities
            fetch('/api/activities')
              .then(res => res.json())
              .then(activities => addToBatch({ activities }))
              .catch(console.error);
            break;
            
          default:
            console.log('Unknown WebSocket message type:', message.type);
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };

    ws.onclose = () => {
      console.log('Dashboard WebSocket disconnected');
      setConnectionStatus('disconnected');
      
      // Attempt to reconnect with exponential backoff
      if (retryCountRef.current < retryAttempts) {
        retryCountRef.current++;
        const delay = Math.pow(2, retryCountRef.current) * 1000;
        
        setTimeout(() => {
          connectWebSocket();
        }, delay);
      }
    };

    ws.onerror = (error) => {
      console.error('Dashboard WebSocket error:', error);
      setConnectionStatus('disconnected');
    };

    wsRef.current = ws;
  }, [enableWebSocket, retryAttempts, addToBatch, data?.agents]);

  // Manual refresh function
  const refresh = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    abortControllerRef.current = new AbortController();
    fetchData(abortControllerRef.current.signal);
  }, [fetchData]);

  // Update specific agent data
  const updateAgent = useCallback((agentId: string, updates: Partial<Agent>) => {
    addToBatch({
      agents: data?.agents.map(agent => 
        agent.id === agentId ? { ...agent, ...updates } : agent
      ) || []
    });
  }, [data?.agents, addToBatch]);

  // Add new activity
  const addActivity = useCallback((activity: any) => {
    addToBatch({
      activities: [activity, ...(data?.activities || [])].slice(0, 100) // Keep only last 100
    });
  }, [data?.activities, addToBatch]);

  // Initialize data fetching
  useEffect(() => {
    abortControllerRef.current = new AbortController();
    fetchData(abortControllerRef.current.signal);

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchData]);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Auto refresh via HTTP polling (fallback)
  useEffect(() => {
    if (!autoRefresh || enableWebSocket) return;

    const interval = setInterval(() => {
      if (connectionStatus === 'connected') {
        refresh();
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, enableWebSocket, refreshInterval, connectionStatus, refresh]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (batchTimeoutRef.current) {
        clearTimeout(batchTimeoutRef.current);
      }
    };
  }, []);

  // Filter and search functions
  const filterAgents = useCallback((
    agents: Agent[],
    searchQuery: string,
    statusFilter?: string
  ) => {
    return agents.filter(agent => {
      const matchesSearch = !searchQuery || 
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.id.toLowerCase().includes(searchQuery.toLowerCase());
        
      const matchesStatus = !statusFilter || statusFilter === 'all' || 
        agent.status === statusFilter;
        
      return matchesSearch && matchesStatus;
    });
  }, []);

  return {
    // Data
    data,
    metrics,
    loading,
    error,
    connectionStatus,
    
    // Actions
    refresh,
    updateAgent,
    addActivity,
    filterAgents,
    
    // Connection info
    isConnected: connectionStatus === 'connected',
    isLoading: loading,
    hasError: !!error,
    
    // Performance stats
    lastUpdate: metrics?.lastUpdate,
    retryCount: retryCountRef.current
  };
};