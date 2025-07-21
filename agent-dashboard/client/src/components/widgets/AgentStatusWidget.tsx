import React from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Bot, Users } from 'lucide-react';
import { DashboardData } from '../../types';

interface AgentStatusWidgetProps {
  data: DashboardData;
  size: 'small' | 'medium' | 'large';
  compactMode?: boolean;
}

export const AgentStatusWidget: React.FC<AgentStatusWidgetProps> = ({ 
  data, 
  size, 
  compactMode = false 
}) => {
  const { agents } = data;

  const statusCounts = agents.reduce((acc, agent) => {
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

  const chartData = Object.entries(statusCounts).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    color: statusColors[status as keyof typeof statusColors] || '#6b7280',
    percentage: Math.round((count / agents.length) * 100)
  }));

  const chartSize = size === 'small' ? 120 : size === 'medium' ? 160 : 200;
  const innerRadius = size === 'small' ? 35 : size === 'medium' ? 50 : 60;
  const outerRadius = size === 'small' ? 55 : size === 'medium' ? 70 : 80;

  return (
    <div className="space-y-4">
      {/* Header Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600/20 rounded-lg">
            <Users className={`w-${compactMode ? '4' : '5'} h-${compactMode ? '4' : '5'} text-blue-400`} />
          </div>
          <div>
            <div className={`${compactMode ? 'text-lg' : 'text-xl'} font-bold text-white`}>
              {agents.length}
            </div>
            <div className={`text-gray-400 ${compactMode ? 'text-xs' : 'text-sm'}`}>
              Total Agents
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className={`${compactMode ? 'text-sm' : 'text-base'} font-medium text-green-400`}>
            {agents.filter(a => a.status !== 'offline').length} Online
          </div>
          <div className={`text-gray-400 ${compactMode ? 'text-xs' : 'text-sm'}`}>
            {Math.round((agents.filter(a => a.status !== 'offline').length / agents.length) * 100)}% Availability
          </div>
        </div>
      </div>

      {/* Chart and Legend */}
      <div className={`flex ${size === 'large' ? 'flex-row' : 'flex-col'} items-center gap-${compactMode ? '4' : '6'}`}>
        {/* Pie Chart */}
        <div className="flex-shrink-0">
          <ResponsiveContainer width={chartSize} height={chartSize}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={innerRadius}
                outerRadius={outerRadius}
                paddingAngle={5}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgb(31 41 55)',
                  border: '1px solid rgb(75 85 99)',
                  borderRadius: '8px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-2">
          {chartData.map((item, index) => (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }} 
                />
                <span className={`text-gray-300 ${compactMode ? 'text-sm' : 'text-base'}`}>
                  {item.name}
                </span>
              </div>
              <div className="text-right">
                <div className={`text-white font-medium ${compactMode ? 'text-sm' : 'text-base'}`}>
                  {item.value}
                </div>
                <div className={`text-gray-400 ${compactMode ? 'text-xs' : 'text-sm'}`}>
                  {item.percentage}%
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Agent Grid (for larger sizes) */}
      {size === 'large' && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Recent Agent Activity</h4>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
            {agents.slice(0, 6).map((agent, index) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center gap-2 p-2 bg-gray-700/30 rounded-lg"
              >
                <div 
                  className={`w-2 h-2 rounded-full ${
                    agent.status === 'working' ? 'bg-blue-400' :
                    agent.status === 'online' ? 'bg-green-400' :
                    agent.status === 'idle' ? 'bg-yellow-400' :
                    agent.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
                  }`} 
                />
                <span className="text-xs text-gray-300 truncate">
                  {agent.name}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};