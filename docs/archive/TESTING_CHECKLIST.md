# Agritrust Architecture Refactor - Testing Checklist

## Pre-Testing Setup

### 1. Update Hosts File (Windows)
- [ ] Open `C:\Windows\System32\drivers\etc\hosts` as Administrator
- [ ] Add: `127.0.0.1 admin.localhost`
- [ ] Add: `127.0.0.1 agent.localhost`
- [ ] Save file
- [ ] Flush DNS: `ipconfig /flushdns`
- [ ] Test: `ping admin.localhost`
- [ ] Test: `ping agent.localhost`

### 2. Start Services
```bash
# Option A: Development (direct port access)
docker-compose up -d

# Option B: Production-like (with nginx subdomain routing)
docker-compose -f docker-compose.subdomains.yml up -d
```

- [ ] Services started successfully
- [ ] No container errors in logs
- [ ] Backend healthy: `curl http://localhost:8080/`
- [ ] PostgreSQL healthy: `docker-compose exec postgres pg_isready -U postgres`
- [ ] Redis healthy: `docker-compose exec redis redis-cli ping`

## Phase 1: Authentication Flow Testing

### Farmer Authentication
- [ ] Register as farmer on public-website (http://localhost:3000)
- [ ] Receive OTP via SMS/WhatsApp (test mode)
- [ ] Verify OTP
- [ ] Complete 2FA verification
- [ ] Verify redirect to `/dashboard`
- [ ] See farmer-specific dashboard
- [ ] Logout successfully
- [ ] Login again with existing credentials
- [ ] Verify redirect to `/dashboard` on login

### Buyer Authentication
- [ ] Register as buyer on public-website (http://localhost:3000)
- [ ] Receive OTP via SMS/WhatsApp (test mode)
- [ ] Verify OTP
- [ ] Complete 2FA verification
- [ ] Verify redirect to `/dashboard`
- [ ] See buyer-specific dashboard
- [ ] Logout successfully
- [ ] Login again with existing credentials
- [ ] Verify redirect to `/dashboard` on login

### Driver Authentication (Web)
- [ ] Attempt to register as driver on public-website
- [ ] Verify redirect to `/download-mobile-app`
- [ ] See download page with app information
- [ ] Verify driver CANNOT access `/dashboard`
- [ ] Verify driver CANNOT access admin/agent portals

### Driver Authentication (Mobile)
- [ ] Start driver-mobile app: `cd apps/driver-mobile && npm start`
- [ ] Login as driver (transporter role)
- [ ] Verify access to Jobs screen
- [ ] Verify access to Deliveries screen
- [ ] Verify access to Earnings screen
- [ ] Verify access to Profile screen
- [ ] Verify driver CANNOT see farmer/buyer features

### Admin Authentication
- [ ] Login as admin
- [ ] Verify redirect to `http://localhost:3001` (or `admin.localhost`)
- [ ] Access admin dashboard
- [ ] Verify admin-specific features work
- [ ] Logout successfully
- [ ] Verify admin CANNOT access farmer/buyer dashboard
- [ ] Verify admin CANNOT access agent portal

### Agent Authentication
- [ ] Login as agent
- [ ] Verify redirect to `http://localhost:3002` (or `agent.localhost`)
- [ ] Access agent portal
- [ ] Verify agent-specific features work
- [ ] Logout successfully
- [ ] Verify agent CANNOT access admin dashboard
- [ ] Verify agent CANNOT access farmer/buyer dashboard

## Phase 2: Route Guard Testing

### Public Website Routes
- [ ] `/` - Landing page loads
- [ ] `/dashboard` - Redirects to login if not authenticated
- [ ] `/dashboard` - Shows farmer dashboard if farmer
- [ ] `/dashboard` - Shows buyer dashboard if buyer
- [ ] `/dashboard` - Redirects to download page if driver
- [ ] `/download-mobile-app` - Loads download page

### Admin Dashboard Routes
- [ ] `/admin` - Redirects to login if not admin
- [ ] `/admin/*` - Accessible only by admin
- [ ] `/admin/*` - Blocked for non-admin roles

### Agent Portal Routes
- [ ] `/agent` - Redirects to login if not agent
- [ ] `/agent/*` - Accessible only by agent
- [ ] `/agent/*` - Blocked for non-agent roles

### App Portal Routes
- [ ] `/app/*` - Accessible by farmers and buyers
- [ ] `/app/*` - Blocked for drivers
- [ ] `/app/*` - Blocked for admins and agents

## Phase 3: RBAC Testing

### Permission Checks
- [ ] Farmer can create listings
- [ ] Farmer can manage listings
- [ ] Buyer can browse marketplace
- [ ] Buyer can make offers
- [ ] Driver can view delivery jobs
- [ ] Driver can accept delivery jobs
- [ ] Admin can manage users
- [ ] Agent can verify crops
- [ ] Roles cannot access unauthorized permissions

### Role-Based Redirects
- [ ] Farmers redirected to `/dashboard` after login
- [ ] Buyers redirected to `/dashboard` after login
- [ ] Drivers redirected to `/download-mobile-app` after login
- [ ] Admins redirected to admin portal after login
- [ ] Agents redirected to agent portal after login

## Phase 4: Subdomain Routing Testing (if using nginx)

### Main Domain
- [ ] `http://localhost/` → Public website
- [ ] `http://localhost/dashboard` → App portal (farmer/buyer dashboard)
- [ ] `http://localhost/download-mobile-app` → Download page

### Admin Subdomain
- [ ] `http://admin.localhost/` → Admin dashboard
- [ ] `http://admin.localhost/*` → Admin routes only
- [ ] Non-admins blocked from admin subdomain

### Agent Subdomain
- [ ] `http://agent.localhost/` → Agent portal
- [ ] `http://agent.localhost/*` → Agent routes only
- [ ] Non-agents blocked from agent subdomain

## Phase 5: Mobile App Testing

### User Mobile App (Farmer + Buyer)
- [ ] App starts successfully on Expo
- [ ] Login works for farmer
- [ ] Login works for buyer
- [ ] Login blocked for driver
- [ ] Farmer sees farmer-specific tabs
- [ ] Buyer sees buyer-specific tabs
- [ ] Driver sees blocking message
- [ ] API calls work to backend
- [ ] Navigation between screens works

### Driver Mobile App
- [ ] App starts successfully on Expo
- [ ] Login works for driver
- [ ] Login blocked for farmer/buyer
- [ ] Driver sees driver-specific tabs
- [ ] Jobs screen loads available jobs
- [ ] Deliveries screen shows active deliveries
- [ ] Earnings screen shows balance
- [ ] Profile screen shows driver info
- [ ] API calls work to backend
- [ ] Navigation between screens works

## Phase 6: Security Testing

### Rate Limiting
- [ ] Send 100+ requests in 60 seconds
- [ ] Verify rate limit error after threshold
- [ ] Admin has stricter rate limit (30 requests)

### Session Timeout
- [ ] Login as admin
- [ ] Wait 30 minutes without activity
- [ ] Verify auto-logout
- [ ] Verify redirect to login

### Account Lockout
- [ ] Attempt 5 failed logins
- [ ] Verify account locked
- [ ] Verify lockout message
- [ ] Wait 30 minutes
- [ ] Verify account unlocked
- [ ] Login successfully after unlock

### Password Complexity
- [ ] Try password < 8 characters - rejected
- [ ] Try password without uppercase - rejected
- [ ] Try password without lowercase - rejected
- [ ] Try password without digit - rejected
- [ ] Try password without special char - rejected
- [ ] Try common password - rejected
- [ ] Try valid complex password - accepted

### Audit Logging
- [ ] Perform admin action
- [ ] Check logs for audit entry
- [ ] Verify IP logged
- [ ] Verify user logged
- [ ] Verify timestamp logged
- [ ] Verify action logged

## Phase 7: Integration Testing

### Cross-Application Flow
- [ ] Register as farmer on web
- [ ] Login to mobile app with same credentials
- [ ] Verify data syncs
- [ ] Logout from web
- [ ] Verify mobile session still valid
- [ ] Logout from mobile
- [ ] Verify web session invalid

### Backend API
- [ ] Test `/api/v1/auth/login` - returns role
- [ ] Test `/api/v1/auth/verify-login-2fa` - returns user with role
- [ ] Test farmer endpoints with farmer token
- [ ] Test buyer endpoints with buyer token
- [ ] Test driver endpoints with driver token
- [ ] Test admin endpoints with admin token
- [ ] Test agent endpoints with agent token
- [ ] Verify unauthorized requests blocked

### CORS Configuration
- [ ] Request from port 3000 - allowed
- [ ] Request from port 3001 - allowed
- [ ] Request from port 3002 - allowed
- [ ] Request from port 3003 - allowed
- [ ] Request from port 19000 - allowed
- [ ] Request from port 19001 - allowed
- [ ] Request from port 19002 - allowed
- [ ] Request from unknown port - blocked

## Phase 8: Performance Testing

### Response Times
- [ ] Public website loads < 2 seconds
- [ ] Admin dashboard loads < 2 seconds
- [ ] Agent portal loads < 2 seconds
- [ ] App portal loads < 2 seconds
- [ ] Mobile apps load < 3 seconds
- [ ] API responses < 500ms

### Load Testing
- [ ] 10 concurrent users - no errors
- [ ] 50 concurrent users - no errors
- [ ] Database queries optimized
- [ ] No memory leaks
- [ ] No CPU spikes

## Phase 9: Error Handling

### Error Pages
- [ ] 404 page shows friendly message
- [ ] 500 page shows friendly message
- [ ] 403 page shows permission denied
- [ ] 401 page redirects to login

### Validation Errors
- [ ] Invalid phone number - shows error
- [ ] Invalid password - shows error
- [ ] Missing required fields - shows error
- [ ] Invalid OTP - shows error
- [ ] Error messages are clear and helpful

## Phase 10: Browser Compatibility

### Desktop Browsers
- [ ] Chrome - all features work
- [ ] Firefox - all features work
- [ ] Edge - all features work
- [ ] Safari - all features work

### Mobile Browsers
- [ ] Chrome Mobile - all features work
- [ ] Safari Mobile - all features work
- [ ] Responsive design works
- [ ] Touch interactions work

## Test Results Summary

| Test Category | Total Tests | Passed | Failed | Status |
|---------------|-------------|--------|--------|--------|
| Authentication | 30 | 0 | 0 | ⏳ Pending |
| Route Guards | 15 | 0 | 0 | ⏳ Pending |
| RBAC | 10 | 0 | 0 | ⏳ Pending |
| Subdomain Routing | 10 | 0 | 0 | ⏳ Pending |
| Mobile Apps | 15 | 0 | 0 | ⏳ Pending |
| Security | 10 | 0 | 0 | ⏳ Pending |
| Integration | 10 | 0 | 0 | ⏳ Pending |
| Performance | 5 | 0 | 0 | ⏳ Pending |
| Error Handling | 5 | 0 | 0 | ⏳ Pending |
| Browser Compatibility | 5 | 0 | 0 | ⏳ Pending |
| **TOTAL** | **115** | **0** | **0** | **⏳ Pending** |

## Known Issues

Document any issues found during testing:

1. 
2. 
3. 

## Sign-Off

- **Tester:** _______________
- **Date:** _______________
- **Status:** _______________

## Notes

- All tests should be performed in development environment first
- Critical issues must be resolved before production deployment
- Non-critical issues can be tracked for future releases
- Document any deviations from expected behavior
