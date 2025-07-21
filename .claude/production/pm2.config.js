module.exports = {
  apps: [
    {
      name: 'super-agent-dashboard',
      script: './agent-dashboard/server/index-robust.js',
      cwd: 'C:\\Jarvis\\AI Workspace\\Super Agent',
      instances: 1,
      exec_mode: 'fork',
      
      // Auto-restart configuration
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      restart_delay: 1000,
      max_restarts: 10,
      min_uptime: '10s',
      
      // Environment variables
      env: {
        NODE_ENV: 'production',
        PORT: 3001
      },
      
      // Logging
      log_file: './logs/dashboard-combined.log',
      out_file: './logs/dashboard-out.log',
      error_file: './logs/dashboard-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // Advanced PM2 features
      kill_timeout: 5000,
      listen_timeout: 10000,
      shutdown_with_message: true,
      
      // Health monitoring
      health_check_grace_period: 3000,
      health_check_fatal_exceptions: false
    },
    
    {
      name: 'dashboard-monitor',
      script: './.claude/dashboard-monitor.py',
      cwd: 'C:\\Jarvis\\AI Workspace\\Super Agent',
      interpreter: 'python',
      args: 'start',
      instances: 1,
      exec_mode: 'fork',
      
      // Monitor configuration
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      restart_delay: 5000,
      max_restarts: 5,
      min_uptime: '30s',
      
      // Environment
      env: {
        PYTHONPATH: 'C:\\Jarvis\\AI Workspace\\Super Agent',
        MONITOR_INTERVAL: '30'
      },
      
      // Logging
      log_file: './logs/monitor-combined.log',
      out_file: './logs/monitor-out.log',
      error_file: './logs/monitor-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    
    {
      name: 'agent-heartbeats',
      script: './.claude/agent-heartbeat.py',
      cwd: 'C:\\Jarvis\\AI Workspace\\Super Agent',
      interpreter: 'python',
      instances: 1,
      exec_mode: 'fork',
      
      // Heartbeat configuration
      autorestart: true,
      watch: false,
      max_memory_restart: '128M',
      restart_delay: 2000,
      max_restarts: 10,
      min_uptime: '5s',
      
      // Environment
      env: {
        PYTHONPATH: 'C:\\Jarvis\\AI Workspace\\Super Agent',
        HEARTBEAT_INTERVAL: '30'
      },
      
      // Logging
      log_file: './logs/heartbeat-combined.log',
      out_file: './logs/heartbeat-out.log',
      error_file: './logs/heartbeat-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};