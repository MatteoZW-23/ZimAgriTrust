# AgriTrust Enterprise Architecture Design
**Version:** 1.0  
**Date:** May 3, 2026  
**Status:** Reference Architecture - Implementation Phase

---

## TABLE OF CONTENTS
1. [Architecture Overview](#architecture-overview)
2. [Design Principles](#design-principles)
3. [System Architecture](#system-architecture)
4. [Folder Structure](#folder-structure)
5. [Core Patterns & Anti-Patterns](#core-patterns)
6. [Module Descriptions](#module-descriptions)
7. [Scalability & Performance](#scalability)
8. [Security Framework](#security)
9. [Migration Strategy](#migration)

---

## ARCHITECTURE OVERVIEW

### Current State Problems
- **52+ services** with overlapping responsibilities
- **2,500+ LOC** of duplicate code
- **God objects** (User, Agent, Listing models with 15+ concerns each)
- **Tight coupling** (services depend on each other directly)
- **No abstraction layer** for persistence (direct model access)
- **Monolithic frontends** with repeated API client logic
- **Inconsistent error handling** and logging
- **No clear domain boundaries**

### Target State: DDD + Layered Architecture
```
┌─────────────────────────────────────────────────────┐
│           PRESENTATION LAYER                         │
│  (Frontend Apps: Admin, Agent, App, Mobile Portals)  │
└────────────────┬──────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────┐
│           API GATEWAY / SERVICE LAYER                 │
│  (Orchestration, cross-cutting concerns)             │
└────────────────┬──────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────┐
│        DOMAIN / APPLICATION LAYER                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │   Onboarding │ │ Marketplace  │ │  Payments    │  │
│  │   Domain     │ │   Domain     │ │   Domain     │  │
│  └──────────────┘ └──────────────┘ └──────────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │    Supply    │ │  Analytics   │ │  Compliance  │  │
│  │    Domain    │ │   Domain     │ │   Domain     │  │
│  └──────────────┘ └──────────────┘ └──────────────┘  │
└────────────────┬──────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────┐
│         PERSISTENCE LAYER (Repository Pattern)        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │   User Repo  │ │ Listing Repo │ │  Agent Repo  │  │
│  └──────────────┘ └──────────────┘ └──────────────┘  │
└────────────────┬──────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────┐
│              INFRASTRUCTURE LAYER                      │
│  (Database, Cache, Message Queue, External APIs)     │
└──────────────────────────────────────────────────────┘
```

---

## DESIGN PRINCIPLES

### 1. SEPARATION OF CONCERNS
- Each service handles ONE domain
- Clear boundaries between bounded contexts
- No circular dependencies

**Example - WRONG:**
```python
# ❌ BAD: Agent service handles onboarding, compliance, training, jobs
class AgentService:
    def onboard_agent(self): pass
    def check_compliance(self): pass
    def assign_training(self): pass
    def post_job(self): pass
```

**Example - CORRECT:**
```python
# ✅ GOOD: Separate domains
class AgentOnboardingService:
    def apply(self): pass
    def verify_documents(self): pass
    def provision_account(self): pass

class ComplianceService:
    def check_status(self): pass
    def verify_qualification(self): pass

class TrainingService:
    def assign_module(self): pass
    def track_progress(self): pass
```

### 2. SINGLE RESPONSIBILITY PRINCIPLE (SRP)
- A class/function should have ONE reason to change
- Models should NOT contain business logic

**Example - WRONG:**
```python
# ❌ BAD: User model with 15+ concerns
class User(Base):
    # Identity
    id, email, phone_number
    # Profile
    first_name, last_name, profile_picture
    # Agent properties
    agent_rating, specialization, years_experience
    # Farmer properties
    farm_size, crops_grown, certified_organic
    # Buyer properties
    business_license, monthly_volume
    # Compliance
    kyc_verified, kyc_date, kyc_document_path
    # Payment
    payment_method, bank_account, mobile_money
    # Addresses
    home_address, work_address, farm_location
    # Settings
    notification_preferences, language, timezone
    # Activity
    last_login, created_at, updated_at
    # Methods that do business logic
    def calculate_risk_score(self): pass
    def verify_identity(self): pass
    def process_payment(self): pass
```

**Example - CORRECT:**
```python
# ✅ GOOD: Focused models with separated concerns
class BaseUser:
    id, email, phone_number, first_name, last_name

class UserIdentity:
    user_id, kyc_verified, kyc_document_path, risk_score

class AgentProfile:
    user_id, rating, specialization, years_experience, agent_rating

class FarmerProfile:
    user_id, farm_size, crops_grown, certified_organic

class PaymentInfo:
    user_id, payment_method, bank_account, mobile_money

class UserPreferences:
    user_id, notification_settings, language, timezone
```

### 3. DRY (DON'T REPEAT YOURSELF)
- Common logic in shared utilities
- Service layer abstraction
- Reusable components

### 4. LOOSE COUPLING, HIGH COHESION
- Services communicate via interfaces/events
- Not direct dependencies
- Clear contracts (schemas/DTOs)

### 5. TESTABILITY
- Dependencies injectable
- Pure functions where possible
- Mockable external services

---

## SYSTEM ARCHITECTURE

### Layered Architecture (Clean Architecture)

#### Layer 1: PRESENTATION LAYER
- **Frontend Applications** (React/Vue/React Native)
- **API Contracts** (OpenAPI specs)
- **Responsibilities:**
  - User interface rendering
  - Form validation (client-side)
  - Client-side state management
  - Call appropriate API endpoints

#### Layer 2: APPLICATION LAYER (API/Controllers)
- **HTTP Handlers** (FastAPI routes)
- **Request/Response DTO validation**
- **Orchestration of domain services**
- **Responsibilities:**
  - Route mapping
  - Request validation against schema
  - Call domain services
  - Format responses
  - Error handling
  - Logging

**Example:**
```python
# ✅ GOOD: Controller delegates to service
@router.post("/agents/apply", response_model=AgentApplicationSchema)
async def submit_agent_application(
    payload: AgentApplicationCreate,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends()
) -> AgentApplicationSchema:
    """
    POST /agents/apply
    Submit agent application for onboarding
    """
    try:
        application = await agent_service.apply(
            user_id=current_user.id,
            payload=payload
        )
        return AgentApplicationSchema.model_validate(application)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### Layer 3: DOMAIN/APPLICATION SERVICE LAYER
- **Use Case Implementation** (Business Logic)
- **Domain Models** (Value Objects, Aggregates)
- **Responsibilities:**
  - Enforce business rules
  - Coordinate between repositories
  - Transaction management
  - Domain events emission
  - Cross-domain orchestration

**Example:**
```python
# ✅ GOOD: Service implements business logic
class AgentOnboardingService:
    def __init__(self, 
        user_repo: UserRepository,
        agent_repo: AgentRepository,
        document_repo: DocumentRepository,
        notification_service: NotificationService
    ):
        self.user_repo = user_repo
        self.agent_repo = agent_repo
        self.document_repo = document_repo
        self.notification_service = notification_service
    
    async def apply(self, user_id: UUID, payload: AgentApplicationCreate) -> Agent:
        # Business rule: Check if user already applied
        existing = await self.agent_repo.find_by_user(user_id)
        if existing:
            raise ValueError("User already has pending application")
        
        # Business rule: Validate user can apply (not debarred, etc)
        user = await self.user_repo.get(user_id)
        if user.is_debarred:
            raise ValueError("User not eligible to apply")
        
        # Create application
        agent = Agent(user_id=user_id, status=AgentStatus.APPLIED, **payload.dict())
        agent = await self.agent_repo.create(agent)
        
        # Emit domain event
        await self.notification_service.notify_user(
            user_id,
            "Application submitted successfully"
        )
        
        return agent
```

#### Layer 4: PERSISTENCE/DATA ACCESS LAYER
- **Repository Pattern** (Abstract data access)
- **Query objects** (Complex queries)
- **Unit of Work Pattern** (Transaction management)
- **Responsibilities:**
  - Data retrieval/storage abstraction
  - Query construction
  - Transaction management
  - Data mapping (ORM)

**Example:**
```python
# ✅ GOOD: Repository abstracts persistence
class AgentRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, agent: Agent) -> Agent:
        self.db.add(agent)
        await self.db.flush()
        return agent
    
    async def get(self, agent_id: UUID) -> Optional[Agent]:
        return self.db.query(AgentModel).filter(
            AgentModel.id == agent_id
        ).first()
    
    async def find_by_user(self, user_id: UUID) -> Optional[Agent]:
        return self.db.query(AgentModel).filter(
            AgentModel.user_id == user_id
        ).first()
    
    async def find_by_status(self, status: AgentStatus) -> List[Agent]:
        return self.db.query(AgentModel).filter(
            AgentModel.status == status
        ).all()
    
    async def update(self, agent: Agent) -> Agent:
        self.db.merge(agent)
        await self.db.flush()
        return agent
    
    async def delete(self, agent_id: UUID) -> None:
        self.db.query(AgentModel).filter(
            AgentModel.id == agent_id
        ).delete()
        await self.db.flush()
```

#### Layer 5: INFRASTRUCTURE LAYER
- **External services** (Payment gateways, SMS providers)
- **Message queues** (Background jobs)
- **Caching** (Redis)
- **Logging & Monitoring**
- **Responsibilities:**
  - Technical implementation details
  - External API calls
  - Async job processing
  - Cross-cutting concerns

---

## FOLDER STRUCTURE

### Backend Structure (New)
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app initialization
│   │
│   ├── api/                             # APPLICATION LAYER
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agents.py            # Agent endpoints
│   │   │   │   ├── marketplace.py       # Marketplace endpoints
│   │   │   │   ├── users.py             # User endpoints
│   │   │   │   ├── payments.py          # Payment endpoints
│   │   │   │   ├── analytics.py         # Analytics endpoints
│   │   │   │   ├── compliance.py        # Compliance endpoints
│   │   │   │   └── health.py            # Health check endpoints
│   │   │   └── dependencies.py          # Dependency injection
│   │   └── schemas/                     # DTOs and validation
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       ├── marketplace.py
│   │       ├── user.py
│   │       ├── payment.py
│   │       ├── errors.py                # Error response schemas
│   │       └── common.py                # Shared schemas
│   │
│   ├── domains/                         # DOMAIN LAYER (Business Logic)
│   │   ├── __init__.py
│   │   ├── agent/                       # Agent bounded context
│   │   │   ├── __init__.py
│   │   │   ├── models.py                # Domain models (Agent, AgentApplication)
│   │   │   ├── value_objects.py         # Value objects (AgentStatus, Specialization)
│   │   │   ├── services.py              # Business logic (AgentOnboardingService)
│   │   │   ├── events.py                # Domain events (AgentCreated, etc)
│   │   │   └── exceptions.py            # Domain exceptions
│   │   │
│   │   ├── marketplace/
│   │   │   ├── __init__.py
│   │   │   ├── models.py                # Listing, Offer, BuyerRequest
│   │   │   ├── value_objects.py         # ListingStatus, OfferStatus, etc
│   │   │   ├── services.py              # Marketplace business logic
│   │   │   ├── events.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── user/
│   │   │   ├── __init__.py
│   │   │   ├── models.py                # Focused User model
│   │   │   ├── value_objects.py
│   │   │   ├── services.py              # User management
│   │   │   ├── events.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── payment/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── services.py
│   │   │   ├── events.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── compliance/
│   │   ├── supply/
│   │   └── analytics/
│   │
│   ├── infrastructure/                  # INFRASTRUCTURE LAYER
│   │   ├── __init__.py
│   │   ├── repositories/               # PERSISTENCE LAYER
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # Base repository class
│   │   │   ├── agent_repository.py
│   │   │   ├── user_repository.py
│   │   │   ├── listing_repository.py
│   │   │   ├── payment_repository.py
│   │   │   └── query_objects.py        # Complex query builders
│   │   │
│   │   ├── external/                  # External service integrations
│   │   │   ├── __init__.py
│   │   │   ├── payment_gateway.py
│   │   │   ├── whatsapp_client.py
│   │   │   ├── sms_provider.py
│   │   │   ├── ml_service.py
│   │   │   └── abstractions.py         # Interfaces for loose coupling
│   │   │
│   │   ├── queue/                     # Message queue (async jobs)
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── tasks.py
│   │   │   └── handlers.py
│   │   │
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py
│   │   │   └── strategies.py
│   │   │
│   │   └── observability/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       ├── metrics.py
│   │       └── tracer.py
│   │
│   ├── shared/                         # SHARED UTILITIES
│   │   ├── __init__.py
│   │   ├── exceptions.py               # Common exceptions
│   │   ├── types.py                    # Type definitions
│   │   ├── constants.py                # Enums, constants
│   │   ├── utils.py                    # Utility functions
│   │   └── security.py                 # Auth, encryption
│   │
│   ├── models.py                       # SQLAlchemy ORM models (separate from domain)
│   ├── database.py                     # DB session, connection
│   └── config.py                       # Configuration management
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   ├── unit/
│   │   ├── domains/
│   │   │   ├── agent/
│   │   │   ├── marketplace/
│   │   │   └── ...
│   │   ├── infrastructure/
│   │   │   ├── repositories/
│   │   │   └── external/
│   │   └── api/
│   ├── integration/
│   │   ├── test_agent_onboarding_flow.py
│   │   ├── test_marketplace_flow.py
│   │   ├── test_payment_flow.py
│   │   └── test_multi_domain_interactions.py
│   └── e2e/                            # End-to-end tests (with real DB)
│       └── test_user_journey.py
│
├── alembic/                            # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

### Frontend Structure (Shared)
```
packages/
├── shared/                              # SHARED CODE
│   ├── src/
│   │   ├── api/
│   │   │   ├── __init__.ts
│   │   │   ├── client.ts                # Single API client (not 3 copies!)
│   │   │   ├── endpoints/
│   │   │   │   ├── agent.ts
│   │   │   │   ├── marketplace.ts
│   │   │   │   ├── user.ts
│   │   │   │   ├── payment.ts
│   │   │   │   └── index.ts
│   │   │   ├── types/
│   │   │   │   ├── agent.ts
│   │   │   │   ├── marketplace.ts
│   │   │   │   └── index.ts
│   │   │   └── errors.ts
│   │   │
│   │   ├── hooks/                      # Reusable custom hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useApi.ts               # Generic API hook
│   │   │   ├── useNotification.ts
│   │   │   ├── useLocalStorage.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── components/                 # Shared UI components
│   │   │   ├── form/
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Select.tsx
│   │   │   │   ├── Upload.tsx
│   │   │   │   └── FormField.tsx
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── Container.tsx
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   ├── Loading.tsx
│   │   │   │   └── ErrorBoundary.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── store/                      # State management (Zustand/Redux)
│   │   │   ├── auth/
│   │   │   │   ├── authSlice.ts
│   │   │   │   └── authSelectors.ts
│   │   │   ├── ui/
│   │   │   ├── notification/
│   │   │   └── store.ts
│   │   │
│   │   ├── utils/
│   │   │   ├── validation.ts
│   │   │   ├── formatting.ts
│   │   │   ├── date.ts
│   │   │   └── constants.ts
│   │   │
│   │   ├── types/
│   │   │   ├── api.ts
│   │   │   ├── domain.ts
│   │   │   └── common.ts
│   │   │
│   │   ├── middleware/
│   │   │   ├── authMiddleware.ts
│   │   │   └── errorMiddleware.ts
│   │   │
│   │   └── index.ts
│   │
│   ├── package.json
│   └── tsconfig.json

apps/
├── admin-dashboard/
│   ├── src/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   └── vite.config.js
│
├── agent-portal/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── app-portal/                          # Buyer/Farmer portal
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
└── driver-mobile/                       # React Native
    └── src/
```

---

## CORE PATTERNS & ANTI-PATTERNS

### Pattern 1: Repository Pattern (Persistence Abstraction)

**WHY:** Abstracts data access logic, makes testing easier, allows switching DB without changing business logic.

**IMPLEMENTATION:**

```python
# ✅ GOOD: Repository interface
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

class IRepository(ABC):
    @abstractmethod
    async def get(self, id: UUID): pass
    
    @abstractmethod
    async def create(self, entity): pass
    
    @abstractmethod
    async def update(self, entity): pass
    
    @abstractmethod
    async def delete(self, id: UUID): pass


class AgentRepository(IRepository):
    def __init__(self, db: Session):
        self.db = db
    
    async def get(self, agent_id: UUID) -> Optional[Agent]:
        return self.db.query(AgentORM).filter_by(id=agent_id).first()
    
    async def create(self, agent: Agent) -> Agent:
        orm_agent = AgentORM(**agent.dict())
        self.db.add(orm_agent)
        self.db.flush()
        return Agent.from_orm(orm_agent)
    
    async def find_pending_applications(self) -> List[Agent]:
        return self.db.query(AgentORM).filter_by(
            status=AgentStatus.APPLIED
        ).all()


# ✅ GOOD: Service uses repository
class AgentOnboardingService:
    def __init__(self, agent_repo: IRepository):
        self.agent_repo = agent_repo  # Depends on interface, not implementation
    
    async def apply(self, user_id: UUID, payload: AgentApplicationCreate) -> Agent:
        agent = Agent(user_id=user_id, status=AgentStatus.APPLIED, **payload.dict())
        return await self.agent_repo.create(agent)
```

### Pattern 2: Service Locator / Dependency Injection

**WHY:** Services don't create their own dependencies, reducing coupling and enabling testing.

```python
# ✅ GOOD: Constructor injection
class AgentController:
    def __init__(self,
        agent_service: AgentOnboardingService = Depends(),
        notification_service: NotificationService = Depends()
    ):
        self.agent_service = agent_service
        self.notification_service = notification_service
    
    async def apply(self, payload: AgentApplicationCreate):
        return await self.agent_service.apply(payload)


# ✅ GOOD: Dependency container
class ServiceContainer:
    @staticmethod
    def get_agent_service(db: Session) -> AgentOnboardingService:
        agent_repo = AgentRepository(db)
        user_repo = UserRepository(db)
        notification_service = NotificationService()
        return AgentOnboardingService(agent_repo, user_repo, notification_service)
```

### Pattern 3: Value Objects & Enums

**WHY:** Encapsulates domain concepts, prevents invalid states.

```python
# ✅ GOOD: Type-safe enums
from enum import Enum

class AgentStatus(str, Enum):
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class ListingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SOLD = "sold"
    CLOSED = "closed"


# ✅ GOOD: Value objects for complex data
from pydantic import BaseModel, validator

class Money(BaseModel):
    amount: float
    currency: str = "USD"
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class Address(BaseModel):
    street: str
    city: str
    region: str
    postal_code: str
    country: str


# Usage
listing = Listing(
    title="Maize 50kg",
    price=Money(amount=5000, currency="KES"),
    location=Address(
        street="123 Main St",
        city="Nairobi",
        region="Nairobi",
        postal_code="00100",
        country="Kenya"
    )
)
```

### Pattern 4: Service Layer for Business Logic

**WHY:** Centralizes business rules, reusable across different APIs/clients.

```python
# ❌ BAD: Logic in controller
@router.post("/marketplace/offers")
async def create_offer(payload: OfferCreate, db: Session):
    listing = db.query(ListingORM).get(payload.listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    
    if listing.seller_id == current_user.id:
        raise HTTPException(400, "Cannot bid on own listing")
    
    if payload.price < listing.minimum_price:
        raise HTTPException(400, "Price below minimum")
    
    if current_user.wallet_balance < payload.price:
        raise HTTPException(400, "Insufficient funds")
    
    offer = OfferORM(
        listing_id=payload.listing_id,
        buyer_id=current_user.id,
        **payload.dict()
    )
    db.add(offer)
    db.commit()
    return offer


# ✅ GOOD: Logic in service
class MarketplaceService:
    def __init__(self, listing_repo, offer_repo, payment_repo):
        self.listing_repo = listing_repo
        self.offer_repo = offer_repo
        self.payment_repo = payment_repo
    
    async def create_offer(self, buyer_id: UUID, payload: OfferCreate) -> Offer:
        # Business rule: Listing must exist
        listing = await self.listing_repo.get(payload.listing_id)
        if not listing:
            raise ListingNotFoundError()
        
        # Business rule: Cannot bid on own listing
        if listing.seller_id == buyer_id:
            raise CannotBidOnOwnListingError()
        
        # Business rule: Price validation
        if payload.price < listing.minimum_price:
            raise PriceBelowMinimumError()
        
        # Business rule: Buyer must have sufficient balance
        buyer = await self.user_repo.get(buyer_id)
        if buyer.wallet_balance < payload.price:
            raise InsufficientFundsError()
        
        # Create offer
        offer = Offer(
            listing_id=payload.listing_id,
            buyer_id=buyer_id,
            **payload.dict()
        )
        
        return await self.offer_repo.create(offer)


# ✅ GOOD: Controller calls service
@router.post("/marketplace/offers", response_model=OfferSchema)
async def create_offer(
    payload: OfferCreate,
    current_user: User = Depends(get_current_user),
    marketplace_service: MarketplaceService = Depends()
):
    try:
        offer = await marketplace_service.create_offer(
            buyer_id=current_user.id,
            payload=payload
        )
        return OfferSchema.model_validate(offer)
    except (ListingNotFoundError, CannotBidOnOwnListingError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=402, detail=str(e))
```

### Pattern 5: Event-Driven Architecture (Optional but Recommended)

**WHY:** Decouples domains, enables async processing, maintains audit trail.

```python
# ✅ GOOD: Domain events
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class DomainEvent:
    event_id: UUID
    timestamp: datetime
    aggregate_id: UUID

@dataclass
class AgentAppliedEvent(DomainEvent):
    user_id: UUID
    specialization: str

@dataclass
class ListingCreatedEvent(DomainEvent):
    seller_id: UUID
    title: str
    price: float

@dataclass
class OfferCreatedEvent(DomainEvent):
    listing_id: UUID
    buyer_id: UUID
    offer_price: float


# ✅ GOOD: Event publisher
class EventPublisher:
    async def publish(self, event: DomainEvent):
        # Publish to message queue (e.g., Kafka, RabbitMQ, Redis)
        await self.queue.publish(event.event_id, event.dict())


# ✅ GOOD: Service emits events
class AgentOnboardingService:
    def __init__(self, agent_repo, event_publisher):
        self.agent_repo = agent_repo
        self.event_publisher = event_publisher
    
    async def apply(self, user_id: UUID, payload: AgentApplicationCreate) -> Agent:
        agent = Agent(user_id=user_id, **payload.dict())
        agent = await self.agent_repo.create(agent)
        
        # Emit domain event
        event = AgentAppliedEvent(
            event_id=uuid4(),
            timestamp=datetime.now(),
            aggregate_id=agent.id,
            user_id=user_id,
            specialization=payload.specialization
        )
        await self.event_publisher.publish(event)
        
        return agent


# ✅ GOOD: Event handlers (subscribers)
class AgentAppliedEventHandler:
    async def handle(self, event: AgentAppliedEvent):
        # Send email to admin
        # Create training plan
        # Add to review queue
        # Update analytics
        pass
```

### ANTI-PATTERN 1: Duplicate Services

**❌ PROBLEM:**
```python
# File 1: agent_onboarding_service.py
class AgentOnboardingService:
    @staticmethod
    def submit_application(db, payload):
        pass

# File 2: onboarding_service.py
class OnboardingService:
    @staticmethod
    def submit_application(db, payload):
        pass  # DUPLICATE!

# File 3: recruitment_service.py
class RecruitmentService:
    @staticmethod
    def submit_application(db, payload):
        pass  # DUPLICATE!
```

**✅ SOLUTION:**
```python
# File: domains/agent/services.py
class AgentOnboardingService:
    @staticmethod
    def submit_application(db, payload):
        # Single source of truth
        pass

# Usage everywhere
from domains.agent.services import AgentOnboardingService
```

### ANTI-PATTERN 2: God Objects

**❌ PROBLEM:**
```python
class User:
    # 50+ fields from different contexts
    id, email, phone, first_name, last_name
    kyc_verified, kyc_date, kyc_document
    agent_rating, specialization, years_exp
    farm_size, crops, certified_organic
    payment_method, bank_account, mobile_money
    # Methods from different domains
    def calculate_risk_score(self): pass
    def verify_identity(self): pass
    def process_payment(self): pass
    def assign_job(self): pass
```

**✅ SOLUTION:**
```python
# Core user
class User:
    id: UUID
    email: str
    phone: str
    first_name: str
    last_name: str

# Separate concerns into different aggregates
class UserIdentity:
    user_id: UUID
    kyc_verified: bool
    kyc_date: datetime
    
class AgentProfile:
    user_id: UUID
    agent_rating: float
    specialization: str
    
class FarmerProfile:
    user_id: UUID
    farm_size: float
    crops: List[str]
    
class PaymentProfile:
    user_id: UUID
    payment_method: str
    bank_account: str
```

### ANTI-PATTERN 3: Tight Coupling Between Services

**❌ PROBLEM:**
```python
class TransactionService:
    def __init__(self):
        self.marketplace_service = MarketplaceService()
        self.payment_service = PaymentService()
        self.whatsapp_service = WhatsappService()  # Why is this here?
    
    def process_transaction(self):
        listing = self.marketplace_service.get_listing()  # Direct call
        payment = self.payment_service.process()          # Direct call
        self.whatsapp_service.send_notification()          # Direct call
```

**✅ SOLUTION:**
```python
class TransactionService:
    def __init__(self,
        listing_repo: IRepository,
        transaction_repo: IRepository,
        event_publisher: IEventPublisher  # Notify via events, not direct calls
    ):
        self.listing_repo = listing_repo
        self.transaction_repo = transaction_repo
        self.event_publisher = event_publisher
    
    async def process(self, payload):
        # Get data via repository
        listing = await self.listing_repo.get(payload.listing_id)
        
        # Save transaction
        transaction = await self.transaction_repo.create(transaction)
        
        # Emit event - NotificationService will handle it
        await self.event_publisher.publish(
            TransactionCompletedEvent(transaction_id=transaction.id)
        )
```

---

## MODULE DESCRIPTIONS

### 1. AGENT DOMAIN
**Responsibility:** Manage agent lifecycle (application → onboarding → compliance → deactivation)
**Models:** User, Agent, AgentApplication, AgentTraining, ComplianceStatus
**Services:**
- `AgentOnboardingService`: Application → Account provisioning
- `AgentComplianceService`: Verification, certifications
- `AgentPerformanceService`: Rating, activity tracking

**Example Service:**
```python
class AgentOnboardingService:
    def __init__(self, user_repo, agent_repo, doc_repo, event_publisher):
        self.user_repo = user_repo
        self.agent_repo = agent_repo
        self.doc_repo = doc_repo
        self.event_publisher = event_publisher
    
    async def apply(self, user_id: UUID, payload: AgentApplicationCreate) -> Agent:
        # Check no existing application
        # Create application record
        # Emit AgentAppliedEvent
        pass
    
    async def verify_documents(self, app_id: UUID) -> Agent:
        # Check documents valid
        # Move to APPROVED status
        # Emit AgentApprovedEvent
        pass
    
    async def provision_account(self, agent_id: UUID) -> None:
        # Set up user permissions
        # Create wallet
        # Send welcome email
        # Emit AgentProvisionedEvent
        pass
```

### 2. MARKETPLACE DOMAIN
**Responsibility:** Listing creation, offer management, negotiations
**Models:** Listing, Offer, BuyerRequest, FarmerResponse
**Services:**
- `ListingService`: Create, update, publish listings
- `OfferService`: Manage offers, counter-offers
- `NegotiationService`: Handle buyer requests, negotiations

### 3. PAYMENT DOMAIN
**Responsibility:** Wallet management, transactions, settlements
**Models:** Wallet, Transaction, Payment, Settlement
**Services:**
- `PaymentService`: Process payments
- `WalletService`: Balance management
- `SettlementService`: Periodic settlements to farmers

### 4. COMPLIANCE DOMAIN
**Responsibility:** KYC, AML, regulatory compliance
**Models:** KYCStatus, ComplianceRecord, ComplianceAlert
**Services:**
- `KYCService`: Identity verification
- `AMLService`: Anti-money laundering checks
- `ComplianceReportingService`: Regulatory reporting

### 5. SUPPLY DOMAIN
**Responsibility:** Crop sourcing, supplier management
**Models:** Supplier, CropAvailability, SupplyAgreement
**Services:**
- `SupplierService`: Supplier management
- `CropService`: Crop listing, availability

### 6. ANALYTICS DOMAIN
**Responsibility:** Reporting, insights, dashboards
**Models:** AnalyticsEvent, Metric, Report
**Services:**
- `ReportingService`: Generate reports
- `InsightsService`: Calculate KPIs
- `DashboardService`: Dashboard data

---

## SCALABILITY & PERFORMANCE

### 1. Caching Strategy
```python
class CachedListingRepository:
    def __init__(self, db: Session, cache: Redis):
        self.db = db
        self.cache = cache
    
    async def get(self, listing_id: UUID) -> Optional[Listing]:
        # Try cache first (1ms)
        cached = await self.cache.get(f"listing:{listing_id}")
        if cached:
            return Listing.parse_obj(cached)
        
        # Fall back to DB (50ms)
        listing = self.db.query(ListingORM).get(listing_id)
        
        # Cache for 5 minutes
        if listing:
            await self.cache.setex(
                f"listing:{listing_id}",
                300,  # 5 minutes
                listing.json()
            )
        
        return listing
```

### 2. Async Processing
```python
# Heavy operations in background
class AnalyticsService:
    def __init__(self, event_publisher, queue):
        self.queue = queue
    
    async def on_transaction_completed(self, event: TransactionCompletedEvent):
        # Queue async job instead of blocking
        await self.queue.enqueue(
            "calculate_seller_metrics",
            {"transaction_id": event.transaction_id}
        )
        
        # Return immediately (user sees instant confirmation)
```

### 3. Database Optimization
```python
# Use appropriate indexes
class ListingORM(Base):
    __tablename__ = "listings"
    
    id = Column(UUID, primary_key=True)
    seller_id = Column(UUID, ForeignKey("users.id"), index=True)  # Search by seller
    status = Column(String, index=True)  # Search by status
    created_at = Column(DateTime, index=True)  # Sort by created_at
    
    __table_args__ = (
        Index("idx_seller_status", "seller_id", "status"),  # Composite index
    )
```

### 4. API Pagination & Filtering
```python
@router.get("/listings")
async def list_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),  # Max 100
    status: Optional[ListingStatus] = None,
    seller_id: Optional[UUID] = None,
    listing_service: ListingService = Depends()
):
    listings = await listing_service.search(
        skip=skip,
        limit=limit,
        filters={
            "status": status,
            "seller_id": seller_id
        }
    )
    return listings
```

### 5. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/agents/apply")
@limiter.limit("5/minute")
async def submit_application(
    request: Request,
    payload: AgentApplicationCreate,
    agent_service: AgentService = Depends()
):
    return await agent_service.apply(payload)
```

### 6. Connection Pooling
```python
# In database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Reuse 20 connections
    max_overflow=40,        # Allow 40 additional connections
    pool_recycle=3600,      # Recycle connections after 1 hour
    echo=False
)
```

---

## SECURITY FRAMEWORK

### 1. Authentication
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredential
import jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredential = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: UUID = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Fetch user from DB
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

### 2. Authorization (RBAC)
```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    FARMER = "farmer"
    BUYER = "buyer"

async def require_role(role: Role):
    async def check_role(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return check_role

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role(Role.ADMIN))
):
    # Only admins can delete users
    pass
```

### 3. Input Validation
```python
from pydantic import BaseModel, validator, EmailStr

class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    phone: str
    password: str
    
    @validator('password')
    def password_strong(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
    
    @validator('phone')
    def phone_valid(cls, v):
        # Validate format (e.g., +254...)
        if not v.startswith('+'):
            raise ValueError('Phone must start with +')
        return v
```

### 4. Encryption
```python
from cryptography.fernet import Fernet
import os

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_sensitive_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# Usage
kyc_document = encrypt_sensitive_data(user.kyc_document_path)
```

### 5. API Security Headers
```python
from fastapi.middleware import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## MIGRATION STRATEGY

### Phase 1: Foundation (Week 1-2)
1. Create new folder structure
2. Build repository pattern abstractions
3. Consolidate agent onboarding services → single service
4. Consolidate marketplace services → single service
5. Create shared utilities

### Phase 2: Frontend (Week 2-3)
1. Create shared `packages/shared`
2. Move common API client → single instance
3. Move shared hooks → shared package
4. Move shared components → shared package
5. Update imports in all 3 portals

### Phase 3: Domain Models (Week 3-4)
1. Refactor User model (split concerns)
2. Refactor Listing model
3. Create value objects
4. Add domain events

### Phase 4: Testing & Deployment (Week 4-6)
1. Write comprehensive tests
2. Update documentation
3. Deploy incrementally
4. Gradual traffic switch

---

## SUCCESS METRICS

After refactoring, measure:
- **Code duplication:** From 2,500 LOC → <100 LOC (96% reduction)
- **Test coverage:** From ~40% → >80%
- **Average response time:** Should remain same or improve (caching)
- **Service count:** From 52 → ~20 (62% reduction)
- **Deployment frequency:** Increase (less risk per change)
- **Mean time to recovery:** Decrease (better error handling)
- **Developer ramp-up time:** From 2 weeks → 3 days (better docs)
