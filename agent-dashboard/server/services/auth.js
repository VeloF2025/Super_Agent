/**
 * Authentication Service
 * Handles user authentication and session management
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import crypto from 'crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class AuthService {
  constructor(db, securityMiddleware) {
    this.db = db;
    this.security = securityMiddleware;
    this.initializeSchema();
    this.ensureDefaultAdmin();
  }

  initializeSchema() {
    // Create users table
    this.db.db.exec(`
      CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'viewer',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME,
        is_active BOOLEAN DEFAULT 1,
        failed_attempts INTEGER DEFAULT 0,
        locked_until DATETIME
      )
    `);

    // Create sessions table
    this.db.db.exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
      )
    `);

    // Create audit log table
    this.db.db.exec(`
      CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        action TEXT NOT NULL,
        resource TEXT,
        ip_address TEXT,
        user_agent TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        success BOOLEAN DEFAULT 1,
        details TEXT
      )
    `);

    // Create indexes
    this.db.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
      CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
      CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
    `);
  }

  async ensureDefaultAdmin() {
    const adminExists = this.db.db.prepare('SELECT id FROM users WHERE username = ?').get('admin');
    
    if (!adminExists) {
      // Generate secure random password
      const defaultPassword = crypto.randomBytes(16).toString('hex');
      const passwordHash = await this.security.hashPassword(defaultPassword);
      
      const stmt = this.db.db.prepare(`
        INSERT INTO users (id, username, password_hash, role)
        VALUES (@id, @username, @password_hash, @role)
      `);
      
      stmt.run({
        id: crypto.randomUUID(),
        username: 'admin',
        password_hash: passwordHash,
        role: 'admin'
      });

      // Save credentials to file (first time setup only)
      const credsPath = path.join(__dirname, '../../../ADMIN_CREDENTIALS.txt');
      const credentials = `
========================================
SUPER AGENT DASHBOARD - ADMIN CREDENTIALS
========================================

Username: admin
Password: ${defaultPassword}

IMPORTANT: 
- Change this password immediately after first login
- Delete this file after noting the credentials
- This file is in .gitignore and won't be committed

Login URL: http://localhost:3010/login
========================================
`;
      
      fs.writeFileSync(credsPath, credentials, { mode: 0o600 });
      console.log('\n⚠️  DEFAULT ADMIN USER CREATED');
      console.log(`📄 Credentials saved to: ${credsPath}`);
      console.log('🔒 Please change the password after first login!\n');
    }
  }

  async login(username, password, ipAddress, userAgent) {
    const user = this.db.db.prepare('SELECT * FROM users WHERE username = ?').get(username);
    
    if (!user) {
      this.logAudit(null, 'login_failed', 'auth', ipAddress, userAgent, false, 'User not found');
      throw new Error('Invalid credentials');
    }

    // Check if account is locked
    if (user.locked_until && new Date(user.locked_until) > new Date()) {
      this.logAudit(user.id, 'login_blocked', 'auth', ipAddress, userAgent, false, 'Account locked');
      throw new Error('Account locked. Please try again later.');
    }

    // Verify password
    const isValid = await this.security.verifyPassword(password, user.password_hash);
    
    if (!isValid) {
      // Increment failed attempts
      const newFailedAttempts = user.failed_attempts + 1;
      let lockedUntil = null;
      
      if (newFailedAttempts >= 5) {
        // Lock account for 30 minutes after 5 failed attempts
        lockedUntil = new Date(Date.now() + 30 * 60 * 1000).toISOString();
      }
      
      this.db.db.prepare(`
        UPDATE users 
        SET failed_attempts = ?, locked_until = ?
        WHERE id = ?
      `).run(newFailedAttempts, lockedUntil, user.id);
      
      this.logAudit(user.id, 'login_failed', 'auth', ipAddress, userAgent, false, 'Invalid password');
      throw new Error('Invalid credentials');
    }

    // Reset failed attempts and update last login
    this.db.db.prepare(`
      UPDATE users 
      SET failed_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
      WHERE id = ?
    `).run(user.id);

    // Generate token
    const token = this.security.generateToken(user);
    const sessionId = crypto.randomUUID();
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    // Store session
    this.db.db.prepare(`
      INSERT INTO sessions (id, user_id, token, expires_at, ip_address, user_agent)
      VALUES (@id, @user_id, @token, @expires_at, @ip_address, @user_agent)
    `).run({
      id: sessionId,
      user_id: user.id,
      token: token,
      expires_at: expiresAt,
      ip_address: ipAddress,
      user_agent: userAgent
    });

    this.logAudit(user.id, 'login_success', 'auth', ipAddress, userAgent, true);

    return {
      token,
      user: {
        id: user.id,
        username: user.username,
        role: user.role
      },
      expiresAt
    };
  }

  async logout(token, ipAddress, userAgent) {
    const session = this.db.db.prepare('SELECT * FROM sessions WHERE token = ?').get(token);
    
    if (session) {
      this.db.db.prepare('DELETE FROM sessions WHERE token = ?').run(token);
      this.logAudit(session.user_id, 'logout', 'auth', ipAddress, userAgent, true);
    }
  }

  async changePassword(userId, currentPassword, newPassword) {
    const user = this.db.db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
    
    if (!user) {
      throw new Error('User not found');
    }

    const isValid = await this.security.verifyPassword(currentPassword, user.password_hash);
    
    if (!isValid) {
      this.logAudit(userId, 'password_change_failed', 'auth', null, null, false, 'Invalid current password');
      throw new Error('Invalid current password');
    }

    const newPasswordHash = await this.security.hashPassword(newPassword);
    
    this.db.db.prepare(`
      UPDATE users SET password_hash = ? WHERE id = ?
    `).run(newPasswordHash, userId);

    // Invalidate all existing sessions
    this.db.db.prepare('DELETE FROM sessions WHERE user_id = ?').run(userId);

    this.logAudit(userId, 'password_changed', 'auth', null, null, true);
  }

  async createUser(username, password, role = 'viewer') {
    const existingUser = this.db.db.prepare('SELECT id FROM users WHERE username = ?').get(username);
    
    if (existingUser) {
      throw new Error('Username already exists');
    }

    const userId = crypto.randomUUID();
    const passwordHash = await this.security.hashPassword(password);

    this.db.db.prepare(`
      INSERT INTO users (id, username, password_hash, role)
      VALUES (@id, @username, @password_hash, @role)
    `).run({
      id: userId,
      username: username,
      password_hash: passwordHash,
      role: role
    });

    this.logAudit(userId, 'user_created', 'auth', null, null, true);

    return { id: userId, username, role };
  }

  getUsers() {
    return this.db.db.prepare(`
      SELECT id, username, role, created_at, last_login, is_active
      FROM users
      ORDER BY created_at DESC
    `).all();
  }

  deleteUser(userId) {
    // Don't allow deleting the last admin
    const adminCount = this.db.db.prepare('SELECT COUNT(*) as count FROM users WHERE role = "admin"').get().count;
    const userRole = this.db.db.prepare('SELECT role FROM users WHERE id = ?').get(userId)?.role;
    
    if (adminCount === 1 && userRole === 'admin') {
      throw new Error('Cannot delete the last admin user');
    }

    // Delete user sessions first
    this.db.db.prepare('DELETE FROM sessions WHERE user_id = ?').run(userId);
    
    // Delete user
    this.db.db.prepare('DELETE FROM users WHERE id = ?').run(userId);

    this.logAudit(userId, 'user_deleted', 'auth', null, null, true);
  }

  cleanupExpiredSessions() {
    const deleted = this.db.db.prepare(`
      DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP
    `).run();

    if (deleted.changes > 0) {
      console.log(`Cleaned up ${deleted.changes} expired sessions`);
    }
  }

  logAudit(userId, action, resource, ipAddress, userAgent, success, details = null) {
    this.db.db.prepare(`
      INSERT INTO audit_logs (user_id, action, resource, ip_address, user_agent, success, details)
      VALUES (@user_id, @action, @resource, @ip_address, @user_agent, @success, @details)
    `).run({
      user_id: userId,
      action: action,
      resource: resource,
      ip_address: ipAddress,
      user_agent: userAgent,
      success: success ? 1 : 0,
      details: details
    });
  }

  getAuditLogs(limit = 100) {
    return this.db.db.prepare(`
      SELECT al.*, u.username
      FROM audit_logs al
      LEFT JOIN users u ON al.user_id = u.id
      ORDER BY al.timestamp DESC
      LIMIT ?
    `).all(limit);
  }
}