# AgriTrust Refactoring Roadmap

## Phase 1: CRITICAL CONSOLIDATIONS (Weeks 1-2)

### 1.1 Agent Onboarding Service Consolidation

**Goal:** Single source of truth for agent recruitment → training → deployment

**Current State:**
- `recruitment_service.py` - Application submission and doc verification
- `onboarding_service.py` - Contract signing and quizzes
- `agent_onboarding_service.py` - Unified (but others still exist)

**Actions:**
1. Keep `agent_onboarding_service.py` as the canonical service
2. Migrate all endpoints from `recruitment_service.py` to use `agent_onboarding_service.py`
3. Migrate all endpoints from `onboarding_service.py` to use `agent_onboarding_service.py`
4. Audit all service imports across codebase
5. Delete `recruitment_service.py`
6. Delete `onboarding_service.py`
7. Create integration tests covering full pipeline

**Files to Update:**
- `backend/app/api/v1/endpoints/agents.py` - Import from agent_onboarding_service only
- `backend/app/api/v1/endpoints/recruitment.py` - Import from agent_onboarding_service only
- `backend/app/services/__init__.py` - Update imports

**Estimated Effort:** 4 hours
**Risk:** Medium (ensure no endpoints depend on removed services)

---

### 1.2 Marketplace Logic Consolidation

**Goal:** Single service for all marketplace operations

**Current State:**
- `marketplace_service.py` - Both module-level functions AND class methods (DUPLICATES)
- `transaction_service.py` - Duplicate functions for create_listing, create_offer, etc.

**Actions:**
1. Audit all imports of both services
2. Keep only class methods in `MarketplaceService`
3. Remove module-level duplicate functions from `marketplace_service.py`
4. Update `transaction_service.py` to delegate to `MarketplaceService`
5. Update all endpoints to use `MarketplaceService` class methods
6. Add comprehensive unit tests

**Files to Update:**
- `backend/app/services/marketplace_service.py` - Remove module-level functions
- `backend/app/services/transaction_service.py` - Delegate to MarketplaceService
- `backend/app/api/v1/endpoints/listings.py` - Use MarketplaceService
- `backend/app/api/v1/endpoints/offers.py` - Use MarketplaceService
- `backend/app/api/v1/endpoints/market.py` - Use MarketplaceService

**Estimated Effort:** 6 hours
**Risk:** High (marketplace is business-critical)

---

### 1.3 Frontend API Client Consolidation

**Goal:** Single shared API client, used by all 3 portals

**Current State:**
- Three identical `api.js` files with 80% duplication

**Actions:**

1. Create `packages/shared/src/api/client.js`:
```javascript
// Shared HTTP request handler
export async function request(path, options = {}) {
  const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
  // ... implementation
}

// Shared endpoint factories by role
export const createAuthApi = () => ({ login, register, logout, ... })
export const createMarketplaceApi = () => ({ createListing, getListings, ... })
export const createWalletApi = () => ({ getBalance, getTransactions, ... })
```

2. Create `packages/shared/src/api/index.js`:
```javascript
export { request } from './client.js'
export { createAuthApi, createMarketplaceApi, ... } from './endpoints/index.js'
```

3. Update portals to import from shared:
```javascript
// Before
import { login, createListing } from '../api.js'

// After
import { createAuthApi, createMarketplaceApi } from '@agritrust/shared/api'
```

4. Delete duplicate files:
- `apps/admin-dashboard/src/api.js`
- `apps/agent-portal/src/api.js`
- `apps/app-portal/src/api.js`

**Files to Create:**
- `packages/shared/src/api/client.js`
- `packages/shared/src/api/endpoints/auth.js`
- `packages/shared/src/api/endpoints/marketplace.js`
- `packages/shared/src/api/endpoints/wallet.js`
- `packages/shared/src/api/endpoints/index.js`
- `packages/shared/src/api/index.js`

**Files to Update:**
- `apps/admin-dashboard/src/api.js` → Remove, import from shared
- `apps/agent-portal/src/api.js` → Remove, import from shared
- `apps/app-portal/src/api.js` → Remove, import from shared
- All component files using api.js

**Estimated Effort:** 8 hours
**Risk:** High (all portals depend on API client)

---

### 1.4 Move Frontend Route Guards to Shared

**Goal:** Centralized, reusable route protection logic

**Current State:**
- `apps/admin-dashboard/src/utils/routeGuard.jsx`
- `apps/agent-portal/src/utils/routeGuard.jsx`
- `apps/app-portal/src/utils/routeGuard.jsx`
- ~90% duplicate code

**Actions:**
1. Create `packages/shared/src/components/ProtectedRoute.jsx`:
```javascript
export function ProtectedRoute({ 
  children, 
  allowedRoles = [],
  sessionTimeout = 30 * 60 * 1000 
}) {
  // Shared logic with configurable timeout
}
```

2. Create role-specific route components:
```javascript
export function AdminRoute({ children }) { /* ... */ }
export function AgentRoute({ children }) { /* ... */ }
export function FarmerRoute({ children }) { /* ... */ }
export function BuyerRoute({ children }) { /* ... */ }
```

3. Update all portals:
```javascript
// Before
import { AdminRoute } from '../utils/routeGuard.jsx'

// After
import { AdminRoute } from '@agritrust/shared/components'
```

4. Delete duplicate files:
- `apps/admin-dashboard/src/utils/routeGuard.jsx`
- `apps/agent-portal/src/utils/routeGuard.jsx`
- `apps/app-portal/src/utils/routeGuard.jsx`

**Files to Create:**
- `packages/shared/src/components/ProtectedRoute.jsx`
- `packages/shared/src/components/RoleRoute.jsx`
- `packages/shared/src/components/index.js`

**Files to Update:**
- `packages/shared/package.json` - Export components
- All App.jsx files - Use shared route guards

**Estimated Effort:** 4 hours
**Risk:** Medium (session timeout logic needs careful testing)

---

### 1.5 Extract Frontend Data Utilities

**Goal:** Shared import/export functionality

**Current State:**
- Only `apps/admin-dashboard/src/utils/dataTransfer.js` has it
- Other portals don't have this functionality

**Actions:**
1. Move to `packages/shared/src/utils/dataTransfer.js`
2. Enhance with:
   - Better error handling
   - Progress callbacks for large files
   - Multiple format support (CSV, JSON, XLSX)
   - Validation schemas

3. Use in all portals

**Files to Create:**
- `packages/shared/src/utils/dataTransfer.js`
- `packages/shared/src/utils/validation.js`
- `packages/shared/src/utils/index.js`

**Files to Update:**
- `apps/admin-dashboard/src/utils/dataTransfer.js` → Import from shared

**Estimated Effort:** 3 hours

---

## Phase 2: STRUCTURAL IMPROVEMENTS (Weeks 3-4)

### 2.1 Refactor User Model

**Goal:** Split God object into focused models

**Current State:**
- Single `User` model with 186 lines handling all concerns

**New Structure:**
```
User (Core)
├── id, phone_number, full_name, email, password_hash, role, created_at

UserVerification (KYC)
├── user_id, national_id, id_document_url, id_verified, id_verified_at, 
    id_verification_notes, phone_verified, email_verified, location_verified

UserWallet (Financial)
├── user_id, wallet_balance, pending_earnings, blocked_balance

UserRiskProfile (Risk)
├── user_id, risk_score, trust_score, last_risk_review_date, 
    fraud_flags, dispute_count

UserPreferences (Settings)
├── user_id, language, currency, notification_preference_global,
    subscription_tier, plan_dates, profile_image_url, bio
```

**Migration Plan:**
1. Create new models in `backend/app/models/`
2. Create Alembic migration script
3. Data migration script
4. Update all queries to use new models
5. Update schemas/responses
6. Test thoroughly

**Files to Create:**
- `backend/app/models/user_verification.py`
- `backend/app/models/user_wallet.py`
- `backend/app/models/user_risk_profile.py`
- `backend/app/models/user_preferences.py`
- `backend/alembic/versions/split_user_model.py`

**Files to Update:**
- `backend/app/models/user.py` - Remove fields moved to other tables
- All schemas
- All services (50+ files)
- All endpoints (30+ files)

**Estimated Effort:** 40 hours
**Risk:** Very High (core model change, affects everything)

---

### 2.2 Refactor Monolithic Frontend App Components

**Goal:** Split 1000+ line App.jsx into focused components

**Current: admin-dashboard/src/App.jsx (1000+ lines)**
```jsx
function App() {
  // Auth state
  const [token, setToken] = useState(...)
  const [profile, setProfile] = useState(...)
  
  // UI state
  const [currentView, setCurrentView] = useState('overview')
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [theme, setTheme] = useState('auto')
  const [language, setLanguage] = useState('EN')
  
  // Data loading
  const [loading, setLoading] = useState(false)
  
  // 50+ event handlers
  const handleLogin = async () => { ... }
  const handleLogout = () => { ... }
  const handleViewChange = () => { ... }
  
  // 50+ views
  return (
    <div>
      {!token && <StaffLoginScreen onLogin={handleLogin} />}
      {token && role !== 'admin' && <AccessDenied />}
      {token && (
        <>
          {/* Sidebar */}
          {/* Header */}
          {/* Views */}
          {currentView === 'overview' && <OverviewPanel />}
          {currentView === 'users' && <UserDirectoryPanel />}
          // ... 40+ more views
        </>
      )}
    </div>
  )
}
```

**Refactored Structure:**
```
src/
├── contexts/
│   ├── AuthContext.jsx       // Auth state + methods
│   ├── ThemeContext.jsx      // Theme state + methods
│   └── NotificationContext.jsx
├── components/
│   ├── Layout/
│   │   ├── Sidebar.jsx
│   │   ├── Header.jsx
│   │   └── Layout.jsx
│   ├── Auth/
│   │   ├── LoginScreen.jsx
│   │   └── AccessDenied.jsx
│   └── Panels/
│       ├── OverviewPanel.jsx (move from src/components/)
│       ├── UserDirectoryPanel.jsx
│       └── ... (moved from inline)
├── hooks/
│   ├── useAuth.js
│   ├── useApi.js
│   └── useNotification.js
├── views/
│   ├── OverviewView.jsx
│   ├── UsersView.jsx
│   └── ViewRouter.jsx
└── App.jsx (50 lines, just routes)
```

**New App.jsx:**
```jsx
export default function App() {
  const { token, profile } = useAuth()
  
  if (!token) return <LoginScreen />
  if (profile?.role !== 'admin') return <AccessDenied />
  
  return (
    <Layout>
      <ViewRouter />
    </Layout>
  )
}
```

**Steps:**
1. Create AuthContext with all auth logic
2. Create ThemeContext
3. Extract Layout component
4. Move all panels from components/ to dedicated component files
5. Create ViewRouter
6. Refactor App.jsx to just use contexts and router
7. Repeat for agent-portal and app-portal

**Files to Create:**
- `src/contexts/AuthContext.jsx`
- `src/contexts/ThemeContext.jsx`
- `src/components/Layout/`
- `src/views/`
- `src/hooks/`

**Files to Update:**
- Hundreds of imports in components
- App.jsx
- main.jsx

**Estimated Effort:** 30 hours per app, 90 hours total
**Risk:** High (UI refactor, hard to test)

---

### 2.3 Event-Driven Architecture for Notifications

**Goal:** Decouple WhatsApp notifications from business logic

**Current Problem:**
```python
# backend/app/services/marketplace_service.py
async def accept_offer(...) -> Order:
    # ... business logic ...
    
    # Tightly coupled notification
    from app.services.whatsapp_service import WhatsAppService
    await WhatsAppService.send_whatsapp_message(buyer.phone_number, msg)
```

**New Pattern:**

1. Create event system:
```python
# backend/app/services/events.py
from enum import Enum
from typing import Any, Callable, Dict, List

class Event(str, Enum):
    OFFER_ACCEPTED = "offer.accepted"
    ORDER_CREATED = "order.created"
    PAYMENT_RECEIVED = "payment.received"
    DISPUTE_RAISED = "dispute.raised"

class EventBus:
    _listeners: Dict[Event, List[Callable]] = {}
    
    @classmethod
    def subscribe(cls, event: Event, handler: Callable):
        if event not in cls._listeners:
            cls._listeners[event] = []
        cls._listeners[event].append(handler)
    
    @classmethod
    async def publish(cls, event: Event, data: Any):
        if event in cls._listeners:
            for handler in cls._listeners[event]:
                await handler(data)
```

2. Register handlers:
```python
# backend/app/services/notification_dispatcher.py
from app.services.events import EventBus, Event

async def on_offer_accepted(data):
    from app.services.whatsapp_service import WhatsAppService
    await WhatsAppService.send_whatsapp_message(
        data['buyer_phone'],
        f"Offer accepted! Order: {data['order_id']}"
    )

# Register on startup
EventBus.subscribe(Event.OFFER_ACCEPTED, on_offer_accepted)
```

3. Publish events from business logic:
```python
# backend/app/services/marketplace_service.py
async def accept_offer(...) -> Order:
    # ... business logic ...
    
    # Just publish event, don't care about notifications
    await EventBus.publish(Event.OFFER_ACCEPTED, {
        'order_id': order.id,
        'buyer_phone': order.buyer.phone_number,
        'seller_phone': order.seller.phone_number,
    })
    
    return order
```

**Files to Create:**
- `backend/app/core/events.py`
- `backend/app/services/event_handlers/`
- `backend/app/services/event_handlers/notification_handlers.py`
- `backend/app/services/event_handlers/analytics_handlers.py`

**Files to Update:**
- All services (remove direct WhatsApp calls)
- `backend/app/main.py` (register handlers on startup)

**Estimated Effort:** 20 hours
**Risk:** Medium (needs comprehensive testing)

---

## Phase 3: OPTIMIZATION (Weeks 5-6)

### 3.1 Split Listing Model

**Current Issue:** Single model with too many concerns

**New Structure:**
```
Listing (Core)
├── id, seller_id, created_at, expires_at, status

ListingProduct (What's being sold)
├── listing_id, product_type, product_subtype, crop, quantity

ListingLocation (Where it is)
├── listing_id, location_province, location_district, pickup_address,
    latitude, longitude, is_location_verified

ListingPricing (How much)
├── listing_id, price_per_unit, currency, logistics_type

ListingVerification (Trust)
├── listing_id, verification_status, verified_by_agent, verification_completed_at

ListingMedia (Photos)
├── listing_id, photos (array)
```

**Estimated Effort:** 25 hours
**Risk:** High (core model change)

---

### 3.2 Split Whatsapp Endpoint

**Current:** `backend/app/api/v1/endpoints/whatsapp.py` (500+ lines, 30+ routes)

**New Structure:**
```
endpoints/whatsapp/
├── __init__.py
├── webhooks.py      (webhook handling, validation)
├── alerts.py        (price, weather, harvest alerts)
├── messaging.py     (broadcasts, group management)
├── payments.py      (payment initiation, receipts)
├── analytics.py     (engagement tracking)
└── interactive.py   (listings, locations)
```

**Estimated Effort:** 8 hours
**Risk:** Low (straightforward file splitting)

---

### 3.3 Repository Pattern

**Goal:** Abstract database access from business logic

**Current:**
```python
# endpoint/admin/users.py
db.query(User).filter(User.role == 'farmer').all()
```

**New:**
```python
# services/repositories/user_repository.py
class UserRepository:
    @staticmethod
    def find_by_role(db: Session, role: str) -> List[User]:
        return db.query(User).filter(User.role == role).all()

# endpoint/admin/users.py
from app.services.repositories import user_repository
users = user_repository.find_by_role(db, 'farmer')
```

**Estimated Effort:** 40 hours
**Risk:** Medium (large refactor, easier to test)

---

### 3.4 Configuration Centralization

**Goal:** Single source of truth for all configuration

**New Structure:**
```
backend/app/core/
├── config.py      (environment, database, api, feature flags)
├── constants.py   (business constants: trust scores, fees, etc.)
└── secrets.py     (API keys, credentials - from env only)

frontend/src/
├── config.ts      (API_URL, feature flags, theme defaults)
├── constants.ts   (roles, statuses, provinces)
└── .env.example   (template for .env.local)
```

**Estimated Effort:** 10 hours
**Risk:** Low

---

## Phase 4: SHARED PACKAGE POPULATION (Ongoing)

### Create Common Components Library

```
packages/shared/src/components/
├── Button.jsx
├── Modal.jsx
├── Card.jsx
├── DataTable.jsx
├── Form/
│   ├── Input.jsx
│   ├── Select.jsx
│   ├── DatePicker.jsx
│   └── Checkbox.jsx
├── Layout/
│   ├── Container.jsx
│   └── Grid.jsx
└── index.js
```

### Create Custom Hooks

```
packages/shared/src/hooks/
├── useApi.js        (API call handling, loading, error)
├── useAuth.js       (Authentication state)
├── useNotification.js (Toast, alerts)
├── useForm.js       (Form handling, validation)
├── useLocalStorage.js
└── index.js
```

### Create Utilities

```
packages/shared/src/utils/
├── validation.js    (Common validators)
├── formatting.js    (Date, currency, phone number formatting)
├── errors.js        (Error handling)
├── storage.js       (LocalStorage wrapper)
└── index.js
```

### Create Constants

```
packages/shared/src/constants/
├── roles.js         (ADMIN, AGENT, FARMER, BUYER)
├── statuses.js      (Order statuses, verification statuses, etc.)
├── provinces.js     (Zimbabwe provinces)
├── currencies.js    (USD, ZWL)
└── index.js
```

---

## Testing Strategy

### Phase 1 (Critical): Unit Tests
- Agent onboarding pipeline consolidation
- Marketplace logic consolidation
- API client consolidation

### Phase 2: Integration Tests
- Full user journey (signup → listing → order → delivery)
- Payment flow
- Dispute resolution

### Phase 3: E2E Tests
- Each portal's critical paths
- Cross-portal interactions

### Phase 4: Performance Tests
- API response times
- Bundle sizes
- Database query optimization

---

## Success Metrics

| Metric | Before | Target | Timeline |
|--------|--------|--------|----------|
| Backend Services | 52 | 20 | End of Phase 2 |
| API Client Files | 3 | 1 | End of Phase 1 |
| App.jsx LOC | 1000+ | 50 | End of Phase 2 |
| User Model Size | 186 lines | 50 lines | End of Phase 2 |
| Duplicated Code | 2,500 LOC | <100 | End of Phase 2 |
| Test Coverage | 20% | 70% | End of Phase 3 |
| Bundle Size | 500KB | 300KB | End of Phase 4 |

---

## Risk Mitigation

### High-Risk Areas
1. **User Model Refactoring** → Create comprehensive test suite first
2. **API Client Consolidation** → Test in beta branch before merge
3. **App.jsx Refactoring** → Incrementally extract components
4. **Event-Driven Arch** → Implement alongside old system, gradual migration

### Rollback Plans
- Keep old services in separate branch for 2 weeks
- Database migrations must be reversible
- Feature flags for conditional behavior
- Comprehensive logging of all changes

---

## Resource Requirements

| Phase | Weeks | Engineers | Effort |
|-------|-------|-----------|--------|
| Phase 1 | 2 | 2 | 25 engineer-days |
| Phase 2 | 2 | 3 | 40 engineer-days |
| Phase 3 | 2 | 2 | 30 engineer-days |
| Phase 4 | Ongoing | 1 | 20 engineer-days |
| **Total** | **6+** | - | **115 engineer-days** |

---

## Next Steps

1. **This week:** Review and approve roadmap
2. **Week 1:** Start Phase 1.1 (Agent Onboarding)
3. **Week 1-2:** Complete Phase 1 consolidations
4. **Week 3-4:** Begin Phase 2 refactorings
5. **Week 5-6:** Phase 3 optimizations
6. **Ongoing:** Phase 4 shared package

---

**Prepared by:** AI Code Analysis  
**Date:** May 3, 2026  
**Document:** CODEBASE_ANALYSIS_REFACTORING_ROADMAP.md
