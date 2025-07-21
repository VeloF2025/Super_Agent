/**
 * Security Middleware Tests
 * Test coverage for security middleware functions
 */

import { jest } from '@jest/globals';
import SecurityMiddleware from '../../server/middleware/security.js';
import config from '../../../config/environment.js';

describe('SecurityMiddleware', () => {
  let securityMiddleware;
  let mockReq, mockRes, mockNext;

  beforeEach(() => {
    securityMiddleware = new SecurityMiddleware(config);
    
    // Mock Express request, response, and next
    mockReq = {
      headers: {},
      body: {},
      query: {},
      path: '/api/test',
      ip: '127.0.0.1',
      connection: { remoteAddress: '127.0.0.1' }
    };
    
    mockRes = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
      setHeader: jest.fn(),
      on: jest.fn()
    };
    
    mockNext = jest.fn();
  });

  describe('Authentication Middleware', () => {
    test('should allow health check endpoint without auth', () => {
      mockReq.path = '/api/health';
      
      securityMiddleware.authenticate(mockReq, mockRes, mockNext);
      
      expect(mockNext).toHaveBeenCalled();
      expect(mockRes.status).not.toHaveBeenCalled();
    });

    test('should reject requests without authorization header', () => {
      securityMiddleware.authenticate(mockReq, mockRes, mockNext);
      
      expect(mockRes.status).toHaveBeenCalledWith(401);
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Authentication required',
        message: 'Please provide a valid Bearer token'
      });
      expect(mockNext).not.toHaveBeenCalled();
    });

    test('should reject requests with invalid authorization format', () => {
      mockReq.headers.authorization = 'InvalidFormat token123';
      
      securityMiddleware.authenticate(mockReq, mockRes, mockNext);
      
      expect(mockRes.status).toHaveBeenCalledWith(401);
      expect(mockNext).not.toHaveBeenCalled();
    });

    test('should accept valid JWT token', () => {
      const validToken = securityMiddleware.generateToken({
        id: 'user123',
        username: 'testuser',
        role: 'admin'
      });
      
      mockReq.headers.authorization = `Bearer ${validToken}`;
      
      securityMiddleware.authenticate(mockReq, mockRes, mockNext);
      
      expect(mockNext).toHaveBeenCalled();
      expect(mockReq.user).toBeDefined();
      expect(mockReq.user.username).toBe('testuser');
    });

    test('should handle expired tokens', () => {
      const jwt = require('jsonwebtoken');
      const expiredToken = jwt.sign(
        { userId: 'test' },
        config.security.jwtSecret,
        { expiresIn: '-1h' }
      );
      
      mockReq.headers.authorization = `Bearer ${expiredToken}`;
      
      securityMiddleware.authenticate(mockReq, mockRes, mockNext);
      
      expect(mockRes.status).toHaveBeenCalledWith(401);
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Token expired',
        message: 'Please login again'
      });
    });

    test('should handle invalid tokens', () => {
      mockReq.headers.authorization = 'Bearer invalid.token.here';
      
      securityMiddleware.authenticate(mockReq, mockRes, mockNext);
      
      expect(mockRes.status).toHaveBeenCalledWith(403);
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Invalid token',
        message: 'Token verification failed'
      });
    });
  });

  describe('Security Headers', () => {
    test('should set all security headers', () => {
      securityMiddleware.securityHeaders(mockReq, mockRes, mockNext);
      
      expect(mockRes.setHeader).toHaveBeenCalledWith(
        'Strict-Transport-Security',
        'max-age=31536000; includeSubDomains; preload'
      );
      expect(mockRes.setHeader).toHaveBeenCalledWith('X-Content-Type-Options', 'nosniff');
      expect(mockRes.setHeader).toHaveBeenCalledWith('X-Frame-Options', 'DENY');
      expect(mockRes.setHeader).toHaveBeenCalledWith('X-XSS-Protection', '1; mode=block');
      expect(mockRes.setHeader).toHaveBeenCalledWith(
        'Referrer-Policy',
        'strict-origin-when-cross-origin'
      );
      expect(mockRes.setHeader).toHaveBeenCalledWith(
        'Permissions-Policy',
        'geolocation=(), microphone=(), camera=()'
      );
      expect(mockNext).toHaveBeenCalled();
    });

    test('should set CSP header based on configuration', () => {
      // Test report-only mode
      config.security.cspReportOnly = true;
      const middleware = new SecurityMiddleware(config);
      
      middleware.securityHeaders(mockReq, mockRes, mockNext);
      
      const cspCalls = mockRes.setHeader.mock.calls.filter(
        call => call[0].includes('Content-Security-Policy')
      );
      expect(cspCalls.length).toBeGreaterThan(0);
      expect(cspCalls[0][0]).toBe('Content-Security-Policy-Report-Only');
    });
  });

  describe('Input Sanitization', () => {
    test('should sanitize string inputs in body', () => {
      mockReq.body = {
        username: 'test<script>alert("xss")</script>user',
        description: 'Normal text with "quotes"',
        nested: {
          field: '<img src=x onerror=alert(1)>'
        }
      };
      
      securityMiddleware.sanitizeInput(mockReq, mockRes, mockNext);
      
      expect(mockReq.body.username).toBe('testscriptalert(xss)/scriptuser');
      expect(mockReq.body.description).toBe('Normal text with quotes');
      expect(mockReq.body.nested.field).toBe('img src=x onerror=alert(1)');
      expect(mockNext).toHaveBeenCalled();
    });

    test('should sanitize query parameters', () => {
      mockReq.query = {
        search: "'; DROP TABLE users; --",
        page: '1'
      };
      
      securityMiddleware.sanitizeInput(mockReq, mockRes, mockNext);
      
      expect(mockReq.query.search).toBe(' DROP TABLE users --');
      expect(mockReq.query.page).toBe('1');
    });

    test('should handle non-string values', () => {
      mockReq.body = {
        number: 123,
        boolean: true,
        array: [1, 2, 3],
        null: null
      };
      
      securityMiddleware.sanitizeInput(mockReq, mockRes, mockNext);
      
      expect(mockReq.body.number).toBe(123);
      expect(mockReq.body.boolean).toBe(true);
      expect(mockReq.body.array).toEqual([1, 2, 3]);
      expect(mockReq.body.null).toBe(null);
    });
  });

  describe('Rate Limiting', () => {
    test('should create rate limiter with default settings', () => {
      const limiter = securityMiddleware.createRateLimiter();
      expect(limiter).toBeDefined();
      expect(typeof limiter).toBe('function');
    });

    test('should create auth rate limiter with strict settings', () => {
      const authLimiter = securityMiddleware.createAuthRateLimiter();
      expect(authLimiter).toBeDefined();
      expect(typeof authLimiter).toBe('function');
    });
  });

  describe('Password Security', () => {
    test('should hash passwords with bcrypt', async () => {
      const password = 'MySecurePassword123!';
      const hash = await securityMiddleware.hashPassword(password);
      
      expect(hash).not.toBe(password);
      expect(hash).toMatch(/^\$2[ayb]\$.{56}$/); // bcrypt pattern
    });

    test('should verify correct passwords', async () => {
      const password = 'TestPassword456';
      const hash = await securityMiddleware.hashPassword(password);
      
      const isValid = await securityMiddleware.verifyPassword(password, hash);
      expect(isValid).toBe(true);
    });

    test('should reject incorrect passwords', async () => {
      const password = 'CorrectPassword';
      const hash = await securityMiddleware.hashPassword(password);
      
      const isValid = await securityMiddleware.verifyPassword('WrongPassword', hash);
      expect(isValid).toBe(false);
    });

    test('should generate different hashes for same password', async () => {
      const password = 'SamePassword';
      const hash1 = await securityMiddleware.hashPassword(password);
      const hash2 = await securityMiddleware.hashPassword(password);
      
      expect(hash1).not.toBe(hash2); // Different salts
      
      // But both should verify correctly
      expect(await securityMiddleware.verifyPassword(password, hash1)).toBe(true);
      expect(await securityMiddleware.verifyPassword(password, hash2)).toBe(true);
    });
  });

  describe('WebSocket Authentication', () => {
    test('should authenticate WebSocket with valid token', (done) => {
      const token = securityMiddleware.generateToken({
        id: 'user123',
        username: 'wsuser',
        role: 'viewer'
      });
      
      const mockInfo = {
        req: {
          url: `/?token=${token}`
        }
      };
      
      securityMiddleware.authenticateWebSocket(mockInfo, (result) => {
        expect(result).toBe(true);
        expect(mockInfo.req.user).toBeDefined();
        expect(mockInfo.req.user.username).toBe('wsuser');
        done();
      });
    });

    test('should reject WebSocket without token', (done) => {
      const mockInfo = {
        req: {
          url: '/'
        }
      };
      
      securityMiddleware.authenticateWebSocket(mockInfo, (result, code, message) => {
        expect(result).toBe(false);
        expect(code).toBe(401);
        expect(message).toBe('Authentication required');
        done();
      });
    });

    test('should reject WebSocket with invalid token', (done) => {
      const mockInfo = {
        req: {
          url: '/?token=invalid.token.here'
        }
      };
      
      securityMiddleware.authenticateWebSocket(mockInfo, (result, code, message) => {
        expect(result).toBe(false);
        expect(code).toBe(403);
        expect(message).toBe('Invalid token');
        done();
      });
    });
  });

  describe('Audit Logging', () => {
    test('should log requests on finish', (done) => {
      const startTime = Date.now();
      mockReq.method = 'POST';
      mockReq.url = '/api/auth/login';
      mockReq.headers['user-agent'] = 'Test Agent';
      mockReq.user = { username: 'testuser' };
      
      // Mock response finish event
      mockRes.on = jest.fn((event, callback) => {
        if (event === 'finish') {
          setTimeout(() => {
            mockRes.statusCode = 200;
            callback();
            
            // Verify console.log was called with audit data
            expect(global.console.log).toHaveBeenCalledWith(
              'AUDIT:',
              expect.stringContaining('"method":"POST"')
            );
            expect(global.console.log).toHaveBeenCalledWith(
              'AUDIT:',
              expect.stringContaining('"url":"/api/auth/login"')
            );
            expect(global.console.log).toHaveBeenCalledWith(
              'AUDIT:',
              expect.stringContaining('"user":"testuser"')
            );
            done();
          }, 10);
        }
      });
      
      securityMiddleware.auditLog(mockReq, mockRes, mockNext);
      expect(mockNext).toHaveBeenCalled();
    });
  });

  describe('CORS Configuration', () => {
    test('should have proper CORS options', () => {
      expect(securityMiddleware.corsOptions).toBeDefined();
      expect(securityMiddleware.corsOptions.credentials).toBe(true);
      expect(securityMiddleware.corsOptions.methods).toContain('GET');
      expect(securityMiddleware.corsOptions.methods).toContain('POST');
      expect(securityMiddleware.corsOptions.allowedHeaders).toContain('Authorization');
    });
  });

  describe('Helmet Configuration', () => {
    test('should have proper helmet options', () => {
      expect(securityMiddleware.helmetOptions).toBeDefined();
      expect(securityMiddleware.helmetOptions.contentSecurityPolicy).toBe(false);
      expect(securityMiddleware.helmetOptions.hsts).toBeDefined();
      expect(securityMiddleware.helmetOptions.hsts.maxAge).toBe(31536000);
      expect(securityMiddleware.helmetOptions.hsts.includeSubDomains).toBe(true);
    });
  });
});