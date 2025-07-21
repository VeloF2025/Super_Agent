import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface MetricCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend: string
  color: 'blue' | 'green' | 'yellow' | 'purple'
}

export default function MetricCard({ title, value, icon: Icon, trend, color }: MetricCardProps) {
  const colorClasses = {
    blue: 'from-blue-500/20 to-blue-600/20 border-blue-500/30 text-blue-400',
    green: 'from-green-500/20 to-green-600/20 border-green-500/30 text-green-400',
    yellow: 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30 text-yellow-400',
    purple: 'from-purple-500/20 to-purple-600/20 border-purple-500/30 text-purple-400',
  }

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={clsx(
        'bg-gradient-to-br backdrop-blur-md rounded-xl border p-6 relative overflow-hidden',
        colorClasses[color]
      )}
    >
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-400">{title}</h3>
          <Icon className={clsx('w-5 h-5', colorClasses[color].split(' ')[3])} />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-gray-100">{value}</span>
        </div>
        <p className="text-xs text-gray-500 mt-2">{trend}</p>
      </div>
      
      {/* Background decoration */}
      <div className="absolute -bottom-8 -right-8 w-32 h-32 rounded-full bg-gradient-to-br from-white/5 to-transparent" />
    </motion.div>
  )
}