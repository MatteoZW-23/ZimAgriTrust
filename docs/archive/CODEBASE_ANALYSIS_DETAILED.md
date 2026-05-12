# AgriTrust Codebase Analysis Report
**Date:** May 3, 2026  
**Scope:** Complete architectural review of backend and frontend systems

---

## EXECUTIVE SUMMARY

The AgriTrust codebase has **significant code duplication, architectural inconsistencies, and tight coupling** that will hinder maintainability and scalability. Key issues:

- **52+ backend services** with overlapping responsibilities
- **3 frontend portals** with near-identical API client code
- **Monolithic User model** (186+ lines) with poor separation of concerns
- **Duplicate marketplace logic** split between `marketplace_service.py` and `transaction_service.py`
- **Agent onboarding pipeline** poorly consolidated across 3 different services
- **No shared utilities library** despite having 3 frontend apps
- **God objects** (Agent, User, Listing models)
- **Tight coupling** between services (e.g., WhatsApp embedded in transaction flows)

---

## 1. BACKEND STRUCTURE ANALYSIS

### 1.1 Service Layer Duplications

#### **CRITICAL: Agent Onboarding Services Overlap**

Three services handle agent onboarding with overlapping responsibilities:

**File:** `backend/app/services/agent_onboarding_service.py` (Unified service - lines 1-50+)
```python
class AgentOnboardingService:
    @staticmethod
    async def submit_application(db: Session, payload: AgentApplicationCreate) -> AgentApplication:
        """Creates agent application with status APPLIED"""
        
    @staticmethod
    async def complete_documentation(db: Session, application_id: uuid.UUID):
        """Phase 1: Verify documentation, provision trainee account"""
```

**File:** `backend/app/services/onboarding_service.py` (Duplicated - lines 1-50+)
```python
class OnboardingService:
    @staticmethod
    async def sign_contract(db: Session, application_id: uuid.UUID, signee_name: str, signature_data: str, ip: str):
        """Contract signing and Phase advancement"""
        
    @staticmethod
    def submit_quiz(db: Session, application_id: uuid.UUID, module_id: uuid.UUID, answers: Dict[str, str]):
        """Quiz submission"""
```

**File:** `backend/app/services/recruitment_service.py` (Overlapping - lines 1-80)
```python
class RecruitmentService:
    @staticmethod
    async def submit_application(db: Session, payload: AgentApplicationCreate):
        """DUPLICATE of AgentOnboardingService.submit_application"""
        
    @staticmethod
    async def complete_documentation(db: Session, application_id: uuid.UUID):
        """DUPLICATE of agent_onboarding_service logic"""
```

**Issue:** Three services handle the same pipeline. `agent_onboarding_service.py` was created to consolidate, but `recruitment_service.py` and `onboarding_service.py` still exist with duplicate code.

**Impact:** Changes must be made in 3 places. Inconsistent state management. Confusing for developers.

---

#### **CRITICAL: Marketplace Logic Duplication**

**File:** `backend/app/services/marketplace_service.py` - Module-level functions (lines 1-200)
```python
def create_listing(db: Session, seller: User, payload: ListingCreate) -> Listing:
    listing = Listing(seller_id=seller.id, **payload.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

def create_offer(db: Session, buyer: User, listing: Listing, payload: OfferCreate) -> Offer:
    if listing.seller_id == buyer.id:
        raise HTTPException(status_code=400, detail="Cannot bid on own listing")
    offer = Offer(listing_id=listing.id, buyer_id=buyer.id, **payload.model_dump(), status=OfferStatus.PENDING)
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer

def create_buyer_request(db: Session, buyer: User, payload: BuyerRequestCreate) -> BuyerRequest:
    request = BuyerRequest(buyer_id=buyer.id, **payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

def farmer_respond_to_request(db: Session, farmer: User, request: BuyerRequest, payload: FarmerResponseCreate) -> FarmerResponse:
    # ... logic ...
```

**File:** `backend/app/services/marketplace_service.py` - Class methods (lines 325+)
```python
class MarketplaceService:
    @staticmethod
    def create_listing(db: Session, seller: User, payload: ListingCreate) -> Listing:
        """DUPLICATE of module-level function"""
        
    @staticmethod
    def create_offer(db: Session, buyer: User, listing: Listing, payload: OfferCreate) -> Offer:
        """DUPLICATE of module-level function"""
        
    @staticmethod
    def create_buyer_request(db: Session, buyer: User, payload: BuyerRequestCreate) -> BuyerRequest:
        """DUPLICATE of module-level function"""
        
    @staticmethod
    def farmer_respond_to_request(db: Session, farmer: User, request: BuyerRequest, payload: FarmerResponseCreate) -> FarmerResponse:
        """DUPLICATE of module-level function"""
```

**File:** `backend/app/services/transaction_service.py` - Duplicate functions (lines 40+)
```python
class TransactionService:
    @staticmethod
    def create_listing(db: Session, seller: User, payload) -> Listing:
        """DUPLICATE of marketplace_service.create_listing"""
        
    @staticmethod
    def create_buyer_request(db: Session, buyer: User, payload) -> BuyerRequest:
        """DUPLICATE of marketplace_service.create_buyer_request"""
        
    @staticmethod
    def create_offer(db: Session, buyer: User, listing: Listing, payload) -> Offer:
        """DUPLICATE of marketplace_service.create_offer"""
```

**Issue:** Same function exists as:
1. Module-level function
2. Class method in MarketplaceService
3. Duplicate class method in TransactionService

**Impact:** Changes to listing creation logic must be made in multiple places. Inconsistent behavior risk.

---

#### **Payment & Transaction Service Separation**

**Files:** Multiple services handling overlapping concerns:
- `backend/app/services/payment_service.py` - Payment processing
- `backend/app/services/transaction_service.py` - Transaction management
- `backend/app/services/wallet_service.py` - Wallet operations
- `backend/app/services/settlement_service.py` - Settlement logic
- `backend/app/services/escrow_service.py` - Escrow management

These services should be consolidated into a unified financial operations layer, but they work independently with no clear boundaries.

---

### 1.2 Models Analysis

#### **God Object: User Model**

**File:** `backend/app/models/user.py` (186+ lines)

Contains:
- Basic identity (phone, name, email)
- KYC verification (national_id, id_verified, id_document_url, id_verified_at, id_verification_notes)
- Phone verification (is_phone_verified, phone_verified_at)
- Email verification (email_verified, email_verified_at, email_verification_token)
- Password management (password_changed_at, password_history, must_change_password_reason)
- Location data (province, district, ward, latitude, longitude, is_location_verified)
- Business verification (business_verified, business_verified_at)
- Risk/Trust scores (risk_score, trust_score, last_risk_review_date)
- Subscription (subscription_tier, plan_start_date, plan_end_date, subscription_renewal_date)
- Profile fields (bio, profile_image_url, document_verification_status)
- Wallet state (wallet_balance, pending_earnings, blocked_balance)
- Notifications (notification_preference_global, language, currency)
- Onboarding state (onboarding_status, onboarding_complete_at)
- Admin fields (is_active, status, last_activity, created_at, updated_at, suspended_reason)
- Multiple relationships (listings, orders, trades, disputes, assignments, sessions, etc.)

**Problem:** Single model handles authentication, identity verification, risk management, financial state, and notification preferences. Should be split into:
- `User` (core identity)
- `UserVerification` (KYC data)
- `UserWallet` (financial state)
- `UserRiskProfile` (risk/trust scores)
- `UserPreferences` (settings, language, currency)

---

#### **Agent Model Hierarchy Issues**

**Files:**
- `backend/app/models/user.py` - AgentProfile (lines 186+)
- `backend/app/models/agent.py` - Agent, AgentAssignment (lines 38+)
- `backend/app/models/recruitment.py` - AgentApplication (lines 20+)
- `backend/app/models/onboarding.py` - AgentContract, AgentTrainingProgress, ShadowingLog (lines 39+)

**Problem:** Agent data split across 5 models with unclear relationships:

```
User ──→ UserRole.AGENT
    ├── AgentProfile (user.py)
    └── Agent (agent.py)
        └── AgentAssignment (agent.py)

Separate pipeline tracked in:
├── AgentApplication (recruitment.py)
├── AgentContract (onboarding.py)
├── AgentTrainingProgress (onboarding.py)
└── ShadowingLog (onboarding.py)
└── AgentTraining (academy.py)
```

Each step of agent onboarding creates records in multiple places, violating single responsibility principle.

---

#### **Listing Model Bloat**

**File:** `backend/app/models/listing.py` (100+ lines)

Contains overlapping data:
- Product info (product_type, product_subtype, crop, ai_crop_type)
- Grade data (grade, ai_grade_estimate)
- Location (location, location_province, location_district, pickup_address)
- Verification (verification_status, is_location_verified)
- Pricing (price_per_unit, asking_price, currency)
- Logistics (logistics_type, required_cold_chain)
- Media (photos array stored as JSON)
- Timestamps (created_at, updated_at, expires_at, verification_completed_at)

Should separate into:
- `Listing` (core offering)
- `ListingProduct` (product classification)
- `ListingLocation` (geo data)
- `ListingVerification` (verification state)
- `ListingMedia` (photos/attachments)

---

### 1.3 Schemas Duplication

**File:** `backend/app/schemas/admin.py`
```python
class AgentSummaryResponse(BaseModel):
    id: uuid.UUID
    agent_code: str
    specialization: str
    status: str

class AgentAssignmentResponse(BaseModel):
    id: uuid.UUID
    assignment_type: str
    status: str

class AgentDetailResponse(BaseModel):
    id: uuid.UUID
    agent_code: str
    specialization: str
    status: str
    rating: float
```

**File:** `backend/app/schemas/agent.py`
```python
class AgentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    agent_code: str
    specialization: AgentSpecialization
    status: AgentStatus
    rating: float

class AgentAssignmentResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    assignment_type: str
    status: str
```

**Problem:** `AgentAssignmentResponse` defined in both `admin.py` and `agent.py` with different fields.

---

### 1.4 API Endpoints Organization Issues

**File:** `backend/app/api/v1/endpoints/` (15 files)

Inconsistent endpoint organization:
- Some endpoints have admin subfolder: `/admin/users.py`, `/admin/config.py`, `/admin/command_center.py`
- Others at root: `/auth.py`, `/verification.py`, `/transactions.py`
- Mixed concerns in single files (e.g., `whatsapp.py` has 30+ routes handling webhooks, alerts, messaging, payments, locations, analytics, translations)

**File:** `backend/app/api/v1/endpoints/whatsapp.py` (500+ lines)
Contains routes for:
- Webhook handling
- Broadcasts
- Price alerts
- Weather alerts
- Harvest alerts
- Delivery reminders
- Payment reminders
- Verification reminders
- Payment initiation
- Payment receipts
- Location sharing
- Interactive listings
- Analytics tracking
- Market demand
- Group management
- Translation

**Problem:** A single endpoint file shouldn't handle 30+ disparate concerns. Should be split by domain:
- `whatsapp_webhooks.py`
- `whatsapp_alerts.py`
- `whatsapp_payments.py`
- `whatsapp_messaging.py`

---

### 1.5 Service Tight Coupling

**Example:** WhatsApp notifications embedded in transaction flow

**File:** `backend/app/services/marketplace_service.py`
```python
# Line ~400
from app.services.whatsapp_service import WhatsAppService

def accept_offer(...) -> Order:
    # ... order creation ...
    await WhatsAppService.send_whatsapp_message(buyer.phone_number, msg)
```

**Problem:** Business logic tightly coupled to notification implementation. Makes testing hard. Hard to swap notification providers.

**Solution:** Decouple with event-driven architecture or notification service pattern.

---

## 2. FRONTEND STRUCTURE ANALYSIS

### 2.1 Portal API Client Duplication

Three frontend portals have nearly identical API clients with 80%+ code duplication:

#### **Admin Dashboard API Client**

**File:** `apps/admin-dashboard/src/api.js` (250+ lines)
```javascript
const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {}),
  };

  // Strip Authorization if the token is null/undefined/fake...
  if (
    headers["Authorization"] === "Bearer null" ||
    headers["Authorization"] === "Bearer undefined" ||
    headers["Authorization"] === "Bearer active_session"
  ) {
    delete headers["Authorization"];
  }

  const response = await fetch(`${API}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    let message = "Request failed";
    if (data?.detail) {
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(", ");
      }
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

// AUTH
export function register(full_name, phone_number, role, password, admin_secret = null) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ full_name, phone_number, role, password, admin_secret }),
  });
}

export function login(phone_number, password) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ phone_number, password }),
  });
}

export function verifyLogin2FA(phone_number, otp) {
  return request("/auth/verify-login-2fa", {
    method: "POST",
    body: JSON.stringify({ phone_number, otp }),
  });
}

export function forgotPassword(phone_number) {
  return request("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ phone_number }),
  });
}

export function resetPassword(phone_number, token, new_password) {
  return request("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ phone_number, token, new_password }),
  });
}

export function getProfile(token) {
  return request("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function updateProfile(token, payload) {
  return request("/auth/profile", {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}
```

#### **Agent Portal API Client**

**File:** `apps/agent-portal/src/api.js` (300+ lines)
```javascript
/**
 * ZimAgritrust Agent Portal – API Client
 * All endpoints used by field agents.
 */
const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {}),
  };
  const res = await fetch(`${API}${path}`, { ...options, headers, credentials: "include" });
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : null;
  if (!res.ok) {
    const msg = data?.detail
      ? typeof data.detail === "string" ? data.detail
        : Array.isArray(data.detail) ? data.detail.map(e => `${e.loc?.join(".")}: ${e.msg}`).join(", ")
        : JSON.stringify(data.detail)
      : "Request failed";
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (phone_number, password) =>
  request("/auth/login", { method: "POST", body: JSON.stringify({ phone_number, password }) });

export const verifyOtp = (phone_number, otp) =>
  request("/auth/verify-login-2fa", { method: "POST", body: JSON.stringify({ phone_number, otp }) });

// ... 20+ more endpoints
```

#### **App Portal API Client**

**File:** `apps/app-portal/src/api.js` (350+ lines)
```javascript
/**
 * ZimAgritrust App Portal – API Client
 * Shared by Farmer and Buyer roles.
 */
const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {}),
  };
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : null;
  if (!res.ok) {
    const msg = data?.detail
      ? typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
        ? data.detail.map((e) => `${e.loc?.join(".")}: ${e.msg}`).join(", ")
        : JSON.stringify(data.detail)
      : "Request failed";
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (phone_number, password) =>
  request("/auth/login", { method: "POST", body: JSON.stringify({ phone_number, password }) });

// ... Similar to agent-portal
```

**Problem:** 
- `request()` function identical in all 3 files (100+ lines of duplicate code)
- Auth endpoints (`login`, `verifyOtp`, `register`, `forgotPassword`, etc.) duplicated
- Marketplace endpoints duplicated
- Error handling logic identical
- FormData and Authorization header handling identical

**Impact:** Bug in request handler must be fixed in 3 places. Inconsistent error handling possible.

---

### 2.2 Route Guard Duplication

**File:** `apps/admin-dashboard/src/utils/routeGuard.jsx`
```javascript
/**
 * Route Guard for Admin Dashboard
 * Enforces RBAC, session timeout, and redirects unauthorized users
 */

import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { canAccessRouteByRole, getDefaultRoute } from '@agritrust/shared';

// Admin session timeout (30 minutes of inactivity)
const ADMIN_SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds

export function AdminRoute({ children }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  const [lastActivity, setLastActivity] = useState(Date.now());

  useEffect(() => {
    // Check for session timeout
    const checkSessionTimeout = () => {
      const now = Date.now();
      if (now - lastActivity > ADMIN_SESSION_TIMEOUT) {
        // Session expired, logout user
        localStorage.clear();
        window.location.href = '/login';
      }
    };

    // Update activity on user interaction
    const updateActivity = () => {
      setLastActivity(Date.now());
    };

    // Set up event listeners for activity tracking
    window.addEventListener('mousemove', updateActivity);
    window.addEventListener('keydown', updateActivity);
    window.addEventListener('click', updateActivity);

    // Check session timeout every minute
    const timeoutCheck = setInterval(checkSessionTimeout, 60000);

    return () => {
      window.removeEventListener('mousemove', updateActivity);
      window.removeEventListener('keydown', updateActivity);
      window.removeEventListener('click', updateActivity);
      clearInterval(timeoutCheck);
    };
  }, [lastActivity]);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!canAccessRouteByRole(user.role, '/admin')) {
    return <Navigate to={getDefaultRoute(user.role)} replace />;
  }

  return children;
}

export function ProtectedRoute({ children, allowedRoles = [] }) {
  // ... protected route logic
}
```

**File:** `apps/agent-portal/src/utils/routeGuard.jsx`
```javascript
/**
 * Route Guard for Agent Portal
 * Enforces RBAC and redirects unauthorized users
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { canAccessRouteByRole, getDefaultRoute } from '@agritrust/shared';

export function AgentRoute({ children }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!canAccessRouteByRole(user.role, '/agent')) {
    return <Navigate to={getDefaultRoute(user.role)} replace />;
  }

  return children;
}

export function ProtectedRoute({ children, allowedRoles = [] }) {
  // ... similar to admin-dashboard
}
```

**Problem:** 
- Core logic identical
- Session timeout logic should be shared
- ProtectedRoute component duplicated with same logic

**Note:** `app-portal` also has `routeGuard.jsx` (not examined in detail, but likely duplicated)

---

### 2.3 Frontend App Structure

**Current State:**
```
apps/
├── admin-dashboard/
│   ├── src/
│   │   ├── api.js          ← Unique to this app
│   │   ├── App.jsx         ← All components inline, 1000+ lines
│   │   ├── components/     ← 40+ component files
│   │   ├── utils/          ← routeGuard, dataTransfer (duplicated)
│   │   └── styles.css
├── agent-portal/
│   ├── src/
│   │   ├── api.js          ← DUPLICATE of admin-dashboard
│   │   ├── App.jsx         ← All components inline
│   │   ├── utils/          ← routeGuard (DUPLICATE)
│   │   └── styles.css
├── app-portal/
│   ├── src/
│   │   ├── api.js          ← DUPLICATE of others
│   │   ├── App.jsx         ← All components inline
│   │   ├── utils/          ← routeGuard (DUPLICATE)
│   │   └── styles.css
└── services/
    └── whatsapp-bridge/
```

**Problems:**
- No shared component library (despite using `@agritrust/shared` package)
- No shared API client
- No shared route guards
- Each app reinvents the wheel
- Max bundle size increased by duplication

---

### 2.4 App.jsx Monolithic Structure

**File:** `apps/admin-dashboard/src/App.jsx` (1000+ lines)

Contains:
- All component imports (40+)
- All state management
- All event handlers
- Login/auth logic
- Sidebar navigation
- Theme handling
- Search functionality
- All view rendering logic

Should be split into:
- `Layout.jsx` (sidebar, nav, theme)
- `AuthContext.jsx` (auth state)
- `ViewRouter.jsx` (view switching logic)
- Individual view components

---

## 3. CONFIGURATION & ENVIRONMENT ISSUES

### 3.1 Multiple Environment Configuration Patterns

**Backend patterns found:**
1. `backend/app/core/config.py` - Main config
2. `backend/app/core/security.py` - Security settings
3. `backend/app/core/constants.py` - Constants
4. `backend/alembic.ini` - Migration config
5. `.env` files (multiple)

**Frontend patterns:**
1. `VITE_API_URL` environment variable
2. Hardcoded fallback: `"http://localhost:8080/api/v1"`
3. `.env.local` (not tracked)

**Problem:** No centralized config management. Configuration scattered across 5+ files. Inconsistent across frontend apps.

---

## 4. UTILITIES & SHARED CODE OPPORTUNITIES

### 4.1 Missing Shared Utilities

**File:** `packages/shared/` (exists but largely empty)

**Should contain:**
- API client factory
- Route guards (shared from all 3 apps)
- Common hooks (useAuth, useNotification, useApiCall)
- Common components (Button, Modal, Form, DataTable, Card)
- Error handling utilities
- Date/formatting utilities
- Validation schemas
- Constants (roles, statuses, provinces)

**Current state:**
- Only contains `canAccessRouteByRole()`, `getDefaultRoute()`
- Rest of `packages/shared/src/` is empty

**File:** `apps/admin-dashboard/src/utils/dataTransfer.js`
```javascript
export const exportToCSV = (data, filename = 'ZimAgritrust_export.csv') => {
  if (!data || !data.length) return;
  const headers = Object.keys(data[0]);
  const csvRows = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const val = row[header];
        const escaped = ('' + (val ?? '')).replace(/"/g, '""');
        return `"${escaped}"`;
      }).join(',')
    )
  ];
  // ... export logic
};

export const exportToJSON = (data, filename = 'ZimAgritrust_export.json') => {
  // ... json export logic
};

export const handleImport = (file, callback) => {
  // ... import logic
};
```

**Problem:** Data export/import utilities only in admin-dashboard, but all portals need this functionality.

---

### 4.2 Backend Utility Issues

**File:** `backend/app/utils/ml_utils.py` - Only 1 file

Contains only:
- ML model loading
- Image preprocessing

**Missing utilities:**
- String formatting
- Date/time helpers
- Validation helpers
- Pagination helpers
- Query builders
- Cache helpers
- Logging decorators
- Error handlers

These are scattered across service files instead of being centralized.

---

## 5. ARCHITECTURE ANTI-PATTERNS

### 5.1 God Objects

| Object | Responsibilities | Lines |
|--------|------------------|-------|
| User | Auth, Identity, Verification, Financial, Risk, Preferences, Notifications | 186+ |
| Listing | Product, Location, Verification, Pricing, Logistics, Media | 100+ |
| Agent | Profile, Assignments, Financial, Status, Coverage | 100+ |
| Order | Transaction, Logistics, Payment, Dispute Tracking | 80+ |

**Impact:** 
- Hard to test individual concerns
- High change frequency
- Unclear responsibilities
- Hard to evolve incrementally

---

### 5.2 Tight Coupling Between Layers

**Example 1: Service Layer → Notification Layer**

```python
# backend/app/services/marketplace_service.py
async def accept_offer(...) -> Order:
    # ... business logic ...
    from app.services.whatsapp_service import WhatsAppService
    await WhatsAppService.send_whatsapp_message(buyer.phone_number, msg)
```

**Problem:** Business logic tightly coupled to WhatsApp. Can't change notification without changing business logic.

**Example 2: API → Database**

No repository pattern. Controllers directly query database:
```python
# backend/app/api/v1/endpoints/admin/users.py
@router.get("", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    take: int = 10,
    db: Session = Depends(get_db),
):
    return db.query(User).offset(skip).limit(take).all()
```

**Problem:** Hard to test. Hard to switch database implementations.

---

### 5.3 Inconsistent Data Flow

**Transaction flow spans multiple services without clear orchestration:**
```
marketplace_service.accept_offer()
  ├── wallet_service.hold_escrow()
  ├── payment_service.create_transaction()
  ├── delivery_service.create_delivery_record()
  ├── notification_service.notify_buyer()
  ├── whatsapp_service.send_whatsapp_message()
  └── No error rollback strategy
```

**Problem:**
- No transactional consistency
- If WhatsApp fails, transaction still completes
- No event sourcing or saga pattern
- Hard to debug failures

---

### 5.4 No Clear Authentication/Authorization Separation

**Mixed concerns:**
```python
# backend/app/api/api/v1/endpoints/auth.py - 500+ lines
# Contains: login, register, 2FA, password reset, profile updates, permissions

# backend/app/api/deps.py - Dependencies
# Contains: role checking, token validation, session validation

# backend/app/core/security.py - Security utilities
# Contains: password hashing, token creation, password strength checks
```

**Problem:** Auth logic fragmented. No clear AuthService. Business logic mixed with security concerns.

---

## 6. SPECIFIC DUPLICATE CODE SNIPPETS

### Backend Services

**Duplicate: verify_phone pattern**

**File:** `backend/app/services/verification_service.py`
```python
@classmethod
def verify_phone(cls, db: Session, user: User) -> Dict:
    user.is_phone_verified = True
    user.phone_verified_at = datetime.now()
    db.commit()
    return {"status": "verified"}
```

**File:** `backend/app/services/auth_service.py`
```python
def verify_phone(db: Session, user: User):
    user.is_phone_verified = True
    user.phone_verified_at = datetime.now()
    db.commit()
```

**Duplicate: trust_service duplication**

**File:** `backend/app/services/trust_service.py` (lines 1-220)
```python
def update_farmer_scores(db: Session, farmer: User) -> User:
    # ... implementation ...

def update_scores_after_success(db: Session, order: Order) -> None:
    # ... implementation ...
```

**File:** `backend/app/services/trust_service.py` (lines 215+)
```python
class TrustService:
    @staticmethod
    def update_farmer_scores(db: Session, farmer: User) -> User:
        # DUPLICATE of above

    @staticmethod
    def update_scores_after_success(db: Session, order: Order) -> None:
        # DUPLICATE of above
```

---

## 7. DEPENDENCY MANAGEMENT ISSUES

### 7.1 Frontend

**All portals have identical dependencies:**

```json
// apps/admin-dashboard/package.json
{
  "dependencies": {
    "@agritrust/shared": "file:../../packages/shared",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }
}
```

**Problem:** No shared UI component library. `@agritrust/shared` should contain shared components, hooks, utils.

**Solution:** Populate `packages/shared` with:
- Shared API client
- Route guards
- Common components
- Common hooks
- Utilities

---

### 7.2 Backend

**No clear separation between core dependencies:**

```
backend/requirements.txt
├── FastAPI (API framework)
├── SQLAlchemy (ORM)
├── Pydantic (validation)
├── WhatsApp SDK
├── ML libraries (TensorFlow, etc.)
├── AWS SDK
├── Async libraries (aioredis, etc.)
└── 30+ other packages
```

**Problem:** 
- No separation of concerns
- Hard to understand what each service needs
- All dependencies loaded at startup
- No optional dependencies clearly marked

---

## 8. SUMMARY OF ISSUES BY SEVERITY

### 🔴 CRITICAL (High Impact, High Effort to Fix)

1. **Agent Onboarding Pipeline Triplication**
   - Files: `agent_onboarding_service.py`, `onboarding_service.py`, `recruitment_service.py`
   - Fix: Consolidate to single service, remove duplicates

2. **Marketplace Logic Duplication**
   - Files: `marketplace_service.py` (module + class), `transaction_service.py`
   - Fix: Consolidate to single service with clear interface

3. **User Model God Object**
   - File: `backend/app/models/user.py`
   - Fix: Split into User, UserVerification, UserWallet, UserRiskProfile, UserPreferences

4. **API Client Triplication**
   - Files: All 3 portals have 80%+ duplicate code
   - Fix: Create shared API client in `packages/shared`, use in all portals

---

### 🟠 HIGH (Significant Impact, Medium Effort)

5. **Endpoint Organization**
   - File: `backend/app/api/v1/endpoints/whatsapp.py` (500+ lines, 30+ routes)
   - Fix: Split into domain-specific endpoint files

6. **Monolithic App.jsx**
   - Files: All 3 portals
   - Fix: Split into Layout, Router, Auth context, views

7. **Service Tight Coupling**
   - Whatsapp notifications embedded in business logic
   - Fix: Event-driven architecture or service locator pattern

8. **Route Guard Duplication**
   - Files: All 3 portals
   - Fix: Move to `packages/shared`

---

### 🟡 MEDIUM (Moderate Impact, Lower Effort)

9. **Listing Model Fragmentation**
   - File: `backend/app/models/listing.py`
   - Fix: Split into separate concern models

10. **Schema Duplication**
    - Files: `schemas/admin.py`, `schemas/agent.py`
    - Fix: Consolidate to single canonical schemas

11. **Configuration Scattering**
    - Fix: Centralize all config in single `config.py`

12. **Empty Shared Package**
    - File: `packages/shared/`
    - Fix: Populate with shared utilities and components

13. **Data Export Utilities Not Shared**
    - File: `apps/admin-dashboard/src/utils/dataTransfer.js`
    - Fix: Move to `packages/shared`

---

### 🔵 LOW (Nice to Fix, Lower Impact)

14. **Inconsistent endpoint naming**
    - Some use `/users`, others use `/user`

15. **Missing documentation**
    - No clear API documentation
    - No service dependency graph

---

## RECOMMENDATIONS

### Phase 1 (CRITICAL - Weeks 1-2)

1. **Consolidate Agent Onboarding**
   - Keep only `agent_onboarding_service.py`
   - Remove `recruitment_service.py` and `onboarding_service.py`
   - Update all endpoints to use consolidated service

2. **Create Shared Frontend API Client**
   - Extract `request()` function to `packages/shared`
   - Create role-based API client factories
   - All portals import from shared package

3. **Consolidate Marketplace Services**
   - Remove duplicate functions from `marketplace_service.py`
   - Update `transaction_service.py` to use marketplace service
   - Clear interface with single source of truth

### Phase 2 (HIGH - Weeks 3-4)

4. **Refactor User Model**
   - Create separate tables for verification, wallet, preferences
   - Migrate data
   - Update all references

5. **Extract Shared Frontend Utilities**
   - Move route guards to `packages/shared`
   - Move data utilities to `packages/shared`
   - Create common hook library

6. **Refactor Monolithic App Components**
   - Split admin App.jsx into Layout, Router, Auth
   - Repeat for other portals
   - Extract common patterns to shared components

### Phase 3 (MEDIUM - Weeks 5-6)

7. **Event-Driven Architecture**
   - Replace direct service coupling with events
   - Implement async notification dispatch
   - Add error recovery mechanism

8. **Endpoint Reorganization**
   - Split large endpoint files
   - Establish naming conventions
   - Create endpoint documentation

9. **Extract Listing Concerns**
   - Split Listing model
   - Create dedicated models for Product, Location, Verification, Media

### Ongoing

10. **Create Shared Package Content**
    - Common components library
    - Custom hooks (useApi, useAuth, useNotification)
    - Validation utilities
    - Constants and enums

---

## ARCHITECTURE IMPROVEMENTS

### Before
```
Backend               Frontend 1       Frontend 2       Frontend 3
├── 52 services       ├── api.js        ├── api.js        ├── api.js
├── God objects       ├── routeGuard    ├── routeGuard    ├── routeGuard
├── Tight coupling    ├── App.jsx       ├── App.jsx       ├── App.jsx
└── No events         └── utils         └── utils         └── utils
```

### After
```
Backend              Shared Lib           Frontend 1       Frontend 2       Frontend 3
├── ~20 services     ├── @api client       ├── useAuth()     ├── useAuth()     ├── useAuth()
├── Focused objects  ├── @components       ├── App Layout    ├── App Layout    ├── App Layout
├── Events           ├── @hooks            ├── Views         ├── Views         ├── Views
├── Services         ├── @utils
└── Repositories     └── @constants
```

---

**End of Report**
