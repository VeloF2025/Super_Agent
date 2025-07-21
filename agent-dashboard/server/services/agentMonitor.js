import { EventEmitter } from 'events';
import fs from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execPromise = promisify(exec);

export class AgentMonitor extends EventEmitter {
  constructor(db) {
    super();
    this.db = db;
    this.agents = new Map();
    this.activities = new Map();
    this.projects = new Map();
    this.workspacePath = 'C:\\Jarvis\\AI Workspace';
    this.superAgentPath = 'C:\\Jarvis\\AI Workspace\\Super Agent';
    
    this.initializeAgents();
    this.startHealthCheck();
  }

  async initializeAgents() {
    try {
      // First scan Super Agent directory
      await this.scanSuperAgentDirectory();
      
      // Then scan entire AI Workspace for other projects
      await this.scanWorkspaceProjects();
      
      // Check for running processes
      await this.checkRunningProcesses();
      
      this.emit('update', { type: 'agents-initialized', agents: Array.from(this.agents.values()) });
    } catch (error) {
      console.error('Error initializing agents:', error);
    }
  }

  async checkRunningProcesses() {
    try {
      // Use cross-platform approach to check for running processes
      let stdout = '';
      
      if (process.platform === 'win32') {
        try {
          // Try PowerShell first (more reliable than wmic)
          const psCommand = 'Get-Process node -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CommandLine | ConvertTo-Json';
          const { stdout: psOutput } = await execPromise(`powershell -Command "${psCommand}"`);
          stdout = psOutput;
        } catch (psError) {
          try {
            // Fallback to tasklist for Windows
            const { stdout: taskOutput } = await execPromise('tasklist /fi "imagename eq node.exe" /fo csv');
            stdout = taskOutput;
          } catch (taskError) {
            console.warn('Could not check running processes on Windows:', taskError.message);
            await this.checkRecentLogActivity();
            return;
          }
        }
      } else {
        try {
          // For Linux/macOS, use ps command
          const { stdout: psOutput } = await execPromise('ps aux | grep node');
          stdout = psOutput;
        } catch (psError) {
          console.warn('Could not check running processes on Unix:', psError.message);
          await this.checkRecentLogActivity();
          return;
        }
      }
      
      // Parse the output to find agent processes
      const processes = stdout.split('\n').filter(p => p.trim());
      
      for (const process of processes) {
        // Check if this is an agent process
        for (const [agentId, agent] of this.agents) {
          // Check various patterns that might indicate this agent is running
          const patterns = [
            agentId,
            agent.name.toLowerCase().replace(/\s+/g, '-'),
            agent.name.toLowerCase().replace(/\s+/g, '_'),
            path.basename(agent.path || '')
          ];
          
          if (patterns.some(pattern => pattern && process.toLowerCase().includes(pattern.toLowerCase()))) {
            console.log(`Detected running process for agent: ${agent.name}`);
            this.updateAgentStatus(agentId, 'active');
            break;
          }
        }
      }
      
      // Also check for recent log files
      await this.checkRecentLogActivity();
      
    } catch (error) {
      console.error('Error checking running processes:', error);
    }
  }

  async checkRecentLogActivity() {
    const logsPath = path.join(this.superAgentPath, 'logs');
    
    try {
      const logDirs = await fs.readdir(logsPath);
      const now = Date.now();
      
      for (const dir of logDirs) {
        if (dir.startsWith('agent-')) {
          const agentId = dir;
          const agent = this.agents.get(agentId);
          
          if (agent) {
            try {
              const logPath = path.join(logsPath, dir);
              const stat = await fs.stat(logPath);
              
              // If directory was modified in the last 5 minutes, consider agent active
              if (now - stat.mtimeMs < 5 * 60 * 1000) {
                console.log(`Recent log activity detected for: ${agent.name}`);
                this.updateAgentStatus(agentId, 'active');
              }
            } catch (e) {
              // Ignore errors for individual directories
            }
          }
        }
      }
    } catch (error) {
      console.error('Error checking log activity:', error);
    }
  }

  async scanSuperAgentDirectory() {
    // Scan for agents in the Super Agent agents directory
    const agentsPath = path.join(this.superAgentPath, 'agents');
    try {
      const agentDirs = await fs.readdir(agentsPath);
      
      for (const dir of agentDirs) {
        if (dir.startsWith('agent-')) {
          const agentId = dir; // Keep original ID for now
          const agentPath = path.join(agentsPath, dir);
          
          // Try to read CLAUDE.md for agent info
          let agentInfo = {
            id: agentId,
            name: dir.replace('agent-', '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            type: dir.replace('agent-', ''),
            status: 'offline',
            capabilities: [],
            location: 'Super Agent',
            project: 'Super Agent System',
            path: agentPath
          };
          
          try {
            const claudePath = path.join(agentPath, 'CLAUDE.md');
            const claudeContent = await fs.readFile(claudePath, 'utf-8');
            // Extract capabilities from CLAUDE.md if possible
            const capMatch = claudeContent.match(/## Capabilities([\s\S]*?)##/);
            if (capMatch) {
              agentInfo.capabilities = capMatch[1]
                .split('\n')
                .filter(line => line.trim().startsWith('-'))
                .map(line => line.replace(/^-\s*/, '').trim());
            }
          } catch (e) {
            // CLAUDE.md not found or readable
          }
          
          this.agents.set(agentId, agentInfo);
          this.db.upsertAgent(agentInfo);
        }
      }
    } catch (error) {
      console.error('Error scanning Super Agent directory:', error);
    }
  }

  async scanWorkspaceProjects() {
    try {
      // Scan entire AI Workspace directory
      const entries = await fs.readdir(this.workspacePath, { withFileTypes: true });
      
      for (const entry of entries) {
        if (entry.isDirectory()) {
          const projectPath = path.join(this.workspacePath, entry.name);
          
          // Skip Super Agent directory as it's already scanned
          if (entry.name === 'Super Agent') continue;
          
          // Look for agent-related directories or files
          await this.scanProjectForAgents(projectPath, entry.name);
        }
      }
      
      // Also scan Super Agent projects
      await this.scanSuperAgentProjects();
    } catch (error) {
      console.error('Error scanning workspace projects:', error);
    }
  }

  async scanProjectForAgents(projectPath, projectName) {
    try {
      // Common agent directory patterns
      const agentPatterns = [
        'agents',
        'agent-workspace/agents',
        'src/agents',
        'lib/agents',
        '.agents'
      ];
      
      let projectInfo = {
        id: projectName.toLowerCase().replace(/\s+/g, '-'),
        name: projectName,
        path: projectPath,
        status: 'active',
        agents: [],
        location: 'AI Workspace'
      };
      
      // Check for agents in common locations
      for (const pattern of agentPatterns) {
        const agentPath = path.join(projectPath, pattern);
        try {
          const stat = await fs.stat(agentPath);
          if (stat.isDirectory()) {
            const agentDirs = await fs.readdir(agentPath);
            
            for (const dir of agentDirs) {
              if (dir.includes('agent') || dir.endsWith('-agent')) {
                const agentId = `${projectInfo.id}-${dir}`;
                const fullAgentPath = path.join(agentPath, dir);
                
                const agentInfo = {
                  id: agentId,
                  name: dir.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                  type: 'project-agent',
                  status: 'offline',
                  capabilities: [],
                  location: projectName,
                  project: projectName,
                  path: fullAgentPath
                };
                
                this.agents.set(agentId, agentInfo);
                this.db.upsertAgent(agentInfo);
                projectInfo.agents.push(agentId);
              }
            }
          }
        } catch (e) {
          // Directory doesn't exist
        }
      }
      
      if (projectInfo.agents.length > 0 || await this.projectHasAgentFiles(projectPath)) {
        this.projects.set(projectInfo.id, projectInfo);
      }
    } catch (error) {
      console.error(`Error scanning project ${projectName}:`, error);
    }
  }

  async projectHasAgentFiles(projectPath) {
    // Check if project has agent-related files
    const agentFilePatterns = ['agent.config', 'agents.json', '.agentrc', 'agent-manifest.json'];
    
    for (const pattern of agentFilePatterns) {
      try {
        await fs.stat(path.join(projectPath, pattern));
        return true;
      } catch (e) {
        // File doesn't exist
      }
    }
    
    return false;
  }

  async scanSuperAgentProjects() {
    try {
      const projectsPath = path.join(this.superAgentPath, 'projects');
      const projects = await fs.readdir(projectsPath);
      
      for (const projectName of projects) {
        const projectPath = path.join(projectsPath, projectName);
        const stat = await fs.stat(projectPath);
        
        if (stat.isDirectory()) {
          let projectInfo = {
            id: projectName.toLowerCase().replace(/\s+/g, '-'),
            name: projectName,
            path: projectPath,
            status: 'active',
            agents: [],
            location: 'Super Agent Projects'
          };
          
          try {
            const configPath = path.join(projectPath, 'project.json');
            const config = JSON.parse(await fs.readFile(configPath, 'utf-8'));
            projectInfo = { ...projectInfo, ...config };
          } catch (e) {
            // No project.json
          }
          
          // Check for agent assignments in agent-workspace
          const workspacePath = path.join(projectPath, 'agent-workspace', 'agents');
          try {
            const assignedAgents = await fs.readdir(workspacePath);
            for (const agentDir of assignedAgents) {
              if (agentDir.includes('agent-')) {
                const agentId = agentDir; // Keep original ID
                const agentPath = path.join(workspacePath, agentDir);
                
                const agentInfo = {
                  id: agentId,
                  name: agentDir.replace('agent-', '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                  type: 'project-instance',
                  status: 'offline',
                  capabilities: [],
                  location: projectInfo.location,
                  project: projectName,
                  path: agentPath
                };
                
                this.agents.set(agentId, agentInfo);
                this.db.upsertAgent(agentInfo);
                projectInfo.agents.push(agentId);
              }
            }
          } catch (e) {
            // No agent workspace
          }
          
          this.projects.set(projectInfo.id, projectInfo);
        }
      }
    } catch (error) {
      console.error('Error scanning Super Agent projects:', error);
    }
  }

  startActivity(agentId, activity) {
    const activityId = `${agentId}-${Date.now()}`;
    const activityData = {
      id: activityId,
      agent_id: agentId,
      activity_type: activity.type,
      description: activity.description,
      status: 'in_progress',
      priority: activity.priority || 'medium',
      started_at: new Date()
    };
    
    this.activities.set(activityId, activityData);
    this.db.recordActivity(activityData);
    
    // Update agent status
    const agent = this.agents.get(agentId);
    if (agent) {
      agent.status = 'working';
      agent.currentActivity = activityId;
      this.db.upsertAgent(agent);
    }
    
    this.emit('update', { type: 'activity-start', agent: agentId, activity: activityData });
    return activityId;
  }

  completeActivity(activityId, result) {
    const activity = this.activities.get(activityId);
    if (!activity) return;
    
    const duration = Date.now() - activity.started_at.getTime();
    activity.status = 'completed';
    activity.completed_at = new Date();
    activity.duration_ms = duration;
    activity.result = result;
    
    this.db.completeActivity(activityId, JSON.stringify(result), duration);
    
    // Update agent status
    const agent = this.agents.get(activity.agent_id);
    if (agent && agent.currentActivity === activityId) {
      agent.status = 'idle';
      delete agent.currentActivity;
      this.db.upsertAgent(agent);
    }
    
    this.emit('update', { type: 'activity-complete', activity });
  }

  updateAgentStatus(agentId, status) {
    const agent = this.agents.get(agentId);
    if (agent) {
      agent.status = status;
      agent.last_seen = new Date();
      this.db.upsertAgent(agent);
      this.emit('update', { type: 'agent-status', agent });
    }
  }

  startHealthCheck() {
    // Check agent health every 30 seconds
    setInterval(async () => {
      const now = Date.now();
      
      // First check for running processes
      await this.checkRunningProcesses();
      
      // Then check last seen times
      for (const [agentId, agent] of this.agents) {
        const lastSeen = agent.last_seen ? new Date(agent.last_seen).getTime() : 0;
        const timeSinceLastSeen = now - lastSeen;
        
        // Mark as offline if not seen for 5 minutes and not currently active
        if (timeSinceLastSeen > 5 * 60 * 1000 && agent.status !== 'offline' && agent.status !== 'active') {
          this.updateAgentStatus(agentId, 'offline');
        }
      }
    }, 30000);
    
    // Also run the check immediately
    this.checkRunningProcesses();
  }

  getAgents() {
    return Array.from(this.agents.values());
  }

  getAgent(agentId) {
    return this.agents.get(agentId);
  }

  getRecentActivities(limit = 50) {
    return this.db.getRecentActivities(limit);
  }

  getProjects() {
    return Array.from(this.projects.values());
  }

  getAgentMetrics() {
    return this.db.getAgentPerformanceStats();
  }
}