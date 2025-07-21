/**
 * Authentication Service Tests
 * Test coverage for authentication and authorization
 */

import { jest } from '@jest/globals';
import { DatabaseService } from '../../server/services/database.js';
import { AuthService } from '../../server/services/auth.js';
import SecurityMiddleware from '../../server/middleware/security.js';
import config from '../../../config/environment.js';

describe('AuthService', () => {
  let db;
  let authService;
  let securityMiddleware;

  beforeEach(() => {
    db = new DatabaseService(':memory:');
    securityMiddleware = new SecurityMiddleware(config);
    authService = new AuthService(db, securityMiddleware);
  });

  afterEach(() => {
    if (db) {
      db.close();
    }
  });

  describe('User Management', () => {
    test('should create default admin user on initialization', () => {
      const users = authService.getUsers();
      expect(users).toHaveLength(1);
      expect(users[0].username).toBe('admin');
      expect(users[0].role).toBe('admin');
    });

    test('should create new user with hashed password', async () => {
      const user = await authService.createUser('testuser', 'password123', 'viewer');
      
      expect(user.id).toBeDefined();
      expect(user.username).toBe('testuser');
      expect(user.role).toBe('viewer');
      
      // Verify password is hashed
      const savedUser = db.db.prepare('SELECT * FROM users WHERE id = ?').get(user.id);
      expect(savedUser.password_hash).not.toBe('password123');
      expect(savedUser.password_hash).toMatch(/^\$2[ayb]\$.{56}$/); // bcrypt hash pattern
    });

    test('should reject duplicate usernames', async () => {
      await authService.createUser('duplicate', 'password123');
      
      await expect(
        authService.createUser('duplicate', 'password456')
      ).rejects.toThrow('Username already exists');
    });

    test('should delete user and their sessions', async () => {
      const user = await authService.createUser('deleteme', 'password123');
      
      // Create a session for the user
      await authService.login('deleteme', 'password123', '127.0.0.1', 'Test Agent');
      
      // Delete user
      authService.deleteUser(user.id);
      
      // Verify user is deleted
      const users = authService.getUsers();
      expect(users.find(u => u.id === user.id)).toBeUndefined();
      
      // Verify sessions are deleted
      const sessions = db.db.prepare('SELECT * FROM sessions WHERE user_id = ?').all(user.id);
      expect(sessions).toHaveLength(0);
    });

    test('should prevent deleting last admin user', async () => {
      const adminUsers = authService.getUsers().filter(u => u.role === 'admin');
      expect(adminUsers).toHaveLength(1);
      
      expect(() => {
        authService.deleteUser(adminUsers[0].id);
      }).toThrow('Cannot delete the last admin user');
    });
  });

  describe('Authentication', () => {
    beforeEach(async () => {
      await authService.createUser('testuser', 'correctpassword', 'viewer');
    });

    test('should login with correct credentials', async () => {
      const result = await authService.login('testuser', 'correctpassword', '127.0.0.1', 'Test Agent');
      
      expect(result.token).toBeDefined();
      expect(result.user.username).toBe('testuser');
      expect(result.user.role).toBe('viewer');
      expect(result.expiresAt).toBeDefined();
      
      // Verify session is created
      const sessions = db.db.prepare('SELECT * FROM sessions WHERE user_id = ?').all(result.user.id);
      expect(sessions).toHaveLength(1);
    });

    test('should reject invalid username', async () => {
      await expect(
        authService.login('wronguser', 'password', '127.0.0.1', 'Test Agent')
      ).rejects.toThrow('Invalid credentials');
    });

    test('should reject invalid password', async () => {
      await expect(
        authService.login('testuser', 'wrongpassword', '127.0.0.1', 'Test Agent')
      ).rejects.toThrow('Invalid credentials');
    });

    test('should track failed login attempts', async () => {
      // Make 4 failed attempts
      for (let i = 0; i < 4; i++) {
        try {
          await authService.login('testuser', 'wrongpassword', '127.0.0.1', 'Test Agent');
        } catch (e) {
          // Expected to fail
        }
      }
      
      // Check failed attempts count
      const user = db.db.prepare('SELECT failed_attempts FROM users WHERE username = ?').get('testuser');
      expect(user.failed_attempts).toBe(4);
      
      // 5th attempt should lock the account
      try {
        await authService.login('testuser', 'wrongpassword', '127.0.0.1', 'Test Agent');
      } catch (e) {
        // Expected to fail
      }
      
      // Account should be locked
      const lockedUser = db.db.prepare('SELECT locked_until FROM users WHERE username = ?').get('testuser');
      expect(lockedUser.locked_until).toBeDefined();
      
      // Even correct password should fail
      await expect(
        authService.login('testuser', 'correctpassword', '127.0.0.1', 'Test Agent')
      ).rejects.toThrow('Account locked');
    });

    test('should reset failed attempts on successful login', async () => {
      // Make 2 failed attempts
      for (let i = 0; i < 2; i++) {
        try {
          await authService.login('testuser', 'wrongpassword', '127.0.0.1', 'Test Agent');
        } catch (e) {
          // Expected
        }
      }
      
      // Successful login
      await authService.login('testuser', 'correctpassword', '127.0.0.1', 'Test Agent');
      
      // Check failed attempts reset
      const user = db.db.prepare('SELECT failed_attempts FROM users WHERE username = ?').get('testuser');
      expect(user.failed_attempts).toBe(0);
    });

    test('should logout and remove session', async () => {
      const { token } = await authService.login('testuser', 'correctpassword', '127.0.0.1', 'Test Agent');
      
      // Verify session exists
      let sessions = db.db.prepare('SELECT * FROM sessions WHERE token = ?').all(token);
      expect(sessions).toHaveLength(1);
      
      // Logout
      await authService.logout(token, '127.0.0.1', 'Test Agent');
      
      // Verify session is removed
      sessions = db.db.prepare('SELECT * FROM sessions WHERE token = ?').all(token);
      expect(sessions).toHaveLength(0);
    });
  });

  describe('Password Management', () => {
    let userId;

    beforeEach(async () => {
      const user = await authService.createUser('passuser', 'oldpassword', 'viewer');
      userId = user.id;
    });

    test('should change password with correct current password', async () => {
      await authService.changePassword(userId, 'oldpassword', 'newpassword');
      
      // Verify can login with new password
      const result = await authService.login('passuser', 'newpassword', '127.0.0.1', 'Test Agent');
      expect(result.token).toBeDefined();
    });

    test('should reject password change with wrong current password', async () => {
      await expect(
        authService.changePassword(userId, 'wrongpassword', 'newpassword')
      ).rejects.toThrow('Invalid current password');
    });

    test('should invalidate all sessions after password change', async () => {
      // Create multiple sessions
      await authService.login('passuser', 'oldpassword', '127.0.0.1', 'Agent 1');
      await authService.login('passuser', 'oldpassword', '192.168.1.1', 'Agent 2');
      
      // Verify sessions exist
      let sessions = db.db.prepare('SELECT * FROM sessions WHERE user_id = ?').all(userId);
      expect(sessions).toHaveLength(2);
      
      // Change password
      await authService.changePassword(userId, 'oldpassword', 'newpassword');
      
      // Verify all sessions are invalidated
      sessions = db.db.prepare('SELECT * FROM sessions WHERE user_id = ?').all(userId);
      expect(sessions).toHaveLength(0);
    });
  });

  describe('Session Management', () => {
    test('should clean up expired sessions', async () => {
      const user = await authService.createUser('sessionuser', 'password', 'viewer');
      
      // Create sessions with different expiry times
      const now = Date.now();
      const expired = new Date(now - 1000).toISOString(); // Expired
      const valid = new Date(now + 3600000).toISOString(); // Valid for 1 hour
      
      db.db.prepare(`
        INSERT INTO sessions (id, user_id, token, expires_at)
        VALUES (?, ?, ?, ?)
      `).run('session1', user.id, 'expired-token', expired);
      
      db.db.prepare(`
        INSERT INTO sessions (id, user_id, token, expires_at)
        VALUES (?, ?, ?, ?)
      `).run('session2', user.id, 'valid-token', valid);
      
      // Clean up
      authService.cleanupExpiredSessions();
      
      // Verify only valid session remains
      const sessions = db.db.prepare('SELECT * FROM sessions').all();
      expect(sessions).toHaveLength(1);
      expect(sessions[0].token).toBe('valid-token');
    });
  });

  describe('Audit Logging', () => {
    test('should log authentication events', async () => {
      const user = await authService.createUser('audituser', 'password', 'viewer');
      
      // Failed login
      try {
        await authService.login('audituser', 'wrongpassword', '127.0.0.1', 'Test Agent');
      } catch (e) {
        // Expected
      }
      
      // Successful login
      await authService.login('audituser', 'password', '127.0.0.1', 'Test Agent');
      
      // Get audit logs
      const logs = authService.getAuditLogs();
      
      // Should have: user_created, login_failed, login_success
      expect(logs.length).toBeGreaterThanOrEqual(3);
      
      const failedLogin = logs.find(l => l.action === 'login_failed');
      expect(failedLogin).toBeDefined();
      expect(failedLogin.success).toBe(0);
      
      const successLogin = logs.find(l => l.action === 'login_success');
      expect(successLogin).toBeDefined();
      expect(successLogin.success).toBe(1);
    });

    test('should include user information in audit logs', async () => {
      await authService.createUser('audituser2', 'password', 'admin');
      
      const logs = authService.getAuditLogs();
      const createLog = logs.find(l => l.action === 'user_created' && l.username === 'audituser2');
      
      expect(createLog).toBeDefined();
      expect(createLog.username).toBe('audituser2');
    });
  });

  describe('Token Validation', () => {
    test('should generate valid JWT tokens', async () => {
      const { token } = await authService.login('admin', 'password', '127.0.0.1', 'Test Agent');
      
      // Manually verify token
      const jwt = await import('jsonwebtoken');
      const decoded = jwt.default.verify(token, config.security.jwtSecret);
      
      expect(decoded.username).toBe('admin');
      expect(decoded.role).toBe('admin');
      expect(decoded.iat).toBeDefined();
      expect(decoded.exp).toBeDefined();
    });

    test('should reject expired tokens', async () => {
      const jwt = await import('jsonwebtoken');
      const expiredToken = jwt.default.sign(
        { userId: 'test', username: 'test', role: 'viewer' },
        config.security.jwtSecret,
        { expiresIn: '-1h' } // Already expired
      );
      
      expect(() => {
        securityMiddleware.authenticate(
          { headers: { authorization: `Bearer ${expiredToken}` } },
          { status: () => ({ json: jest.fn() }) },
          jest.fn()
        );
      }).toThrow();
    });
  });
});