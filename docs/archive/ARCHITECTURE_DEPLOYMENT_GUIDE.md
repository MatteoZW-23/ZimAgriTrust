# Agritrust Architecture & Deployment Guide

## Overview

This document describes the refactored multi-app architecture for Agritrust with separated driver application and provides deployment procedures.

## Architecture Summary

### Application Structure

```
apps/
├── admin-dashboard/          # Admin web application (port 3001)
├── agent-portal/             # Agent web application (port 3002)
├── app-portal/              # Farmer/Buyer web dashboard (port 3003)
├── public-website/          # Public-facing website (port 3000)
├── user-mobile/             # Unified mobile app (farmer + buyer only)
├── driver-mobile/           # Dedicated driver mobile app (driver only)
├── whatsapp-bridge/         # WhatsApp integration service (port 3006)
├── ussd-simulator/          # USSD testing tool (port 5000)
├── iot-gateway/             # IoT device gateway (port 3005)
└── services/                # Shared services

packages/
└── shared/                  # Shared types, utilities, API clients

backend/                     # Single backend API (port 8080)
```

### Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| Public Website | 3000 | Main entry point, company info, auth, web dashboard |
| Admin Dashboard | 3001 | Admin operations and management |
| Agent Portal | 3002 | Agent operations and field work |
| App Portal | 3003 | Farmer/Buyer web dashboard |
| Backend API | 8080 | Single backend for all apps |
| USSD Simulator | 5000 | USSD testing and development |
| IoT Gateway | 3005 | IoT device communication |
| WhatsApp Bridge | 3006 | WhatsApp bot integration |
| PostgreSQL | 5434 | Database (internal 5432) |
| Redis | 6380 | Cache (internal 6379) |

### Routing Strategy

```
Main Domain (http://localhost):
/ (port 3000)              → Public website
/dashboard (port 3003)     → Farmer/Buyer web dashboard
/download-mobile-app      → Driver app download page

Subdomains:
admin.localhost (port 3001) → Admin dashboard
agent.localhost (port 3002) → Agent portal

Mobile Apps:
- User Mobile App → Farmer + Buyer (unified app)
- Driver Mobile App → Driver only (separate app)
```

### Role-Based Access Control

**Roles:**
- `admin` - System administration
- `agent` - Field operations and verification
- `farmer` - Crop selling and farm management
- `buyer` - Crop purchasing and procurement
- `transporter` - Delivery and logistics

**RBAC Enforcement:**
- Backend: Authoritative RBAC via permissions.py
- Frontend: Route guards in each application
- Shared: RBAC configuration in packages/shared/src/rbac/config.ts

### User Access Patterns

**Drivers (Transporter Role):**
- **MOBILE ONLY** - No web dashboard access
- Must use the dedicated driver-mobile app
- Web login attempts redirect to `/download-mobile-app`
- Mobile provides: Job management, delivery tracking, earnings
- App is optimized for logistics workflows

**Farmers:**
- Access via: Public Website (port 3000) → `/dashboard` OR Mobile App
- Unique farmer dashboard with crop listings, orders, wallet
- Safe functions: Create listings, respond to offers, manage wallet
- Can use both web and mobile interfaces

**Buyers:**
- Access via: Public Website (port 3000) → `/dashboard` OR Mobile App
- Unique buyer dashboard with marketplace, offers, order tracking
- Safe functions: Browse marketplace, make offers, track orders, manage wallet
- Can use both web and mobile interfaces

**Agents:**
- Web-only via Agent Portal (port 3002) or agent.localhost
- Task management, verifications, training
- No mobile access required

**Admins:**
- Web-only via Admin Dashboard (port 3001) or admin.localhost
- System management and analytics
- No mobile access required

## Deployment Procedures

### Prerequisites

- Docker and Docker Compose installed
- Git repository cloned
- Environment variables configured

### Development Environment

1. **Start all services (direct port access for development):**
```bash
docker-compose up -d
```

2. **Start with nginx subdomain routing (production-like):**
```bash
docker-compose -f docker-compose.subdomains.yml up -d
```

3. **Start specific services:**
```bash
# Start only backend and database
docker-compose up -d postgres redis backend

# Start a specific frontend
docker-compose up -d public-website

# Start admin dashboard
docker-compose up -d admin-dashboard
```

3. **View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f public-website
```

4. **Stop services:**
```bash
docker-compose down
```

### Production Deployment

1. **Update environment variables:**
```bash
# Copy example env file
cp .env.example .env

# Edit with production values
nano .env
```

Required variables:
- `SECRET_KEY` - JWT signing key
- `DATABASE_URL` - Production database URL
- `REDIS_URL` - Production Redis URL
- `CORS_ORIGINS` - Allowed frontend origins

2. **Build production images:**
```bash
docker-compose build --no-cache
```

3. **Deploy with production compose:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **Run database migrations:**
```bash
docker-compose exec backend alembic upgrade head
```

### Application-Specific Deployment

#### Public Website
```bash
# Standalone deployment
cd apps/public-website
docker build -t agritrust-public-website .
docker run -p 3000:3000 agritrust-public-website
```

#### Admin Dashboard
```bash
cd apps/admin-dashboard
docker build -t agritrust-admin-dashboard .
docker run -p 3001:3001 agritrust-admin-dashboard
```

#### Agent Portal
```bash
cd apps/agent-portal
docker build -t agritrust-agent-portal .
docker run -p 3002:3002 agritrust-agent-portal
```

#### User Mobile App (Farmer + Buyer)
```bash
# Development
cd apps/user-mobile
npm install
npm start

# Production build
cd apps/user-mobile
expo build:android
expo build:ios
```

#### Driver Mobile App (Driver Only)
```bash
# Development
cd apps/driver-mobile
npm install
npm start

# Production build
cd apps/driver-mobile
expo build:android
expo build:ios
```

## Shared Packages

### Installation

```bash
cd packages/shared
npm install
npm run build
```

### Usage in Applications

```javascript
// Import from shared package
import { getApiClient, USER_ROLES, hasPermission } from '@agritrust/shared';

// Use API client
const api = getApiClient();
const user = await api.getCurrentUser();

// Check permissions
if (hasPermission(user.role, 'create_listing')) {
  // Show create listing button
}
```

## Authentication Flow

### Web Applications

1. User logs in via public-website (port 3000)
2. Backend validates credentials and returns JWT
3. Frontend stores token in localStorage
4. User redirected to role-specific dashboard:
   - Admin → http://localhost:3001
   - Agent → http://localhost:3002
   - Farmer/Buyer → http://localhost:3003/dashboard

### Mobile Application

1. User opens mobile app
2. Selects role (farmer/buyer/driver)
3. Enters phone number and PIN
4. Backend validates and returns JWT
5. App shows role-specific interface

## API Endpoints

All applications use the same backend API at `http://localhost:8080/api/v1`

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user

### Listings
- `GET /listings` - Get all listings
- `GET /listings/{id}` - Get specific listing
- `POST /listings` - Create listing
- `PUT /listings/{id}` - Update listing

### Orders
- `GET /orders` - Get user orders
- `GET /orders/{id}` - Get specific order
- `POST /orders` - Create order
- `PATCH /orders/{id}/status` - Update order status

### Wallet
- `GET /wallet` - Get wallet balance
- `POST /wallet/withdraw` - Request withdrawal
- `GET /wallet/transactions` - Get transaction history

## Monitoring and Maintenance

### Health Checks

```bash
# Check backend health
curl http://localhost:8080/health

# Check database connection
docker-compose exec postgres pg_isready -U postgres
```

### Database Backups

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres agri_trust > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres agri_trust < backup.sql
```

### Log Management

```bash
# View logs
docker-compose logs -f

# Rotate logs
docker-compose logs --tail=1000 > app.log
```

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port
netstat -ano | findstr :3000

# Kill process
taskkill /PID <PID> /F
```

**Database connection failed:**
```bash
# Check postgres is running
docker-compose ps postgres

# Restart postgres
docker-compose restart postgres
```

**CORS errors:**
- Ensure `CORS_ORIGINS` includes all frontend URLs
- Check backend environment variables

### Debug Mode

Enable debug logging:
```bash
# In docker-compose.yml
environment:
  - DEBUG=true
  - LOG_LEVEL=debug
```

## Security Considerations

1. **Environment Variables:** Never commit `.env` files
2. **Secrets:** Use strong, randomly generated secrets
3. **CORS:** Restrict CORS origins in production
4. **HTTPS:** Use HTTPS in production with SSL certificates
5. **RBAC:** Ensure all endpoints have proper role checks
6. **Rate Limiting:** Implement rate limiting on public endpoints
7. **Input Validation:** Validate all user inputs on backend

## Scaling

### Horizontal Scaling

```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

### Load Balancing

Use nginx or traefik to distribute traffic across multiple backend instances.

## Backup Strategy

1. **Database:** Daily automated backups
2. **Redis:** Periodic snapshots
3. **File Storage:** S3 or equivalent for user uploads
4. **Logs:** Centralized logging (ELK stack)

## Migration from Old Architecture

### Step 1: Backup Current System
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres agri_trust > pre-migration-backup.sql
```

### Step 2: Update Code
```bash
git pull origin main
```

### Step 3: Rebuild Services
```bash
docker-compose build --no-cache
```

### Step 4: Restart Services
```bash
docker-compose down
docker-compose up -d
```

### Step 5: Verify
```bash
# Test each application
curl http://localhost:3000
curl http://localhost:3001
curl http://localhost:3002
curl http://localhost:3003
curl http://localhost:8080/health
```

## Support

For issues or questions:
- Check logs: `docker-compose logs -f <service>`
- Review architecture documentation
- Contact development team
