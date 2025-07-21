import { motion } from 'framer-motion'
import { Filter, FolderOpen, X } from 'lucide-react'
import clsx from 'clsx'

interface ProjectFilterProps {
  projects: string[]
  selectedProject: string | null
  onProjectSelect: (project: string | null) => void
}

export default function ProjectFilter({ projects, selectedProject, onProjectSelect }: ProjectFilterProps) {
  const uniqueProjects = Array.from(new Set(projects)).sort()

  return (
    <div className="flex items-center space-x-4">
      <div className="flex items-center space-x-2 text-gray-400">
        <Filter className="w-4 h-4" />
        <span className="text-sm">Filter by Project:</span>
      </div>
      
      <div className="flex items-center space-x-2">
        <button
          onClick={() => onProjectSelect(null)}
          className={clsx(
            'px-3 py-1 rounded-lg text-sm transition-all',
            selectedProject === null
              ? 'bg-neon-blue/20 text-neon-blue border border-neon-blue/30'
              : 'bg-gray-800/30 text-gray-400 hover:bg-gray-800/50 border border-gray-700'
          )}
        >
          All Projects
        </button>
        
        {uniqueProjects.map((project) => (
          <motion.button
            key={project}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onProjectSelect(project)}
            className={clsx(
              'px-3 py-1 rounded-lg text-sm transition-all flex items-center space-x-1',
              selectedProject === project
                ? 'bg-neon-purple/20 text-neon-purple border border-neon-purple/30'
                : 'bg-gray-800/30 text-gray-400 hover:bg-gray-800/50 border border-gray-700'
            )}
          >
            <FolderOpen className="w-3 h-3" />
            <span>{project}</span>
          </motion.button>
        ))}
        
        {selectedProject && (
          <button
            onClick={() => onProjectSelect(null)}
            className="p-1 rounded hover:bg-gray-800/50 text-gray-500 hover:text-gray-300"
            title="Clear filter"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}