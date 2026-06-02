# System Migration Guides

This document consolidates all migration guides for the ZimAgritrust platform, including verification system, transaction flow, and onboarding/recruitment system unifications.

---

## Table of Contents
1. [Verification System Migration Guide](#verification-system-migration-guide)
2. [Transaction Flow Migration Guide](#transaction-flow-migration-guide)
3. [Onboarding & Recruitment Migration Guide](#onboarding--recruitment-migration-guide)

---

## Verification System Migration Guide

### Overview

This document describes the migration from the legacy verification system (`/verification`) to the new verification workflow system (`/verification-workflow`). The new system provides enhanced functionality, better data modeling, and improved scalability.

### Migration Status: Phase 1 Complete âœ…

### Completed Changes

1. **Frontend Updates**
   - Admin dashboard now uses `/verification-workflow` endpoints
   - Mobile farmer app now uses `/verification-workflow` endpoints
   - IDVerificationQueuePanel updated to handle new API response format

2. **Backend Changes**
   - Legacy verification.py endpoints marked as deprecated
   - Legacy endpoints hidden from OpenAPI schema
   - Data migration script created (`0017_migrate_verification_data.py`)

3. **API Endpoint Changes**

| Legacy Endpoint | New Endpoint | Status |
|----------------|--------------|--------|
| `/verification/submit` | `/verification-workflow/submit` | âœ… Migrated |
| `/verification/my-status` | `/verification-workflow/my-status` | âœ… Migrated |
| `/verification/queue` | `/verification-workflow/review-queue` | âœ… Migrated |
| `/verification/{id}/approve` | `/verification-workflow/review/{document_id}` | âœ… Migrated |
| `/verification/{id}/reject` | `/verification-workflow/review/{document_id}` | âœ… Migrated |

### New Verification Workflow API

#### User Endpoints

##### Submit Document
```
POST /api/v1/verification-workflow/submit
Content-Type: multipart/form-data

Parameters:
- document_type: string (required) - e.g., "national_id", "passport", "drivers_license"
- primary_file: file (required) - Primary document image/PDF
- back_file: file (optional) - Back of document
- selfie_file: file (optional) - Selfie holding document
- supporting_file: file (optional) - Supporting document
- document_number: string (optional) - Document number/ID
- issue_date: string (optional) - Issue date (ISO format)
- expiry_date: string (optional) - Expiry date (ISO format)
- issuing_authority: string (optional) - Issuing authority
- submission_channel: string (optional) - Default: "web"

Response:
{
  "success": true,
  "message": "Document submitted successfully",
  "document_id": "uuid",
  "document_type": "national_id",
  "status": "pending_admin",
  "review_stage": "admin_review",
  "submitted_at": "2024-01-01T00:00:00Z"
}
```

##### Get My Documents
```
GET /api/v1/verification-workflow/my-documents?status=pending

Response:
{
  "total": 5,
  "documents": [
    {
      "id": "uuid",
      "document_type": "national_id",
      "document_label": "National ID",
      "status": "approved",
      "current_stage": "admin_review",
      "submitted_at": "2024-01-01T00:00:00Z",
      "reviewed_at": "2024-01-02T00:00:00Z",
      "rejection_reason": null,
      "resubmission_deadline": null,
      "trust_score_delta": 15,
      "has_selfie": true,
      "can_resubmit": false
    }
  ]
}
```

##### Get Verification Status
```
GET /api/v1/verification-workflow/my-status

Response:
{
  "user_id": "uuid",
  "role": "farmer",
  "overall_status": "approved",
  "verification_level": 3,
  "identity": {
    "status": "approved",
    "verified_at": "2024-01-01T00:00:00Z",
    "document_type": "national_id"
  },
  "address": {
    "status": "not_submitted",
    "verified_at": null
  },
  "business": {
    "status": "approved",
    "verified_at": "2024-01-01T00:00:00Z"
  },
  "permissions": {
    "can_list_products": true,
    "can_make_purchases": true,
    "can_receive_payments": true,
    "can_access_loans": false,
    "can_use_platform_services": true
  },
  "required_documents": [...],
  "trust_score": 85,
  "next_steps": [...]
}
```

#### Reviewer Endpoints (Admin/Agent)

##### Get Review Queue
```
GET /api/v1/verification-workflow/review-queue?status=pending&document_type=national_id&user_role=farmer&limit=50&offset=0

Response:
{
  "total": 25,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "queue_id": "uuid",
      "document_id": "uuid",
      "document_type": "national_id",
      "document_label": "National ID",
      "status": "pending",
      "priority": 5,
      "is_urgent": false,
      "submitted_at": "2024-01-01T00:00:00Z",
      "due_by": "2024-01-02T00:00:00Z",
      "assigned_to": null,
      "user": {
        "id": "uuid",
        "name": "John Doe",
        "phone": "+263123456789",
        "role": "farmer",
        "trust_score": 75
      },
      "fraud_score": 10,
      "has_selfie": true,
      "resubmission_count": 0
    }
  ]
}
```

##### Review Document
```
POST /api/v1/verification-workflow/review/{document_id}
Content-Type: multipart/form-data

Parameters:
- decision: string (required) - "approve", "reject", "escalate", or "request_info"
- notes: string (optional) - Review notes/reason
- rejection_category: string (optional) - Rejection reason category

Response:
{
  "success": true,
  "document_id": "uuid",
  "document_type": "national_id",
  "new_status": "approved",
  "trust_score_delta": 15,
  "reviewed_at": "2024-01-02T00:00:00Z"
}
```

### Data Model Changes

#### Legacy Model: DocumentVerificationRequest
- Single table with all verification data
- Limited fraud detection
- Simple review workflow
- No audit trail

#### New Model: DocumentVerificationRecord
- Enhanced fraud detection with scoring
- Multi-stage review workflow (agent â†’ admin)
- Comprehensive audit logging
- Resubmission tracking
- Trust score integration

#### Additional New Models
- **UserVerificationSummary**: Consolidated view of user's verification status
- **VerificationQueue**: Task management for reviewers
- **VerificationAuditLog**: Complete audit trail
- **VerificationNotification**: Notification management

### Data Migration

#### Running the Migration

```bash
# Using Docker
docker-compose exec backend python alembic/versions/0017_migrate_verification_data.py

# Or directly with Python
python backend/alembic/versions/0017_migrate_verification_data.py <DATABASE_URL>
```

#### Migration Script Features
- Migrates all legacy document records
- Creates user verification summaries
- Generates queue entries for pending documents
- Creates audit logs for reviewed documents
- Handles error cases gracefully
- Provides detailed statistics

### Legacy System Deprecation

The legacy verification system (`/verification`) is now deprecated:
- Endpoints marked as deprecated in API
- Hidden from OpenAPI documentation
- Will be removed in a future release (TBD)

#### Graceful Period
The legacy endpoints will remain functional for a transition period to allow:
- Mobile app updates to propagate
- Third-party integrations to update
- Data migration verification

---

## Transaction Flow Migration Guide

### Overview

This document describes the unification of the transaction-related endpoints (`listings.py`, `trades.py`, `transactions.py`, and `requests.py`) into a single, coherent `TransactionService`. This consolidation eliminates duplicated functionality, provides a single source of truth for transaction operations, and simplifies the codebase.

### Migration Status: Phase 3 Complete âœ…

### Completed Changes

1. **Service Layer**
   - Created unified `TransactionService` in `backend/app/services/transaction_service.py`
   - Updated `listings.py` endpoints to use unified service
   - Updated `trades.py` endpoints to use unified service
   - Updated `transactions.py` endpoints to use unified service
   - Updated `requests.py` endpoints to use unified service
   - Added deprecation notice to `marketplace_core` for direct usage

2. **Data Validation**
   - Created data validation script `0019_validate_transaction_data.py`
   - Validates data consistency across all transaction tables
   - Checks for orphaned records and missing references

3. **Frontend**
   - All endpoints maintain the same API structure (backward compatible)
   - No frontend changes required

### Service Comparison

| Legacy Service | New Service | Status |
|----------------|--------------|--------|
| marketplace_core.create_listing | TransactionService.create_listing | âœ… Unified |
| marketplace_core.search_listings | TransactionService.search_listings | âœ… Unified |
| marketplace_core.create_offer | TransactionService.create_offer | âœ… Unified |
| marketplace_core.accept_offer | TransactionService.accept_offer | âœ… Unified |
| marketplace_core.reject_offer | TransactionService.reject_offer | âœ… Unified |
| marketplace_core.counter_offer | TransactionService.counter_offer | âœ… Unified |
| marketplace_core.create_buyer_request | TransactionService.create_buyer_request | âœ… Unified |
| marketplace_core.farmer_respond_to_request | TransactionService.respond_to_request | âœ… Unified |
| marketplace_core.accept_farmer_response | TransactionService.create_order_from_response | âœ… Unified |
| Direct DB operations (trades.py) | TransactionService.start_trade_session | âœ… Unified |
| Direct DB operations (trades.py) | TransactionService.send_trade_message | âœ… Unified |
| Direct DB operations (trades.py) | TransactionService.get_trade_messages | âœ… Unified |
| escrow_service.release_payment | TransactionService.confirm_delivery | âœ… Unified |
| receipt_service.generate_receipt_pdf | TransactionService.generate_receipt | âœ… Unified |
| verification_service.record_positive_rating | TransactionService.submit_review | âœ… Unified |

### Unified TransactionService API

#### Listing Management

##### Create Listing
```python
def create_listing(db: Session, seller: User, payload) -> Listing
```
Creates a new market listing.

##### Search Listings
```python
def search_listings(
    db: Session,
    crop: Optional[str] = None,
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    grade: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[Listing], int]
```
Searches market listings with filters.

#### Order Management

##### Confirm Delivery
```python
def confirm_delivery(
    db: Session,
    order: Order,
    user: User,
    handover_code: Optional[str] = None
) -> Order
```
Confirms order delivery and releases escrow payment.

##### Submit Review
```python
def submit_review(
    db: Session,
    order: Order,
    reviewer: User,
    rating: int,
    comment: Optional[str] = None
) -> TradeReview
```
Submits a review for a completed order. Includes trust score updates for positive ratings.

### API Endpoint Changes

All endpoints now use `TransactionService` internally. The API structure remains unchanged for backward compatibility.

**Updated Endpoints:**
- `POST /listings` - Uses TransactionService.create_listing
- `GET /listings/search` - Uses TransactionService.search_listings
- `POST /listings/{id}/offers` - Uses TransactionService.create_offer
- `POST /listings/{id}/offers/{offer_id}/accept` - Uses TransactionService.accept_offer
- `POST /trades/{listing_id}/start` - Uses TransactionService.start_trade_session
- `POST /trades/{session_id}/messages` - Uses TransactionService.send_trade_message
- `GET /transactions` - Uses TransactionService.get_orders
- `POST /transactions/{order_id}/confirm-delivery` - Uses TransactionService.confirm_delivery
- `POST /transactions/{order_id}/review` - Uses TransactionService.submit_review
- `POST /requests` - Uses TransactionService.create_buyer_request
- `POST /requests/{request_id}/respond` - Uses TransactionService.respond_to_request

### Data Model Changes

#### No Schema Changes Required

The unified service uses the same underlying data models as the legacy endpoints:
- **Listing**: Market listings (unchanged)
- **Offer**: Structured offers on listings (unchanged)
- **BuyerRequest**: Buyer requests (unchanged)
- **TradeSession**: Message-based negotiation sessions (unchanged)
- **Order**: Finalized transactions (unchanged)
- **Transaction**: Financial transactions within orders (unchanged)

### Running Data Validation

```bash
# Using Docker
docker-compose exec backend python alembic/versions/0019_validate_transaction_data.py

# Or directly with Python
python backend/alembic/versions/0019_validate_transaction_data.py <DATABASE_URL>
```

### Legacy Service Deprecation

#### MarketplaceService

**Status**: Deprecated for direct usage

**Deprecation Notice**: Added to service docstring

**Migration Path**:
```python
# Old
from app.services.marketplace_service import marketplace_core
listing = marketplace_core.create_listing(db, seller, payload)

# New
from app.services.transaction_service import transaction_service
listing = transaction_service.create_listing(db, seller, payload)
```

**Note**: MarketplaceService is still used internally by TransactionService, so do not remove it.

---

## Onboarding & Recruitment Migration Guide

### Overview

This document describes the unification of the recruitment and onboarding services into a single, coherent `AgentOnboardingService`. This consolidation eliminates duplicated functionality, provides a single source of truth for agent onboarding, and simplifies the codebase.

### Migration Status: Phase 2 Complete âœ…

### Completed Changes

1. **Service Layer**
   - Created unified `AgentOnboardingService` in `backend/app/services/agent_onboarding_service.py`
   - Updated `recruitment.py` endpoints to use unified service
   - Updated `onboarding.py` endpoints to use unified service (with deprecation warnings)
   - Added deprecation notices to legacy `RecruitmentService` and `OnboardingService`

2. **Data Validation**
   - Created data validation script `0018_validate_onboarding_data.py`
   - Validates data consistency across all onboarding tables
   - Auto-fixes common data issues

3. **Frontend**
   - Admin dashboard recruitment panel requires no changes (uses same endpoints)
   - Backend endpoint structure unchanged (backward compatible)

### Service Comparison

| Legacy Service | New Service | Status |
|----------------|--------------|--------|
| RecruitmentService.submit_application | AgentOnboardingService.submit_application | âœ… Unified |
| RecruitmentService.complete_documentation | AgentOnboardingService.complete_documentation | âœ… Unified |
| RecruitmentService.complete_training_module | AgentOnboardingService.complete_training_module | âœ… Unified (enhanced) |
| RecruitmentService.setup_equipment | AgentOnboardingService.setup_equipment | âœ… Unified |
| RecruitmentService.complete_practical_assessment | AgentOnboardingService.complete_practical_assessment | âœ… Unified |
| RecruitmentService.complete_shadowing | AgentOnboardingService.complete_shadowing | âœ… Unified (enhanced) |
| RecruitmentService.record_supervised_work | AgentOnboardingService.record_supervised_work | âœ… Unified |
| RecruitmentService.certify_agent | AgentOnboardingService.certify_agent | âœ… Unified |
| OnboardingService.sign_contract | AgentOnboardingService.complete_documentation (with sign_contract) | âœ… Unified |
| OnboardingService.submit_quiz | AgentOnboardingService.complete_training_module (with answers) | âœ… Unified |
| OnboardingService.log_shadowing | AgentOnboardingService.complete_shadowing (with rubric) | âœ… Unified |
| OnboardingService.get_onboarding_status | AgentOnboardingService.get_onboarding_status | âœ… Unified |

### Unified AgentOnboardingService API

#### Pipeline Orchestration Methods

##### Submit Application
```python
async def submit_application(db: Session, payload: AgentApplicationCreate) -> AgentApplication
```
**Step 1**: Creates initial agent application with status `APPLIED`.

##### Complete Documentation
```python
async def complete_documentation(
    db: Session,
    application_id: uuid.UUID,
    sign_contract: bool = False,
    signee_name: Optional[str] = None,
    signature_data: Optional[str] = None,
    ip_address: Optional[str] = None
) -> AgentApplication
```
**Step 2**: Verifies documentation, creates trainee account, optionally signs contract.

**Enhancements**:
- Now supports optional contract signing parameters
- Combines functionality from both legacy services
- Creates trainee account with temporary PIN
- Initializes academy progress

##### Complete Training Module
```python
async def complete_training_module(
    db: Session,
    application_id: uuid.UUID,
    module_id: str,
    answers: Optional[Dict[str, str]] = None
) -> Dict
```
**Step 3-5**: Completes training module with optional detailed quiz scoring.

**Enhancements**:
- Supports both simple completion and detailed quiz scoring
- If `answers` provided: uses detailed scoring with AgentTrainingProgress
- If no `answers`: uses simple completion tracking
- Maintains backward compatibility

##### Complete Shadowing
```python
async def complete_shadowing(
    db: Session,
    application_id: uuid.UUID,
    supervisor_id: uuid.UUID,
    rating: Optional[float] = None,
    rubric: Optional[Dict] = None
) -> AgentApplication
```
**Step 7**: Completes shadowing phase.

**Enhancements**:
- Supports both simple rating and detailed rubric evaluation
- If `rubric` provided: uses detailed ShadowingLog evaluation
- If no `rubric`: uses simple rating
- Maintains backward compatibility

##### Certify Agent
```python
async def certify_agent(db: Session, application_id: uuid.UUID) -> Dict
```
**Step 9**: Final certification and agent activation.

### API Endpoint Changes

#### Recruitment Endpoints (Updated)

All recruitment endpoints now use `AgentOnboardingService` internally. The API structure remains unchanged for backward compatibility.

**Updated Endpoints**:
- `POST /recruitment/apply` - Uses AgentOnboardingService.submit_application
- `POST /recruitment/{application_id}/documentation` - Now accepts optional contract signing parameters
- `POST /recruitment/{application_id}/training/module/{module_id}` - Now accepts optional quiz answers
- `POST /recruitment/{application_id}/equipment` - Uses AgentOnboardingService.setup_equipment
- `POST /recruitment/{application_id}/practical` - Uses AgentOnboardingService.complete_practical_assessment
- `POST /recruitment/{application_id}/shadowing` - Now accepts optional rubric parameter
- `POST /recruitment/{application_id}/supervised-task` - Uses AgentOnboardingService.record_supervised_work
- `POST /recruitment/{application_id}/certify` - Uses AgentOnboardingService.certify_agent

#### Onboarding Endpoints (Deprecated)

Onboarding endpoints now use `AgentOnboardingService` internally but are marked as deprecated.

**Deprecated Endpoints**:
- `POST /onboarding/contract/{application_id}/sign` - Use /recruitment/{application_id}/documentation instead
- `POST /onboarding/academy/{application_id}/quiz` - Use /recruitment/{application_id}/training/module/{module_id} instead
- `POST /onboarding/shadowing` - Use /recruitment/{application_id}/shadowing instead
- `POST /onboarding/shadowing/{application_id}/evaluate` - Use /recruitment/{application_id}/shadowing with rubric instead

### Data Model Changes

#### No Schema Changes Required

The unified service uses the same underlying data models as the legacy services:
- **AgentApplication**: Primary record for agent applications (unchanged)
- **AgentContract**: Digital contract signatures (unchanged)
- **AgentTrainingProgress**: Detailed quiz progress (unchanged)
- **ShadowingLog**: Detailed shadowing evaluations (unchanged)
- **Agent**: Agent profiles (unchanged)

### Running Data Validation

```bash
# Using Docker
docker-compose exec backend python alembic/versions/0018_validate_onboarding_data.py

# Or directly with Python
python backend/alembic/versions/0018_validate_onboarding_data.py <DATABASE_URL>
```

### Legacy Service Deprecation

#### RecruitmentService

**Status**: Deprecated but functional

**Deprecation Notice**: Added to service docstring

**Migration Path**:
```python
# Old
from app.services.recruitment_service import RecruitmentService
await RecruitmentService.submit_application(db, payload)

# New
from app.services.agent_onboarding_service import AgentOnboardingService
await AgentOnboardingService.submit_application(db, payload)
```

#### OnboardingService

**Status**: Deprecated but functional

**Deprecation Notice**: Added to service docstring

**Migration Path**:
```python
# Old
from app.services.onboarding_service import OnboardingService
await OnboardingService.sign_contract(db, application_id, signee_name, signature_data, ip)

# New
from app.services.agent_onboarding_service import AgentOnboardingService
await AgentOnboardingService.complete_documentation(
    db, application_id,
    sign_contract=True,
    signee_name=signee_name,
    signature_data=signature_data,
    ip_address=ip
)
```

---

## General Migration Best Practices

### Testing Checklist

For all migrations, ensure you test:
- [ ] All CRUD operations work correctly
- [ ] Data validation passes
- [ ] No orphaned records exist
- [ ] Frontend functionality unchanged
- [ ] Error handling works properly
- [ ] Permissions are enforced
- [ ] Audit logs are generated

### Rollback Plan

If issues arise after migration:

1. **Immediate Rollback**
   - Revert endpoint imports to use legacy services
   - Legacy services remain functional

2. **Data Rollback**
   - No data migration was performed, so no rollback needed
   - Data validation script can be run to fix any issues

3. **Investigation**
   - Review error logs
   - Identify root cause
   - Fix and retry

### Benefits of Unification

### Code Quality
- **Single Source of Truth**: One service for all operations
- **Reduced Duplication**: Eliminates scattered logic
- **Better Maintainability**: Easier to update logic
- **Clearer Data Flow**: Explicit handling of all flows

### Functionality
- **Enhanced Features**: Detailed tracking now available
- **Backward Compatibility**: Simple modes still supported
- **Flexible API**: Optional parameters for advanced features
- **Better Progress Tracking**: Comprehensive status reporting

### Developer Experience
- **Clearer API**: Single entry point for operations
- **Better Documentation**: Comprehensive migration guides
- **Deprecation Warnings**: Clear guidance for legacy code
- **Validation Tools**: Data validation scripts for consistency

---

**Last Updated:** May 1, 2026
