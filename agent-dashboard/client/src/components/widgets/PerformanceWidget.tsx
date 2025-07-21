import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  AreaChart, Area, BarChart, Bar, LineChart, Line, 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import { Activity, BarChart3, TrendingUp, Zap } from 'lucide-react';
import { DashboardData } from '../../types';

interface PerformanceWidgetProps {
  data: DashboardData;
  size: 'small' | 'medium' | 'large';
  compactMode?: boolean;
}

export const PerformanceWidget: React.FC<PerformanceWidgetProps> = ({ 
  data, 
  size, 
  compactMode = false 
}) => {
  const [chartType, setChartType] = useState<'area' | 'bar' | 'line'>('area');
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('1h');

  // Generate sample performance data
  const generateTimeSeriesData = () => {
    const now = new Date();
    const dataPoints = size === 'small' ? 10 : size === 'medium' ? 20 : 30;
    const intervalMinutes = timeRange === '1h' ? 6 : timeRange === '24h' ? 72 : 504; // 6min, 1.2h, 8.4h

    return Array.from({ length: dataPoints }, (_, i) => {
      const time = new Date(now.getTime() - (dataPoints - i - 1) * intervalMinutes * 60000);
      return {
        time: timeRange === '1h' 
          ? time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : timeRange === '24h'
          ? time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : time.toLocaleDateString([], { month: 'short', day: 'numeric' }),
        responseTime: Math.round(150 + Math.random() * 100 + Math.sin(i * 0.3) * 50),
        throughput: Math.round(45 + Math.random() * 30 + Math.cos(i * 0.4) * 15),
        success: Math.round(95 + Math.random() * 4),
        activeAgents: Math.round(8 + Math.random() * 4 + Math.sin(i * 0.2) * 2)
      };
    });
  };

  const performanceData = generateTimeSeriesData();
  const latestMetrics = performanceData[performanceData.length - 1];

  const chartHeight = size === 'small' ? 120 : size === 'medium' ? 200 : 250;

  const renderChart = () => {
    const commonProps = {
      data: performanceData,
      margin: { top: 5, right: 5, left: 5, bottom: 5 }
    };

    switch (chartType) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            <defs>
              <linearGradient id="responseGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="throughputGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(55 65 81)" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={10} />
            <YAxis stroke="#9ca3af" fontSize={10} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: '1px solid rgb(75 85 99)',
                borderRadius: '8px'
              }}
            />
            <Area
              type="monotone"
              dataKey="responseTime"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#responseGradient)"
            />
            {size !== 'small' && (
              <Area
                type="monotone"
                dataKey="throughput"
                stroke="#10b981"
                strokeWidth={2}
                fill="url(#throughputGradient)"
              />
            )}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(55 65 81)" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={10} />
            <YAxis stroke="#9ca3af" fontSize={10} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: '1px solid rgb(75 85 99)',
                borderRadius: '8px'
              }}
            />
            <Bar dataKey="responseTime" fill="#3b82f6" radius={[2, 2, 0, 0]} />
            {size !== 'small' && (
              <Bar dataKey="throughput" fill="#10b981" radius={[2, 2, 0, 0]} />
            )}
          </BarChart>
        );

      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(55 65 81)" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={10} />
            <YAxis stroke="#9ca3af" fontSize={10} />
            <Tooltip
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
            />
            {size !== 'small' && (
              <Line
                type="monotone"
                dataKey="throughput"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
              />
            )}
          </LineChart>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-600/20 rounded-lg">
            <Activity className={`w-${compactMode ? '4' : '5'} h-${compactMode ? '4' : '5'} text-purple-400`} />
          </div>
          <div>
            <div className={`${compactMode ? 'text-base' : 'text-lg'} font-semibold text-white`}>
              Performance Metrics
            </div>
            {!compactMode && (
              <div className="text-xs text-gray-400">
                Real-time system performance
              </div>
            )}
          </div>
        </div>

        {size !== 'small' && (
          <div className="flex items-center gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as '1h' | '24h' | '7d')}
              className="bg-gray-700/50 border border-gray-600 rounded px-2 py-1 text-xs text-white"
            >
              <option value="1h">1h</option>
              <option value="24h">24h</option>
              <option value="7d">7d</option>
            </select>
            
            <div className="flex bg-gray-700/30 rounded p-1">
              {(['area', 'bar', 'line'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => setChartType(type)}
                  className={`p-1 rounded text-xs transition-colors ${
                    chartType === type 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                  title={type.charAt(0).toUpperCase() + type.slice(1)}
                >
                  {type === 'area' ? '📈' : type === 'bar' ? '📊' : '📉'}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Key Stats Row */}
      <div className={`grid ${size === 'small' ? 'grid-cols-2' : 'grid-cols-4'} gap-3`}>
        {[
          { label: 'Response Time', value: `${latestMetrics.responseTime}ms`, color: 'blue' },
          { label: 'Throughput', value: `${latestMetrics.throughput}/min`, color: 'green' },
          ...(size !== 'small' ? [
            { label: 'Success Rate', value: `${latestMetrics.success}%`, color: 'purple' },
            { label: 'Active Agents', value: latestMetrics.activeAgents.toString(), color: 'yellow' }
          ] : [])
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-700/30 rounded-lg p-3"
          >
            <div className={`text-${compactMode ? 'sm' : 'base'} font-bold text-white`}>
              {stat.value}
            </div>
            <div className={`text-gray-400 ${compactMode ? 'text-xs' : 'text-sm'}`}>
              {stat.label}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Performance Chart */}
      <div className="mt-4">
        <ResponsiveContainer width="100%" height={chartHeight}>
          {renderChart()}
        </ResponsiveContainer>
      </div>

      {/* Performance Indicators */}
      {size === 'large' && (
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="space-y-2">
            <div className="text-sm text-gray-300">Response Time Trend</div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-400" />
              <span className="text-green-400 text-sm">12% improvement</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm text-gray-300">System Health</div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-green-400 text-sm">All systems operational</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};