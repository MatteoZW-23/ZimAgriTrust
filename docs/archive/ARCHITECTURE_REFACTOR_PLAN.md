# Agritrust Architecture Refactor Plan

## Overview
This document outlines the refactoring of the Agritrust system into a modular multi-app architecture while preserving all existing functionality.

## Current Architecture Issues
1. Docker-compose misconfigured (agent-dashboard points to admin-dashboard)
2. Duplicate/conflicting directories (apps/web vs apps/admin-dashboard)
3. No shared packages for types and API clients
4. Missing services in docker-compose (agent-portal, public-website, unified-app)
5. Inconsistent port allocation

## Target Architecture

### Application Structure
```
apps/
├── admin-dashboard/          # Admin web application (port 3001)
├── agent-portal/             # Agent web application (port 3002)
├── public-website/           # Public-facing website (port 3000)
├── unified-mobile/           # Unified mobile app (farmer/buyer/driver)
├── whatsapp-bridge/          # WhatsApp integration service
├── ussd-simulator/           # USSD testing tool
└── iot-gateway/              # IoT device gateway

packages/
├── shared/                   # Shared types, utilities, API clients
└── ui/                       # Shared UI components (optional)

backend/                      # Single backend API (port 8080)
```

### Routing Strategy
```
/ (port 3000)              → Public website
/admin (port 3001)         → Admin dashboard
/agent (port 3002)         → Agent portal
/dashboard (port 3003)     → Farmer/Buyer web portal
mobile app                 → Unified mobile app (farmer/buyer/driver)
```

### Role-Based Access Control
- **Backend**: Authoritative RBAC enforcement
- **Frontend**: Guarded navigation based on user role
- **Roles**: farmer, buyer, driver, agent, admin

## Implementation Steps

### Phase 1: Shared Infrastructure
1. Create `packages/shared` with:
   - TypeScript type definitions
   - API client utilities
   - Shared constants
   - Authentication helpers

2. Create `packages/ui` (optional) with:
   - Reusable components
   - Theme definitions
   - Common layouts

### Phase 2: Application Cleanup
1. Remove duplicate directories:
   - Remove `apps/web` (content moved to respective apps)
   - Consolidate `apps/public-marketplace` into `apps/public-website`
   - Remove empty directories (`apps/driver-app`, `apps/mobile`)

2. Rename for clarity:
   - `apps/unified-app` → `apps/unified-mobile`

### Phase 3: Application Configuration
1. **Admin Dashboard** (port 3001)
   - Ensure standalone deployment
   - Add RBAC enforcement
   - Configure routing

2. **Agent Portal** (port 3002)
   - Ensure standalone deployment
   - Add RBAC enforcement
   - Configure routing

3. **Public Website** (port 3000)
   - Enhance as primary entry point
   - Add authentication flow
   - Route to appropriate dashboards

4. **Unified Mobile** (farmer/buyer/driver)
   - Enhance role-based rendering
   - Add driver-specific features
   - Ensure all flows work

### Phase 4: Docker Compose Update
1. Update service definitions
2. Fix port allocations
3. Add environment variables
4. Configure networking

### Phase 5: RBAC Configuration
1. Backend permissions (already exists)
2. Frontend route guards
3. API client integration
4. Role-based UI rendering

## Port Allocation
- Public Website: 3000
- Admin Dashboard: 3001
- Agent Portal: 3002
- Farmer/Buyer Portal: 3003 (app-portal)
- Backend API: 8080
- USSD Simulator: 5000
- IoT Gateway: 3005
- WhatsApp Bridge: 3006

## Non-Breaking Constraints
- All existing features must remain unchanged
- Database schema unchanged
- API endpoints unchanged
- Incremental migration approach
