import React, { useState } from 'react';
import { motion, Reorder } from 'framer-motion';
import { MoreVertical, Maximize2, Minimize2, X, Eye, EyeOff } from 'lucide-react';
import { DashboardPreferences } from '../DashboardSettings';

interface WidgetContainerProps {
  id: string;
  title: string;
  size: 'small' | 'medium' | 'large';
  children: React.ReactNode;
  onSizeChange?: (size: 'small' | 'medium' | 'large') => void;
  onToggleVisibility?: () => void;
  onRemove?: () => void;
  preferences: DashboardPreferences;
  isVisible?: boolean;
}

const sizeClasses = {
  small: 'col-span-1 row-span-1',
  medium: 'col-span-1 lg:col-span-2 row-span-1',
  large: 'col-span-1 lg:col-span-3 row-span-2'
};

const minHeights = {
  small: 'min-h-[200px]',
  medium: 'min-h-[300px]',
  large: 'min-h-[400px]'
};

export const WidgetContainer: React.FC<WidgetContainerProps> = ({
  id,
  title,
  size,
  children,
  onSizeChange,
  onToggleVisibility,
  onRemove,
  preferences,
  isVisible = true
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  if (!isVisible) return null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={preferences.animationsEnabled ? { scale: 1.01 } : undefined}
      className={`
        ${sizeClasses[size]} 
        ${minHeights[size]}
        ${preferences.compactMode ? 'p-3' : 'p-6'}
        bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 
        hover:border-gray-600/50 transition-all duration-200 relative group
        ${isExpanded ? 'z-20 fixed inset-4 max-w-6xl max-h-[90vh] mx-auto overflow-auto' : ''}
      `}
    >
      {/* Widget Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className={`font-semibold text-white ${preferences.compactMode ? 'text-base' : 'text-lg'}`}>
          {title}
        </h3>
        
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {/* Expand/Collapse Button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-400 hover:text-white transition-colors"
            title={isExpanded ? 'Minimize' : 'Expand'}
          >
            {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          {/* Options Menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 text-gray-400 hover:text-white transition-colors"
            >
              <MoreVertical className="w-4 h-4" />
            </button>

            <AnimatePresence>
              {showMenu && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: -10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: -10 }}
                  className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-30 py-1 min-w-[140px]"
                >
                  <div className="px-2 py-1 text-xs text-gray-400 border-b border-gray-700 mb-1">
                    Widget Size
                  </div>
                  
                  {(['small', 'medium', 'large'] as const).map((sizeOption) => (
                    <button
                      key={sizeOption}
                      onClick={() => {
                        onSizeChange?.(sizeOption);
                        setShowMenu(false);
                      }}
                      className={`w-full text-left px-3 py-1 text-sm hover:bg-gray-700 transition-colors ${
                        size === sizeOption ? 'text-blue-400' : 'text-gray-300'
                      }`}
                    >
                      {sizeOption.charAt(0).toUpperCase() + sizeOption.slice(1)}
                    </button>
                  ))}

                  <hr className="border-gray-700 my-1" />
                  
                  <button
                    onClick={() => {
                      onToggleVisibility?.();
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-3 py-1 text-sm text-gray-300 hover:bg-gray-700 transition-colors flex items-center gap-2"
                  >
                    <EyeOff className="w-3 h-3" />
                    Hide Widget
                  </button>

                  {onRemove && (
                    <button
                      onClick={() => {
                        onRemove();
                        setShowMenu(false);
                      }}
                      className="w-full text-left px-3 py-1 text-sm text-red-400 hover:bg-gray-700 transition-colors flex items-center gap-2"
                    >
                      <X className="w-3 h-3" />
                      Remove
                    </button>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Widget Content */}
      <div className={`${isExpanded ? 'h-full overflow-auto' : ''}`}>
        {children}
      </div>

      {/* Click outside to close menu */}
      {showMenu && (
        <div 
          className="fixed inset-0 z-10" 
          onClick={() => setShowMenu(false)} 
        />
      )}

      {/* Expanded overlay background */}
      {isExpanded && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-10"
          onClick={() => setIsExpanded(false)}
        />
      )}
    </motion.div>
  );
};