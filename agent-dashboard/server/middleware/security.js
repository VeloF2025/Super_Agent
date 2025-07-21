/**
 * Security Middleware Collection
 * Comprehensive security measures for the dashboard server
 */

import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import { body, validationResult } from 'express-validator';

class SecurityMiddleware {
  constructor(config) {
    this.config = config;
    this.jwtSecret = config.security.jwtSecret;
    this.saltRounds = 12;
  }

  // JWT Authentication
  authenticate = (req, res, next) => {
    // Skip auth for health check endpoint
    if (req.path === '/api/health') {
      return next();
    }

    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        error: 'Authentication required',
        message: 'Please provide a valid Bearer token'
      });
    }

    const token = authHeader.split(' ')[1];

    try {
      const decoded = jwt.verify(token, this.jwtSecret);
      req.user = decoded;
      next();
    } catch (error) {
      if (error.name === 'TokenExpiredError') {
        return res.status(401).json({
          error: 'Token expired',
          message: 'Please login again'
        });
      } else if (error.name === 'JsonWebTokenError') {
        return res.status(403).json({
          error: 'Invalid token',
          message: 'Token verification failed'
        });
      } else {
        return res.status(500).json({
          error: 'Authentication error',
          message: 'Internal server error'
        });
      }
    }
  };

  // Generate JWT token
  generateToken(user) {
    return jwt.sign(
      {
        userId: user.id,
        username: user.username,
        role: user.role || 'admin',
        iat: Math.floor(Date.now() / 1000)
      },
      this.jwtSecret,
      {
        expiresIn: '24h',
        issuer: 'super-agent-dashboard'
      }
    );
  }

  // Hash password
  async hashPassword(password) {
    return await bcrypt.hash(password, this.saltRounds);
  }

  // Verify password
  async verifyPassword(password, hash) {
    return await bcrypt.compare(password, hash);
  }

  // Rate limiting
  createRateLimiter(windowMs = 15 * 60 * 1000, max = 100) {
    return rateLimit({
      windowMs,
      max,
      message: {
        error: 'Too many requests',
        message: 'Rate limit exceeded. Please try again later.',
        retryAfter: Math.ceil(windowMs / 1000)
      },
      standardHeaders: true,
      legacyHeaders: false,
      handler: (req, res) => {
        res.status(429).json({
          error: 'Rate limit exceeded',
          message: `Too many requests from ${req.ip}, please try again later.`,
          retryAfter: Math.ceil(windowMs / 1000)
        });
      }
    });
  }

  // Strict rate limiting for auth endpoints
  createAuthRateLimiter() {
    return rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 5, // Only 5 login attempts per 15 minutes
      skipSuccessfulRequests: true,
      message: {
        error: 'Too many login attempts',
        message: 'Please wait 15 minutes before trying again.'
      }
    });
  }

  // Security headers
  securityHeaders = (req, res, next) => {
    // Strict Transport Security
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
    
    // Content Security Policy
    const cspDirectives = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "connect-src 'self' ws: wss:",
      "font-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'"
    ];

    if (this.config.security.cspReportOnly) {
      res.setHeader('Content-Security-Policy-Report-Only', cspDirectives.join('; '));
    } else {
      res.setHeader('Content-Security-Policy', cspDirectives.join('; '));
    }

    // Other security headers
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
    res.setHeader('X-Permitted-Cross-Domain-Policies', 'none');

    next();
  };

  // Input validation
  validateLogin = [
    body('username')
      .isLength({ min: 3, max: 50 })
      .matches(/^[a-zA-Z0-9_-]+$/)
      .withMessage('Username must be 3-50 characters and contain only letters, numbers, underscore, or dash'),
    body('password')
      .isLength({ min: 8, max: 100 })
      .withMessage('Password must be 8-100 characters'),
    (req, res, next) => {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({
          error: 'Validation failed',
          details: errors.array()
        });
      }
      next();
    }
  ];

  validateAgent = [
    body('id')
      .isLength({ min: 1, max: 50 })
      .matches(/^[a-zA-Z0-9_-]+$/)
      .withMessage('Agent ID must be 1-50 characters and contain only letters, numbers, underscore, or dash'),
    body('name')
      .isLength({ min: 1, max: 100 })
      .withMessage('Agent name must be 1-100 characters'),
    body('type')
      .isIn(['frontend', 'backend', 'quality', 'research', 'development', 'orchestrator'])
      .withMessage('Invalid agent type'),
    (req, res, next) => {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({
          error: 'Validation failed',
          details: errors.array()
        });
      }
      next();
    }
  ];

  // Input sanitization
  sanitizeInput = (req, res, next) => {
    const sanitize = (obj) => {
      for (const key in obj) {
        if (typeof obj[key] === 'string') {
          // Remove potentially dangerous characters
          obj[key] = obj[key]
            .replace(/[<>]/g, '') // Remove HTML brackets
            .replace(/['";\\]/g, '') // Remove potential SQL injection chars
            .trim();
        } else if (typeof obj[key] === 'object' && obj[key] !== null) {
          sanitize(obj[key]);
        }
      }
    };

    if (req.body && typeof req.body === 'object') {
      sanitize(req.body);
    }
    
    if (req.query && typeof req.query === 'object') {
      sanitize(req.query);
    }

    next();
  };

  // WebSocket authentication
  authenticateWebSocket = (info, callback) => {
    const url = new URL(info.req.url, 'ws://localhost');
    const token = url.searchParams.get('token');

    if (!token) {
      callback(false, 401, 'Authentication required');
      return;
    }

    try {
      const decoded = jwt.verify(token, this.jwtSecret);
      info.req.user = decoded;
      callback(true);
    } catch (error) {
      callback(false, 403, 'Invalid token');
    }
  };

  // Audit logging middleware
  auditLog = (req, res, next) => {
    const startTime = Date.now();
    
    res.on('finish', () => {
      const duration = Date.now() - startTime;
      const logData = {
        timestamp: new Date().toISOString(),
        method: req.method,
        url: req.url,
        statusCode: res.statusCode,
        duration,
        userAgent: req.headers['user-agent'],
        ip: req.ip || req.connection.remoteAddress,
        user: req.user ? req.user.username : 'anonymous'
      };

      // Log security-relevant events
      if (req.url.includes('/auth') || res.statusCode >= 400) {
        console.log('AUDIT:', JSON.stringify(logData));
      }
    });

    next();
  };

  // CORS configuration
  corsOptions = {
    origin: this.config.cors.origin,
    credentials: this.config.cors.credentials,
    optionsSuccessStatus: 200,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
  };

  // Helmet configuration for additional security
  helmetOptions = {
    contentSecurityPolicy: false, // We handle CSP manually
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true
    }
  };
}

export default SecurityMiddleware;