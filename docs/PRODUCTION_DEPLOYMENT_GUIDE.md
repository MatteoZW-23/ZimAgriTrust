# ZimAgriTrust Production Deployment Guide
**Version:** 1.0  
**Last Updated:** May 19, 2026  
**Classification:** Internal - Production Operations

---

## Table of Contents
1. [Infrastructure Requirements](#infrastructure-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Monitoring & Alerting Setup](#monitoring--alerting-setup)
7. [Backup & Disaster Recovery](#backup--disaster-recovery)

---

## Infrastructure Requirements

### Minimum Production Specs

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Application Server** | 2 vCPU, 4GB RAM | 4 vCPU, 8GB RAM | FastAPI backend + workers |
| **Database Server** | 2 vCPU, 4GB RAM, 50GB SSD | 4 vCPU, 8GB RAM, 100GB SSD | PostgreSQL 16 |
| **Cache Server** | 1 vCPU, 2GB RAM | 2 vCPU, 4GB RAM | Redis 7 with persistence |
| **Storage** | 20GB | 100GB | For uploads, logs, backups |
| **Network** | 100 Mbps | 1 Gbps | Low latency to payment providers |
| **SSL Certificate** | Required | Let's Encrypt or commercial | Wildcard cert recommended |

### Cloud Provider Recommendations

#### AWS (Recommended)
```
- ECS/Fargate or EKS for containers
- RDS PostgreSQL (Multi-AZ)
- ElastiCache Redis (Cluster mode)
- Application Load Balancer
- S3 for file storage and backups
- CloudFront for CDN
- Route 53 for DNS
- CloudWatch for monitoring
```

#### Alternative: DigitalOcean
```
- Kubernetes (DOKS)
- Managed PostgreSQL
- Managed Redis
- Load Balancer
- Spaces (S3-compatible)
```

---

## Pre-Deployment Checklist

### 1. Domain & DNS Setup

- [ ] Register domain: `zimagritrust.co.zw` (or your preferred)
- [ ] Set up DNS records:
  ```
  A     @         → Load Balancer IP
  A     api       → Load Balancer IP  
  A     admin     → Load Balancer IP
  A     agent     → Load Balancer IP
  CNAME www       → zimagritrust.co.zw
  ```

### 2. SSL/TLS Certificates

```bash
# Option 1: Let's Encrypt (Free)
sudo apt-get install certbot
sudo certbot certonly --standalone \
  -d zimagritrust.co.zw \
  -d api.zimagritrust.co.zw \
  -d admin.zimagritrust.co.zw \
  -d agent.zimagritrust.co.zw

# Certificates will be at:
# /etc/letsencrypt/live/zimagritrust.co.zw/fullchain.pem
# /etc/letsencrypt/live/zimagritrust.co.zw/privkey.pem
```

### 3. Server Setup (Ubuntu 22.04 LTS)

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install security tools
sudo apt-get install -y nginx fail2ban ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# Start fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## Environment Configuration

### Step 1: Generate All Secrets

Run this script on your **local secure machine** (NOT on the server):

```bash
#!/bin/bash
# generate_secrets.sh
# Run this locally to generate secrets, then copy to server

echo "# Copy these to your .env.production file"
echo ""
echo "# Database"
echo "POSTGRES_PASSWORD=$(openssl rand -hex 32)"
echo ""
echo "# Redis"
echo "REDIS_PASSWORD=$(openssl rand -hex 32)"
echo ""
echo "# JWT Keys (all different!)"
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo "REFRESH_SECRET_KEY=$(openssl rand -hex 32)"
echo "SUPER_ADMIN_SECRET_KEY=$(openssl rand -hex 32)"
echo ""
echo "# PIN Security"
echo "PIN_PEPPER=$(openssl rand -hex 16)"
echo ""
echo "# Financial Signing"
echo "TRANSACTION_SIGNING_KEY=$(openssl rand -hex 32)"
echo "AUDIT_CHAIN_KEY=$(openssl rand -hex 32)"
```

Run it:
```bash
chmod +x generate_secrets.sh
./generate_secrets.sh > my_secrets.txt
```

**⚠️ CRITICAL:** Store `my_secrets.txt` securely. Never commit to git.

### Step 2: Create `.env.production`

```bash
cp .env.production.example .env.production
nano .env.production  # Fill in your secrets
```

**Key Values to Set:**

| Variable | How to Get | Example |
|----------|-----------|---------|
| `POSTGRES_PASSWORD` | `openssl rand -hex 32` | 64-char hex string |
| `REDIS_PASSWORD` | `openssl rand -hex 32` | 64-char hex string |
| `SECRET_KEY` | `openssl rand -hex 32` | 64-char hex string |
| `REFRESH_SECRET_KEY` | `openssl rand -hex 32` | Different from SECRET_KEY |
| `SUPER_ADMIN_SECRET_KEY` | `openssl rand -hex 32` | Different from both above |
| `ECOCASH_WEBHOOK_SECRET` | EcoCash merchant dashboard | From provider |
| `ONEMONEY_WEBHOOK_SECRET` | OneMoney merchant dashboard | From provider |
| `ADMIN_IP_WHITELIST` | Your office IP | `192.168.1.100` |

### Step 3: Upload to Server

```bash
# On your local machine
scp .env.production root@your-server-ip:/opt/agritrust/

# SSH into server
ssh root@your-server-ip

# Set proper permissions
chmod 600 /opt/agritrust/.env.production
```

---

## Step-by-Step Deployment

### Step 1: Clone Repository on Server

```bash
mkdir -p /opt/agritrust
cd /opt/agritrust
git clone https://github.com/your-org/zimagritrust.git .
```

### Step 2: Deploy Services

```bash
cd /opt/agritrust

# Pull images
docker compose -f docker-compose.yml pull

# Deploy with production env
docker compose \
  -f docker-compose.yml \
  --env-file .env.production \
  up -d

# Check status
docker compose ps
```

### Step 3: Run Database Migrations

```bash
docker compose exec backend alembic upgrade head
docker compose exec postgres pg_isready -U agritrust
```

### Step 4: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/zimagritrust
```

Add this configuration:

```nginx
# Backend upstream
upstream backend {
    server 127.0.0.1:8080;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name zimagritrust.co.zw www.zimagritrust.co.zw api.zimagritrust.co.zw;
    return 301 https://$server_name$request_uri;
}

# HTTPS API
server {
    listen 443 ssl http2;
    server_name api.zimagritrust.co.zw;

    ssl_certificate /etc/letsencrypt/live/zimagritrust.co.zw/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zimagritrust.co.zw/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/zimagritrust /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# Test API health
curl https://api.zimagritrust.co.zw/health

# Test webhook signature (should fail without signature)
curl -X POST https://api.zimagritrust.co.zw/api/v1/payments/ecocash/callback \
  -d '{"test":"data"}'
# Expected: 401 Missing signature header

# Test with valid signature (after getting real secret)
# Expected: 200 or processing
```

### 2. Security Verification Script

```bash
docker compose exec backend python -c "
from app.core.config import settings
print('Config loaded successfully')
print(f'SECRET_KEY length: {len(settings.SECRET_KEY)}')
print(f'WEBHOOK secrets configured: {bool(settings.ECOCASH_WEBHOOK_SECRET)}')
"
```

### 3. Run Verification Script

```bash
# On server
cd /opt/agritrust
python scripts/verify_security_patches.py
```

---

## Monitoring & Alerting Setup

### 1. Set Up Sentry

1. Create account at https://sentry.io
2. Create new project for ZimAgriTrust
3. Get DSN from project settings
4. Add to `.env.production`:
   ```bash
   SENTRY_DSN=https://<key>@sentry.io/<project>
   ```
5. Restart backend:
   ```bash
   docker compose restart backend
   ```

### 2. Configure Log Aggregation

Install Vector or Fluentd:

```bash
# Install Vector
curl -1sLf 'https://repositories.timber.io/public/vector/cfg/setup/bash.deb.sh' | sudo bash
sudo apt-get install vector

# Configure for production logs
sudo nano /etc/vector/vector.toml
```

### 3. Key Metrics to Monitor

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| API 5xx errors | > 1% in 5 min | Page on-call |
| DB connections | > 80% of max | Scale DB pool |
| Redis memory | > 90% | Investigate cache usage |
| Payment failures | > 5% | Check provider status |
| JWT validation failures | > 10/min | Security alert |
| Webhook signature failures | > 1 | Immediate investigation |

---

## Backup & Disaster Recovery

### 1. Automated Database Backups

```bash
# Create backup script
sudo nano /opt/agritrust/scripts/backup.sh
```

```bash
#!/bin/bash
# backup.sh - Run via cron daily

BACKUP_DIR="/backups/postgres"
S3_BUCKET="zimagritrust-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
docker compose exec -T postgres pg_dump -U agritrust agri_trust > "$BACKUP_DIR/backup_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/backup_$DATE.sql"

# Upload to S3
aws s3 cp "$BACKUP_DIR/backup_$DATE.sql.gz" s3://$S3_BUCKET/postgres/

# Keep only last 30 days locally
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Set up cron:
```bash
chmod +x /opt/agritrust/scripts/backup.sh
sudo crontab -e

# Add line:
0 2 * * * /opt/agritrust/scripts/backup.sh >> /var/log/agritrust-backup.log 2>&1
```

### 2. Redis Persistence

Already configured in `docker-compose.yml`:
```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 256mb
  volumes:
    - redis_data:/data
```

### 3. Disaster Recovery Plan

**Scenario 1: Database Corruption**
```bash
# 1. Stop services
docker compose stop backend

# 2. Restore from backup
docker compose exec -T postgres psql -U agritrust agri_trust < backup_file.sql

# 3. Restart
docker compose up -d
```

**Scenario 2: Complete Server Failure**
1. Spin up new server
2. Install Docker
3. Clone repository
4. Restore `.env.production` from secure backup
5. Restore database from S3 backup
6. Run `docker compose up -d`

---

## Maintenance Schedule

### Daily
- [ ] Check error logs
- [ ] Verify backup completion
- [ ] Monitor payment success rate

### Weekly
- [ ] Review failed login attempts
- [ ] Check disk space
- [ ] Update SSL certificates if expiring soon

### Monthly
- [ ] Rotate secrets (recommended)
- [ ] Security patch updates
- [ ] Database optimization (VACUUM ANALYZE)

### Quarterly
- [ ] Full disaster recovery drill
- [ ] Penetration testing
- [ ] Access review (remove inactive admins)

---

## Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| CTO | [Name] | [Phone] | [Email] |
| DevOps Lead | [Name] | [Phone] | [Email] |
| Security Officer | [Name] | [Phone] | [Email] |
| Payment Provider (EcoCash) | Support | [Number] | [Email] |
| Cloud Provider Support | AWS/DigitalOcean | [Number] | [Email] |

---

## Quick Reference Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f --tail 100 backend

# Restart services
docker compose restart backend
docker compose restart

# Scale workers (if using Swarm/K8s)
docker compose up -d --scale celery-worker=3

# Database access
docker compose exec postgres psql -U agritrust -d agri_trust

# Redis access
docker compose exec redis redis-cli -a $REDIS_PASSWORD

# Check resource usage
docker stats

# Update deployment
git pull
docker compose -f docker-compose.yml --env-file .env.production up -d
```

---

## Troubleshooting

### Issue: "Webhook verification not configured" error

**Cause:** `ECOCASH_WEBHOOK_SECRET` not set in `.env.production`

**Fix:**
```bash
# 1. Get secret from EcoCash dashboard
# 2. Add to .env.production
# 3. Restart backend
docker compose restart backend
```

### Issue: "SECRET_KEY too short" error

**Cause:** Default placeholder secret in config

**Fix:**
```bash
# Generate new secret
openssl rand -hex 32

# Update .env.production
# Restart
docker compose restart backend
```

### Issue: Database connection refused

**Cause:** Postgres not ready or credentials wrong

**Fix:**
```bash
# Check postgres is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Verify credentials match
docker compose exec postgres env | grep POSTGRES
```

### Issue: Redis AUTH failed

**Cause:** Redis password not set or mismatch

**Fix:**
```bash
# Check Redis URL in env
docker compose exec backend env | grep REDIS

# Verify password is set
docker compose exec redis redis-cli AUTH <password> PING
```

---

**END OF DOCUMENT**

For questions or updates, contact the DevOps team.
