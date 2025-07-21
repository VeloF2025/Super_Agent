# Security Migration Guide - Super Agent Dashboard

This guide walks you through migrating from the unsecured dashboard to the secure implementation with authentication and HTTPS.

## Quick Start

### 1. Install Dependencies
```bash
cd agent-dashboard
npm install
```

### 2. Set Up Environment
```bash
# Copy the example environment file
cp ../.env.example ../.env

# The system will generate secure keys automatically on first run
```

### 3. Start Secure Server
```bash
# Development mode
npm run dev:secure

# Production mode
npm run start:secure
```

### 4. Initial Login
Check `ADMIN_CREDENTIALS.txt` for the auto-generated admin password:
- Username: `admin`
- Password: (see ADMIN_CREDENTIALS.txt)
- Login URL: http://localhost:3010/login

⚠️ **IMPORTANT**: Change the admin password immediately after first login!

## What's New

### Security Features Added
✅ **JWT Authentication** - All API endpoints now require authentication
✅ **Secure Password Storage** - Bcrypt hashing with salt rounds
✅ **Rate Limiting** - Protection against brute force attacks
✅ **Security Headers** - CSP, HSTS, XSS protection, etc.
✅ **Input Validation** - All inputs sanitized and validated
✅ **Audit Logging** - Track all authentication events
✅ **HTTPS Support** - SSL/TLS encryption for production

### API Changes

#### Authentication Required
All API endpoints (except `/api/health`) now require a Bearer token:
```javascript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN'
}
```

#### Login Flow
```javascript
// 1. Login to get token
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'your-password'
  })
});

const { token } = await response.json();

// 2. Use token for API calls
const agents = await fetch('/api/agents', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

#### WebSocket Authentication
WebSocket connections now require token in URL:
```javascript
const ws = new WebSocket(`ws://localhost:3010?token=${token}`);
```

## Migration Steps

### 1. Update Client Code

#### Add Login Component
```javascript
// client/src/components/Login.jsx
import { useState } from 'react';

export default function Login({ onLogin }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.token);
        onLogin(data.token, data.user);
      } else {
        const error = await res.json();
        setError(error.message || 'Login failed');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Login form UI */}
    </form>
  );
}
```

#### Update API Service
```javascript
// client/src/services/api.js
class APIService {
  constructor() {
    this.baseURL = '/api';
  }

  getHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    };
  }

  async fetch(endpoint, options = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers
      }
    });

    if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
      throw new Error('Authentication required');
    }

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}
```

#### Update WebSocket Connection
```javascript
// client/src/services/websocket.js
class WebSocketService {
  connect() {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token');
    }

    this.ws = new WebSocket(`ws://localhost:3010?token=${token}`);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onerror = (error) => {
      if (error.type === 'error') {
        // Authentication failed
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    };
  }
}
```

### 2. Production Setup

#### Generate SSL Certificates
For production, obtain proper SSL certificates. For testing:
```bash
# Generate self-signed certificate (development only!)
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt -days 365 -nodes
```

#### Update Environment
```bash
# .env for production
NODE_ENV=production
ENABLE_HTTPS=true
SSL_CERT_PATH=./certs/server.crt
SSL_KEY_PATH=./certs/server.key
```

### 3. User Management

#### Create New Users (Admin Only)
```javascript
await fetch('/api/auth/admin/users', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'newuser',
    password: 'secure-password',
    role: 'viewer' // or 'admin'
  })
});
```

#### Change Password
```javascript
await fetch('/api/auth/change-password', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    currentPassword: 'old-password',
    newPassword: 'new-secure-password'
  })
});
```

## Testing

### Run Security Audit
```bash
npm run audit:security
```

### Test Authentication
```bash
# Test login
curl -X POST http://localhost:3010/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# Test authenticated endpoint
curl http://localhost:3010/api/agents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Rate Limiting
```bash
# Try multiple failed logins
for i in {1..10}; do
  curl -X POST http://localhost:3010/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}'
done
# Should get rate limited after 5 attempts
```

## Troubleshooting

### Common Issues

1. **"JWT_SECRET not configured"**
   - Ensure `.env` file exists
   - Run the server once to auto-generate secrets

2. **"Authentication required" errors**
   - Check token is included in Authorization header
   - Verify token hasn't expired (24h lifetime)

3. **WebSocket connection fails**
   - Ensure token is passed in WebSocket URL
   - Check browser console for specific errors

4. **CORS errors**
   - Update `DEVELOPMENT_CORS_ORIGIN` in `.env`
   - Ensure credentials are included in requests

### Debug Mode
Enable debug logging:
```bash
DEBUG_MODE=true npm run dev:secure
```

## Security Best Practices

1. **Change Default Password** - Always change the admin password immediately
2. **Use HTTPS in Production** - Never run without SSL in production
3. **Regular Updates** - Keep dependencies updated for security patches
4. **Monitor Audit Logs** - Review `/api/auth/admin/audit-logs` regularly
5. **Backup Credentials** - Store admin credentials securely
6. **Rate Limiting** - Adjust limits based on your usage patterns
7. **Session Management** - Tokens expire after 24h by default

## Rollback Plan

If you need to temporarily rollback to the unsecured version:
```bash
# Use original server file
npm run start

# Or rename files
mv server/index.js server/index-original.js
mv server/index-secure.js server/index.js
```

⚠️ **WARNING**: Only rollback in emergencies. The unsecured version should never be used in production!

## Next Steps

1. ✅ Complete client-side authentication UI
2. ✅ Test all API endpoints with authentication
3. ✅ Set up proper SSL certificates
4. ✅ Configure production environment
5. ✅ Train users on new login process
6. ✅ Schedule regular security audits

For questions or issues, check the security audit report or contact the development team.