# Agritrust Enterprise Deployment Guide

## Overview
Complete enterprise-grade deployment guide for Agritrust platform with monitoring, security, backup, and disaster recovery.

## Prerequisites

### Infrastructure Requirements
- **Server**: 4+ CPU cores, 16GB RAM, 100GB SSD
- **Operating System**: Ubuntu 22.04 LTS or equivalent
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Domain**: agrictrust.com with subdomains configured
- **SSL Certificates**: Valid SSL certificates for all domains

### Software Requirements
- Docker & Docker Compose
- Git
- OpenSSL (for SSL certificate generation)
- Text editor (vim/nano)

## Pre-Deployment Checklist

- [ ] Domain DNS configured (A records for all subdomains)
- [ ] SSL certificates obtained and placed in `nginx/ssl/`
- [ ] Production environment file configured (`.env.production`)
- [ ] Database backup strategy defined
- [ ] Monitoring stack configured (Prometheus, Grafana)
- [ ] CI/CD pipeline configured (GitHub Actions)
- [ ] Security credentials set (SECRET_KEY, database passwords)
- [ ] Firewall rules configured (ports 80, 443, 22)
- [ ] SSH keys configured for deployment
- [ ] Monitoring alerts configured (Slack/email)

## Deployment Steps

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/agritrust
sudo chown $USER:$USER /opt/agritrust
cd /opt/agritrust

# Clone repository
git clone <repository-url> .
```

### Step 2: SSL Certificate Setup

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Option A: Use Let's Encrypt (recommended)
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d agrictrust.com -d www.agrictrust.com -d admin.agrictrust.com -d agent.agrictrust.com
sudo cp /etc/letsencrypt/live/agrictrust.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/agrictrust.com/privkey.pem nginx/ssl/

# Option B: Use existing certificates
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/

# Set permissions
chmod 600 nginx/ssl/*.pem
```

### Step 3: Environment Configuration

```bash
# Copy environment template
cp .env.production.example .env.production

# Edit with production values
nano .env.production

# Required changes:
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - POSTGRES_PASSWORD (generate strong password)
# - REDIS_PASSWORD (generate strong password)
# - CORS_ORIGINS (add production domains)
# - ADMIN_IP_WHITELIST (add admin IPs)
# - SENTRY_DSN (for error tracking)
# - GRAFANA_PASSWORD (for monitoring dashboard)
```

### Step 4: Database Initialization

```bash
# Start services temporarily
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Wait for database to be ready
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U postgres

# Run migrations
docker-compose -f docker-compose.prod.yml up -d backend
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create initial admin user (if needed)
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
db = SessionLocal()
admin = User(
    phone_number='+1234567890',
    full_name='System Administrator',
    password_hash=get_password_hash('secure_password'),
    role=UserRole.ADMIN,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created')
"

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Step 5: Deploy Application

```bash
# Option A: Manual deployment
docker-compose -f docker-compose.prod.yml up -d

# Option B: Automated deployment script
chmod +x scripts/deploy_production.sh
./scripts/deploy_production.sh

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

### Step 6: Health Checks

```bash
# Check backend health
curl https://api.agritrust.com/health
curl https://api.agritrust.com/health/ready
curl https://api.agritrust.com/health/detailed

# Check frontend
curl https://agrictrust.com
curl https://admin.agrictrust.com
curl https://agent.agrictrust.com

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 7: Configure Monitoring

```bash
# Access Grafana
# URL: https://monitoring.agrictrust.com (or configured port)
# Default credentials: admin / GRAFANA_PASSWORD

# Import dashboards from:
# - infra/monitoring/grafana/dashboards/

# Configure alerts in Grafana
# - Set up alert notifications (Slack, email)
# - Configure alert rules for:
#   - High error rate
#   - High response time
#   - Database connection issues
#   - Redis connection issues
#   - High CPU/memory usage
```

### Step 8: Configure Backups

```bash
# Database backups are automated via db-backup service
# Backups stored in ./backups directory

# Manual backup
chmod +x scripts/backup_database.sh
./scripts/backup_database.sh

# Restore from backup
./scripts/restore_database.sh agrictrust_backup_YYYYMMDD_HHMMSS.sql.gz

# Configure off-site backup (optional)
# - Set up AWS S3 or similar
# - Sync backups to remote location
# - Test restore process regularly
```

## Monitoring

### Key Metrics to Monitor

**Application Metrics:**
- Request rate and response time
- Error rate (4xx, 5xx)
- Database query performance
- Redis cache hit rate
- Active user sessions

**Infrastructure Metrics:**
- CPU usage per service
- Memory usage per service
- Disk usage
- Network I/O
- Container restarts

**Security Metrics:**
- Failed login attempts
- Rate limit violations
- Suspicious IP addresses
- Account lockouts
- Audit log anomalies

### Monitoring Stack

**Prometheus:**
- URL: http://localhost:9090
- Collects metrics from all services
- Stores time-series data

**Grafana:**
- URL: http://localhost:3001
- Visualizes metrics
- Custom dashboards
- Alert configuration

### Alert Configuration

Set up alerts for:
- Backend down for > 5 minutes
- Error rate > 5% for > 10 minutes
- Response time > 2s for > 10 minutes
- Database connection failures
- Redis connection failures
- Disk usage > 80%
- Memory usage > 90%

## Security

### Security Checklist

- [ ] All secrets use strong passwords (32+ characters)
- [ ] SECRET_KEY uses high-entropy value
- [ ] SSL/TLS enabled and enforced
- [ ] HTTP redirected to HTTPS
- [ ] Rate limiting enabled
- [ ] IP whitelisting configured for admin
- [ ] Account lockout enabled
- [ ] Password complexity enforced
- [ ] Audit logging enabled
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Database access restricted
- [ ] Redis password protected
- [ ] Firewall rules configured
- [ ] SSH key-based authentication only
- [ ] Regular security audits scheduled

### Security Best Practices

1. **Secrets Management**
   - Never commit secrets to git
   - Use environment variables for all secrets
   - Rotate secrets regularly (quarterly)
   - Use different secrets per environment

2. **Network Security**
   - Use firewall to restrict access
   - Only expose necessary ports (80, 443)
   - Use VPN for admin access
   - Implement IP whitelisting

3. **Application Security**
   - Keep dependencies updated
   - Run security scans regularly
   - Monitor for vulnerabilities
   - Implement zero-trust architecture

4. **Data Security**
   - Encrypt sensitive data at rest
   - Encrypt data in transit (TLS)
   - Regular database backups
   - Secure backup storage

## Backup and Recovery

### Backup Strategy

**Database Backups:**
- Automated daily backups
- Retention: 7 daily, 4 weekly, 6 monthly
- Stored locally in `./backups`
- Optional: Off-site backup to S3

**Application Backups:**
- Code stored in Git
- Docker images in Docker Hub
- Configuration in environment files
- Static assets in CDN (optional)

### Recovery Procedures

**Database Recovery:**
```bash
# Stop application services
docker-compose -f docker-compose.prod.yml stop backend

# Restore from backup
./scripts/restore_database.sh agrictrust_backup_YYYYMMDD_HHMMSS.sql.gz

# Restart services
docker-compose -f docker-compose.prod.yml start backend

# Verify data
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
users = db.query(User).count()
print(f'Total users: {users}')
"
```

**Disaster Recovery:**
1. Restore from latest backup
2. Verify data integrity
3. Test critical functionality
4. Monitor for errors
5. Communicate with stakeholders

## Performance Optimization

### Database Optimization

```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_transactions_created ON transactions(created_at);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE phone_number = '+1234567890';

-- Vacuum and reindex regularly
docker-compose -f docker-compose.prod.yml exec postgres vacuumdb -U postgres -d agri_trust -z -v
```

### Caching Strategy

- Redis for session storage
- Redis for rate limiting
- Redis for cached API responses
- Nginx for static file caching
- CDN for static assets (optional)

### Load Testing

```bash
# Install k6
curl https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz -L | tar xvz
sudo mv k6-v0.47.0-linux-amd64/k6 /usr/local/bin/

# Run load test
k6 run --out influxdb=http://localhost:8086/k6 tests/load-test.js
```

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs <service>

# Check disk space
df -h

# Check memory
free -h

# Restart service
docker-compose -f docker-compose.prod.yml restart <service>
```

**Database connection issues:**
```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U postgres
```

**High memory usage:**
```bash
# Check memory per service
docker stats

# Restart heavy services
docker-compose -f docker-compose.prod.yml restart backend

# Increase server resources if needed
```

**SSL certificate issues:**
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew
sudo cp /etc/letsencrypt/live/agrictrust.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/agrictrust.com/privkey.pem nginx/ssl/
docker-compose -f docker-compose.prod.yml restart nginx
```

## Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor Grafana dashboards
- Check error logs
- Verify backups completed

**Weekly:**
- Review security logs
- Check disk usage
- Update dependencies
- Review performance metrics

**Monthly:**
- Rotate secrets (passwords, keys)
- Test disaster recovery
- Review and optimize database
- Security audit
- Update SSL certificates (if needed)

**Quarterly:**
- Full security audit
- Performance review
- Capacity planning
- Backup strategy review

### Updates and Upgrades

**Application Updates:**
```bash
# Pull latest code
git pull origin main

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**System Updates:**
```bash
# Update OS packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io

# Update Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

## Support and Documentation

### Documentation
- Architecture Guide: `ARCHITECTURE_DEPLOYMENT_GUIDE.md`
- Migration Plan: `MIGRATION_PLAN.md`
- Security Guide: `ADMIN_SECURITY_IMPROVEMENTS.md`
- API Reference: `docs/api/API_REFERENCE.md`

### Contact Information
- Technical Support: [contact]
- Emergency Contact: [contact]
- Documentation: [documentation portal]

### Escalation Procedures
1. Check logs and metrics
2. Review troubleshooting guide
3. Contact technical support
4. Initiate disaster recovery if critical

## Appendix

### Environment Variables Reference

See `.env.production.example` for complete list of environment variables.

### Docker Compose Commands

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View service status
docker-compose -f docker-compose.prod.yml ps

# Execute command in container
docker-compose -f docker-compose.prod.yml exec backend <command>
```

### Health Check Endpoints

- `/health` - Basic health check
- `/health/ready` - Readiness check (includes dependencies)
- `/health/live` - Liveness check
- `/health/detailed` - Detailed health status
- `/health/metrics` - Application metrics

---

**Enterprise Deployment Guide Version 1.0**
**Last Updated: May 2, 2026**
**Status: Production Ready**
