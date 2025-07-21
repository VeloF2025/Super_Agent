/**
 * Global Error Handler Middleware
 * Centralized error handling with proper logging and client responses
 */

import { ValidationError } from 'express-validator';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Error types
export class AppError extends Error {
  constructor(message, statusCode, code = 'GENERIC_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

export class ValidationError extends AppError {
  constructor(message, errors = []) {
    super(message, 400, 'VALIDATION_ERROR');
    this.errors = errors;
  }
}

export class AuthenticationError extends AppError {
  constructor(message = 'Authentication required') {
    super(message, 401, 'AUTHENTICATION_ERROR');
  }
}

export class AuthorizationError extends AppError {
  constructor(message = 'Insufficient permissions') {
    super(message, 403, 'AUTHORIZATION_ERROR');
  }
}

export class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super(`${resource} not found`, 404, 'NOT_FOUND');
    this.resource = resource;
  }
}

export class ConflictError extends AppError {
  constructor(message = 'Resource conflict') {
    super(message, 409, 'CONFLICT');
  }
}

export class RateLimitError extends AppError {
  constructor(message = 'Too many requests', retryAfter = 60) {
    super(message, 429, 'RATE_LIMIT_EXCEEDED');
    this.retryAfter = retryAfter;
  }
}

export class DatabaseError extends AppError {
  constructor(message = 'Database operation failed', originalError = null) {
    super(message, 500, 'DATABASE_ERROR');
    this.originalError = originalError;
  }
}

// Error logger
class ErrorLogger {
  constructor() {
    const logDir = path.join(__dirname, '../../../logs');
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    this.errorLogPath = path.join(logDir, 'errors.log');
  }

  log(error, req) {
    const errorLog = {
      timestamp: new Date().toISOString(),
      error: {
        message: error.message,
        code: error.code || 'UNKNOWN',
        statusCode: error.statusCode || 500,
        stack: error.stack
      },
      request: {
        method: req.method,
        url: req.url,
        ip: req.ip || req.connection.remoteAddress,
        userAgent: req.headers['user-agent'],
        user: req.user ? req.user.username : 'anonymous'
      }
    };

    // Append to error log file
    fs.appendFileSync(
      this.errorLogPath,
      JSON.stringify(errorLog) + '\n',
      'utf8'
    );

    // Also log to console in development
    if (process.env.NODE_ENV !== 'production') {
      console.error('Error logged:', errorLog);
    }
  }
}

const errorLogger = new ErrorLogger();

// Async error wrapper for route handlers
export const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// Global error handler middleware
export const errorHandler = (err, req, res, next) => {
  // Log the error
  errorLogger.log(err, req);

  // Default to 500 server error
  let statusCode = err.statusCode || 500;
  let message = err.message || 'Internal server error';
  let code = err.code || 'INTERNAL_ERROR';

  // Handle specific error types
  if (err.name === 'ValidationError' && err.errors) {
    // Express-validator errors
    statusCode = 400;
    code = 'VALIDATION_ERROR';
    message = 'Validation failed';
    
    const errors = err.errors.map(e => ({
      field: e.param,
      message: e.msg,
      value: e.value
    }));

    return res.status(statusCode).json({
      success: false,
      error: {
        code,
        message,
        errors
      }
    });
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    statusCode = 403;
    code = 'INVALID_TOKEN';
    message = 'Invalid authentication token';
  } else if (err.name === 'TokenExpiredError') {
    statusCode = 401;
    code = 'TOKEN_EXPIRED';
    message = 'Authentication token has expired';
  }

  // Database errors
  if (err.code === 'SQLITE_CONSTRAINT') {
    statusCode = 409;
    code = 'DATABASE_CONSTRAINT';
    message = 'Database constraint violation';
  } else if (err.code === 'SQLITE_ERROR') {
    statusCode = 500;
    code = 'DATABASE_ERROR';
    message = 'Database operation failed';
  }

  // Rate limit errors
  if (err.statusCode === 429) {
    res.setHeader('Retry-After', err.retryAfter || 60);
  }

  // Send error response
  const errorResponse = {
    success: false,
    error: {
      code,
      message
    }
  };

  // Add additional error details in development
  if (process.env.NODE_ENV !== 'production') {
    errorResponse.error.details = {
      statusCode,
      stack: err.stack,
      originalError: err.originalError?.message
    };
  }

  // Add request ID if available
  if (req.id) {
    errorResponse.error.requestId = req.id;
  }

  res.status(statusCode).json(errorResponse);
};

// 404 handler
export const notFoundHandler = (req, res) => {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Cannot ${req.method} ${req.url}`,
      path: req.url
    }
  });
};

// Uncaught exception handler
export const handleUncaughtExceptions = () => {
  process.on('uncaughtException', (error) => {
    console.error('UNCAUGHT EXCEPTION! 💥 Shutting down...');
    console.error(error);
    
    // Log to file
    const errorLog = {
      timestamp: new Date().toISOString(),
      type: 'UNCAUGHT_EXCEPTION',
      error: {
        message: error.message,
        stack: error.stack
      }
    };
    
    try {
      const logPath = path.join(__dirname, '../../../logs/critical-errors.log');
      fs.appendFileSync(logPath, JSON.stringify(errorLog) + '\n', 'utf8');
    } catch (logError) {
      console.error('Failed to log critical error:', logError);
    }
    
    process.exit(1);
  });
};

// Unhandled rejection handler
export const handleUnhandledRejections = () => {
  process.on('unhandledRejection', (reason, promise) => {
    console.error('UNHANDLED REJECTION! 💥 Shutting down...');
    console.error('Reason:', reason);
    console.error('Promise:', promise);
    
    // Log to file
    const errorLog = {
      timestamp: new Date().toISOString(),
      type: 'UNHANDLED_REJECTION',
      error: {
        reason: reason?.toString(),
        promise: promise?.toString()
      }
    };
    
    try {
      const logPath = path.join(__dirname, '../../../logs/critical-errors.log');
      fs.appendFileSync(logPath, JSON.stringify(errorLog) + '\n', 'utf8');
    } catch (logError) {
      console.error('Failed to log critical error:', logError);
    }
    
    process.exit(1);
  });
};

// Request ID middleware
export const requestIdMiddleware = (req, res, next) => {
  req.id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  res.setHeader('X-Request-ID', req.id);
  next();
};

export default {
  AppError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  RateLimitError,
  DatabaseError,
  asyncHandler,
  errorHandler,
  notFoundHandler,
  handleUncaughtExceptions,
  handleUnhandledRejections,
  requestIdMiddleware
};