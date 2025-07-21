import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import {
  Activity, AlertTriangle, CheckCircle, Clock, Cpu, Database,
  HardDrive, Network, Zap, TrendingUp, TrendingDown, Eye,
  RefreshCw, Settings, AlertCircle
} from 'lucide-react';

interface PerformanceMetrics {
  timestamp: number;
  responseTime: number;
  throughput: number;
  errorRate: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkLatency: number;
  activeConnections: number;
}

interface Alert {
  id: string;
  type: 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: number;
  resolved: boolean;
}

interface PerformanceMonitoringProps {
  refreshInterval?: number;
  alertThresholds?: {
    responseTime: number;
    errorRate: number;
    cpuUsage: number;
    memoryUsage: number;
  };
}

export const PerformanceMonitoring: React.FC<PerformanceMonitoringProps> = ({
  refreshInterval = 5000,
  alertThresholds = {
    responseTime: 500,
    errorRate: 5,
    cpuUsage: 80,
    memoryUsage: 85
  }
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'5m' | '15m' | '1h' | '6h'>('15m');

  // Generate realistic performance metrics
  const generateMetrics = (): PerformanceMetrics => {
    const now = Date.now();
    const hour = new Date().getHours();
    const loadFactor = hour >= 9 && hour <= 17 ? 1.3 : 0.7; // Business hours load

    return {
      timestamp: now,
      responseTime: Math.round(100 + Math.random() * 200 * loadFactor + Math.sin(now / 60000) * 50),
      throughput: Math.round(50 + Math.random() * 100 * loadFactor + Math.cos(now / 30000) * 20),
      errorRate: Math.max(0, Math.round((Math.random() * 8 - 2) + (loadFactor - 1) * 3)),
      cpuUsage: Math.round(30 + Math.random() * 40 * loadFactor + Math.sin(now / 45000) * 15),
      memoryUsage: Math.round(40 + Math.random() * 35 * loadFactor + Math.cos(now / 50000) * 12),
      diskUsage: Math.round(20 + Math.random() * 15 + Math.sin(now / 120000) * 8),
      networkLatency: Math.round(10 + Math.random() * 30 * loadFactor + Math.sin(now / 40000) * 10),
      activeConnections: Math.round(25 + Math.random() * 50 * loadFactor + Math.cos(now / 35000) * 15)
    };
  };

  // Initialize metrics
  useEffect(() => {
    const initialMetrics = Array.from({ length: 20 }, (_, i) => {
      const timestamp = Date.now() - (20 - i) * 30000; // 30-second intervals
      return { ...generateMetrics(), timestamp };
    });
    setMetrics(initialMetrics);
  }, []);

  // Real-time monitoring loop
  useEffect(() => {
    if (!isMonitoring) return;

    const interval = setInterval(() => {
      const newMetric = generateMetrics();
      
      setMetrics(prev => {
        const updated = [...prev, newMetric];
        const maxPoints = {
          '5m': 10,
          '15m': 30,
          '1h': 120,
          '6h': 720
        }[selectedTimeframe];
        return updated.slice(-maxPoints);
      });

      // Check for alerts
      checkThresholds(newMetric);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [isMonitoring, refreshInterval, selectedTimeframe, alertThresholds]);

  // Alert threshold checking
  const checkThresholds = (metric: PerformanceMetrics) => {
    const newAlerts: Alert[] = [];

    if (metric.responseTime > alertThresholds.responseTime) {
      newAlerts.push({
        id: `response-${Date.now()}`,
        type: 'warning',
        title: 'High Response Time',
        message: `Response time exceeded ${alertThresholds.responseTime}ms (current: ${metric.responseTime}ms)`,
        timestamp: metric.timestamp,
        resolved: false
      });
    }

    if (metric.errorRate > alertThresholds.errorRate) {
      newAlerts.push({
        id: `error-${Date.now()}`,
        type: 'error',
        title: 'High Error Rate',
        message: `Error rate exceeded ${alertThresholds.errorRate}% (current: ${metric.errorRate}%)`,
        timestamp: metric.timestamp,
        resolved: false
      });
    }

    if (metric.cpuUsage > alertThresholds.cpuUsage) {
      newAlerts.push({
        id: `cpu-${Date.now()}`,
        type: 'warning',
        title: 'High CPU Usage',
        message: `CPU usage exceeded ${alertThresholds.cpuUsage}% (current: ${metric.cpuUsage}%)`,
        timestamp: metric.timestamp,
        resolved: false
      });
    }

    if (metric.memoryUsage > alertThresholds.memoryUsage) {
      newAlerts.push({
        id: `memory-${Date.now()}`,
        type: 'error',
        title: 'High Memory Usage',
        message: `Memory usage exceeded ${alertThresholds.memoryUsage}% (current: ${metric.memoryUsage}%)`,
        timestamp: metric.timestamp,
        resolved: false
      });
    }

    if (newAlerts.length > 0) {
      setAlerts(prev => [...prev, ...newAlerts].slice(-10)); // Keep last 10 alerts
    }
  };

  // Current metrics (latest values)
  const currentMetrics = useMemo(() => {
    if (metrics.length === 0) return null;
    return metrics[metrics.length - 1];
  }, [metrics]);

  // Metric trends (compare current vs average)
  const metricTrends = useMemo(() => {
    if (metrics.length < 5) return {};

    const recent = metrics.slice(-5);
    const previous = metrics.slice(-10, -5);

    const calculateTrend = (key: keyof PerformanceMetrics) => {
      const recentAvg = recent.reduce((acc, m) => acc + (m[key] as number), 0) / recent.length;
      const previousAvg = previous.reduce((acc, m) => acc + (m[key] as number), 0) / previous.length;
      const change = ((recentAvg - previousAvg) / previousAvg) * 100;
      return {
        value: recentAvg,
        change: change,
        trend: Math.abs(change) < 2 ? 'stable' : change > 0 ? 'up' : 'down'
      };
    };

    return {
      responseTime: calculateTrend('responseTime'),
      throughput: calculateTrend('throughput'),
      errorRate: calculateTrend('errorRate'),
      cpuUsage: calculateTrend('cpuUsage'),
      memoryUsage: calculateTrend('memoryUsage')
    };
  }, [metrics]);

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Performance Monitoring</h2>
          <p className="text-gray-400">Real-time system health and performance metrics</p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value as any)}
            className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="5m">5 minutes</option>
            <option value="15m">15 minutes</option>
            <option value="1h">1 hour</option>
            <option value="6h">6 hours</option>
          </select>

          <button
            onClick={() => setIsMonitoring(!isMonitoring)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
              isMonitoring 
                ? 'bg-green-600/20 text-green-400 border border-green-600/30' 
                : 'bg-gray-700/50 text-gray-400 border border-gray-600'
            }`}
          >
            <Eye className="w-4 h-4" />
            <span className="text-sm">{isMonitoring ? 'Monitoring' : 'Paused'}</span>
          </button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {currentMetrics && [
          {
            key: 'responseTime',
            label: 'Response Time',
            value: `${Math.round(currentMetrics.responseTime)}ms`,
            icon: Clock,
            color: currentMetrics.responseTime > alertThresholds.responseTime ? 'red' : 'blue',
            threshold: alertThresholds.responseTime
          },
          {
            key: 'throughput',
            label: 'Throughput',
            value: `${Math.round(currentMetrics.throughput)}/min`,
            icon: Zap,
            color: 'green'
          },
          {
            key: 'errorRate',
            label: 'Error Rate',
            value: `${currentMetrics.errorRate}%`,
            icon: AlertTriangle,
            color: currentMetrics.errorRate > alertThresholds.errorRate ? 'red' : 'yellow',
            threshold: alertThresholds.errorRate
          },
          {
            key: 'cpuUsage',
            label: 'CPU Usage',
            value: `${currentMetrics.cpuUsage}%`,
            icon: Cpu,
            color: currentMetrics.cpuUsage > alertThresholds.cpuUsage ? 'red' : 'purple',
            threshold: alertThresholds.cpuUsage
          },
          {
            key: 'memoryUsage',
            label: 'Memory Usage',
            value: `${currentMetrics.memoryUsage}%`,
            icon: Database,
            color: currentMetrics.memoryUsage > alertThresholds.memoryUsage ? 'red' : 'indigo',
            threshold: alertThresholds.memoryUsage
          }
        ].map((metric, index) => {
          const trend = metricTrends[metric.key as keyof typeof metricTrends];
          
          return (
            <motion.div
              key={metric.key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`bg-gray-800/50 rounded-xl border p-4 ${
                metric.color === 'red' ? 'border-red-500/50' : 'border-gray-700/50'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2 rounded-lg bg-${metric.color}-600/20`}>
                  <metric.icon className={`w-4 h-4 text-${metric.color}-400`} />
                </div>
                {trend && (
                  <div className={`flex items-center text-xs ${
                    trend.trend === 'up' ? 'text-red-400' : 
                    trend.trend === 'down' ? 'text-green-400' : 'text-gray-400'
                  }`}>
                    {trend.trend === 'up' ? <TrendingUp className="w-3 h-3" /> : 
                     trend.trend === 'down' ? <TrendingDown className="w-3 h-3" /> : null}
                    {trend.change > 0 ? '+' : ''}{trend.change.toFixed(1)}%
                  </div>
                )}
              </div>
              <div>
                <div className="text-lg font-bold text-white mb-1">{metric.value}</div>
                <div className="text-xs text-gray-400">{metric.label}</div>
                {metric.threshold && (
                  <div className={`text-xs mt-1 ${
                    metric.color === 'red' ? 'text-red-400' : 'text-gray-500'
                  }`}>
                    Threshold: {metric.threshold}
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Performance Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Response Time & Throughput */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Response Time & Throughput</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={metrics}>
              <XAxis 
                dataKey="timestamp"
                tickFormatter={formatTime}
                stroke="#9ca3af"
                fontSize={12}
              />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip
                labelFormatter={(value) => formatTime(value as number)}
                contentStyle={{
                  backgroundColor: 'rgb(31 41 55)',
                  border: '1px solid rgb(75 85 99)',
                  borderRadius: '8px'
                }}
              />
              <Line
                type="monotone"
                dataKey="responseTime"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                name="Response Time (ms)"
              />
              <Line
                type="monotone"
                dataKey="throughput"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                name="Throughput (req/min)"
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        {/* System Resources */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">System Resources</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={metrics}>
              <defs>
                <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis 
                dataKey="timestamp"
                tickFormatter={formatTime}
                stroke="#9ca3af"
                fontSize={12}
              />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip
                labelFormatter={(value) => formatTime(value as number)}
                contentStyle={{
                  backgroundColor: 'rgb(31 41 55)',
                  border: '1px solid rgb(75 85 99)',
                  borderRadius: '8px'
                }}
              />
              <Area
                type="monotone"
                dataKey="cpuUsage"
                stroke="#8b5cf6"
                strokeWidth={2}
                fill="url(#cpuGradient)"
                name="CPU Usage (%)"
              />
              <Area
                type="monotone"
                dataKey="memoryUsage"
                stroke="#06b6d4"
                strokeWidth={2}
                fill="url(#memoryGradient)"
                name="Memory Usage (%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-semibold text-white">Active Alerts</h3>
            <span className="bg-red-600/20 text-red-400 text-xs px-2 py-1 rounded-full">
              {alerts.filter(a => !a.resolved).length} active
            </span>
          </div>

          <div className="space-y-3 max-h-60 overflow-y-auto">
            {alerts.slice(-5).reverse().map((alert) => (
              <div
                key={alert.id}
                className={`flex items-start gap-3 p-3 rounded-lg border ${
                  alert.type === 'error' 
                    ? 'bg-red-900/20 border-red-500/30' 
                    : alert.type === 'warning'
                    ? 'bg-yellow-900/20 border-yellow-500/30'
                    : 'bg-blue-900/20 border-blue-500/30'
                }`}
              >
                <div className={`p-1 rounded ${
                  alert.type === 'error' ? 'bg-red-600/20' :
                  alert.type === 'warning' ? 'bg-yellow-600/20' : 'bg-blue-600/20'
                }`}>
                  <AlertTriangle className={`w-4 h-4 ${
                    alert.type === 'error' ? 'text-red-400' :
                    alert.type === 'warning' ? 'text-yellow-400' : 'text-blue-400'
                  }`} />
                </div>
                <div className="flex-1">
                  <div className="font-medium text-white">{alert.title}</div>
                  <div className="text-sm text-gray-300 mt-1">{alert.message}</div>
                  <div className="text-xs text-gray-400 mt-2">
                    {formatTime(alert.timestamp)}
                  </div>
                </div>
                {!alert.resolved && (
                  <button
                    onClick={() => setAlerts(prev => 
                      prev.map(a => a.id === alert.id ? { ...a, resolved: true } : a)
                    )}
                    className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded border border-gray-600 hover:border-gray-500"
                  >
                    Resolve
                  </button>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};