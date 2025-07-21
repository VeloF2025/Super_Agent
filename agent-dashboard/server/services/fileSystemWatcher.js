import { EventEmitter } from 'events';
import chokidar from 'chokidar';
import fs from 'fs/promises';
import path from 'path';

export class FileSystemWatcher extends EventEmitter {
  constructor(agentMonitor) {
    super();
    this.agentMonitor = agentMonitor;
    this.workspacePath = 'C:\\Jarvis\\AI Workspace';
    this.superAgentPath = 'C:\\Jarvis\\AI Workspace\\Super Agent';
    this.watchers = new Map();
    this.messageQueue = new Map();
  }

  startWatching() {
    // Watch communication queues
    this.watchCommunicationQueues();
    
    // Watch agent logs
    this.watchAgentLogs();
    
    // Watch project directories
    this.watchProjects();
    
    console.log('File system monitoring started');
  }

  watchCommunicationQueues() {
    const queuePaths = [
      path.join(this.superAgentPath, 'shared', 'communication', 'queue', 'incoming'),
      path.join(this.superAgentPath, 'shared', 'communication', 'queue', 'processing'),
      path.join(this.superAgentPath, 'shared', 'communication', 'queue', 'completed')
    ];

    queuePaths.forEach(queuePath => {
      const queueType = path.basename(queuePath);
      const watcher = chokidar.watch(queuePath, {
        persistent: true,
        ignoreInitial: true,
        depth: 0
      });

      watcher
        .on('add', async (filePath) => {
          try {
            const content = await fs.readFile(filePath, 'utf-8');
            const message = JSON.parse(content);
            
            // Extract agent info from filename
            const filename = path.basename(filePath);
            const parts = filename.split('_');
            const agentId = parts[2] || 'unknown';
            
            // Process based on queue type
            if (queueType === 'incoming') {
              this.handleIncomingMessage(agentId, message, filePath);
            } else if (queueType === 'processing') {
              this.handleProcessingMessage(agentId, message, filePath);
            } else if (queueType === 'completed') {
              this.handleCompletedMessage(agentId, message, filePath);
            }
            
            this.emit('file-change', {
              type: 'queue-message',
              queue: queueType,
              agent: agentId,
              message
            });
          } catch (error) {
            console.error(`Error processing queue file ${filePath}:`, error);
          }
        })
        .on('unlink', (filePath) => {
          const filename = path.basename(filePath);
          const parts = filename.split('_');
          const agentId = parts[2] || 'unknown';
          
          this.emit('file-change', {
            type: 'queue-message-removed',
            queue: queueType,
            agent: agentId,
            path: filePath
          });
        });

      this.watchers.set(`queue-${queueType}`, watcher);
    });
  }

  watchAgentLogs() {
    const logsPath = path.join(this.superAgentPath, 'logs');
    
    const watcher = chokidar.watch(logsPath, {
      persistent: true,
      ignoreInitial: true,
      depth: 2,
      ignored: /node_modules|\.git/
    });

    watcher
      .on('add', async (filePath) => {
        if (filePath.endsWith('.log')) {
          // Extract agent from path
          const relativePath = path.relative(logsPath, filePath);
          const parts = relativePath.split(path.sep);
          const agentId = parts[0];
          
          // Read last few lines of log
          try {
            const content = await fs.readFile(filePath, 'utf-8');
            const lines = content.split('\n').slice(-10); // Last 10 lines
            
            this.emit('file-change', {
              type: 'log-update',
              agent: agentId,
              lines: lines.filter(l => l.trim()),
              path: filePath
            });
          } catch (error) {
            console.error(`Error reading log ${filePath}:`, error);
          }
        }
      })
      .on('change', async (filePath) => {
        if (filePath.endsWith('.log')) {
          // Similar to add, but only emit last line
          const relativePath = path.relative(logsPath, filePath);
          const parts = relativePath.split(path.sep);
          const agentId = parts[0];
          
          try {
            const content = await fs.readFile(filePath, 'utf-8');
            const lines = content.split('\n');
            const lastLine = lines[lines.length - 2] || lines[lines.length - 1]; // -2 because last is usually empty
            
            if (lastLine.trim()) {
              this.emit('file-change', {
                type: 'log-append',
                agent: agentId,
                line: lastLine.trim(),
                path: filePath
              });
            }
          } catch (error) {
            // Ignore read errors on change
          }
        }
      });

    this.watchers.set('logs', watcher);
  }

  watchProjects() {
    // Watch both Super Agent projects and entire workspace
    const projectPaths = [
      path.join(this.superAgentPath, 'projects'),
      this.workspacePath
    ];
    
    const watcher = chokidar.watch(projectPaths, {
      persistent: true,
      ignoreInitial: true,
      depth: 3,
      ignored: /node_modules|\.git|dist|build|Super Agent/
    });

    watcher
      .on('add', (filePath) => {
        const relativePath = filePath.includes('Super Agent') 
          ? path.relative(path.join(this.superAgentPath, 'projects'), filePath)
          : path.relative(this.workspacePath, filePath);
        const parts = relativePath.split(path.sep);
        const projectName = parts[0];
        
        // Check if it's an agent workspace file
        if (relativePath.includes('agent-workspace') && filePath.endsWith('.json')) {
          this.emit('file-change', {
            type: 'project-file-add',
            project: projectName,
            path: filePath,
            isAgentFile: true
          });
        }
      })
      .on('change', async (filePath) => {
        if (filePath.endsWith('.json') && filePath.includes('agent-workspace')) {
          try {
            const content = await fs.readFile(filePath, 'utf-8');
            const data = JSON.parse(content);
            
            const relativePath = path.relative(projectsPath, filePath);
            const parts = relativePath.split(path.sep);
            const projectName = parts[0];
            
            this.emit('file-change', {
              type: 'project-update',
              project: projectName,
              data,
              path: filePath
            });
          } catch (error) {
            // Ignore parse errors
          }
        }
      });

    this.watchers.set('projects', watcher);
  }

  async handleIncomingMessage(agentId, message, filePath) {
    // Start activity for the agent
    const activityId = this.agentMonitor.startActivity(agentId, {
      type: message.type || 'task',
      description: message.task || message.description || 'Processing message',
      priority: message.priority || 'medium'
    });
    
    // Store message ID to activity mapping
    this.messageQueue.set(filePath, activityId);
  }

  async handleProcessingMessage(agentId, message, filePath) {
    // Update agent status to working
    this.agentMonitor.updateAgentStatus(agentId, 'working');
  }

  async handleCompletedMessage(agentId, message, filePath) {
    // Find corresponding activity
    const originalPath = filePath.replace('completed', 'incoming');
    const activityId = this.messageQueue.get(originalPath);
    
    if (activityId) {
      this.agentMonitor.completeActivity(activityId, {
        success: message.success !== false,
        result: message.result || message.response || 'Completed'
      });
      this.messageQueue.delete(originalPath);
    }
    
    // Update agent status
    this.agentMonitor.updateAgentStatus(agentId, 'idle');
  }

  stopWatching() {
    for (const [name, watcher] of this.watchers) {
      watcher.close();
    }
    this.watchers.clear();
    console.log('File system monitoring stopped');
  }
}