# Developer Guide - ZimAgritrust Platform

This guide consolidates deployment instructions, contribution guidelines, and implementation details for developers working on the ZimAgritrust platform.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Contributing Guidelines](#contributing-guidelines)
5. [Admin Multi-Location Implementation](#admin-multi-location-implementation)
6. [Quality Standards](#quality-standards)

---

## Prerequisites

### Required Software
- Docker and Docker Compose
- PostgreSQL 16
- Python 3.12+
- Node.js 20+

### Environment Variables
Ensure `.env` matches `.env.example` but using strong passwords and securely rotated `SECRET_KEY` variables. Set `MASTER_TEST_LOGIN_ENABLED="false"` for production.

---

## Local Development Setup

### Option 1: Docker (Recommended)

Using Docker Compose for orchestrated launches:

```bash
docker-compose up -d --build
```

### Option 2: Local Setup (Without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd apps/web/admin-dashboard
npm install
npm run dev
```

---

## Production Deployment

### Docker Compose Production

We use a hardened Docker Compose configuration for orchestrated launches:

```bash
docker-compose -f docker-compose.yml up -d --build
```

### High Availability Setup

- Use a managed PostgreSQL instance instead of Docker volumes in production
- Put the API and Node Gateway behind an Nginx reverse proxy with SSL termination
- Configure proper monitoring and alerting
- Set up automated backups

### Environment Configuration

**Critical Settings for Production:**
- Strong, rotated `SECRET_KEY` variables
- `MASTER_TEST_LOGIN_ENABLED="false"`
- Secure database passwords
- Proper CORS configuration
- SSL/TLS enabled
- Rate limiting configured
- Monitoring and logging enabled

---

## Contributing Guidelines

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

#### Python
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Use conventional commits

#### JavaScript/React
- Follow ESLint rules
- Use functional components with hooks
- Write meaningful component names
- Add comments for complex logic

### Intelligence Modeling

When adding new ML models, please follow the Sovereign Engineering patterns established in `backend/app/ml/` and include a corresponding research notebook in `data/research/notebooks/`.

### Quality Standards

- All code must pass `pytest tests/`
- Document all API endpoints in API_REFERENCE.md
- Ensure new models are registered in relevant service files
- Write unit tests for new features
- Ensure backward compatibility when modifying APIs

---

## Admin Multi-Location Implementation

### Overview

This section summarizes the complete implementation of the multi-location, multi-role admin authorization system for the ZimAgritrust platform. The system enables secure and scalable admin onboarding and authorization across various regions and towns in Zimbabwe.

### Implementation Date

April 30, 2026

### Completed Components

#### 1. Database Schema

**File:** `backend/app/models/admin.py`

**Models Created:**

- **AdminUser** - Enhanced admin user model with:
  - Hierarchical roles (superadmin, regional, provincial, district)
  - Location assignments
  - MFA settings (TOTP secret, backup codes)
  - Session tracking (last login, failed attempts, lockout)
  - Audit trail relationships
  - Delegation relationships (delegator and delegate)

- **AdminLocation** - Location hierarchy model:
  - Types: national, province, district, town
  - Parent-child relationships for hierarchy
  - Level system (1=national, 2=province, 3=district, 4=town)
  - Active/inactive status

- **AdminPermission** - Permission management:
  - Scoped permissions by resource type
  - Location-based scoping (all, location, self)
  - Expiration support for temporary grants
  - Grant tracking (who granted, when)

- **AdminAuditLog** - Comprehensive audit logging:
  - All admin actions logged
  - Before/after values for changes
  - IP address and user agent tracking
  - Success/failure status
  - Location context

- **AdminDelegation** - Temporary permission delegation:
  - Delegator and delegate relationships
  - Permission key specification
  - Expiration time (max 7 days)
  - Revocation tracking
  - Reason documentation

**Migration:** `backend/alembic/versions/0013_admin_hierarchy_and_permissions.py`
- Drops and recreates admin_users table with new schema
- Creates all new tables with proper relationships
- Seeds default Zimbabwe provinces and key districts

#### 2. Backend API Endpoints

**File:** `backend/app/api/v1/endpoints/admin/admin_management.py`

**Endpoints Implemented:**

##### Location Management
- `GET /admin/admin-management/locations` - List all locations with filtering
- `POST /admin/admin-management/locations` - Create new location

##### Admin Management
- `POST /admin/admin-management/create` - Create new admin with temporary password
- `POST /admin/admin-management/invite` - Invite admin with auto-generated credentials
- `GET /admin/admin-management/list` - List admins with filtering (role, location, status)
- `GET /admin/admin-management/{admin_id}` - Get detailed admin information
- `PATCH /admin/admin-management/{admin_id}/status` - Activate/deactivate admin
- `DELETE /admin/admin-management/{admin_id}` - Soft delete admin

##### Permission Management
- `POST /admin/admin-management/permissions/grant` - Grant permission to admin
- `POST /admin/admin-management/permissions/revoke` - Revoke permission from admin
- `GET /admin/admin-management/{admin_id}/permissions` - List admin permissions

##### Delegation Management
- `POST /admin/admin-management/delegations/create` - Create temporary delegation
- `POST /admin/admin-management/delegations/{delegation_id}/revoke` - Revoke delegation
- `GET /admin/admin-management/delegations` - List delegations with filtering

##### Audit Logs
- `GET /admin/admin-management/audit-logs` - List audit logs with filtering

#### 3. Location-Based Access Control

**File:** `backend/app/core/location_access.py`

**Class:** `LocationAccessControl`

**Features:**
- Hierarchical location access based on admin role
- Superadmins have access to all locations
- Regional admins access their region and sub-locations
- Provincial admins access their province and sub-locations
- District admins access only their district
- Permission checking with role-based defaults
- Resource filtering by location
- Admin action audit logging

**FastAPI Dependencies:**
- `require_location_access()` - Enforce location-based access
- `require_permission()` - Enforce permission-based access

**Role-Based Default Permissions:**
- Superadmin: Full system access
- Regional: Admin management, location editing, user management, dispute resolution
- Provincial: Admin view/edit, location view, user view/edit, transaction view
- District: Admin view, location view, permission view, user view, transaction view

#### 4. Frontend Components

##### Admin Login Screen Update

**File:** `apps/web/admin-dashboard/src/components/AdminLoginScreen.jsx`

**Changes:**
- Stores location information in localStorage after successful login
- Stores admin role and level in user context
- Passes location context to dashboard

##### Admin Management UI

**File:** `apps/web/admin-dashboard/src/components/AdminManagement.jsx`

**Features:**
- Tab-based interface with 5 tabs:
  1. **Administrators** - List, create, invite, activate/deactivate admins
  2. **Locations** - View and manage location hierarchy
  3. **Permissions** - View and manage admin permissions
  4. **Audit Logs** - View comprehensive audit trail
  5. **Delegations** - Create and manage temporary permission delegations

**Modals:**
- Create Admin Modal - Full admin creation form
- Invite Admin Modal - Simplified invitation form
- Create Location Modal - Add new locations
- Create Delegation Modal - Grant temporary permissions

**Dashboard Integration:**
- Added to admin sidebar navigation
- Accessible via "Admin Management" menu item
- Integrated into main content area

#### 5. Default Data Seeding

**Zimbabwe Provinces Seeded:**
- Zimbabwe - National (Level 1)
- Mashonaland East (Level 2)
- Mashonaland West (Level 2)
- Mashonaland Central (Level 2)
- Matabeleland North (Level 2)
- Matabeleland South (Level 2)
- Midlands (Level 2)
- Masvingo (Level 2)
- Manicaland (Level 2)
- Bulawayo (Level 2)
- Harare (Level 2)

**Key Districts Seeded:**
- Harare Central, Harare South
- Bulawayo Central, Bulawayo South
- Mutare, Gweru, Masvingo

### Security Features

#### Authentication Flow
1. Phone + password credentials
2. OTP verification (SMS/WhatsApp)
3. MFA/TOTP verification (Google Authenticator, Authy)
4. Forced password change on first login
5. CAPTCHA after 3 failed attempts
6. Account lockout after excessive failures

#### Authorization
- Role-based access control (RBAC)
- Location-based access control (LBAC)
- Permission scoping (all, location, self)
- Temporary permission grants with expiration
- Delegation system for temporary elevated access
- Comprehensive audit logging of all actions

#### Password Policy
- Minimum 12 characters
- Uppercase and lowercase letters
- At least one digit
- At least one special character
- Forced change on first login
- Temporary credentials for new admins

#### MFA Requirements
- TOTP authenticator app required for all admins
- Backup codes provided on setup
- MFA enforcement for all admin actions
- Device ID tracking for session management

### Testing Instructions

#### Prerequisites
1. Run database migration: `alembic upgrade head`
2. Ensure backend is running on `http://localhost:8080`
3. Ensure admin dashboard is running

#### Test 1: Create Superadmin
```bash
curl -X POST http://localhost:8080/api/v1/admin/admin-management/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <superadmin_token>" \
  -d '{
    "username": "superadmin",
    "email": "superadmin@ZimAgritrust.co.zw",
    "phone_number": "+263771234567",
    "full_name": "Super Administrator",
    "role": "superadmin",
    "location_id": null
  }'
```

#### Test 2: Create Regional Admin
```bash
curl -X POST http://localhost:8080/api/v1/admin/admin-management/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <superadmin_token>" \
  -d '{
    "username": "regional_harare",
    "email": "regional.harare@ZimAgritrust.co.zw",
    "phone_number": "+263772345678",
    "full_name": "Harare Regional Admin",
    "role": "regional",
    "location_id": 12
  }'
```

#### Test 3: Invite District Admin
```bash
curl -X POST http://localhost:8080/api/v1/admin/admin-management/invite \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <superadmin_token>" \
  -d '{
    "email": "district.mutare@ZimAgritrust.co.zw",
    "phone_number": "+263773456789",
    "full_name": "Mutare District Admin",
    "role": "district",
    "location_id": 15
  }'
```

#### Test 4: Login Flow
1. Navigate to admin portal: `http://localhost:5173/?portal=hq`
2. Enter phone number and temporary password
3. Verify OTP sent to phone
4. Set up MFA with authenticator app
5. Save backup codes
6. Change password to permanent password
7. Access dashboard

#### Test 5: Location-Based Access
1. Log in as regional admin (Harare)
2. Verify access to Harare and sub-locations
3. Attempt to access Bulawayo data (should be denied)
4. Log in as superadmin
5. Verify access to all locations

#### Test 6: Permission Delegation
1. Log in as superadmin
2. Navigate to Admin Management > Delegations
3. Create delegation to regional admin for "admin.create"
4. Set expiration to 24 hours
5. Log in as regional admin
6. Verify ability to create new admins
7. Revoke delegation
8. Verify permission revoked

#### Test 7: Audit Logs
1. Perform various admin actions
2. Navigate to Admin Management > Audit Logs
3. Verify all actions are logged
4. Check timestamps, IP addresses, and action details
5. Verify success/failure status

### File Structure

#### Backend
```
backend/
├── alembic/versions/
│   └── 0013_admin_hierarchy_and_permissions.py
├── app/
│   ├── api/v1/endpoints/admin/
│   │   ├── __init__.py (updated)
│   │   └── admin_management.py (new)
│   ├── core/
│   │   └── location_access.py (new)
│   └── models/
│       ├── __init__.py (updated)
│       └── admin.py (updated)
```

#### Frontend
```
apps/web/admin-dashboard/src/
├── components/
│   ├── AdminLoginScreen.jsx (updated)
│   └── AdminManagement.jsx (new)
└── App.jsx (updated)
```

### Deployment Checklist

- [ ] Run database migration: `alembic upgrade head`
- [ ] Verify admin_users table has new schema
- [ ] Verify admin_locations, admin_permissions, admin_audit_logs, admin_delegations tables exist
- [ ] Test admin creation API endpoint
- [ ] Test admin invitation API endpoint
- [ ] Test login flow with MFA
- [ ] Test location-based access control
- [ ] Test permission delegation
- [ ] Verify audit logging works
- [ ] Test Admin Management UI in dashboard
- [ ] Verify role-based permissions work correctly
- [ ] Test account lockout after failed attempts
- [ ] Verify CAPTCHA appears after 3 failures
- [ ] Test password change on first login

### Notes

#### Temporary Credentials
- When creating or inviting admins, temporary passwords are generated
- These passwords are shown once in the API response
- Must be sent to the admin via secure channel
- Admin must change password on first login

#### Location Hierarchy
- National (Level 1) → Province (Level 2) → District (Level 3) → Town (Level 4)
- Higher-level admins can access lower-level locations
- Lower-level admins cannot access higher-level locations
- Superadmins bypass location restrictions

#### Delegation Limits
- Maximum delegation duration: 168 hours (7 days)
- Delegations can be revoked at any time
- Delegations are logged in audit trail
- Only admins with a permission can delegate it

#### Audit Log Retention
- All admin actions are logged
- Logs include before/after values for changes
- IP address and user agent are captured
- Logs are filterable by admin, action, resource type

---

## Quality Standards

### Testing

- Write unit tests for all new features
- Write integration tests for API endpoints
- Test edge cases and error conditions
- Ensure test coverage above 80%
- Run tests before committing: `pytest tests/`

### Code Review

- All code must be reviewed before merging
- Ensure code follows project standards
- Verify no security vulnerabilities
- Check for performance issues
- Validate documentation is updated

### Documentation

- Update API_REFERENCE.md for new endpoints
- Update README.md for major features
- Add comments to complex code
- Maintain inline documentation
- Update migration guides for schema changes

### Security

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user inputs
- Sanitize all outputs
- Use parameterized queries
- Implement proper authentication and authorization

---

**Last Updated:** May 1, 2026
