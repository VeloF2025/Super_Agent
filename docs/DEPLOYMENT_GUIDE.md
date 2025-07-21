# Deployment Guide - Jarvis Super Agent System

This guide covers deploying the Jarvis Super Agent System to production environments.

## 🎯 Pre-Deployment Requirements

### System Requirements
- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 11+
- **Python**: 3.8 or higher
- **Node.js**: 18.0 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB available space minimum
- **Network**: Stable internet connection for updates

### Dependencies
- **Git** for version control
- **Python packages**: `schedule`, `watchdog`, `sqlite3`
- **Node.js packages**: See `agent-dashboard/package.json`

## 🔄 Automated Pre-Deployment Process

### 1. Run Pre-Deployment Check
```bash
# Full deployment readiness check
python pre-deployment-docs.py

# Quick documentation update only
python pre-deployment-docs.py docs-only
```

### 2. Review Generated Reports
The system generates several reports:
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- `PRE_DEPLOYMENT_REPORT.md` - Comprehensive status report
- `DOC_UPDATE_REPORT.md` - Documentation changes summary

### 3. Address Any Issues
If the pre-deployment check fails:
1. Review the generated reports
2. Fix identified issues
3. Re-run the pre-deployment check
4. Repeat until all checks pass

## 🚀 Deployment Methods

### Method 1: Local Production Setup

```bash
# 1. Set up the environment
git clone <your-repo-url>
cd jarvis-super-agent

# 2. Install dependencies
pip install -r requirements.txt
cd agent-dashboard && npm install && cd ..

# 3. Run pre-deployment check
python pre-deployment-docs.py

# 4. Start the system
daily-ops\start-daily-ops.bat
```

### Method 2: Git-Based Deployment

```bash
# 1. Prepare for deployment (automatically runs doc updates)
git add .
git commit -m "Prepare for deployment"

# 2. Push to deployment branch (triggers pre-push hook)
git push origin main

# 3. Deploy to production server
# (Your deployment script here)
```

### Method 3: Container Deployment

```dockerfile
# Dockerfile (create if needed)
FROM node:18-alpine AS dashboard-build
WORKDIR /app/dashboard
COPY agent-dashboard/package*.json ./
RUN npm ci --only=production
COPY agent-dashboard/ ./
RUN npm run build

FROM python:3.9-slim AS runtime
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=dashboard-build /app/dashboard/dist ./agent-dashboard/dist
EXPOSE 3000 3001
CMD ["python", "daily-ops/jarvis-scheduler.py", "auto"]
```

## 📋 Deployment Checklist

Use the auto-generated `DEPLOYMENT_CHECKLIST.md` or follow these steps:

### Pre-Deployment
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Git repository clean
- [ ] Dependencies satisfied
- [ ] System health check passed
- [ ] Backup procedures verified

### During Deployment
- [ ] Stop existing services gracefully
- [ ] Deploy new version
- [ ] Update configuration files
- [ ] Restart services
- [ ] Verify system startup

### Post-Deployment
- [ ] Dashboard accessible
- [ ] All agents responding
- [ ] Communication system working
- [ ] Daily operations scheduled
- [ ] Monitoring alerts active
- [ ] Backup systems operational

## 🔧 Configuration for Production

### Environment Variables
```bash
# Set production environment
export JARVIS_ENV=production
export JARVIS_LOG_LEVEL=info
export JARVIS_DATA_DIR=/var/lib/jarvis
export JARVIS_BACKUP_DIR=/var/backups/jarvis
```

### Production Configuration
```json
{
  "environment": "production",
  "log_level": "info",
  "auto_backup": true,
  "backup_retention_days": 30,
  "monitoring_enabled": true,
  "security": {
    "enable_audit_log": true,
    "encrypt_backups": true,
    "access_control": true
  }
}
```

### Service Configuration

#### Systemd Service (Linux)
```ini
[Unit]
Description=Jarvis Super Agent System
After=network.target

[Service]
Type=forking
User=jarvis
WorkingDirectory=/opt/jarvis-super-agent
ExecStart=/opt/jarvis-super-agent/start-production.sh
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Windows Service
```powershell
# Install as Windows service
sc create "JarvisSystem" binpath="C:\Jarvis\AI Workspace\Super Agent\start-service.bat"
sc config "JarvisSystem" start=auto
sc start "JarvisSystem"
```

## 📊 Monitoring and Maintenance

### Health Monitoring
- Dashboard health check: `http://localhost:3000/health`
- API health check: `http://localhost:3001/api/health`
- System status: `python daily-ops/jarvis-scheduler.py status`

### Log Management
```bash
# View system logs
tail -f logs/system/jarvis-*.log

# View agent logs
tail -f logs/agent-*/general_*.log

# Check error logs
grep -i error logs/**/*.log
```

### Backup Procedures
```bash
# Manual backup
python housekeeper/backup-system.py --full

# Verify backup integrity
python housekeeper/verify-backup.py --latest

# Restore from backup
python housekeeper/restore-backup.py --date=2025-01-21
```

## 🔒 Security Considerations

### Access Control
- Restrict dashboard access to authorized users
- Use HTTPS in production
- Secure API endpoints with authentication
- Regular security audits

### Data Protection
- Encrypt sensitive data at rest
- Secure backup storage
- Regular credential rotation
- Audit trail maintenance

### Network Security
- Firewall configuration
- VPN access for remote management
- Regular security updates
- Intrusion detection

## 🚨 Troubleshooting

### Common Issues

#### Dashboard Not Loading
```bash
# Check if services are running
netstat -tulpn | grep :3000
netstat -tulpn | grep :3001

# Check logs
tail -f agent-dashboard/logs/error.log

# Restart dashboard
cd agent-dashboard && npm restart
```

#### Agents Not Responding
```bash
# Check agent status
ls -la ../agents/*/DAILY_CONTEXT_*

# Check communication queue
ls -la communication/queue/

# Restart agents
python daily-ops/morning-standup.py
```

#### Performance Issues
```bash
# Check system resources
top
df -h
free -m

# Check logs for errors
grep -i "error\|exception" logs/**/*.log

# Run system health check
python pre-deployment-docs.py
```

### Recovery Procedures

#### Complete System Recovery
1. Stop all services
2. Restore from latest backup
3. Verify data integrity
4. Restart services
5. Run health checks

#### Partial Recovery
1. Identify affected components
2. Stop affected services
3. Restore specific data
4. Restart affected services
5. Verify functionality

## 📈 Performance Optimization

### Production Tuning
- Increase agent memory limits
- Optimize database queries
- Enable caching
- Configure load balancing

### Monitoring Metrics
- Response times
- Resource utilization
- Error rates
- Throughput

### Scaling Considerations
- Horizontal agent scaling
- Database sharding
- Load balancing
- Caching strategies

## 📞 Support and Maintenance

### Regular Maintenance
- Weekly system health checks
- Monthly performance reviews
- Quarterly security audits
- Annual disaster recovery tests

### Emergency Contacts
- System Administrator
- Development Team
- Infrastructure Team
- Security Team

### Documentation Updates
The documentation is automatically updated before each deployment using the automated documentation system. Manual updates should be made through the standard development process.

---

**Note**: This deployment guide is automatically maintained by the Jarvis documentation system. For the most current version, always refer to the version in the repository.