/**
 * Secure Environment Configuration Manager
 * Handles all environment variables with validation and security
 */

import dotenv from 'dotenv';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';

// Load environment variables
dotenv.config();

class EnvironmentConfig {
  constructor() {
    this.requiredVars = [
      'JWT_SECRET',
      'COOKIE_ENCRYPTION_KEY'
    ];
    
    this.developmentVars = [
      'PERPLEXITY_API_KEY',
      'ANTHROPIC_API_KEY'
    ];
    
    this.validateEnvironment();
  }

  validateEnvironment() {
    const missing = [];
    const weak = [];

    // Check required variables
    for (const varName of this.requiredVars) {
      const value = process.env[varName];
      
      if (!value) {
        missing.push(varName);
      } else if (value.length < 32) {
        weak.push(`${varName} (minimum 32 characters required)`);
      }
    }

    // In production, also require API keys
    if (this.isProduction()) {
      for (const varName of this.developmentVars) {
        if (!process.env[varName]) {
          missing.push(varName);
        }
      }
    }

    if (missing.length > 0) {
      console.error('❌ Missing required environment variables:');
      missing.forEach(varName => console.error(`   - ${varName}`));
      console.error('\nCopy .env.example to .env and fill in the values.');
      process.exit(1);
    }

    if (weak.length > 0) {
      console.warn('⚠️  Weak security configuration:');
      weak.forEach(issue => console.warn(`   - ${issue}`));
    }

    // Generate missing secrets if in development
    if (!this.isProduction()) {
      this.generateMissingSecrets();
    }
  }

  generateMissingSecrets() {
    const envPath = path.join(process.cwd(), '.env');
    let envContent = '';

    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }

    let updated = false;

    // Generate JWT secret if missing
    if (!process.env.JWT_SECRET || process.env.JWT_SECRET === 'your-super-secret-jwt-signing-key-here-minimum-32-chars') {
      const jwtSecret = crypto.randomBytes(64).toString('hex');
      envContent = this.updateEnvVariable(envContent, 'JWT_SECRET', jwtSecret);
      process.env.JWT_SECRET = jwtSecret;
      updated = true;
      console.log('✅ Generated new JWT_SECRET');
    }

    // Generate cookie encryption key if missing
    if (!process.env.COOKIE_ENCRYPTION_KEY || process.env.COOKIE_ENCRYPTION_KEY === 'your-cookie-encryption-key-32-chars-min') {
      const cookieKey = crypto.randomBytes(32).toString('hex');
      envContent = this.updateEnvVariable(envContent, 'COOKIE_ENCRYPTION_KEY', cookieKey);
      process.env.COOKIE_ENCRYPTION_KEY = cookieKey;
      updated = true;
      console.log('✅ Generated new COOKIE_ENCRYPTION_KEY');
    }

    // Generate session secret if missing
    if (!process.env.SESSION_SECRET || process.env.SESSION_SECRET === 'your-session-secret-key-here') {
      const sessionSecret = crypto.randomBytes(32).toString('hex');
      envContent = this.updateEnvVariable(envContent, 'SESSION_SECRET', sessionSecret);
      process.env.SESSION_SECRET = sessionSecret;
      updated = true;
      console.log('✅ Generated new SESSION_SECRET');
    }

    if (updated) {
      fs.writeFileSync(envPath, envContent);
      console.log('💾 Updated .env file with generated secrets');
    }
  }

  updateEnvVariable(content, varName, value) {
    const regex = new RegExp(`^${varName}=.*$`, 'm');
    const newLine = `${varName}="${value}"`;
    
    if (regex.test(content)) {
      return content.replace(regex, newLine);
    } else {
      return content + (content.endsWith('\n') ? '' : '\n') + newLine + '\n';
    }
  }

  // Configuration getters
  get database() {
    return {
      url: process.env.DATABASE_URL || 'file:./data/dashboard.db',
      encryptionKey: process.env.DATABASE_ENCRYPTION_KEY
    };
  }

  get server() {
    return {
      port: parseInt(process.env.PORT) || 3010,
      host: process.env.HOST || 'localhost',
      enableHttps: process.env.ENABLE_HTTPS === 'true'
    };
  }

  get security() {
    return {
      jwtSecret: process.env.JWT_SECRET,
      cookieEncryptionKey: process.env.COOKIE_ENCRYPTION_KEY,
      sessionSecret: process.env.SESSION_SECRET,
      enableSecurityHeaders: process.env.ENABLE_SECURITY_HEADERS !== 'false',
      cspReportOnly: process.env.CSP_REPORT_ONLY === 'true'
    };
  }

  get ssl() {
    return {
      certPath: process.env.SSL_CERT_PATH || './certs/server.crt',
      keyPath: process.env.SSL_KEY_PATH || './certs/server.key'
    };
  }

  get rateLimiting() {
    return {
      windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
      maxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100
    };
  }

  get logging() {
    return {
      level: process.env.LOG_LEVEL || 'info',
      enableAuditLogs: process.env.ENABLE_AUDIT_LOGS === 'true',
      sentryDsn: process.env.SENTRY_DSN
    };
  }

  get apiKeys() {
    return {
      perplexity: process.env.PERPLEXITY_API_KEY,
      anthropic: process.env.ANTHROPIC_API_KEY
    };
  }

  get cors() {
    return {
      origin: this.isDevelopment() 
        ? process.env.DEVELOPMENT_CORS_ORIGIN || 'http://localhost:3000'
        : false,
      credentials: true
    };
  }

  // Environment helpers
  isProduction() {
    return process.env.NODE_ENV === 'production';
  }

  isDevelopment() {
    return process.env.NODE_ENV !== 'production';
  }

  isDebugMode() {
    return process.env.DEBUG_MODE === 'true';
  }

  // Security validation
  validateSecrets() {
    const secrets = [
      this.security.jwtSecret,
      this.security.cookieEncryptionKey,
      this.security.sessionSecret
    ];

    for (const secret of secrets) {
      if (!secret || secret.length < 32) {
        throw new Error('Security configuration validation failed - secrets too weak');
      }
    }

    return true;
  }

  // Mask sensitive values for logging
  getMaskedConfig() {
    const config = {
      database: {
        url: this.database.url,
        encryptionKey: this.database.encryptionKey ? '***masked***' : 'not set'
      },
      server: this.server,
      apiKeys: {
        perplexity: this.apiKeys.perplexity ? '***masked***' : 'not set',
        anthropic: this.apiKeys.anthropic ? '***masked***' : 'not set'
      },
      security: {
        jwtSecret: this.security.jwtSecret ? '***masked***' : 'not set',
        cookieEncryptionKey: this.security.cookieEncryptionKey ? '***masked***' : 'not set',
        sessionSecret: this.security.sessionSecret ? '***masked***' : 'not set',
        enableSecurityHeaders: this.security.enableSecurityHeaders,
        cspReportOnly: this.security.cspReportOnly
      },
      logging: this.logging,
      rateLimiting: this.rateLimiting
    };

    return config;
  }
}

// Create singleton instance
const config = new EnvironmentConfig();

export default config;

// Export specific configurations for easy access
export const {
  database: databaseConfig,
  server: serverConfig,
  security: securityConfig,
  ssl: sslConfig,
  rateLimiting: rateLimitConfig,
  logging: loggingConfig,
  apiKeys: apiKeysConfig,
  cors: corsConfig
} = config;