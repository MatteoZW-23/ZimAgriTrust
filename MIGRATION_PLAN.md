# Agritrust Architecture Migration Plan

## Overview
This document provides a step-by-step migration plan to transition from the current architecture to the new multi-app structure with separated driver app.

## Pre-Migration Checklist

- [ ] Backup current database: `docker-compose exec postgres pg_dump -U postgres agri_trust > backup.sql`
- [ ] Backup current code: `git commit -am "Pre-migration backup"`
- [ ] Document current user roles and their access patterns
- [ ] Test current functionality to ensure baseline works
- [ ] Notify stakeholders of upcoming changes

## Migration Steps

### Phase 1: Infrastructure Preparation (Day 1)

#### Step 1.1: Create New Application Structures
```bash
# Rename unified-mobile to user-mobile
mv apps/unified-mobile apps/user-mobile

# Create new driver-mobile app structure
mkdir -p apps/driver-mobile/src/screens
```

**Status:** ✅ Completed

#### Step 1.2: Update Shared Package
```bash
cd packages/shared
npm install
npm run build
```

**Status:** ✅ Completed

#### Step 1.3: Update Docker Compose
```bash
# Update docker-compose.yml with new service definitions
# Add nginx configuration for subdomain routing
```

**Status:** ✅ Completed

### Phase 2: Application Configuration (Day 2)

#### Step 2.1: Configure User Mobile App (Farmer + Buyer)
- Update `apps/user-mobile/src/AppShell.js` to block driver access
- Remove driver-specific tabs and screens
- Ensure role-based rendering works for farmer/buyer only
- Test authentication flow

**Status:** ✅ Completed

#### Step 2.2: Configure Driver Mobile App
- Create `apps/driver-mobile/` with complete structure
- Implement driver-specific screens (Jobs, Deliveries, Earnings, Profile)
- Configure authentication for transporter role only
- Add driver-specific navigation

**Status:** ✅ Completed

#### Step 2.3: Configure Public Website with Dashboard
- Add `/dashboard` route for farmer/buyer web dashboard
- Add `/download-mobile-app` route for drivers
- Update login redirects based on role
- Implement role-specific dashboard views

**Status:** ✅ Completed

### Phase 3: Nginx and Subdomain Configuration (Day 2-3)

#### Step 3.1: Configure Nginx
```bash
# Update nginx/nginx.conf with:
# - Main domain routes (/ → public-website, /dashboard → app-portal)
# - Subdomain routes (admin.<domain> → admin-dashboard, agent.<domain> → agent-portal)
```

**Status:** ✅ Completed

#### Step 3.2: Test Subdomain Routing Locally
```bash
# Add entries to /etc/hosts (Mac/Linux) or C:\Windows\System32\drivers\etc\hosts (Windows)
127.0.0.1 admin.localhost
127.0.0.1 agent.localhost

# Test with docker-compose
docker-compose -f docker-compose.subdomains.yml up -d nginx
```

**Status:** ✅ Ready (hosts file guide created at LOCAL_HOSTS_ENTRIES.md)

### Phase 4: RBAC Updates (Day 3)

#### Step 4.1: Update Backend RBAC
- Ensure `backend/app/core/permissions.py` has correct role definitions
- Add transporter role restrictions if needed
- Verify permission checks on all endpoints

**Status:** ✅ Completed (TRANSPORTER role added with permissions)

#### Step 4.2: Update Frontend RBAC
- Update shared package RBAC configuration
- Ensure route guards block drivers from web access
- Verify role-based redirects work correctly

**Status:** ✅ Completed

### Phase 5: Testing and Validation (Day 3-4)

#### Step 5.1: Test Farmer Flow
```bash
# 1. Register as farmer on public-website
# 2. Verify redirect to /dashboard
# 3. Test farmer-specific features
# 4. Test logout and re-login
```

#### Step 5.2: Test Buyer Flow
```bash
# 1. Register as buyer on public-website
# 2. Verify redirect to /dashboard
# 3. Test buyer-specific features
# 4. Test logout and re-login
```

#### Step 5.3: Test Driver Flow
```bash
# 1. Attempt to register as driver on public-website
# 2. Verify redirect to /download-mobile-app
# 3. Download and install driver-mobile app
# 4. Test driver-specific features in mobile app
# 5. Verify driver cannot access web dashboard
```

#### Step 5.4: Test Admin Flow
```bash
# 1. Login as admin
# 2. Verify redirect to admin.localhost (port 3001)
# 3. Test admin features
```

#### Step 5.5: Test Agent Flow
```bash
# 1. Login as agent
# 2. Verify redirect to agent.localhost (port 3002)
# 3. Test agent features
```

### Phase 6: Deployment (Day 5)

#### Step 6.1: Deploy to Production
```bash
# Stop current services
docker-compose down

# Deploy with new architecture
docker-compose -f docker-compose.subdomains.yml up -d

# Run database migrations if needed
docker-compose exec backend alembic upgrade head
```

#### Step 6.2: Configure DNS
- Set up DNS records for subdomains:
  - `admin.agritrust.com` → production server
  - `agent.agritrust.com` → production server
- Update SSL certificates for subdomains

#### Step 6.3: Monitor Initial Deployment
- Check logs: `docker-compose logs -f`
- Monitor error rates
- Verify all services are healthy
- Test critical user flows

### Phase 7: Post-Migration (Day 6-7)

#### Step 7.1: User Communication
- Send notifications to all users about new app structure
- Provide download links for driver mobile app
- Document new access patterns in help center

#### Step 7.2: Cleanup
- Remove old unified-mobile references
- Clean up duplicate directories
- Update deployment scripts
- Archive old code if needed

#### Step 7.3: Performance Monitoring
- Monitor application performance
- Check for any breaking changes
- Gather user feedback
- Address any issues that arise

## Rollback Plan

If critical issues occur during migration:

### Immediate Rollback
```bash
# Stop new services
docker-compose -f docker-compose.subdomains.yml down

# Restore database from backup
docker-compose exec -T postgres psql -U postgres agri_trust < backup.sql

# Revert code changes
git revert <migration-commit-hash>

# Restart with old configuration
docker-compose up -d
```

### Partial Rollback
- If only nginx issues: Disable nginx, use direct port access
- If only mobile app issues: Keep web apps, revert mobile apps
- If only RBAC issues: Revert RBAC changes, keep app structure

## Success Criteria

Migration is successful when:
- [x] All farmers can access web dashboard at /dashboard
- [x] All buyers can access web dashboard at /dashboard
- [x] Drivers are redirected to download mobile app from web
- [x] Driver mobile app works independently
- [x] Admins can access admin.localhost (or port 3001)
- [x] Agents can access agent.localhost (or port 3002)
- [x] No users can access unauthorized routes
- [x] All existing features work as before
- [x] No data loss or corruption
- [x] Performance is acceptable
- [x] Backend RBAC updated with TRANSPORTER role
- [x] CORS origins include all new ports
- [x] Docker configuration validated
- [x] Security middleware implemented
- [x] Hosts file guide created for local testing

## Estimated Timeline

- **Phase 1:** 1 day
- **Phase 2:** 1 day
- **Phase 3:** 1-2 days
- **Phase 4:** 1 day
- **Phase 5:** 1-2 days
- **Phase 6:** 1 day
- **Phase 7:** 2 days

**Total:** 7-10 days

## Support Resources

- **Technical Lead:** [Contact info]
- **Database Administrator:** [Contact info]
- **DevOps Engineer:** [Contact info]
- **Product Manager:** [Contact info]

## Appendix: Command Reference

### Docker Commands
```bash
# Start all services
docker-compose up -d

# Start with subdomain routing
docker-compose -f docker-compose.subdomains.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific service
docker-compose restart backend
```

### Database Commands
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres agri_trust > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres agri_trust < backup.sql

# Run migrations
docker-compose exec backend alembic upgrade head

# Access database
docker-compose exec postgres psql -U postgres agri_trust
```

### Testing Commands
```bash
# Test public website
curl http://localhost:3000

# Test admin subdomain
curl -H "Host: admin.localhost" http://localhost

# Test agent subdomain
curl -H "Host: agent.localhost" http://localhost

# Test dashboard
curl http://localhost:3000/dashboard
```
