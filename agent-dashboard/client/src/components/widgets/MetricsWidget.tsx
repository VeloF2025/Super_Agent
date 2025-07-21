import React from 'react';
import { motion } from 'framer-motion';
import { Bot, CheckCircle, TrendingUp, Zap, TrendingDown } from 'lucide-react';
import { DashboardData } from '../../types';

interface MetricsWidgetProps {
  data: DashboardData;
  size: 'small' | 'medium' | 'large';
  compactMode?: boolean;
}

export const MetricsWidget: React.FC<MetricsWidgetProps> = ({ 
  data, 
  size, 
  compactMode = false 
}) => {
  const { metrics, agents, activities } = data;
  const onlineAgents = agents.filter(a => a.status !== 'offline');
  const activeAgents = agents.filter(a => a.status === 'working');

  const metricsData = [
    {
      title: 'Active Agents',
      value: activeAgents.length,
      total: onlineAgents.length,
      icon: Bot,
      color: 'blue',
      trend: '+12%',
      trendUp: true
    },
    {
      title: 'Tasks Completed',
      value: activities.filter(a => a.type === 'task-complete').length,
      icon: CheckCircle,
      color: 'green',
      trend: '+8%',
      trendUp: true
    },
    {
      title: 'Success Rate',
      value: `${metrics?.activities?.successRate || 0}%`,
      icon: TrendingUp,
      color: 'purple',
      trend: '+2%',
      trendUp: true
    },
    {
      title: 'Avg Response',
      value: `${metrics?.performance?.avgResponseTime || 0}ms`,
      icon: Zap,
      color: 'yellow',
      trend: '-15ms',
      trendUp: true
    }
  ];

  const gridCols = size === 'large' ? 'grid-cols-2 lg:grid-cols-4' : 
                   size === 'medium' ? 'grid-cols-2' : 'grid-cols-1';

  const itemsToShow = size === 'small' ? 2 : 
                     size === 'medium' ? 4 : 4;

  return (
    <div className={`grid gap-${compactMode ? '3' : '4'} ${gridCols}`}>
      {metricsData.slice(0, itemsToShow).map((metric, index) => (
        <motion.div
          key={metric.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className={`bg-gray-700/30 rounded-lg border border-gray-600/30 ${
            compactMode ? 'p-3' : 'p-4'
          } hover:border-gray-500/50 transition-colors`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className={`p-2 rounded-lg bg-${metric.color}-600/20`}>
              <metric.icon className={`w-${compactMode ? '4' : '5'} h-${compactMode ? '4' : '5'} text-${metric.color}-400`} />
            </div>
            <div className={`flex items-center gap-1 text-xs ${
              metric.trendUp ? 'text-green-400' : 'text-red-400'
            }`}>
              {metric.trendUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {metric.trend}
            </div>
          </div>
          
          <div>
            <div className={`${compactMode ? 'text-lg' : 'text-xl'} font-bold text-white mb-1`}>
              {metric.value}
              {metric.total && (
                <span className="text-gray-400 text-sm">/{metric.total}</span>
              )}
            </div>
            <div className={`text-gray-400 ${compactMode ? 'text-xs' : 'text-sm'}`}>
              {metric.title}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
};