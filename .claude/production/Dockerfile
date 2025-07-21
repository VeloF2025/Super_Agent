# Multi-stage build for production deployment
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY agent-dashboard/package*.json ./agent-dashboard/
COPY agent-dashboard/client/package*.json ./agent-dashboard/client/

# Install dependencies
RUN cd agent-dashboard && npm ci --only=production
RUN cd agent-dashboard/client && npm ci

# Copy source code
COPY agent-dashboard/ ./agent-dashboard/
COPY shared/ ./shared/
COPY .claude/ ./.claude/

# Build frontend
RUN cd agent-dashboard/client && npm run build

# Production stage
FROM node:18-alpine AS production

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    sqlite \
    procps \
    && ln -sf python3 /usr/bin/python

# Install PM2 globally
RUN npm install -g pm2

# Create app user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S superagent -u 1001

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p data logs shared .claude && \
    chown -R superagent:nodejs /app

# Copy built application
COPY --from=builder --chown=superagent:nodejs /app/agent-dashboard ./agent-dashboard
COPY --from=builder --chown=superagent:nodejs /app/shared ./shared
COPY --from=builder --chown=superagent:nodejs /app/.claude ./.claude

# Copy production configuration
COPY --chown=superagent:nodejs .claude/production/pm2.config.js ./pm2.config.js

# Install Python dependencies for monitoring
RUN pip3 install --no-cache-dir requests psutil

# Switch to non-root user
USER superagent

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3001
ENV DATABASE_PATH=/app/data/dashboard.db

# Start with PM2
CMD ["pm2-runtime", "start", "pm2.config.js"]