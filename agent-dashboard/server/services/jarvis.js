/**
 * Jarvis Orchestration Agent Service
 * Handles Jarvis identity confirmation and status responses
 */

import { EventEmitter } from 'events';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class JarvisService extends EventEmitter {
  constructor(db) {
    super();
    this.db = db;
    this.isInitialized = false;
    this.startTime = new Date();
    this.greetings = [
      "Yes, I'm here. Jarvis at your service.",
      "Jarvis online and operational. How may I assist you?",
      "Indeed, it's Jarvis. All systems functioning within normal parameters.",
      "Jarvis here. Ready to orchestrate your agents.",
      "You called? Jarvis is fully operational and ready.",
      "Jarvis responding. All agent systems are under my supervision.",
      "Present and accounted for. This is Jarvis, your orchestration agent."
    ];
    
    this.initializeJarvis();
  }

  async initializeJarvis() {
    try {
      // Check if Jarvis is properly configured
      await this.validateSystemComponents();
      
      // Register Jarvis as the primary orchestrator
      await this.registerOrchestrator();
      
      this.isInitialized = true;
      this.emit('initialized', {
        message: 'Jarvis orchestration agent initialized successfully',
        timestamp: new Date().toISOString()
      });
      
      console.log('🤖 Jarvis orchestration agent initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Jarvis:', error);
      this.isInitialized = false;
    }
  }

  async validateSystemComponents() {
    const requiredComponents = [
      { name: 'Database', check: () => this.db && this.db.db },
      { name: 'Agent Monitor', check: () => true }, // Will be injected
      { name: 'Communication System', check: () => fs.existsSync(path.join(__dirname, '../../../shared/communication')) },
      { name: 'Daily Operations', check: () => fs.existsSync(path.join(__dirname, '../../../daily-ops')) }
    ];

    for (const component of requiredComponents) {
      if (!component.check()) {
        throw new Error(`Required component missing: ${component.name}`);
      }
    }
  }

  async registerOrchestrator() {
    // Register Jarvis in the database
    const jarvisAgent = {
      id: 'jarvis-orchestrator',
      name: 'Jarvis',
      type: 'orchestrator',
      status: 'online',
      capabilities: [
        'agent-coordination',
        'task-delegation',
        'system-monitoring',
        'context-persistence',
        'workflow-automation',
        'emergency-response'
      ],
      location: 'C:\\Jarvis\\AI Workspace\\Super Agent',
      project: 'Super Agent System'
    };

    this.db.upsertAgent(jarvisAgent);
    
    // Record initialization activity
    this.db.recordActivity({
      agent_id: 'jarvis-orchestrator',
      activity_type: 'system_initialization',
      description: 'Jarvis orchestration agent started',
      status: 'completed',
      priority: 'high'
    });
  }

  // Check if someone is calling for Jarvis
  isJarvisQuery(message) {
    if (!message || typeof message !== 'string') return false;
    
    const lowerMessage = message.toLowerCase().trim();
    const jarvisPatterns = [
      /^(hey\s+)?jarvis\??$/i,
      /^jarvis\s*\?$/i,
      /^hey\s+jarvis$/i,
      /^jarvis\s+are\s+you\s+(there|online|active|operational)\??$/i,
      /^is\s+jarvis\s+(online|active|operational)\??$/i
    ];
    
    return jarvisPatterns.some(pattern => pattern.test(lowerMessage));
  }

  // Generate Jarvis response
  getJarvisResponse() {
    if (!this.isInitialized) {
      return {
        message: "Jarvis is still initializing. Please wait a moment...",
        status: 'initializing',
        agent: 'jarvis-orchestrator'
      };
    }

    const randomGreeting = this.greetings[Math.floor(Math.random() * this.greetings.length)];
    const uptime = this.getUptime();
    
    return {
      message: randomGreeting,
      status: 'operational',
      agent: 'jarvis-orchestrator',
      details: {
        uptime: uptime,
        initialized: this.isInitialized,
        version: '2.0.0',
        capabilities: [
          'agent-coordination',
          'task-delegation', 
          'system-monitoring',
          'context-persistence'
        ]
      }
    };
  }

  // Get system status for Jarvis
  getSystemStatus() {
    const agents = this.db.getAgents();
    const activeAgents = agents.filter(a => a.status === 'online').length;
    const recentActivities = this.db.getRecentActivities(10);
    
    return {
      orchestrator: 'Jarvis',
      status: this.isInitialized ? 'operational' : 'initializing',
      systemHealth: {
        totalAgents: agents.length,
        activeAgents: activeAgents,
        recentActivities: recentActivities.length,
        uptime: this.getUptime()
      },
      message: this.isInitialized 
        ? "All systems nominal. Jarvis is monitoring all agents."
        : "Jarvis is coming online. Initializing systems..."
    };
  }

  // Calculate uptime
  getUptime() {
    const now = new Date();
    const diff = now - this.startTime;
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    return `${hours}h ${minutes}m ${seconds}s`;
  }

  // Handle direct Jarvis commands
  async handleCommand(command, context = {}) {
    if (!this.isInitialized) {
      return {
        success: false,
        message: "Jarvis is still initializing. Please wait.",
        agent: 'jarvis-orchestrator'
      };
    }

    // Log the command
    this.db.recordActivity({
      agent_id: 'jarvis-orchestrator',
      activity_type: 'command_received',
      description: `Command: ${command}`,
      status: 'completed',
      priority: 'medium'
    });

    // Process different types of commands
    const lowerCommand = command.toLowerCase();
    
    if (lowerCommand.includes('status')) {
      return {
        success: true,
        data: this.getSystemStatus(),
        agent: 'jarvis-orchestrator'
      };
    }
    
    if (lowerCommand.includes('help')) {
      return {
        success: true,
        message: "I'm Jarvis, your AI orchestration agent. I coordinate all agents, manage workflows, and ensure smooth operation of the Super Agent system. Ask me about system status, agent coordination, or any tasks you need assistance with.",
        agent: 'jarvis-orchestrator'
      };
    }

    // Default response for other commands
    return {
      success: true,
      message: "Command acknowledged. Jarvis is processing your request.",
      agent: 'jarvis-orchestrator'
    };
  }

  // Shutdown Jarvis gracefully
  async shutdown() {
    console.log('🤖 Jarvis shutting down gracefully...');
    
    this.db.recordActivity({
      agent_id: 'jarvis-orchestrator',
      activity_type: 'system_shutdown',
      description: 'Jarvis orchestration agent shutting down',
      status: 'completed',
      priority: 'high'
    });

    // Update status
    this.db.upsertAgent({
      id: 'jarvis-orchestrator',
      status: 'offline'
    });

    this.isInitialized = false;
    this.emit('shutdown');
  }
}

export default JarvisService;