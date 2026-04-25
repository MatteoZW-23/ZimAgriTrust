# USSD Architecture Documentation

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📱 Feature Phone        📱 Smartphone        💻 USSD Simulator  │
│     (Basic)                 (Any)              (Testing)         │
│        │                      │                     │            │
│        └──────────────────────┴─────────────────────┘            │
│                              │                                   │
│                         Dial *123#                               │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TELECOM GATEWAY LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🌐 Telecom Gateway (Production)    🧪 USSD Simulator (Dev)     │
│     - Africa's Talking                  - Flask App              │
│     - Twilio                            - Port 5000              │
│     - Local Telco                       - Web Interface          │
│                                                                   │
│  Formats: session_id, phone_number, text                         │
│                                                                   │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               │ HTTP POST
                               │ /api/v1/ussd/session
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🚀 FastAPI Backend (Port 8080)                                  │
│     ├── CORS Middleware                                          │
│     ├── Rate Limiting                                            │
│     ├── Authentication                                           │
│     └── Audit Logging                                            │
│                                                                   │
│  Endpoint: POST /api/v1/ussd/session                             │
│  Router: app/api/v1/endpoints/ussd.py                            │
│                                                                   │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🧠 USSDService (app/services/ussd_service.py)                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  State Machine                                          │    │
│  │  ┌──────┐    ┌──────┐    ┌──────────┐    ┌──────┐     │    │
│  │  │ ROOT │───▶│ MENU │───▶│ AUTH_PIN │───▶│ FLOW │     │    │
│  │  └──────┘    └──────┘    └──────────┘    └──────┘     │    │
│  │                                                         │    │
│  │  Flows:                                                │    │
│  │  • SELL_CROP_* (5 states)                             │    │
│  │  • BUY_* (4 states)                                    │    │
│  │  • CHANGE_PIN_* (2 states)                            │    │
│  │  • VIEW_TRANSACTIONS (1 state)                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Features:                                                        │
│  ├── handle_request() - Main entry point                         │
│  ├── handle_menu_selection() - Menu routing                      │
│  ├── root_menu() - Menu display                                  │
│  └── Input validation & error handling                           │
│                                                                   │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│  SESSION CACHE   │  │   DATABASE   │  │   SERVICES   │
├──────────────────┤  ├──────────────┤  ├──────────────┤
│                  │  │              │  │              │
│  🗄️ Redis        │  │  🐘 Postgres │  │  📧 SMS      │
│  Port: 6379      │  │  Port: 5432  │  │  📱 WhatsApp │
│                  │  │              │  │  🤖 AI/ML    │
│  Session Data:   │  │  Tables:     │  │  💰 Payment  │
│  • state         │  │  • users     │  │  📊 Analytics│
│  • product_type  │  │  • listings  │  │              │
│  • quantity      │  │  • orders    │  │              │
│  • grade         │  │  • offers    │  │              │
│  • price         │  │  • disputes  │  │              │
│  • pending_sel   │  │  • trans...  │  │              │
│                  │  │              │  │              │
│  TTL: 5 minutes  │  │  Persistent  │  │  External    │
│                  │  │              │  │              │
└──────────────────┘  └──────────────┘  └──────────────┘
```

## 🔄 Request Flow Diagram

```
User Dials *123#
       │
       ▼
┌─────────────────┐
│ Telecom Gateway │
│  (or Simulator) │
└────────┬────────┘
         │
         │ POST /api/v1/ussd/session
         │ {
         │   "session_id": "abc123",
         │   "phone_number": "+263771234567",
         │   "text": "1*Maize*500"
         │ }
         ▼
┌─────────────────┐
│  FastAPI Router │
│  ussd.router    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  USSDService    │
│ handle_request()│
└────────┬────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│  Get Session    │              │  Parse Input    │
│  from Redis     │              │  text.split("*")│
└────────┬────────┘              └────────┬────────┘
         │                                 │
         └────────────┬────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   State Machine        │
         │   Switch on state      │
         └────────────┬───────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    ┌────────┐  ┌─────────┐  ┌─────────┐
    │  ROOT  │  │  MENU   │  │  FLOW   │
    └───┬────┘  └────┬────┘  └────┬────┘
        │            │            │
        │            │            │
        ▼            ▼            ▼
    ┌────────────────────────────────┐
    │   Business Logic               │
    │   • Validate input             │
    │   • Query database             │
    │   • Update session             │
    │   • Create records             │
    │   • Send notifications         │
    └────────────┬───────────────────┘
                 │
                 ▼
    ┌────────────────────────────────┐
    │   Generate Response            │
    │   USSDResponse(                │
    │     message="CON ...",         │
    │     end_session=False          │
    │   )                            │
    └────────────┬───────────────────┘
                 │
                 ▼
    ┌────────────────────────────────┐
    │   Return to Gateway            │
    │   {                            │
    │     "message": "CON ...",      │
    │     "end_session": false       │
    │   }                            │
    └────────────┬───────────────────┘
                 │
                 ▼
    ┌────────────────────────────────┐
    │   Display to User              │
    │   (on phone screen)            │
    └────────────────────────────────┘
```

## 🗂️ Data Flow

### Session Management
```
┌──────────────────────────────────────────────────────────┐
│                    Session Lifecycle                      │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  1. User Dials *123#                                     │
│     └─▶ session_id generated by gateway                 │
│                                                           │
│  2. First Request (text="")                              │
│     └─▶ Create session in Redis                         │
│         {"state": "ROOT"}                                │
│                                                           │
│  3. Subsequent Requests (text="1*Maize*500")            │
│     └─▶ Load session from Redis                         │
│         Update state and data                            │
│         Save back to Redis                               │
│                                                           │
│  4. Session Expiry (5 minutes)                           │
│     └─▶ Redis auto-deletes                              │
│         Next request creates new session                 │
│                                                           │
│  5. Explicit End (END response)                          │
│     └─▶ Delete session from Redis                       │
│         User must dial again to restart                  │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### State Transitions
```
ROOT
 │
 ├─▶ MENU (display main menu)
      │
      ├─▶ Option 1: SELL_CROP_CROP
      │    └─▶ SELL_CROP_QTY
      │         └─▶ SELL_CROP_GRADE
      │              └─▶ SELL_CROP_PRICE
      │                   └─▶ SELL_CROP_LOCATION
      │                        └─▶ END (listing created)
      │
      ├─▶ Option 2: AUTH_PIN
      │    └─▶ BUY_BROWSE
      │         └─▶ BUY_QUANTITY
      │              └─▶ BUY_CONFIRM
      │                   └─▶ END (offer sent)
      │
      ├─▶ Option 3: Display prices → END
      │
      ├─▶ Option 4: AUTH_PIN → Display profile → END
      │
      ├─▶ Option 5: AUTH_PIN → Display wallet → END
      │
      ├─▶ Option 6: AUTH_PIN → Create dispute → END
      │
      ├─▶ Option 7: AUTH_PIN
      │    └─▶ CHANGE_PIN_NEW
      │         └─▶ CHANGE_PIN_CONFIRM
      │              └─▶ END (PIN changed)
      │
      ├─▶ Option 8: AUTH_PIN → VIEW_TRANSACTIONS
      │    └─▶ END or back to MENU
      │
      └─▶ Option 9: Display help → END
```

## 🔐 Security Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Security Layers                         │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Layer 1: Network Security                               │
│  ├─ HTTPS/TLS encryption                                 │
│  ├─ CORS policy                                          │
│  └─ Trusted host middleware                              │
│                                                           │
│  Layer 2: Authentication                                  │
│  ├─ Phone number verification                            │
│  ├─ PIN authentication (bcrypt)                          │
│  └─ Session validation                                   │
│                                                           │
│  Layer 3: Authorization                                   │
│  ├─ User role checks                                     │
│  ├─ Resource ownership validation                        │
│  └─ Operation permissions                                │
│                                                           │
│  Layer 4: Input Validation                               │
│  ├─ Numeric validation                                   │
│  ├─ Range checks                                         │
│  ├─ Format validation                                    │
│  └─ SQL injection prevention                             │
│                                                           │
│  Layer 5: Rate Limiting                                  │
│  ├─ Request throttling                                   │
│  ├─ Failed attempt tracking                              │
│  └─ Account lockout                                      │
│                                                           │
│  Layer 6: Session Security                               │
│  ├─ 5-minute timeout                                     │
│  ├─ Session isolation                                    │
│  └─ Automatic cleanup                                    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## 📊 Database Schema (USSD-Relevant)

```sql
-- Users Table
users
├── id (UUID, PK)
├── phone_number (VARCHAR, UNIQUE)
├── password_hash (VARCHAR) -- For app login
├── ussd_pin_hash (VARCHAR) -- For USSD auth
├── trust_score (INTEGER)
├── role (ENUM: FARMER, BUYER, AGENT, ADMIN)
├── preferred_language (VARCHAR: en, sn, nd)
└── ...

-- Listings Table
listings
├── id (UUID, PK)
├── seller_id (UUID, FK → users)
├── product_type (VARCHAR)
├── quantity (FLOAT)
├── grade (VARCHAR)
├── price_per_unit (FLOAT)
├── location_province (VARCHAR)
├── status (ENUM: ACTIVE, SOLD, EXPIRED)
└── ...

-- Offers Table
offers
├── id (UUID, PK)
├── listing_id (UUID, FK → listings)
├── buyer_id (UUID, FK → users)
├── quantity (FLOAT)
├── price_per_unit (FLOAT)
├── total_amount (FLOAT)
├── status (ENUM: PENDING, ACCEPTED, REJECTED)
└── ...

-- Orders Table
orders
├── id (UUID, PK)
├── seller_id (UUID, FK → users)
├── buyer_id (UUID, FK → users)
├── total_amount (FLOAT)
├── seller_payout (FLOAT)
├── status (ENUM: PENDING, ESCROW_HELD, DELIVERED, COMPLETED)
└── ...

-- Disputes Table
disputes
├── id (UUID, PK)
├── order_id (UUID, FK → orders)
├── raised_by (UUID, FK → users)
├── reason (TEXT)
├── status (ENUM: OPEN, IN_PROGRESS, RESOLVED)
└── ...

-- Transactions Table
transactions
├── id (UUID, PK)
├── user_id (UUID, FK → users)
├── transaction_type (ENUM: PAYMENT, WITHDRAWAL, ESCROW, etc.)
├── amount (FLOAT)
├── created_at (TIMESTAMP)
└── ...
```

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Load Balancer (Nginx/HAProxy)                       │  │
│  │  - SSL Termination                                   │  │
│  │  - Request routing                                   │  │
│  │  - Health checks                                     │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│         ┌─────────┼─────────┐                              │
│         │         │         │                              │
│         ▼         ▼         ▼                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│  │ Backend │ │ Backend │ │ Backend │                      │
│  │ Node 1  │ │ Node 2  │ │ Node 3  │                      │
│  │ (8080)  │ │ (8080)  │ │ (8080)  │                      │
│  └────┬────┘ └────┬────┘ └────┬────┘                      │
│       │           │           │                            │
│       └───────────┼───────────┘                            │
│                   │                                         │
│         ┌─────────┼─────────┐                              │
│         │         │         │                              │
│         ▼         ▼         ▼                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ Redis    │ │ Postgres │ │ Services │                   │
│  │ Cluster  │ │ Primary  │ │ (SMS,    │                   │
│  │          │ │ +Replica │ │  ML, etc)│                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Monitoring & Observability

```
┌──────────────────────────────────────────────────────────┐
│                  Monitoring Stack                         │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Metrics (Prometheus)                                    │
│  ├─ Request rate                                         │
│  ├─ Response time (p50, p95, p99)                       │
│  ├─ Error rate                                           │
│  ├─ Session count                                        │
│  └─ Feature usage                                        │
│                                                           │
│  Logs (ELK Stack)                                        │
│  ├─ Request/response logs                                │
│  ├─ Error logs                                           │
│  ├─ Audit logs                                           │
│  └─ Security logs                                        │
│                                                           │
│  Tracing (Jaeger)                                        │
│  ├─ Request flow                                         │
│  ├─ Database queries                                     │
│  ├─ External API calls                                   │
│  └─ Performance bottlenecks                              │
│                                                           │
│  Alerts                                                   │
│  ├─ High error rate (> 1%)                              │
│  ├─ Slow response (> 1s)                                │
│  ├─ Service down                                         │
│  └─ High load                                            │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

**Architecture Version**: 2.0  
**Last Updated**: 2026-04-23  
**Status**: Production Ready
