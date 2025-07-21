/**
 * Input Validation Middleware
 * Comprehensive validation rules for all API endpoints
 */

import { body, param, query, validationResult } from 'express-validator';
import validator from 'validator';
import { ValidationError } from './errorHandler.js';

// Custom validators
const customValidators = {
  isAgentType: (value) => {
    const validTypes = ['frontend', 'backend', 'quality', 'research', 'development', 'orchestrator'];
    return validTypes.includes(value);
  },
  
  isPriority: (value) => {
    const validPriorities = ['low', 'medium', 'high', 'critical'];
    return validPriorities.includes(value);
  },
  
  isActivityStatus: (value) => {
    const validStatuses = ['pending', 'in_progress', 'completed', 'failed', 'cancelled'];
    return validStatuses.includes(value);
  },
  
  isValidPath: (value) => {
    // Prevent path traversal
    if (value.includes('..') || value.includes('~')) {
      return false;
    }
    // Must be absolute path or relative to workspace
    return value.startsWith('/') || value.startsWith('./') || /^[a-zA-Z0-9_\-\/]+$/.test(value);
  },
  
  isValidJSON: (value) => {
    try {
      JSON.parse(value);
      return true;
    } catch {
      return false;
    }
  }
};

// Validation result handler
export const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  
  if (!errors.isEmpty()) {
    const formattedErrors = errors.array().map(err => ({
      field: err.path || err.param,
      message: err.msg,
      value: err.value,
      location: err.location
    }));
    
    throw new ValidationError('Validation failed', formattedErrors);
  }
  
  next();
};

// Agent validation rules
export const validateAgent = [
  body('id')
    .trim()
    .notEmpty().withMessage('Agent ID is required')
    .isLength({ min: 1, max: 50 }).withMessage('Agent ID must be 1-50 characters')
    .matches(/^[a-zA-Z0-9_\-]+$/).withMessage('Agent ID must contain only alphanumeric characters, underscore, or dash'),
  
  body('name')
    .trim()
    .notEmpty().withMessage('Agent name is required')
    .isLength({ min: 1, max: 100 }).withMessage('Agent name must be 1-100 characters')
    .escape(), // Escape HTML entities
  
  body('type')
    .trim()
    .notEmpty().withMessage('Agent type is required')
    .custom(customValidators.isAgentType).withMessage('Invalid agent type'),
  
  body('status')
    .optional()
    .trim()
    .isIn(['online', 'offline', 'busy', 'error']).withMessage('Invalid agent status'),
  
  body('capabilities')
    .optional()
    .isArray().withMessage('Capabilities must be an array')
    .custom((value) => value.every(cap => typeof cap === 'string')).withMessage('All capabilities must be strings'),
  
  body('location')
    .optional()
    .trim()
    .custom(customValidators.isValidPath).withMessage('Invalid location path'),
  
  body('project')
    .optional()
    .trim()
    .isLength({ max: 100 }).withMessage('Project name too long'),
  
  handleValidationErrors
];

// Activity validation rules
export const validateActivity = [
  body('agent_id')
    .trim()
    .notEmpty().withMessage('Agent ID is required')
    .isLength({ min: 1, max: 50 }).withMessage('Invalid agent ID length'),
  
  body('activity_type')
    .trim()
    .notEmpty().withMessage('Activity type is required')
    .isLength({ min: 1, max: 50 }).withMessage('Activity type must be 1-50 characters')
    .matches(/^[a-zA-Z0-9_\-]+$/).withMessage('Activity type must contain only alphanumeric characters, underscore, or dash'),
  
  body('description')
    .optional()
    .trim()
    .isLength({ max: 1000 }).withMessage('Description too long (max 1000 characters)')
    .escape(),
  
  body('status')
    .optional()
    .trim()
    .custom(customValidators.isActivityStatus).withMessage('Invalid activity status'),
  
  body('priority')
    .optional()
    .trim()
    .custom(customValidators.isPriority).withMessage('Invalid priority level'),
  
  handleValidationErrors
];

// Metric validation rules
export const validateMetric = [
  body('type')
    .trim()
    .notEmpty().withMessage('Metric type is required')
    .isLength({ min: 1, max: 50 }).withMessage('Metric type must be 1-50 characters')
    .matches(/^[a-zA-Z0-9_\-]+$/).withMessage('Invalid metric type format'),
  
  body('value')
    .notEmpty().withMessage('Metric value is required')
    .isNumeric().withMessage('Metric value must be numeric')
    .toFloat(),
  
  body('agentId')
    .optional()
    .trim()
    .isLength({ min: 1, max: 50 }).withMessage('Invalid agent ID'),
  
  body('metadata')
    .optional()
    .custom((value) => {
      if (typeof value === 'object' && value !== null) {
        return true;
      }
      if (typeof value === 'string') {
        return customValidators.isValidJSON(value);
      }
      return false;
    }).withMessage('Metadata must be a valid object or JSON string'),
  
  handleValidationErrors
];

// Communication validation rules
export const validateCommunication = [
  body('from_agent')
    .trim()
    .notEmpty().withMessage('From agent is required')
    .isLength({ min: 1, max: 50 }).withMessage('Invalid from agent ID'),
  
  body('to_agent')
    .trim()
    .notEmpty().withMessage('To agent is required')
    .isLength({ min: 1, max: 50 }).withMessage('Invalid to agent ID'),
  
  body('message_type')
    .trim()
    .notEmpty().withMessage('Message type is required')
    .isLength({ min: 1, max: 50 }).withMessage('Message type must be 1-50 characters'),
  
  body('priority')
    .optional()
    .trim()
    .custom(customValidators.isPriority).withMessage('Invalid priority level'),
  
  body('content')
    .trim()
    .notEmpty().withMessage('Message content is required')
    .isLength({ min: 1, max: 5000 }).withMessage('Message content must be 1-5000 characters')
    .escape(),
  
  handleValidationErrors
];

// Query parameter validation
export const validatePagination = [
  query('page')
    .optional()
    .isInt({ min: 1 }).withMessage('Page must be a positive integer')
    .toInt(),
  
  query('limit')
    .optional()
    .isInt({ min: 1, max: 1000 }).withMessage('Limit must be between 1 and 1000')
    .toInt(),
  
  query('sort')
    .optional()
    .matches(/^[a-zA-Z_]+$/).withMessage('Invalid sort field')
    .isIn(['created_at', 'updated_at', 'name', 'type', 'status']).withMessage('Invalid sort field'),
  
  query('order')
    .optional()
    .toUpperCase()
    .isIn(['ASC', 'DESC']).withMessage('Order must be ASC or DESC'),
  
  handleValidationErrors
];

// Date range validation
export const validateDateRange = [
  query('startDate')
    .optional()
    .isISO8601().withMessage('Start date must be valid ISO 8601 format')
    .toDate(),
  
  query('endDate')
    .optional()
    .isISO8601().withMessage('End date must be valid ISO 8601 format')
    .toDate()
    .custom((value, { req }) => {
      if (req.query.startDate && value < req.query.startDate) {
        throw new Error('End date must be after start date');
      }
      return true;
    }),
  
  handleValidationErrors
];

// ID parameter validation
export const validateIdParam = [
  param('id')
    .trim()
    .notEmpty().withMessage('ID is required')
    .matches(/^[a-zA-Z0-9_\-]+$/).withMessage('Invalid ID format'),
  
  handleValidationErrors
];

// File path validation
export const validateFilePath = [
  body('path')
    .trim()
    .notEmpty().withMessage('File path is required')
    .custom(customValidators.isValidPath).withMessage('Invalid file path')
    .custom((value) => {
      // Additional security checks
      const blacklistedPaths = ['/etc', '/root', '/home', 'C:\\Windows', 'C:\\Program Files'];
      const normalizedPath = value.replace(/\\/g, '/').toLowerCase();
      
      for (const blacklisted of blacklistedPaths) {
        if (normalizedPath.startsWith(blacklisted.toLowerCase())) {
          throw new Error('Access to this path is not allowed');
        }
      }
      
      return true;
    }),
  
  handleValidationErrors
];

// Search validation
export const validateSearch = [
  query('q')
    .optional()
    .trim()
    .isLength({ min: 1, max: 100 }).withMessage('Search query must be 1-100 characters')
    .escape()
    .customSanitizer((value) => {
      // Remove potential SQL injection attempts
      return value.replace(/[';\\]/g, '');
    }),
  
  query('type')
    .optional()
    .trim()
    .isIn(['agents', 'activities', 'metrics', 'all']).withMessage('Invalid search type'),
  
  handleValidationErrors
];

// Sanitization helpers
export const sanitizeOutput = (data) => {
  if (typeof data === 'string') {
    return validator.escape(data);
  }
  
  if (Array.isArray(data)) {
    return data.map(sanitizeOutput);
  }
  
  if (typeof data === 'object' && data !== null) {
    const sanitized = {};
    for (const [key, value] of Object.entries(data)) {
      sanitized[key] = sanitizeOutput(value);
    }
    return sanitized;
  }
  
  return data;
};

// Middleware to sanitize all responses
export const sanitizeResponse = (req, res, next) => {
  const originalJson = res.json;
  
  res.json = function(data) {
    // Don't sanitize if explicitly disabled
    if (res.locals.skipSanitization) {
      return originalJson.call(this, data);
    }
    
    // Sanitize the response data
    const sanitized = sanitizeOutput(data);
    return originalJson.call(this, sanitized);
  };
  
  next();
};

export default {
  handleValidationErrors,
  validateAgent,
  validateActivity,
  validateMetric,
  validateCommunication,
  validatePagination,
  validateDateRange,
  validateIdParam,
  validateFilePath,
  validateSearch,
  sanitizeOutput,
  sanitizeResponse
};