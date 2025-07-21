import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import {
  Activity, Bot, CheckCircle, AlertCircle, Clock, Zap, Users, Brain,
  TrendingUp, TrendingDown, Server, Cpu, HardDrive, Wifi, Settings,
  RefreshCw, Filter, Search, MoreVertical, Eye, EyeOff, Maximize2,
  Grid, List, BarChart3, PieChart as PieChartIcon, Plus
} from 'lucide-react';
import { DashboardData, Agent } from '../types';
import { DashboardSettings, DashboardPreferences } from './DashboardSettings';
import { 
  WidgetContainer, 
  MetricsWidget, 
  AgentStatusWidget, 
  PerformanceWidget 
} from './widgets';

interface EnhancedDashboardProps {
  data: DashboardData | null;
  onRefresh?: () => void;
}

// Widget types for customizable dashboard
type WidgetType = 'metrics' | 'agent-status' | 'performance-chart' | 'activities' | 'system-health' | 'ml-insights';

interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  size: 'small' | 'medium' | 'large';
  position: { x: number; y: number };
  visible: boolean;
}

const defaultWidgets: DashboardWidget[] = [
  { id: 'metrics', type: 'metrics', title: 'Key Metrics', size: 'large', position: { x: 0, y: 0 }, visible: true },
  { id: 'agent-status', type: 'agent-status', title: 'Agent Status', size: 'medium', position: { x: 0, y: 1 }, visible: true },
  { id: 'performance', type: 'performance-chart', title: 'Performance', size: 'large', position: { x: 1, y: 1 }, visible: true },
  { id: 'activities', type: 'activities', title: 'Recent Activities', size: 'large', position: { x: 0, y: 2 }, visible: true },
  { id: 'system-health', type: 'system-health', title: 'System Health', size: 'medium', position: { x: 2, y: 1 }, visible: true },
  { id: 'ml-insights', type: 'ml-insights', title: 'ML Insights', size: 'medium', position: { x: 2, y: 2 }, visible: true },
];

const defaultPreferences: DashboardPreferences = {
  theme: 'dark',
  layout: 'grid',
  refreshInterval: 5000,
  autoRefresh: true,
  enableNotifications: true,
  enableWebSocket: true,
  retryAttempts: 3,
  batchUpdates: true,
  showSystemHealth: true,
  showMLInsights: true,
  showPerformanceCharts: true,
  compactMode: false,
  animationsEnabled: true,
  soundEnabled: false,
  colorScheme: 'blue',
  widgetSettings: {
    'metrics': { visible: true, size: 'large' },
    'agent-status': { visible: true, size: 'medium' },
    'performance': { visible: true, size: 'large' },
    'activities': { visible: true, size: 'large' },
    'system-health': { visible: true, size: 'medium' },
    'ml-insights': { visible: true, size: 'medium' },
  }
};

export const EnhancedDashboard: React.FC<EnhancedDashboardProps> = ({ data, onRefresh }) => {
  const [widgets, setWidgets] = useState<DashboardWidget[]>(defaultWidgets);
  const [preferences, setPreferences] = useState<DashboardPreferences>(defaultPreferences);
  const [showSettings, setShowSettings] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Auto refresh logic
  useEffect(() => {
    if (!preferences.autoRefresh || !onRefresh) return;
    
    const interval = setInterval(() => {
      onRefresh();
    }, preferences.refreshInterval);

    return () => clearInterval(interval);
  }, [preferences.autoRefresh, preferences.refreshInterval, onRefresh]);

  // Update widgets based on preferences
  useEffect(() => {
    setWidgets(currentWidgets => 
      currentWidgets.map(widget => ({
        ...widget,
        visible: preferences.widgetSettings[widget.id]?.visible ?? widget.visible,
        size: preferences.widgetSettings[widget.id]?.size ?? widget.size
      }))
    );
  }, [preferences.widgetSettings]);

  // Widget management functions
  const updateWidget = (widgetId: string, updates: Partial<DashboardWidget>) => {
    setWidgets(current => 
      current.map(w => w.id === widgetId ? { ...w, ...updates } : w)
    );
    
    // Also update preferences
    if (updates.size || updates.visible !== undefined) {
      setPreferences(prev => ({
        ...prev,
        widgetSettings: {
          ...prev.widgetSettings,
          [widgetId]: {
            ...prev.widgetSettings[widgetId],
            ...(updates.size && { size: updates.size }),
            ...(updates.visible !== undefined && { visible: updates.visible })
          }
        }
      }));
    }
  };

  const toggleWidgetVisibility = (widgetId: string) => {
    const widget = widgets.find(w => w.id === widgetId);
    if (widget) {
      updateWidget(widgetId, { visible: !widget.visible });
    }
  };

  const changeWidgetSize = (widgetId: string, size: 'small' | 'medium' | 'large') => {
    updateWidget(widgetId, { size });
  };

  // Render widget content based on type
  const renderWidgetContent = (widget: DashboardWidget) => {
    if (!data) return <div className="text-gray-400">No data available</div>;

    switch (widget.type) {
      case 'metrics':
        return (
          <MetricsWidget 
            data={data} 
            size={widget.size} 
            compactMode={preferences.compactMode}
          />
        );
      
      case 'agent-status':
        return (
          <AgentStatusWidget 
            data={data} 
            size={widget.size} 
            compactMode={preferences.compactMode}
          />
        );
      
      case 'performance-chart':
        return (
          <PerformanceWidget 
            data={data} 
            size={widget.size} 
            compactMode={preferences.compactMode}
          />
        );
      
      case 'activities':
        return (
          <div className="space-y-3">
            {data.activities.slice(0, widget.size === 'small' ? 3 : 8).map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center gap-3 p-2 bg-gray-700/30 rounded-lg"
              >
                <div className={`w-2 h-2 rounded-full ${
                  activity.status === 'completed' ? 'bg-green-400' :
                  activity.status === 'failed' ? 'bg-red-400' : 'bg-yellow-400'
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white truncate">{activity.description}</div>
                  <div className="text-xs text-gray-400">
                    {activity.agentName} • {new Date(activity.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        );
      
      case 'system-health':
        return (
          <div className="space-y-4">
            {[
              { label: 'CPU Usage', value: 45, color: 'bg-blue-500' },
              { label: 'Memory', value: 62, color: 'bg-green-500' },
              { label: 'Storage', value: 28, color: 'bg-purple-500' },
              { label: 'Network', value: 85, color: 'bg-yellow-500' }
            ].slice(0, widget.size === 'small' ? 2 : 4).map((metric) => (
              <div key={metric.label}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-gray-300 ${preferences.compactMode ? 'text-xs' : 'text-sm'}`}>
                    {metric.label}
                  </span>
                  <span className={`text-white font-medium ${preferences.compactMode ? 'text-xs' : 'text-sm'}`}>
                    {metric.value}%
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${metric.value}%` }}
                    transition={{ duration: 1, delay: 0.5 }}
                    className={`h-2 rounded-full ${metric.color}`}
                  />
                </div>
              </div>
            ))}
          </div>
        );
      
      case 'ml-insights':
        return (
          <div className="space-y-4">
            <div className="text-center">
              <Brain className="w-12 h-12 text-purple-400 mx-auto mb-2" />
              <div className={`font-medium text-white ${preferences.compactMode ? 'text-sm' : 'text-base'}`}>
                ML Optimization Active
              </div>
              <div className={`text-gray-400 ${preferences.compactMode ? 'text-xs' : 'text-sm'}`}>
                Learning from {data.agents.length} agents
              </div>
            </div>
            
            {widget.size !== 'small' && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Prediction Accuracy</span>
                  <span className="text-xs text-green-400">94.2%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Models Updated</span>
                  <span className="text-xs text-blue-400">12h ago</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Performance Gain</span>
                  <span className="text-xs text-purple-400">+18%</span>
                </div>
              </div>
            )}
          </div>
        );
      
      default:
        return <div className="text-gray-400">Widget not implemented</div>;
    }
  };

  // Memoized calculations for better performance
  const dashboardMetrics = useMemo(() => {
    if (!data) return null;

    const { metrics, agents, activities } = data;
    const onlineAgents = agents.filter(a => a.status !== 'offline');
    const activeAgents = agents.filter(a => a.status === 'working');
    
    return {
      totalAgents: agents.length,
      onlineAgents: onlineAgents.length,
      activeAgents: activeAgents.length,
      systemLoad: Math.round((activeAgents.length / Math.max(onlineAgents.length, 1)) * 100),
      avgResponseTime: metrics?.performance?.avgResponseTime || 0,
      tasksCompleted: activities.filter(a => a.type === 'task-complete').length,
      successRate: metrics?.activities?.successRate || 0,
    };
  }, [data]);

  // Enhanced chart data with better formatting
  const chartData = useMemo(() => {
    if (!data) return { agentStatus: [], performance: [], timeline: [] };

    const agentStatusCounts = data.agents.reduce((acc, agent) => {
      acc[agent.status] = (acc[agent.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const statusColors = {
      online: '#10b981',
      working: '#3b82f6',
      idle: '#f59e0b',
      offline: '#6b7280',
      error: '#ef4444'
    };

    const agentStatus = Object.entries(agentStatusCounts).map(([status, count]) => ({
      name: status.charAt(0).toUpperCase() + status.slice(1),
      value: count,
      color: statusColors[status as keyof typeof statusColors] || '#6b7280',
      percentage: Math.round((count / data.agents.length) * 100)
    }));

    return {
      agentStatus,
      performance: data.performance?.slice(-10) || [],
      timeline: data.activities?.slice(-20).map((activity, index) => ({
        time: new Date(activity.timestamp).toLocaleTimeString(),
        activities: index + 1,
        success: activity.status === 'completed' ? 1 : 0
      })) || []
    };
  }, [data]);

  const toggleWidget = (widgetId: string) => {
    setWidgets(widgets.map(w => 
      w.id === widgetId ? { ...w, visible: !w.visible } : w
    ));
  };

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600/20 rounded-full mb-4">
            <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Loading Dashboard</h3>
          <p className="text-gray-400">Gathering system data...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Enhanced Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-blue-600 bg-clip-text text-transparent"
          >
            Jarvis Command Center
          </motion.h1>
          <p className="text-gray-400 mt-1">
            Real-time monitoring • {dashboardMetrics?.onlineAgents} of {dashboardMetrics?.totalAgents} agents online
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search agents, tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent w-64"
            />
          </div>

          {/* View Mode Toggle */}
          <div className="flex bg-gray-800/50 rounded-lg p-1">
            <button
              onClick={() => setPreferences(prev => ({ ...prev, layout: 'grid' }))}
              className={`p-2 rounded-md transition-colors ${
                preferences.layout === 'grid' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPreferences(prev => ({ ...prev, layout: 'list' }))}
              className={`p-2 rounded-md transition-colors ${
                preferences.layout === 'list' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Auto Refresh Toggle */}
          <button
            onClick={() => setPreferences(prev => ({ ...prev, autoRefresh: !prev.autoRefresh }))}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
              preferences.autoRefresh 
                ? 'bg-green-600/20 text-green-400 border border-green-600/30' 
                : 'bg-gray-800/50 text-gray-400 hover:text-white border border-gray-700'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${preferences.autoRefresh ? 'animate-spin' : ''}`} />
            <span className="text-sm">Auto</span>
          </button>

          {/* Settings Button */}
          <button
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-2 px-3 py-2 bg-gray-800/50 text-gray-400 hover:text-white border border-gray-700 rounded-lg transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span className="text-sm">Settings</span>
          </button>
        </div>
      </div>

      {/* System Status Banner */}
      {preferences.showSystemHealth && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-blue-600/10 border border-blue-500/20 rounded-xl p-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                <span className="text-green-400 font-medium">All Systems Operational</span>
              </div>
              <div className="text-gray-400 text-sm">
                Uptime: 99.9% • Load: {dashboardMetrics?.systemLoad}% • Response: {dashboardMetrics?.avgResponseTime}ms
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Clock className="w-4 h-4" />
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </motion.div>
      )}

      {/* Widget-Based Dashboard */}
      <div className={`grid gap-6 ${
        preferences.layout === 'grid' 
          ? 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3' 
          : 'grid-cols-1'
      }`}>
        {widgets
          .filter(widget => widget.visible)
          .map((widget, index) => (
            <motion.div
              key={widget.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <WidgetContainer
                id={widget.id}
                title={widget.title}
                size={widget.size}
                preferences={preferences}
                isVisible={widget.visible}
                onSizeChange={(size) => changeWidgetSize(widget.id, size)}
                onToggleVisibility={() => toggleWidgetVisibility(widget.id)}
              >
                {renderWidgetContent(widget)}
              </WidgetContainer>
            </motion.div>
          ))}
      </div>

      {/* Settings Modal */}
      <DashboardSettings
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        preferences={preferences}
        onPreferencesChange={setPreferences}
      />
    </div>
  );
};