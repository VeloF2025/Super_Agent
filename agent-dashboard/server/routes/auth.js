/**
 * Authentication Routes
 * Handles login, logout, and user management endpoints
 */

import express from 'express';

export default function authRoutes(authService, securityMiddleware) {
  const router = express.Router();

  // Login endpoint
  router.post('/login', 
    securityMiddleware.createAuthRateLimiter(),
    securityMiddleware.validateLogin,
    securityMiddleware.sanitizeInput,
    async (req, res) => {
      try {
        const { username, password } = req.body;
        const ipAddress = req.ip || req.connection.remoteAddress;
        const userAgent = req.headers['user-agent'];

        const result = await authService.login(username, password, ipAddress, userAgent);
        
        res.json({
          success: true,
          token: result.token,
          user: result.user,
          expiresAt: result.expiresAt
        });
      } catch (error) {
        res.status(401).json({
          success: false,
          error: error.message
        });
      }
    }
  );

  // Logout endpoint
  router.post('/logout',
    securityMiddleware.authenticate,
    async (req, res) => {
      try {
        const token = req.headers.authorization?.split(' ')[1];
        const ipAddress = req.ip || req.connection.remoteAddress;
        const userAgent = req.headers['user-agent'];

        await authService.logout(token, ipAddress, userAgent);
        
        res.json({
          success: true,
          message: 'Logged out successfully'
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    }
  );

  // Change password endpoint
  router.post('/change-password',
    securityMiddleware.authenticate,
    async (req, res) => {
      try {
        const { currentPassword, newPassword } = req.body;
        const userId = req.user.userId;

        // Validate new password
        if (!newPassword || newPassword.length < 8) {
          return res.status(400).json({
            success: false,
            error: 'New password must be at least 8 characters'
          });
        }

        await authService.changePassword(userId, currentPassword, newPassword);
        
        res.json({
          success: true,
          message: 'Password changed successfully. Please login again.'
        });
      } catch (error) {
        res.status(400).json({
          success: false,
          error: error.message
        });
      }
    }
  );

  // Get current user info
  router.get('/me',
    securityMiddleware.authenticate,
    async (req, res) => {
      res.json({
        success: true,
        user: {
          id: req.user.userId,
          username: req.user.username,
          role: req.user.role
        }
      });
    }
  );

  // Admin routes
  router.use('/admin', securityMiddleware.authenticate, (req, res, next) => {
    if (req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        error: 'Admin access required'
      });
    }
    next();
  });

  // List users (admin only)
  router.get('/admin/users', async (req, res) => {
    try {
      const users = authService.getUsers();
      res.json({
        success: true,
        users
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });

  // Create user (admin only)
  router.post('/admin/users',
    securityMiddleware.sanitizeInput,
    async (req, res) => {
      try {
        const { username, password, role } = req.body;

        // Validate input
        if (!username || !password) {
          return res.status(400).json({
            success: false,
            error: 'Username and password are required'
          });
        }

        if (password.length < 8) {
          return res.status(400).json({
            success: false,
            error: 'Password must be at least 8 characters'
          });
        }

        if (role && !['admin', 'viewer'].includes(role)) {
          return res.status(400).json({
            success: false,
            error: 'Invalid role. Must be "admin" or "viewer"'
          });
        }

        const user = await authService.createUser(username, password, role);
        
        res.json({
          success: true,
          user
        });
      } catch (error) {
        res.status(400).json({
          success: false,
          error: error.message
        });
      }
    }
  );

  // Delete user (admin only)
  router.delete('/admin/users/:userId', async (req, res) => {
    try {
      const { userId } = req.params;
      
      if (userId === req.user.userId) {
        return res.status(400).json({
          success: false,
          error: 'Cannot delete your own account'
        });
      }

      await authService.deleteUser(userId);
      
      res.json({
        success: true,
        message: 'User deleted successfully'
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error.message
      });
    }
  });

  // Get audit logs (admin only)
  router.get('/admin/audit-logs', async (req, res) => {
    try {
      const limit = parseInt(req.query.limit) || 100;
      const logs = authService.getAuditLogs(limit);
      
      res.json({
        success: true,
        logs
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });

  return router;
}