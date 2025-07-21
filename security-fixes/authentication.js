import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';

export class AuthService {
  constructor() {
    this.jwtSecret = process.env.JWT_SECRET || 'fallback-secret-change-in-production';
    this.saltRounds = 12;
  }

  generateToken(user) {
    return jwt.sign(
      { 
        userId: user.id, 
        username: user.username,
        role: user.role 
      },
      this.jwtSecret,
      { 
        expiresIn: '24h',
        issuer: 'super-agent-system'
      }
    );
  }

  verifyToken(token) {
    try {
      return jwt.verify(token, this.jwtSecret);
    } catch (error) {
      throw new Error('Invalid token');
    }
  }

  async hashPassword(password) {
    return await bcrypt.hash(password, this.saltRounds);
  }

  async verifyPassword(password, hash) {
    return await bcrypt.compare(password, hash);
  }
}

// Authentication middleware
export const authMiddleware = (req, res, next) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      error: 'Authentication required',
      message: 'Please provide a valid Bearer token'
    });
  }
  
  const token = authHeader.split(' ')[1];
  
  try {
    const authService = new AuthService();
    const decoded = authService.verifyToken(token);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(403).json({ 
      error: 'Invalid token',
      message: 'Token verification failed'
    });
  }
};

// Rate limiting middleware
export const rateLimitMiddleware = (windowMs = 15 * 60 * 1000, max = 100) => {
  const requests = new Map();
  
  return (req, res, next) => {
    const ip = req.ip || req.connection.remoteAddress;
    const now = Date.now();
    const window = now - windowMs;
    
    // Clean old entries
    for (const [key, value] of requests.entries()) {
      if (value.timestamp < window) {
        requests.delete(key);
      }
    }
    
    const userRequests = requests.get(ip) || { count: 0, timestamp: now };
    
    if (userRequests.timestamp < window) {
      userRequests.count = 1;
      userRequests.timestamp = now;
    } else {
      userRequests.count++;
    }
    
    requests.set(ip, userRequests);
    
    if (userRequests.count > max) {
      return res.status(429).json({
        error: 'Too many requests',
        message: 'Rate limit exceeded. Please try again later.'
      });
    }
    
    next();
  };
};
