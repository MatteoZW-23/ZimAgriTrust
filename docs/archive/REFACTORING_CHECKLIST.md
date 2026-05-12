# AgriTrust Refactoring Progress Checklist

## Phase 1: CRITICAL CONSOLIDATIONS (Weeks 1-2)

### ☐ 1.1 Agent Onboarding Service Consolidation
- **Target Files:**
  - ✅ Keep: `backend/app/services/agent_onboarding_service.py`
  - ❌ Remove: `backend/app/services/recruitment_service.py`
  - ❌ Remove: `backend/app/services/onboarding_service.py`

#### Sub-tasks:
- [ ] Audit all imports of recruitment_service.py across codebase
- [ ] Audit all imports of onboarding_service.py across codebase
- [ ] Update `backend/app/api/v1/endpoints/agents.py` to use agent_onboarding_service
- [ ] Update `backend/app/api/v1/endpoints/recruitment.py` to use agent_onboarding_service
- [ ] Update `backend/app/services/__init__.py` exports
- [ ] Write integration tests covering full agent pipeline
- [ ] Delete recruitment_service.py
- [ ] Delete onboarding_service.py
- [ ] Code review
- [ ] Deploy and monitor

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 4 hours  

---

### ☐ 1.2 Marketplace Logic Consolidation
- **Target Files:**
  - `backend/app/services/marketplace_service.py` (remove module-level duplicates)
  - `backend/app/services/transaction_service.py` (delegate to marketplace)

#### Sub-tasks:
- [ ] Document all current callers of duplicate functions
- [ ] Create MarketplaceService class methods for all operations
- [ ] Verify MarketplaceService has no duplicate methods
- [ ] Update transaction_service.py to delegate calls
- [ ] Update all endpoints (listings.py, offers.py, market.py, trades.py)
- [ ] Remove module-level functions from marketplace_service.py
- [ ] Write comprehensive unit tests
- [ ] Integration tests for marketplace flow
- [ ] Code review
- [ ] Deploy and monitor

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 6 hours  

---

### ☐ 1.3 Frontend API Client Consolidation
- **Create:**
  - `packages/shared/src/api/client.js` (shared request handler)
  - `packages/shared/src/api/endpoints/auth.js`
  - `packages/shared/src/api/endpoints/marketplace.js`
  - `packages/shared/src/api/endpoints/wallet.js`
  - `packages/shared/src/api/index.js`

- **Delete:**
  - ❌ `apps/admin-dashboard/src/api.js`
  - ❌ `apps/agent-portal/src/api.js`
  - ❌ `apps/app-portal/src/api.js`

#### Sub-tasks:
- [ ] Create shared/api/client.js with request() function
- [ ] Create shared/api/endpoints/auth.js with all auth functions
- [ ] Create shared/api/endpoints/marketplace.js with marketplace functions
- [ ] Create shared/api/endpoints/wallet.js with wallet functions
- [ ] Update packages/shared/package.json exports
- [ ] Update admin-dashboard to import from shared
- [ ] Update agent-portal to import from shared
- [ ] Update app-portal to import from shared
- [ ] Test all 3 apps work correctly
- [ ] Delete duplicate api.js files
- [ ] Code review
- [ ] Deploy to beta
- [ ] Deploy to production

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 8 hours  

---

### ☐ 1.4 Move Route Guards to Shared Package
- **Create:**
  - `packages/shared/src/components/ProtectedRoute.jsx`
  - `packages/shared/src/components/AdminRoute.jsx`
  - `packages/shared/src/components/AgentRoute.jsx`
  - `packages/shared/src/components/FarmerRoute.jsx`
  - `packages/shared/src/components/BuyerRoute.jsx`
  - `packages/shared/src/components/index.js`

- **Delete:**
  - ❌ `apps/admin-dashboard/src/utils/routeGuard.jsx`
  - ❌ `apps/agent-portal/src/utils/routeGuard.jsx`
  - ❌ `apps/app-portal/src/utils/routeGuard.jsx`

#### Sub-tasks:
- [ ] Create shared/components/ProtectedRoute.jsx
- [ ] Create role-specific route components
- [ ] Update packages/shared/package.json exports
- [ ] Update admin-dashboard App.jsx to import from shared
- [ ] Update agent-portal App.jsx to import from shared
- [ ] Update app-portal App.jsx to import from shared
- [ ] Test session timeout logic in all 3 apps
- [ ] Delete duplicate routeGuard.jsx files
- [ ] Code review
- [ ] Deploy

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 4 hours  

---

### ☐ 1.5 Extract Data Transfer Utilities
- **Create:**
  - `packages/shared/src/utils/dataTransfer.js`
  - `packages/shared/src/utils/index.js`

#### Sub-tasks:
- [ ] Move dataTransfer.js to packages/shared/src/utils/
- [ ] Enhance with better error handling
- [ ] Add progress callbacks
- [ ] Update packages/shared/package.json exports
- [ ] Update admin-dashboard to import from shared
- [ ] Test export/import in admin-dashboard
- [ ] Make available to other portals if needed
- [ ] Code review
- [ ] Deploy

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 3 hours  

---

## Phase 2: STRUCTURAL IMPROVEMENTS (Weeks 3-4)

### ☐ 2.1 Refactor User Model
- **Create:**
  - `backend/app/models/user_verification.py`
  - `backend/app/models/user_wallet.py`
  - `backend/app/models/user_risk_profile.py`
  - `backend/app/models/user_preferences.py`

- **Update:**
  - `backend/app/models/user.py` (remove fields, keep core identity)
  - `backend/app/db/base.py` (export new models)
  - `backend/alembic/versions/` (add migration)

#### Sub-tasks:
- [ ] Design new model schemas
- [ ] Create new model files
- [ ] Create Alembic migration script
- [ ] Test migration on staging database
- [ ] Create data migration script
- [ ] Update all schemas (50+ files)
- [ ] Update all services (50+ files)
- [ ] Update all endpoints (30+ files)
- [ ] Test all user flows
- [ ] Code review
- [ ] Deploy with migration
- [ ] Monitor for issues

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 40 hours  
**Risk Level:** 🔴 VERY HIGH

---

### ☐ 2.2 Refactor Monolithic Frontend Apps
- **For each app** (admin-dashboard, agent-portal, app-portal):
  - Extract Layout component
  - Extract Auth context
  - Extract Theme context
  - Move components to dedicated files
  - Create view router

#### Admin Dashboard Sub-tasks:
- [ ] Create src/contexts/AuthContext.jsx
- [ ] Create src/contexts/ThemeContext.jsx
- [ ] Create src/components/Layout/ with Sidebar, Header, Layout
- [ ] Create src/views/ with OverviewView, UsersView, etc.
- [ ] Create src/views/ViewRouter.jsx
- [ ] Refactor src/App.jsx to 50 lines
- [ ] Test all views work
- [ ] Code review
- [ ] Deploy to beta
- [ ] User acceptance testing
- [ ] Deploy to production

#### Agent Portal Sub-tasks:
- [ ] Repeat refactoring process
- [ ] Test all agent flows
- [ ] Code review
- [ ] Deploy

#### App Portal Sub-tasks:
- [ ] Repeat refactoring process
- [ ] Test farmer and buyer flows
- [ ] Code review
- [ ] Deploy

**Status:** ⏳ Not Started  
**Owner:** [ Names ]  
**Est. Time:** 90 hours (30 per app)  
**Risk Level:** 🟠 HIGH

---

### ☐ 2.3 Event-Driven Architecture
- **Create:**
  - `backend/app/core/events.py` (Event enum, EventBus class)
  - `backend/app/services/event_handlers/` (directory)
  - `backend/app/services/event_handlers/notification_handlers.py`
  - `backend/app/services/event_handlers/analytics_handlers.py`

#### Sub-tasks:
- [ ] Design event system
- [ ] Create Event enum with all events
- [ ] Create EventBus class
- [ ] Register notification handlers
- [ ] Register analytics handlers
- [ ] Update marketplace_service to publish events
- [ ] Update payment_service to publish events
- [ ] Update dispute_service to publish events
- [ ] Remove direct WhatsApp calls from business logic
- [ ] Remove direct SMS calls from business logic
- [ ] Test notification delivery still works
- [ ] Add event logging
- [ ] Code review
- [ ] Deploy with feature flag
- [ ] Monitor event delivery
- [ ] Disable old notification methods

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 20 hours  
**Risk Level:** 🟠 HIGH

---

## Phase 3: OPTIMIZATION (Weeks 5-6)

### ☐ 3.1 Split Listing Model
- **Create:**
  - `backend/app/models/listing_product.py`
  - `backend/app/models/listing_location.py`
  - `backend/app/models/listing_pricing.py`
  - `backend/app/models/listing_verification.py`
  - `backend/app/models/listing_media.py`

#### Sub-tasks:
- [ ] Design listing model hierarchy
- [ ] Create new model files
- [ ] Create migration script
- [ ] Test migration
- [ ] Update schemas
- [ ] Update services
- [ ] Update endpoints
- [ ] Test all listing flows
- [ ] Code review
- [ ] Deploy

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 25 hours  
**Risk Level:** 🟠 HIGH

---

### ☐ 3.2 Split Whatsapp Endpoint
- **Create:**
  - `backend/app/api/v1/endpoints/whatsapp/`
  - `backend/app/api/v1/endpoints/whatsapp/__init__.py`
  - `backend/app/api/v1/endpoints/whatsapp/webhooks.py`
  - `backend/app/api/v1/endpoints/whatsapp/alerts.py`
  - `backend/app/api/v1/endpoints/whatsapp/messaging.py`
  - `backend/app/api/v1/endpoints/whatsapp/payments.py`
  - `backend/app/api/v1/endpoints/whatsapp/analytics.py`
  - `backend/app/api/v1/endpoints/whatsapp/interactive.py`

#### Sub-tasks:
- [ ] Create whatsapp/ directory structure
- [ ] Split whatsapp.py into domain files
- [ ] Update router registrations
- [ ] Update imports in router
- [ ] Test all WhatsApp endpoints still work
- [ ] Code review
- [ ] Deploy

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 8 hours  
**Risk Level:** 🟢 LOW

---

### ☐ 3.3 Repository Pattern
- **Create:**
  - `backend/app/services/repositories/` (directory)
  - `backend/app/services/repositories/user_repository.py`
  - `backend/app/services/repositories/listing_repository.py`
  - `backend/app/services/repositories/order_repository.py`
  - `backend/app/services/repositories/base_repository.py`

#### Sub-tasks:
- [ ] Design repository interfaces
- [ ] Create base repository
- [ ] Create specialized repositories
- [ ] Update endpoints to use repositories
- [ ] Remove direct db.query() calls
- [ ] Add repository unit tests
- [ ] Integration tests
- [ ] Code review
- [ ] Deploy

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 40 hours  
**Risk Level:** 🟠 HIGH

---

### ☐ 3.4 Configuration Centralization
- **Update:**
  - `backend/app/core/config.py`
  - `backend/app/core/constants.py`
  - Create `frontend/src/config.ts`
  - Create `frontend/src/constants.ts`

#### Sub-tasks:
- [ ] Consolidate all backend config
- [ ] Remove scattered config files
- [ ] Create frontend config file
- [ ] Update all imports
- [ ] Test all services find config
- [ ] Code review
- [ ] Deploy

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  
**Est. Time:** 10 hours  
**Risk Level:** 🟢 LOW

---

## Phase 4: SHARED PACKAGE POPULATION (Ongoing)

### ☐ 4.1 Common Components Library
- [ ] Create Button.jsx
- [ ] Create Modal.jsx
- [ ] Create Card.jsx
- [ ] Create DataTable.jsx
- [ ] Create Form components (Input, Select, DatePicker, Checkbox)
- [ ] Create Layout components (Container, Grid)
- [ ] Export from packages/shared
- [ ] Document component usage
- [ ] Add Storybook stories

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  

---

### ☐ 4.2 Custom Hooks
- [ ] Create useApi.js
- [ ] Create useAuth.js
- [ ] Create useNotification.js
- [ ] Create useForm.js
- [ ] Create useLocalStorage.js
- [ ] Write hook tests
- [ ] Document hook APIs

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  

---

### ☐ 4.3 Utilities Library
- [ ] Create validation.js
- [ ] Create formatting.js
- [ ] Create errors.js
- [ ] Create storage.js
- [ ] Write utility tests
- [ ] Document utility functions

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  

---

### ☐ 4.4 Constants Library
- [ ] Create roles.js
- [ ] Create statuses.js
- [ ] Create provinces.js
- [ ] Create currencies.js
- [ ] Document constants

**Status:** ⏳ Not Started  
**Owner:** [ Name ]  

---

## Metrics Tracking

### Baseline (Before Refactoring)
- Backend services: 52
- API client files: 3
- Duplicated API code: ~300 LOC
- User model size: 186 lines
- App.jsx size: 1000+ lines each
- Test coverage: 20%
- Bundle size: ~500KB
- Code duplication ratio: ~15%

### Current Progress
| Metric | Baseline | Target | Current | % Complete |
|--------|----------|--------|---------|-----------|
| Backend services | 52 | 20 | ? | ?% |
| API client files | 3 | 1 | ? | ?% |
| Duplicated code | 2500 LOC | 100 LOC | ? | ?% |
| User model LOC | 186 | 50 | ? | ?% |
| App.jsx LOC (avg) | 1000 | 50 | ? | ?% |
| Test coverage | 20% | 70% | ? | ?% |
| Bundle size | 500KB | 300KB | ? | ?% |

---

## Sign-off Tracker

### Phase 1 Sign-offs
- [ ] Agent Onboarding Consolidation - Dev: [ ] QA: [ ] PM: [ ] 
- [ ] Marketplace Logic Consolidation - Dev: [ ] QA: [ ] PM: [ ]
- [ ] Frontend API Client - Dev: [ ] QA: [ ] PM: [ ]
- [ ] Route Guards - Dev: [ ] QA: [ ] PM: [ ]
- [ ] Data Utils - Dev: [ ] QA: [ ] PM: [ ]

### Phase 2 Sign-offs
- [ ] User Model Refactor - Dev: [ ] QA: [ ] PM: [ ]
- [ ] Frontend App Refactor - Dev: [ ] QA: [ ] PM: [ ]
- [ ] Event Architecture - Dev: [ ] QA: [ ] PM: [ ]

### Phase 3 Sign-offs
- [ ] Listing Model Split - Dev: [ ] QA: [ ] PM: [ ]
- [ ] Whatsapp Endpoints - Dev: [ ] QA: [ ] PM: [ ]
- [ ] Repository Pattern - Dev: [ ] QA: [ ] PM: [ ]
- [ ] Config Centralization - Dev: [ ] QA: [ ] PM: [ ]

---

## Issues & Blockers

### Ongoing Issues
| Issue | Status | Resolution | Owner | Due |
|-------|--------|-----------|-------|-----|
| ? | ⏳ Open | | | |

### Resolved Issues
| Issue | Status | Resolution | Owner | Date |
|-------|--------|-----------|-------|------|
| | ✅ Resolved | | | |

---

## Notes & Decisions

**Week 1:** [Add notes here]

**Week 2:** [Add notes here]

...

---

**Last Updated:** [Date]  
**Next Review:** [Date]  
**Prepared by:** [Name]
