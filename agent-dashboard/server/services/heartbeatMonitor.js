import fs from 'fs/promises';
import path from 'path';

export class HeartbeatMonitor {
  constructor(agentMonitor) {
    this.agentMonitor = agentMonitor;
    this.heartbeatPath = 'C:\\Jarvis\\AI Workspace\\Super Agent\\shared\\heartbeats';
    this.checkInterval = 10000; // Check every 10 seconds
  }

  async initialize() {
    // Create heartbeat directory if it doesn't exist
    try {
      await fs.mkdir(this.heartbeatPath, { recursive: true });
    } catch (error) {
      console.error('Error creating heartbeat directory:', error);
    }

    // Start monitoring
    this.startMonitoring();
  }

  startMonitoring() {
    setInterval(async () => {
      await this.checkHeartbeats();
    }, this.checkInterval);

    // Initial check
    this.checkHeartbeats();
  }

  async checkHeartbeats() {
    try {
      const files = await fs.readdir(this.heartbeatPath);
      const now = Date.now();

      for (const file of files) {
        if (file.endsWith('.heartbeat')) {
          const agentId = file.replace('.heartbeat', '');
          
          try {
            const filePath = path.join(this.heartbeatPath, file);
            const stat = await fs.stat(filePath);
            
            // If heartbeat was updated in the last 60 seconds, agent is active
            if (now - stat.mtimeMs < 60000) {
              // Try both the full ID and the base ID (without -001 suffix)
              this.agentMonitor.updateAgentStatus(agentId, 'active');
              
              // Also try base agent ID for agents like agent-orchestrator-001
              const baseAgentId = agentId.replace(/-\d{3}$/, '');
              if (baseAgentId !== agentId) {
                this.agentMonitor.updateAgentStatus(baseAgentId, 'active');
              }
            }
          } catch (error) {
            // Ignore individual file errors
          }
        }
      }
    } catch (error) {
      console.error('Error checking heartbeats:', error);
    }
  }

  // Method for agents to update their heartbeat
  async updateHeartbeat(agentId) {
    try {
      const filePath = path.join(this.heartbeatPath, `${agentId}.heartbeat`);
      await fs.writeFile(filePath, new Date().toISOString());
    } catch (error) {
      console.error(`Error updating heartbeat for ${agentId}:`, error);
    }
  }
}