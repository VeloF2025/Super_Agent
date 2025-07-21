import validator from 'validator';
import DOMPurify from 'isomorphic-dompurify';

export class InputValidator {
  static validateAgent(agent) {
    const errors = [];
    
    if (!agent.id || typeof agent.id !== 'string' || agent.id.length > 50) {
      errors.push('Invalid agent ID');
    }
    
    if (!agent.name || typeof agent.name !== 'string' || agent.name.length > 100) {
      errors.push('Invalid agent name');
    }
    
    if (agent.type && !['frontend', 'backend', 'quality', 'research', 'development'].includes(agent.type)) {
      errors.push('Invalid agent type');
    }
    
    if (agent.project && typeof agent.project !== 'string') {
      errors.push('Invalid project field');
    }
    
    return errors;
  }

  static validateActivity(activity) {
    const errors = [];
    
    if (!activity.agent_id || typeof activity.agent_id !== 'string') {
      errors.push('Invalid agent ID');
    }
    
    if (!activity.activity_type || typeof activity.activity_type !== 'string') {
      errors.push('Invalid activity type');
    }
    
    if (activity.description && activity.description.length > 1000) {
      errors.push('Description too long');
    }
    
    if (activity.priority && !['low', 'medium', 'high', 'critical'].includes(activity.priority)) {
      errors.push('Invalid priority level');
    }
    
    return errors;
  }

  static validateMetric(metric) {
    const errors = [];
    
    if (!metric.type || typeof metric.type !== 'string') {
      errors.push('Invalid metric type');
    }
    
    if (metric.value !== undefined && typeof metric.value !== 'number') {
      errors.push('Invalid metric value');
    }
    
    if (metric.agentId && typeof metric.agentId !== 'string') {
      errors.push('Invalid agent ID');
    }
    
    return errors;
  }

  static sanitizeInput(input) {
    if (typeof input !== 'string') {
      return input;
    }
    
    // Remove potentially dangerous characters
    let sanitized = input.replace(/[<>]/g, '');
    
    // HTML sanitization
    sanitized = DOMPurify.sanitize(sanitized);
    
    // SQL injection prevention (additional layer)
    sanitized = sanitized.replace(/['";\\]/g, '');
    
    return sanitized;
  }

  static validatePath(filePath) {
    // Prevent path traversal attacks
    const normalizedPath = path.normalize(filePath);
    
    if (normalizedPath.includes('..') || normalizedPath.startsWith('/')) {
      throw new Error('Invalid file path');
    }
    
    return normalizedPath;
  }

  static isValidEmail(email) {
    return validator.isEmail(email);
  }

  static isValidURL(url) {
    return validator.isURL(url, {
      protocols: ['http', 'https'],
      require_protocol: true
    });
  }
}

// Validation middleware factory
export const validationMiddleware = (validatorFn) => {
  return (req, res, next) => {
    try {
      const errors = validatorFn(req.body);
      
      if (errors.length > 0) {
        return res.status(400).json({
          error: 'Validation failed',
          details: errors
        });
      }
      
      // Sanitize inputs
      if (req.body && typeof req.body === 'object') {
        const sanitizeObject = (obj) => {
          for (const key in obj) {
            if (typeof obj[key] === 'string') {
              obj[key] = InputValidator.sanitizeInput(obj[key]);
            } else if (typeof obj[key] === 'object' && obj[key] !== null) {
              sanitizeObject(obj[key]);
            }
          }
        };
        
        sanitizeObject(req.body);
      }
      
      next();
    } catch (error) {
      res.status(500).json({
        error: 'Validation error',
        message: error.message
      });
    }
  };
};
