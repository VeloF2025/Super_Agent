import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Cpu, Activity, CheckCircle, AlertCircle } from 'lucide-react';

interface JarvisStatusProps {
  wsConnected: boolean;
  ws: WebSocket | null;
}

interface JarvisData {
  status: string;
  message: string;
  orchestrator: string;
  systemHealth?: {
    totalAgents: number;
    activeAgents: number;
    recentActivities: number;
    uptime: string;
  };
}

export const JarvisStatus: React.FC<JarvisStatusProps> = ({ wsConnected, ws }) => {
  const [jarvisData, setJarvisData] = useState<JarvisData | null>(null);
  const [jarvisResponse, setJarvisResponse] = useState<string>('');
  const [showResponse, setShowResponse] = useState(false);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'initial' && data.data.jarvis) {
          setJarvisData(data.data.jarvis);
        } else if (data.type === 'jarvis-response') {
          setJarvisResponse(data.data.message);
          setShowResponse(true);
          setTimeout(() => setShowResponse(false), 5000);
        } else if (data.type === 'jarvis-initialized') {
          console.log('Jarvis initialized:', data);
          fetchJarvisStatus();
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.addEventListener('message', handleMessage);
    return () => ws.removeEventListener('message', handleMessage);
  }, [ws]);

  const fetchJarvisStatus = async () => {
    try {
      const response = await fetch('/api/jarvis/status');
      const data = await response.json();
      setJarvisData(data);
    } catch (error) {
      console.error('Error fetching Jarvis status:', error);
    }
  };

  const testJarvis = (message: string) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'jarvis-query',
        message: message
      }));
    }
  };

  const getStatusIcon = () => {
    if (!jarvisData) return <AlertCircle className="w-5 h-5 text-gray-400" />;
    
    switch (jarvisData.status) {
      case 'operational':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'initializing':
        return <Activity className="w-5 h-5 text-yellow-500 animate-pulse" />;
      default:
        return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusColor = () => {
    if (!jarvisData) return 'bg-gray-100 border-gray-300';
    
    switch (jarvisData.status) {
      case 'operational':
        return 'bg-green-50 border-green-300 hover:border-green-400';
      case 'initializing':
        return 'bg-yellow-50 border-yellow-300 hover:border-yellow-400';
      default:
        return 'bg-red-50 border-red-300 hover:border-red-400';
    }
  };

  return (
    <div className="relative">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-4 rounded-lg border-2 transition-all duration-200 ${getStatusColor()}`}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-600" />
            <h3 className="text-lg font-semibold">Jarvis Orchestrator</h3>
            {getStatusIcon()}
          </div>
          {wsConnected && (
            <button
              onClick={() => testJarvis('Hey Jarvis')}
              className="px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
            >
              Call Jarvis
            </button>
          )}
        </div>

        {jarvisData && (
          <div className="space-y-2 text-sm">
            <p className="text-gray-600">{jarvisData.message}</p>
            
            {jarvisData.systemHealth && (
              <div className="grid grid-cols-2 gap-2 mt-3">
                <div className="flex items-center gap-1">
                  <Cpu className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-700">
                    {jarvisData.systemHealth.activeAgents}/{jarvisData.systemHealth.totalAgents} agents
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <Activity className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-700">
                    {jarvisData.systemHealth.recentActivities} activities
                  </span>
                </div>
              </div>
            )}
            
            {jarvisData.systemHealth?.uptime && (
              <p className="text-xs text-gray-500 mt-2">
                Uptime: {jarvisData.systemHealth.uptime}
              </p>
            )}
          </div>
        )}
      </motion.div>

      <AnimatePresence>
        {showResponse && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute top-full mt-2 left-0 right-0 p-4 bg-purple-100 border-2 border-purple-300 rounded-lg shadow-lg z-50"
          >
            <div className="flex items-start gap-2">
              <Brain className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-purple-900">Jarvis Response:</p>
                <p className="text-purple-800">{jarvisResponse}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick test buttons */}
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          onClick={() => testJarvis('Jarvis?')}
          className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
        >
          Test "Jarvis?"
        </button>
        <button
          onClick={() => testJarvis('Hey Jarvis')}
          className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
        >
          Test "Hey Jarvis"
        </button>
        <button
          onClick={() => testJarvis('Is Jarvis online?')}
          className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
        >
          Test "Is Jarvis online?"
        </button>
      </div>
    </div>
  );
};