# ZimAgriTrust Production Deployment Guide

This guide provides step-by-step instructions for deploying ZimAgriTrust to a WebDev-managed VPS/cloud hosting environment.

## Prerequisites

- Ubuntu VPS (20.04 LTS or later recommended)
- Docker and Docker Compose installed
- Domain name configured with DNS records
- SSL certificates (Let's Encrypt recommended)
- Minimum 4GB RAM, 2 CPU cores, 40GB storage

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd Agric

# Configure environment variables
cp .env.production.example .env.production
nano .env.production  # Edit with production values

# Generate SSL certificates (Let's Encrypt)
sudo apt install certbot
sudo certbot certonly --standalone -d agritrust.co.zw -d www.agritrust.co.zw \
  -d admin.agritrust.co.zw -d agent.agritrust.co.zw -d app.agritrust.co.zw \
  -d supplier.agritrust.co.zw -d api.agritrust.co.zw

# Copy SSL certificates
sudo cp /etc/letsencrypt/live/agritrust.co.zw/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/agritrust.co.zw/privkey.pem nginx/ssl/

# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# Check service health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Environment Configuration

### Required Environment Variables

Create `.env.production` with the following variables:

```bash
# Database
POSTGRES_USER=agritrust
POSTGRES_PASSWORD=<strong-random-password-32-chars>
POSTGRES_DB=zimagritrust

# Redis
REDIS_PASSWORD=<strong-random-password-32-chars>

# Authentication
SECRET_KEY=<strong-random-secret-64-hex-chars>
REFRESH_SECRET_KEY=<different-strong-random-secret-64-hex-chars>
PIN_PEPPER=<strong-random-secret-32-hex-chars>
ADMIN_BOOTSTRAP_TOKEN=<strong-random-secret-32-hex-chars>

# Domain Configuration
DOMAIN=agritrust.co.zw
API_URL=https://api.agritrust.co.zw
ADMIN_URL=https://admin.agritrust.co.zw
AGENT_URL=https://agent.agritrust.co.zw
APP_PORTAL_URL=https://app.agritrust.co.zw
SUPPLIER_PORTAL_URL=https://supplier.agritrust.co.zw

# CORS & Hosts
CORS_ORIGINS=https://agritrust.co.zw,https://www.agritrust.co.zw,https://admin.agritrust.co.zw,https://agent.agritrust.co.zw,https://app.agritrust.co.zw,https://supplier.agritrust.co.zw
ALLOWED_HOSTS=agritrust.co.zw,www.agritrust.co.zw,admin.agritrust.co.zw,agent.agritrust.co.zw,app.agritrust.co.zw,supplier.agritrust.co.zw,api.agritrust.co.zw
FORCE_HTTPS=true

# Financial Security
TRANSACTION_SIGNING_KEY=<strong-random-secret-64-hex-chars>
AUDIT_CHAIN_KEY=<strong-random-secret-64-hex-chars>
SUPER_ADMIN_SECRET_KEY=<different-strong-random-secret-64-hex-chars>
SUPER_ADMIN_IP_WHITELIST=<your-admin-ip-addresses>

# Grafana
GRAFANA_PASSWORD=<strong-grafana-password>
GRAFANA_USER=admin

# Flower (Celery Monitoring)
FLOWER_USER=admin
FLOWER_PASSWORD=<strong-flower-password>

# Safety Flags (MUST be false in production)
MASTER_TEST_LOGIN_ENABLED=false
AUTO_CONFIRM_PAYMENTS=false
```

### Generate Secure Secrets

```bash
# Generate 64-character hex secrets
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## SSL Certificate Setup

### Using Let's Encrypt

```bash
# Install certbot
sudo apt update
sudo apt install certbot

# Obtain certificates for all subdomains
sudo certbot certonly --standalone \
  -d agritrust.co.zw \
  -d www.agritrust.co.zw \
  -d admin.agritrust.co.zw \
  -d agent.agritrust.co.zw \
  -d app.agritrust.co.zw \
  -d supplier.agritrust.co.zw \
  -d api.agritrust.co.zw \
  -d flower.agritrust.co.zw \
  -d prometheus.agritrust.co.zw \
  -d grafana.agritrust.co.zw

# Create SSL directory
mkdir -p nginx/ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/agritrust.co.zw/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/agritrust.co.zw/privkey.pem nginx/ssl/

# Set permissions
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem
```

### Auto-Renewal Setup

```bash
# Test renewal
sudo certbot renew --dry-run

# Setup auto-renewal (cron)
sudo crontab -e

# Add this line (renews at 3am daily)
0 3 * * * certbot renew --quiet --post-hook "docker-compose -f /path/to/Agric/docker-compose.prod.yml exec nginx nginx -s reload"
```

## Service Architecture

### Production Services

- **postgres**: PostgreSQL 16 database
- **redis**: Redis 7 cache and message broker
- **backend**: FastAPI backend (production-slim build)
- **celery-worker**: Background task processor
- **celery-beat**: Scheduled task executor
- **flower**: Celery monitoring UI
- **whatsapp-service**: WhatsApp business logic
- **whatsapp-bridge**: WhatsApp bridge (Node.js)
- **public-website**: Public marketing site (production build)
- **admin-dashboard**: Admin panel (production build)
- **agent-portal**: Agent portal (production build)
- **app-portal**: Farmer/buyer portal (production build)
- **supplier-portal**: Supplier portal (production build)
- **nginx**: Reverse proxy with SSL termination
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboard

### Network Architecture

All services communicate via the `backend-network` Docker bridge network. Only NGINX exposes ports 80 and 443 to the host.

## Deployment Steps

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Application Deployment

```bash
# Clone repository
git clone <repository-url> Agric
cd Agric

# Configure environment
cp .env.production.example .env.production
nano .env.production

# Setup SSL (see SSL section above)

# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Verify services
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs backend
```

### 3. Database Migration

```bash
# Run migrations (handled automatically by backend entrypoint)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Verify migration status
docker-compose -f docker-compose.prod.yml exec backend alembic current
```

### 4. Create Super Admin

```bash
# Use the bootstrap token to create super admin
curl -X POST https://api.agritrust.co.zw/api/v1/admin/bootstrap \
  -H "Authorization: Bearer ${ADMIN_BOOTSTRAP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@agritrust.co.zw",
    "password": "<strong-admin-password>",
    "full_name": "Super Admin"
  }'
```

## Monitoring

### Access Monitoring Dashboards

- **Grafana**: https://grafana.agritrust.co.zw (admin/GRAFANA_PASSWORD)
- **Prometheus**: https://prometheus.agritrust.co.zw (basic auth)
- **Flower**: https://flower.agritrust.co.zw (admin/FLOWER_PASSWORD)

### Health Checks

```bash
# Backend health
curl https://api.agritrust.co.zw/health

# Service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f celery-worker
```

## Backup and Restore

### Database Backup

```bash
# Automated backup script
./scripts/backup_database.sh

# Manual backup
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U agritrust zimagritrust > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Database Restore

```bash
# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U agritrust zimagritrust < backup_20240527_120000.sql
```

### Volume Backup

```bash
# Backup all volumes
docker run --rm -v agric_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
docker run --rm -v agric_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data
```

## Scaling

### Horizontal Scaling

For high-traffic deployments, consider:

1. **Load Balancer**: Use HAProxy or cloud load balancer
2. **Multiple Backend Instances**: Scale backend with Docker Swarm or Kubernetes
3. **Database Replication**: PostgreSQL read replicas
4. **Redis Cluster**: Redis Sentinel or Cluster mode

### Vertical Scaling

Increase resources in docker-compose.prod.yml:

```yaml
backend:
  environment:
    GUNICORN_WORKERS: 8  # Increase from 4
    DB_POOL_SIZE: 20     # Increase from 10
    DB_MAX_OVERFLOW: 40  # Increase from 20
```

## Security Hardening

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Fail2Ban Setup

```bash
# Install fail2ban
sudo apt install fail2ban

# Configure jail for NGINX
sudo nano /etc/fail2ban/jail.local

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5
```

### Regular Updates

```bash
# Update system packages monthly
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs <service-name>

# Check resource usage
docker stats

# Restart specific service
docker-compose -f docker-compose.prod.yml restart <service-name>
```

### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check Redis status
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Verify network
docker network inspect Agric_backend-network
```

### SSL Certificate Issues

```bash
# Renew certificates
sudo certbot renew

# Reload NGINX
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Check certificate expiry
sudo certbot certificates
```

## Maintenance

### Rolling Updates

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Update with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps backend
docker-compose -f docker-compose.prod.yml up -d backend
```

### Log Rotation

```bash
# Setup logrotate for Docker logs
sudo nano /etc/logrotate.d/docker-compose

/var/log/docker/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 root root
}
```

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
- Review documentation: `/docs`
- Contact DevOps team

## Checklist Before Production Deployment

- [ ] All environment variables configured with secure values
- [ ] SSL certificates obtained and configured
- [ ] DNS records pointing to VPS IP
- [ ] Firewall configured (only 22, 80, 443 open)
- [ ] Database backups scheduled
- [ ] Monitoring dashboards accessible
- [ ] Health checks passing
- [ ] Super admin account created
- [ ] Rate limiting configured
- [ ] CORS origins set to production domains
- [ ] ALLOWED_HOSTS set to production domains
- [ ] MASTER_TEST_LOGIN_ENABLED=false
- [ ] AUTO_CONFIRM_PAYMENTS=false
- [ ] All services running and healthy
