import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings, X, Save, RotateCcw, Monitor, Moon, Sun, Palette,
  Bell, Zap, Clock, Eye, EyeOff, Grid, List, BarChart3,
  Sliders, Download, Upload, RefreshCw, Wifi, Database
} from 'lucide-react';

export interface DashboardPreferences {
  theme: 'light' | 'dark' | 'auto';
  layout: 'grid' | 'list' | 'compact';
  refreshInterval: number;
  autoRefresh: boolean;
  enableNotifications: boolean;
  enableWebSocket: boolean;
  retryAttempts: number;
  batchUpdates: boolean;
  showSystemHealth: boolean;
  showMLInsights: boolean;
  showPerformanceCharts: boolean;
  compactMode: boolean;
  animationsEnabled: boolean;
  soundEnabled: boolean;
  colorScheme: 'blue' | 'purple' | 'green' | 'red' | 'orange';
  widgetSettings: {
    [key: string]: {
      visible: boolean;
      size: 'small' | 'medium' | 'large';
      position?: { x: number; y: number };
    };
  };
}

const defaultPreferences: DashboardPreferences = {
  theme: 'dark',
  layout: 'grid',
  refreshInterval: 5000,
  autoRefresh: true,
  enableNotifications: true,
  enableWebSocket: true,
  retryAttempts: 3,
  batchUpdates: true,
  showSystemHealth: true,
  showMLInsights: true,
  showPerformanceCharts: true,
  compactMode: false,
  animationsEnabled: true,
  soundEnabled: false,
  colorScheme: 'blue',
  widgetSettings: {
    'metrics': { visible: true, size: 'large' },
    'agent-status': { visible: true, size: 'medium' },
    'performance': { visible: true, size: 'large' },
    'activities': { visible: true, size: 'large' },
    'system-health': { visible: true, size: 'medium' },
    'ml-insights': { visible: true, size: 'medium' },
  }
};

interface DashboardSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  preferences: DashboardPreferences;
  onPreferencesChange: (preferences: DashboardPreferences) => void;
}

export const DashboardSettings: React.FC<DashboardSettingsProps> = ({
  isOpen,
  onClose,
  preferences,
  onPreferencesChange
}) => {
  const [localPreferences, setLocalPreferences] = useState<DashboardPreferences>(preferences);
  const [hasChanges, setHasChanges] = useState(false);
  const [activeTab, setActiveTab] = useState<'general' | 'appearance' | 'performance' | 'widgets'>('general');

  useEffect(() => {
    setLocalPreferences(preferences);
    setHasChanges(false);
  }, [preferences]);

  useEffect(() => {
    const changed = JSON.stringify(localPreferences) !== JSON.stringify(preferences);
    setHasChanges(changed);
  }, [localPreferences, preferences]);

  const handleSave = () => {
    onPreferencesChange(localPreferences);
    setHasChanges(false);
  };

  const handleReset = () => {
    setLocalPreferences(defaultPreferences);
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(localPreferences, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'dashboard-preferences.json';
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (event) => {
      const file = (event.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const imported = JSON.parse(e.target?.result as string);
            setLocalPreferences(imported);
          } catch (error) {
            alert('Error importing preferences: Invalid JSON file');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  if (!isOpen) return null;

  const tabContent = {
    general: (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Data & Updates</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Auto Refresh</label>
                <p className="text-xs text-gray-400">Automatically update dashboard data</p>
              </div>
              <button
                onClick={() => setLocalPreferences(prev => ({ ...prev, autoRefresh: !prev.autoRefresh }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localPreferences.autoRefresh ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  localPreferences.autoRefresh ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-300 block mb-2">
                Refresh Interval: {localPreferences.refreshInterval / 1000}s
              </label>
              <input
                type="range"
                min="1000"
                max="30000"
                step="1000"
                value={localPreferences.refreshInterval}
                onChange={(e) => setLocalPreferences(prev => ({ 
                  ...prev, 
                  refreshInterval: parseInt(e.target.value) 
                }))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>1s</span>
                <span>30s</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">WebSocket Connection</label>
                <p className="text-xs text-gray-400">Use real-time WebSocket updates</p>
              </div>
              <button
                onClick={() => setLocalPreferences(prev => ({ ...prev, enableWebSocket: !prev.enableWebSocket }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localPreferences.enableWebSocket ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  localPreferences.enableWebSocket ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Notifications</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Enable Notifications</label>
                <p className="text-xs text-gray-400">Get alerts for system events</p>
              </div>
              <button
                onClick={() => setLocalPreferences(prev => ({ ...prev, enableNotifications: !prev.enableNotifications }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localPreferences.enableNotifications ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  localPreferences.enableNotifications ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Sound Notifications</label>
                <p className="text-xs text-gray-400">Play sounds for alerts</p>
              </div>
              <button
                onClick={() => setLocalPreferences(prev => ({ ...prev, soundEnabled: !prev.soundEnabled }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localPreferences.soundEnabled ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  localPreferences.soundEnabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>
      </div>
    ),

    appearance: (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Theme</h3>
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'light', label: 'Light', icon: Sun },
              { id: 'dark', label: 'Dark', icon: Moon },
              { id: 'auto', label: 'Auto', icon: Monitor }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setLocalPreferences(prev => ({ ...prev, theme: id as any }))}
                className={`flex flex-col items-center p-3 rounded-lg border-2 transition-colors ${
                  localPreferences.theme === id
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <Icon className="w-6 h-6 mb-2" />
                <span className="text-sm">{label}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Color Scheme</h3>
          <div className="flex gap-3">
            {[
              { id: 'blue', color: 'bg-blue-500' },
              { id: 'purple', color: 'bg-purple-500' },
              { id: 'green', color: 'bg-green-500' },
              { id: 'red', color: 'bg-red-500' },
              { id: 'orange', color: 'bg-orange-500' }
            ].map(({ id, color }) => (
              <button
                key={id}
                onClick={() => setLocalPreferences(prev => ({ ...prev, colorScheme: id as any }))}
                className={`w-10 h-10 rounded-full ${color} ${
                  localPreferences.colorScheme === id
                    ? 'ring-4 ring-white ring-opacity-50'
                    : 'hover:scale-110'
                } transition-transform`}
              />
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Layout</h3>
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'grid', label: 'Grid', icon: Grid },
              { id: 'list', label: 'List', icon: List },
              { id: 'compact', label: 'Compact', icon: BarChart3 }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setLocalPreferences(prev => ({ ...prev, layout: id as any }))}
                className={`flex flex-col items-center p-3 rounded-lg border-2 transition-colors ${
                  localPreferences.layout === id
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <Icon className="w-6 h-6 mb-2" />
                <span className="text-sm">{label}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Visual Effects</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Animations</label>
                <p className="text-xs text-gray-400">Enable smooth animations</p>
              </div>
              <button
                onClick={() => setLocalPreferences(prev => ({ ...prev, animationsEnabled: !prev.animationsEnabled }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localPreferences.animationsEnabled ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  localPreferences.animationsEnabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Compact Mode</label>
                <p className="text-xs text-gray-400">Reduce spacing and padding</p>
              </div>
              <button
                onClick={() => setLocalPreferences(prev => ({ ...prev, compactMode: !prev.compactMode }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localPreferences.compactMode ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  localPreferences.compactMode ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>
      </div>
    ),

    performance: (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Update Optimization</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Batch Updates</label>
                <p className="text-xs text-gray-400">Group updates for better performance</p>
              </div>
              <button
                onClick={() => setLocalPreferences(prev => ({ ...prev, batchUpdates: !prev.batchUpdates }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localPreferences.batchUpdates ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  localPreferences.batchUpdates ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-300 block mb-2">
                Retry Attempts: {localPreferences.retryAttempts}
              </label>
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={localPreferences.retryAttempts}
                onChange={(e) => setLocalPreferences(prev => ({ 
                  ...prev, 
                  retryAttempts: parseInt(e.target.value) 
                }))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Data Management</h3>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={handleExport}
              className="flex items-center justify-center gap-2 p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              <span className="text-sm">Export Settings</span>
            </button>
            <button
              onClick={handleImport}
              className="flex items-center justify-center gap-2 p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span className="text-sm">Import Settings</span>
            </button>
          </div>
        </div>
      </div>
    ),

    widgets: (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Widget Visibility</h3>
          <div className="space-y-3">
            {Object.entries(localPreferences.widgetSettings).map(([widgetId, settings]) => (
              <div key={widgetId} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-gray-300 capitalize">
                    {widgetId.replace('-', ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={settings.size}
                    onChange={(e) => setLocalPreferences(prev => ({
                      ...prev,
                      widgetSettings: {
                        ...prev.widgetSettings,
                        [widgetId]: { ...settings, size: e.target.value as any }
                      }
                    }))}
                    className="bg-gray-600 border border-gray-500 rounded px-2 py-1 text-sm"
                  >
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                  </select>
                  <button
                    onClick={() => setLocalPreferences(prev => ({
                      ...prev,
                      widgetSettings: {
                        ...prev.widgetSettings,
                        [widgetId]: { ...settings, visible: !settings.visible }
                      }
                    }))}
                    className="text-gray-400 hover:text-white"
                  >
                    {settings.visible ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gray-800 rounded-xl border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <div className="flex items-center gap-3">
              <Settings className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold text-white">Dashboard Settings</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="flex">
            {/* Sidebar */}
            <div className="w-64 border-r border-gray-700 p-4">
              <nav className="space-y-2">
                {[
                  { id: 'general', label: 'General', icon: Settings },
                  { id: 'appearance', label: 'Appearance', icon: Palette },
                  { id: 'performance', label: 'Performance', icon: Zap },
                  { id: 'widgets', label: 'Widgets', icon: Grid }
                ].map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    onClick={() => setActiveTab(id as any)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                      activeTab === id
                        ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30'
                        : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Content */}
            <div className="flex-1 p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
              {tabContent[activeTab]}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-700">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Reset to Defaults
            </button>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  hasChanges
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                }`}
              >
                <Save className="w-4 h-4" />
                Save Changes
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};