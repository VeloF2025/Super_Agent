import https from 'https';
import fs from 'fs';
import path from 'path';

export class SecureServerConfig {
  constructor() {
    this.sslOptions = this.loadSSLCertificates();
  }

  loadSSLCertificates() {
    const certPath = process.env.SSL_CERT_PATH || './certs/server.crt';
    const keyPath = process.env.SSL_KEY_PATH || './certs/server.key';
    
    if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
      return {
        cert: fs.readFileSync(certPath),
        key: fs.readFileSync(keyPath),
        // Enable secure protocols only
        secureProtocol: 'TLSv1_2_method',
        ciphers: [
          'ECDHE-RSA-AES128-GCM-SHA256',
          'ECDHE-RSA-AES256-GCM-SHA384',
          'ECDHE-RSA-AES128-SHA256',
          'ECDHE-RSA-AES256-SHA384'
        ].join(':'),
        honorCipherOrder: true
      };
    }
    
    console.warn('SSL certificates not found. Generating self-signed certificates...');
    return this.generateSelfSignedCert();
  }

  generateSelfSignedCert() {
    // In production, use proper SSL certificates
    // This is for development only
    const { execSync } = require('child_process');
    
    const certDir = path.join(process.cwd(), 'certs');
    if (!fs.existsSync(certDir)) {
      fs.mkdirSync(certDir, { recursive: true });
    }
    
    try {
      execSync(`openssl req -x509 -newkey rsa:4096 -keyout ${certDir}/server.key -out ${certDir}/server.crt -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"`);
      
      return {
        cert: fs.readFileSync(path.join(certDir, 'server.crt')),
        key: fs.readFileSync(path.join(certDir, 'server.key'))
      };
    } catch (error) {
      console.error('Failed to generate SSL certificates:', error.message);
      return null;
    }
  }

  createSecureServer(app) {
    if (this.sslOptions) {
      return https.createServer(this.sslOptions, app);
    } else {
      console.warn('Running without HTTPS - NOT RECOMMENDED FOR PRODUCTION');
      return require('http').createServer(app);
    }
  }

  // Security headers middleware
  securityHeadersMiddleware(req, res, next) {
    // Strict Transport Security
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
    
    // Content Security Policy
    res.setHeader('Content-Security-Policy', [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "connect-src 'self' ws: wss:",
      "font-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'"
    ].join('; '));
    
    // Other security headers
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
    
    next();
  }
}
