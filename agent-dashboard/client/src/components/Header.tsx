import { motion } from 'framer-motion'
import { Activity, Wifi, WifiOff, Cpu, Zap } from 'lucide-react'

interface HeaderProps {
  isConnected: boolean
}

export default function Header({ isConnected }: HeaderProps) {
  return (
    <header className="bg-gray-900/50 backdrop-blur-md border-b border-gray-800">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <motion.div
              initial={{ rotate: 0 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="text-neon-blue"
            >
              <Cpu size={32} />
            </motion.div>
            <div>
              <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-neon-blue to-neon-purple glitch" data-text="OA Command Center">
                OA Command Center
              </h1>
              <p className="text-sm text-gray-400">Super Agent Monitoring System</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <Zap className="text-neon-yellow" size={20} />
              <span className="text-sm text-gray-300">System Active</span>
            </div>
            
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <>
                  <Wifi className="text-neon-green" size={20} />
                  <span className="text-sm text-neon-green">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="text-red-500" size={20} />
                  <span className="text-sm text-red-500">Disconnected</span>
                </>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <Activity className="text-neon-blue animate-pulse" size={20} />
              <span className="text-sm text-gray-300">
                {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}