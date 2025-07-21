# Super Agent Dashboard - Production Deployment

This directory contains production-ready deployment configurations for the Super Agent Dashboard system.

## Deployment Options

### 1. Local Development/Testing
```powershell
# Basic local deployment
.\deploy.ps1 -Mode local

# With frontend build and monitoring
.\deploy.ps1 -Mode local -Build -Monitor
```

### 2. PM2 Process Manager (Recommended for Windows)
```powershell
# Install PM2 globally
npm install -g pm2

# Deploy with PM2
.\deploy.ps1 -Mode pm2 -Build

# Monitor processes
pm2 monit
pm2 logs
```

### 3. Docker Containers
```powershell
# Deploy with Docker Compose
.\deploy.ps1 -Mode docker -Build

# Monitor containers
docker-compose ps
docker-compose logs -f dashboard
```

### 4. Windows Service
```powershell
# Install as Windows Service (run as Administrator)
.\windows-service.ps1 -Action install

# Manage service
.\windows-service.ps1 -Action start
.\windows-service.ps1 -Action status
```

## Configuration Files

### PM2 Configuration (`pm2.config.js`)
- **Dashboard Server**: Main Node.js application with auto-restart
- **Dashboard Monitor**: Python script for health monitoring
- **Agent Heartbeats**: Keeps agents showing as online
- **Logging**: Centralized logs in `./logs/` directory
- **Resource Limits**: Memory and CPU constraints

### Docker Configuration (`docker-compose.yml`)
- **Multi-container setup**: Dashboard, Redis, Nginx, monitoring
- **Reverse proxy**: Nginx for load balancing and SSL termination
- **Health checks**: Automatic container health monitoring
- **Volume mounts**: Persistent data and shared files
- **Resource limits**: CPU and memory constraints per container

### Nginx Configuration (`nginx.conf`)
- **Reverse proxy**: Routes traffic to Node.js backend
- **WebSocket support**: Real-time dashboard updates
- **Static file serving**: Optimized frontend delivery
- **Security headers**: XSS protection, CORS, CSP
- **Rate limiting**: API and static file protection
- **Gzip compression**: Reduced bandwidth usage

## Security Features

### Application Security
- **Input validation**: All API endpoints validate input
- **Error handling**: Graceful error recovery without exposing internals
- **Resource limits**: Memory and CPU quotas prevent resource exhaustion
- **Request timeouts**: Prevents hanging connections

### Network Security
- **CORS configuration**: Controlled cross-origin requests
- **Security headers**: XSS, clickjacking, and content-type protection
- **Rate limiting**: API abuse prevention
- **WebSocket security**: Secure real-time connections

### System Security
- **Non-root execution**: Containers run as unprivileged user
- **File permissions**: Restricted read/write access
- **Process isolation**: Containerized or service-based isolation
- **Log security**: Structured logging without sensitive data

## Monitoring and Logging

### Health Checks
- **HTTP endpoint**: `/health` returns system status
- **Dashboard API**: `/api/dashboard` validates core functionality
- **Process monitoring**: PM2/Docker health checks
- **Automatic restart**: Failed processes restart automatically

### Logging Strategy
- **Structured logs**: JSON format for easy parsing
- **Log rotation**: Prevents disk space issues
- **Multiple levels**: Error, warn, info, debug
- **Centralized**: All logs in consistent format

### Metrics Collection
- **System metrics**: CPU, memory, disk usage
- **Application metrics**: Response times, error rates
- **Agent metrics**: Online status, activity counts
- **Performance metrics**: Throughput, latency

## Backup and Recovery

### Data Backup
```powershell
# Backup dashboard data
robocopy "C:\Jarvis\AI Workspace\Super Agent\data" "C:\Backup\super-agent\data" /E /R:3 /W:5

# Backup configuration
robocopy "C:\Jarvis\AI Workspace\Super Agent\.claude" "C:\Backup\super-agent\config" /E /R:3 /W:5
```

### Recovery Procedures
1. **Database recovery**: SQLite database in `./data/dashboard.db`
2. **Configuration restore**: Copy `.claude/` directory
3. **Agent state**: Heartbeat files auto-regenerate
4. **Shared data**: Message queues and communication logs

## Performance Optimization

### Frontend Optimization
- **Code splitting**: Lazy-loaded components
- **Asset optimization**: Minified CSS/JS, compressed images
- **Caching**: Browser caching for static assets
- **CDN support**: Ready for content delivery networks

### Backend Optimization
- **Connection pooling**: Efficient database connections
- **Async processing**: Non-blocking I/O operations
- **Memory management**: Garbage collection optimization
- **Caching**: Redis for session and data caching

### Infrastructure Optimization
- **Load balancing**: Nginx upstream configuration
- **Process clustering**: Multiple Node.js instances
- **Resource limits**: Prevents system overload
- **Auto-scaling**: Container orchestration ready

## Troubleshooting

### Common Issues

#### Port Already in Use (3001)
```powershell
# Find process using port
netstat -ano | findstr :3001

# Kill process
taskkill /F /PID <process_id>
```

#### Service Won't Start
```powershell
# Check logs
Get-EventLog -LogName Application -Source "SuperAgentDashboard" -Newest 10

# Manual test
cd "C:\Jarvis\AI Workspace\Super Agent\agent-dashboard"
node server/index-robust.js
```

#### Dashboard Not Loading
1. Check health endpoint: `http://localhost:3001/health`
2. Verify API endpoint: `http://localhost:3001/api/dashboard`
3. Check browser console for errors
4. Review server logs

#### Agent Status Issues
1. Verify heartbeat files in `./shared/heartbeats/`
2. Check agent-heartbeat.py process
3. Restart heartbeat service
4. Validate agent configuration

### Log Locations
- **PM2 logs**: `./logs/dashboard-*.log`
- **Windows Service**: Event Viewer → Application
- **Docker logs**: `docker-compose logs dashboard`
- **Nginx logs**: `/var/log/nginx/` (in container)

### Performance Monitoring
```powershell
# PM2 monitoring
pm2 monit

# Docker monitoring
docker stats

# Windows performance
Get-Counter "\Process(node)\% Processor Time"
Get-Counter "\Process(node)\Working Set"
```

## Production Checklist

### Pre-deployment
- [ ] Build frontend with `npm run build`
- [ ] Test health endpoints
- [ ] Verify agent heartbeats
- [ ] Check log rotation
- [ ] Validate security headers
- [ ] Test backup procedures

### Post-deployment
- [ ] Verify all services running
- [ ] Test dashboard functionality
- [ ] Confirm agent status display
- [ ] Check real-time updates
- [ ] Validate monitoring alerts
- [ ] Document any customizations

### Maintenance
- [ ] Regular log cleanup
- [ ] Database optimization
- [ ] Security updates
- [ ] Performance monitoring
- [ ] Backup verification
- [ ] Capacity planning

## Support

For issues with production deployment:
1. Check this README for common solutions
2. Review application logs
3. Test individual components
4. Check system resources
5. Validate network connectivity

The dashboard is designed for 24/7 operation with automatic recovery from common failure scenarios.