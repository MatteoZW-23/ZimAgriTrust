# Custom Domain Setup for ZimAgriTrust

## Overview
This guide shows how to configure your custom domain for the ZimAgriTrust platform.

## Prerequisites
- Registered domain name (e.g., `zimagritrust.com`)
- Server with public IP address
- Docker and Docker Compose installed
- SSL certificate (recommended for production)

## Step 1: DNS Configuration

### Point your domain to your server:
```
A Record: @ -> YOUR_SERVER_IP
A Record: www -> YOUR_SERVER_IP
A Record: admin -> YOUR_SERVER_IP
A Record: agent -> YOUR_SERVER_IP
```

### Optional: Use subdomains for different environments:
```
A Record: staging -> YOUR_SERVER_IP
A Record: dev -> YOUR_SERVER_IP
```

## Step 2: Update Nginx Configuration

1. Replace `YOURDOMAIN.COM` in `nginx/nginx.custom-domain.conf` with your actual domain
2. Copy the custom configuration:
   ```bash
   cp nginx/nginx.custom-domain.conf nginx/nginx.conf
   ```

## Step 3: SSL Certificate (Recommended)

### Option A: Let's Encrypt (Free)
```bash
# Install certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Generate SSL certificate
sudo certbot --nginx -d YOURDOMAIN.COM -d www.YOURDOMAIN.COM -d admin.YOURDOMAIN.COM -d agent.YOURDOMAIN.COM
```

### Option B: Manual SSL Certificates
1. Place your SSL certificates in `nginx/ssl/`:
   ```
   nginx/ssl/YOURDOMAIN.COM.crt
   nginx/ssl/YOURDOMAIN.COM.key
   ```

2. Update nginx configuration to use SSL:
   ```nginx
   server {
       listen 443 ssl;
       server_name YOURDOMAIN.COM www.YOURDOMAIN.COM;
       
       ssl_certificate /etc/nginx/ssl/YOURDOMAIN.COM.crt;
       ssl_certificate_key /etc/nginx/ssl/YOURDOMAIN.COM.key;
       
       # SSL settings
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
   }
   ```

## Step 4: Update Environment Variables

1. Copy the custom domain environment file:
   ```bash
   cp .env.custom-domain .env
   ```

2. Replace `YOURDOMAIN.COM` with your actual domain

## Step 5: Update Application URLs

### Backend Configuration
Update `backend/app/core/config.py`:
```python
CORS_ORIGINS = "https://YOURDOMAIN.COM,https://www.YOURDOMAIN.COM,https://admin.YOURDOMAIN.COM,https://agent.YOURDOMAIN.COM"
ALLOWED_HOSTS = "YOURDOMAIN.COM,www.YOURDOMAIN.COM,admin.YOURDOMAIN.COM,agent.YOURDOMAIN.COM"
```

### Frontend Applications
Update API URLs in frontend applications:

**Admin Dashboard** (`apps/admin-dashboard/.env`):
```
VITE_API_URL=https://YOURDOMAIN.COM/api/v1
```

**Agent Portal** (`apps/agent-portal/.env`):
```
VITE_API_URL=https://YOURDOMAIN.COM/api/v1
```

**App Portal** (`apps/app-portal/.env`):
```
VITE_API_URL=https://YOURDOMAIN.COM/api/v1
```

**Public Website** (`apps/public-website/.env`):
```
VITE_API_URL=https://YOURDOMAIN.COM/api/v1
```

## Step 6: Deploy with Custom Domain

1. Build and deploy with the new configuration:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

2. Verify the deployment:
   ```bash
   curl -I https://YOURDOMAIN.COM
   curl -I https://admin.YOURDOMAIN.COM
   curl -I https://agent.YOURDOMAIN.COM
   ```

## URL Structure After Setup

### Main Domain (`https://YOURDOMAIN.COM`)
- `/` → Public website
- `/app/` → Farmer/Buyer dashboard
- `/admin/` → Admin dashboard
- `/agent/` → Agent portal
- `/api/` → Backend API

### Subdomains
- `https://admin.YOURDOMAIN.COM` → Admin dashboard
- `https://agent.YOURDOMAIN.COM` → Agent portal

## Testing Your Domain

1. **DNS Propagation**: Check if DNS is working:
   ```bash
   nslookup YOURDOMAIN.COM
   nslookup admin.YOURDOMAIN.COM
   ```

2. **SSL Certificate**: Verify SSL is working:
   ```bash
   openssl s_client -connect YOURDOMAIN.COM:443
   ```

3. **Application Access**: Test all URLs:
   - Main site: `https://YOURDOMAIN.COM`
   - Admin: `https://admin.YOURDOMAIN.COM`
   - Agent: `https://agent.YOURDOMAIN.COM`
   - API: `https://YOURDOMAIN.COM/api/v1/health`

## Troubleshooting

### Common Issues:

1. **DNS not propagating**: Wait 24-48 hours for DNS to propagate
2. **SSL certificate errors**: Ensure certificates are correctly installed
3. **CORS errors**: Check that CORS origins are properly configured
4. **502 Bad Gateway**: Verify backend is running and accessible
5. **404 errors**: Check nginx configuration and file paths

### Useful Commands:
```bash
# Check nginx status
docker-compose exec nginx nginx -t

# View nginx logs
docker-compose logs nginx

# Restart nginx
docker-compose restart nginx

# Check SSL certificate
openssl x509 -in nginx/ssl/YOURDOMAIN.COM.crt -text -noout
```

## Security Considerations

1. **Always use HTTPS** in production
2. **Keep SSL certificates** updated and renewed
3. **Use strong passwords** for database and services
4. **Enable firewalls** to restrict access
5. **Monitor logs** for suspicious activity
6. **Regular updates** of Docker images and dependencies

## Next Steps

After setting up your custom domain:
1. Configure email services with your domain
2. Set up monitoring and alerting
3. Configure backup strategies
4. Set up CDN for better performance
5. Implement additional security measures
