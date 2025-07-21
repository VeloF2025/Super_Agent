import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  ScatterChart, Scatter, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import {
  TrendingUp, TrendingDown, Activity, Zap, Users, Clock,
  Target, Cpu, Database, Network, BarChart3, PieChart as PieChartIcon,
  LineChart as LineChartIcon, Scatter as ScatterIcon
} from 'lucide-react';
import { DashboardData } from '../types';

interface DataVisualizationProps {
  data: DashboardData;
  timeRange: '1h' | '24h' | '7d' | '30d';
  onTimeRangeChange: (range: '1h' | '24h' | '7d' | '30d') => void;
}

interface MetricTrend {
  metric: string;
  current: number;
  previous: number;
  change: number;
  changePercent: number;
  trend: 'up' | 'down' | 'stable';
}

export const DataVisualization: React.FC<DataVisualizationProps> = ({
  data,
  timeRange,
  onTimeRangeChange
}) => {
  const [selectedChart, setSelectedChart] = useState<'area' | 'bar' | 'line' | 'scatter' | 'radar'>('area');
  const [selectedMetric, setSelectedMetric] = useState<'performance' | 'agents' | 'activities' | 'system'>('performance');

  // Generate enhanced time series data
  const generateTimeSeriesData = useMemo(() => {
    const now = new Date();
    const dataPoints = {
      '1h': 12, // 5-minute intervals
      '24h': 24, // 1-hour intervals  
      '7d': 14, // 12-hour intervals
      '30d': 30 // 1-day intervals
    }[timeRange];

    const intervals = {
      '1h': 5 * 60 * 1000, // 5 minutes
      '24h': 60 * 60 * 1000, // 1 hour
      '7d': 12 * 60 * 60 * 1000, // 12 hours
      '30d': 24 * 60 * 60 * 1000 // 1 day
    }[timeRange];

    return Array.from({ length: dataPoints }, (_, i) => {
      const time = new Date(now.getTime() - (dataPoints - i - 1) * intervals);
      const hour = time.getHours();
      const dayOfWeek = time.getDay();
      
      // Simulate realistic patterns based on time
      const businessHoursMultiplier = (hour >= 9 && hour <= 17) ? 1.5 : 0.7;
      const weekdayMultiplier = (dayOfWeek >= 1 && dayOfWeek <= 5) ? 1.2 : 0.8;
      
      return {
        timestamp: time.getTime(),
        time: timeRange === '1h' || timeRange === '24h' 
          ? time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : time.toLocaleDateString([], { month: 'short', day: 'numeric' }),
        
        // Performance metrics
        responseTime: Math.round(
          120 + Math.random() * 80 + 
          Math.sin(i * 0.3) * 30 + 
          (businessHoursMultiplier * 20)
        ),
        throughput: Math.round(
          40 * businessHoursMultiplier * weekdayMultiplier + 
          Math.random() * 20 + Math.cos(i * 0.4) * 10
        ),
        errorRate: Math.max(0, Math.round(
          2 + Math.random() * 3 + Math.sin(i * 0.5) * 1.5 - (businessHoursMultiplier * 0.5)
        )),
        
        // Agent metrics
        activeAgents: Math.round(
          8 * businessHoursMultiplier * weekdayMultiplier + 
          Math.random() * 4 + Math.sin(i * 0.2) * 2
        ),
        totalRequests: Math.round(
          200 * businessHoursMultiplier * weekdayMultiplier + 
          Math.random() * 100 + Math.cos(i * 0.3) * 50
        ),
        
        // Activity metrics
        tasksCompleted: Math.round(
          25 * businessHoursMultiplier * weekdayMultiplier + 
          Math.random() * 15 + Math.sin(i * 0.4) * 8
        ),
        tasksQueued: Math.round(
          5 + Math.random() * 10 + Math.cos(i * 0.6) * 3
        ),
        
        // System metrics
        cpuUsage: Math.round(
          30 + Math.random() * 40 + 
          Math.sin(i * 0.25) * 15 + (businessHoursMultiplier * 10)
        ),
        memoryUsage: Math.round(
          45 + Math.random() * 30 + 
          Math.cos(i * 0.35) * 12 + (businessHoursMultiplier * 8)
        ),
        networkIO: Math.round(
          60 * businessHoursMultiplier + Math.random() * 25 + Math.sin(i * 0.4) * 15
        )
      };
    });
  }, [timeRange]);

  // Calculate metric trends
  const metricTrends = useMemo((): MetricTrend[] => {
    const recent = generateTimeSeriesData.slice(-5);
    const previous = generateTimeSeriesData.slice(-10, -5);
    
    const calculateTrend = (metric: keyof typeof recent[0]) => {
      const currentAvg = recent.reduce((acc, d) => acc + (d[metric] as number), 0) / recent.length;
      const previousAvg = previous.reduce((acc, d) => acc + (d[metric] as number), 0) / previous.length;
      const change = currentAvg - previousAvg;
      const changePercent = (change / previousAvg) * 100;
      
      return {
        metric: metric.toString(),
        current: Math.round(currentAvg),
        previous: Math.round(previousAvg),
        change: Math.round(change * 100) / 100,
        changePercent: Math.round(changePercent * 100) / 100,
        trend: Math.abs(changePercent) < 1 ? 'stable' : changePercent > 0 ? 'up' : 'down'
      } as MetricTrend;
    };

    return [
      calculateTrend('responseTime'),
      calculateTrend('throughput'),
      calculateTrend('activeAgents'),
      calculateTrend('tasksCompleted'),
      calculateTrend('cpuUsage'),
      calculateTrend('memoryUsage')
    ];
  }, [generateTimeSeriesData]);

  // Chart data based on selected metric
  const chartData = useMemo(() => {
    const metricFields = {
      performance: ['responseTime', 'throughput', 'errorRate'],
      agents: ['activeAgents', 'totalRequests'],
      activities: ['tasksCompleted', 'tasksQueued'],
      system: ['cpuUsage', 'memoryUsage', 'networkIO']
    };

    return generateTimeSeriesData.map(d => {
      const result: any = { time: d.time, timestamp: d.timestamp };
      metricFields[selectedMetric].forEach(field => {
        result[field] = d[field as keyof typeof d];
      });
      return result;
    });
  }, [generateTimeSeriesData, selectedMetric]);

  // Color schemes for different metrics
  const colorScheme = {
    performance: ['#3b82f6', '#10b981', '#ef4444'],
    agents: ['#8b5cf6', '#06b6d4'],
    activities: ['#f59e0b', '#84cc16'],
    system: ['#ec4899', '#14b8a6', '#f97316']
  };

  // Radar chart data for system overview
  const radarData = useMemo(() => {
    const latest = generateTimeSeriesData[generateTimeSeriesData.length - 1];
    return [
      { metric: 'Performance', value: Math.round((200 - latest.responseTime) / 2), fullMark: 100 },
      { metric: 'Throughput', value: Math.round(latest.throughput * 1.5), fullMark: 100 },
      { metric: 'Reliability', value: Math.round(100 - latest.errorRate * 10), fullMark: 100 },
      { metric: 'Efficiency', value: Math.round(100 - latest.cpuUsage), fullMark: 100 },
      { metric: 'Capacity', value: Math.round(100 - latest.memoryUsage), fullMark: 100 },
      { metric: 'Activity', value: Math.round(latest.activeAgents * 10), fullMark: 100 }
    ];
  }, [generateTimeSeriesData]);

  const renderChart = () => {
    const commonProps = {
      data: chartData,
      margin: { top: 10, right: 30, left: 0, bottom: 0 }
    };

    const colors = colorScheme[selectedMetric];

    switch (selectedChart) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            <defs>
              {colors.map((color, index) => (
                <linearGradient key={index} id={`gradient${index}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(55 65 81)" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
            <YAxis stroke="#9ca3af" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: '1px solid rgb(75 85 99)',
                borderRadius: '8px'
              }}
            />
            <Legend />
            {Object.keys(chartData[0] || {}).filter(key => key !== 'time' && key !== 'timestamp').map((key, index) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                fill={`url(#gradient${index % colors.length})`}
                name={key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(55 65 81)" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
            <YAxis stroke="#9ca3af" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: '1px solid rgb(75 85 99)',
                borderRadius: '8px'
              }}
            />
            <Legend />
            {Object.keys(chartData[0] || {}).filter(key => key !== 'time' && key !== 'timestamp').map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                fill={colors[index % colors.length]}
                radius={[2, 2, 0, 0]}
                name={key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}
              />
            ))}
          </BarChart>
        );

      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(55 65 81)" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
            <YAxis stroke="#9ca3af" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: '1px solid rgb(75 85 99)',
                borderRadius: '8px'
              }}
            />
            <Legend />
            {Object.keys(chartData[0] || {}).filter(key => key !== 'time' && key !== 'timestamp').map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={false}
                name={key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}
              />
            ))}
          </LineChart>
        );

      case 'radar':
        return (
          <RadarChart data={radarData} margin={{ top: 40, right: 40, bottom: 40, left: 40 }}>
            <PolarGrid stroke="rgb(55 65 81)" />
            <PolarAngleAxis dataKey="metric" className="text-gray-300" fontSize={12} />
            <PolarRadiusAxis
              angle={60}
              domain={[0, 100]}
              className="text-gray-400"
              fontSize={10}
            />
            <Radar
              name="System Metrics"
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.2}
              strokeWidth={2}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: '1px solid rgb(75 85 99)',
                borderRadius: '8px'
              }}
            />
          </RadarChart>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Advanced Analytics</h2>
          <p className="text-gray-400">Deep insights into system performance and trends</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => onTimeRangeChange(e.target.value as any)}
            className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>

          {/* Metric Selector */}
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value as any)}
            className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="performance">Performance</option>
            <option value="agents">Agents</option>
            <option value="activities">Activities</option>
            <option value="system">System</option>
          </select>

          {/* Chart Type Selector */}
          <div className="flex bg-gray-700/30 rounded-lg p-1">
            {[
              { type: 'area', icon: BarChart3 },
              { type: 'bar', icon: BarChart3 },
              { type: 'line', icon: LineChartIcon },
              { type: 'radar', icon: Target }
            ].map(({ type, icon: Icon }) => (
              <button
                key={type}
                onClick={() => setSelectedChart(type as any)}
                className={`p-2 rounded-md transition-colors ${
                  selectedChart === type 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
                title={type.charAt(0).toUpperCase() + type.slice(1)}
              >
                <Icon className="w-4 h-4" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Metric Trends Summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {metricTrends.map((trend, index) => (
          <motion.div
            key={trend.metric}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-4"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400 uppercase tracking-wide">
                {trend.metric.replace(/([A-Z])/g, ' $1').trim()}
              </span>
              {trend.trend === 'up' ? (
                <TrendingUp className="w-3 h-3 text-green-400" />
              ) : trend.trend === 'down' ? (
                <TrendingDown className="w-3 h-3 text-red-400" />
              ) : (
                <div className="w-3 h-3 bg-gray-400 rounded-full" />
              )}
            </div>
            <div className="text-lg font-bold text-white">{trend.current}</div>
            <div className={`text-xs ${
              trend.trend === 'up' ? 'text-green-400' : 
              trend.trend === 'down' ? 'text-red-400' : 'text-gray-400'
            }`}>
              {trend.changePercent > 0 ? '+' : ''}{trend.changePercent.toFixed(1)}%
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main Chart */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6"
      >
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Insights Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4">Key Insights</h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            {
              title: 'Peak Performance',
              value: `${timeRange === '1h' ? '3:45 PM' : 'Tuesday 2-4 PM'}`,
              description: 'Highest throughput period',
              icon: Zap,
              color: 'text-yellow-400'
            },
            {
              title: 'Optimal Load',
              value: '68%',
              description: 'Average system utilization',
              icon: Cpu,
              color: 'text-blue-400'
            },
            {
              title: 'Efficiency Score',
              value: '94.2%',
              description: 'Task completion rate',
              icon: Target,
              color: 'text-green-400'
            }
          ].map((insight, index) => (
            <div key={insight.title} className="flex items-start gap-3 p-3 bg-gray-700/30 rounded-lg">
              <div className={`p-2 rounded-lg bg-gray-600/50 ${insight.color}`}>
                <insight.icon className="w-5 h-5" />
              </div>
              <div>
                <div className="font-semibold text-white">{insight.value}</div>
                <div className="text-sm text-gray-300">{insight.title}</div>
                <div className="text-xs text-gray-400">{insight.description}</div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};