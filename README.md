<h1 align="center">AgriTrust Marketplace System</h1>

<p align="center">
  <strong>An Advanced, Telecom-Powered Digital Economy for Modern Agriculture</strong>
</p>

---

## 🌍 1. Introduction: Solving Real-World Agricultural Problems

In emerging economies, agricultural markets suffer from a massive disconnect. Rural farmers often lack access to smartphones and standard internet services. When trying to sell produce remotely, there is zero intrinsic trust between the farmer and commercial buyers—resulting in exploitation by physical middlemen who absorb the majority of the profit margins.

**The AgriTrust Solution:** 
AgriTrust is a telecom-integrated marketplace designed to dismantle these structural inefficiencies. We connect remote farmers directly with nationwide commercial buyers by bridging the digital divide through native **USSD integration (`*123#`)**. The platform is secured by programmatic financial **Escrow workflows** and advanced data validation that protects participants from fraud and ensures transparent commodity pricing.

---

## 🌟 2. Core Operational Pillars

This platform functions exclusively on the principles of accessibility and absolute trust.

*   📶 **Telecom Inclusion (USSD & SMS)**: Farmers with standard basic feature phones can register, check global market prices, and list metric tons of produce entirely offline over GSM networks.
*   💵 **Zero-Trust Escrow Payments**: Fully integrated with Mobile Money APIs (like EcoCash). When a buyer commits to an order, the specific capital is securely deducted and locked in a central staging wallet. Funds are exclusively released to the farmer upon verified physical delivery.
*   ⚖️ **Agent Dispute Arbitration**: If a logistical discrepancy occurs, funds remain frozen. Designated regional support agents can intervene, reviewing evidence and programmatically forcing a refund or releasing the capital.
*   🛡️ **Security & Validation**: The core backend enforces strict identity verification and transaction monitoring to halt recurring fraud immediately and maintain market stability.

## 🏗️ 3. System Architecture

AgriTrust operates on a highly scalable, decoupled microservices architecture. The entire ecosystem is containerized for seamless, enterprise-grade deployment.

### 3.1 Component Architecture Map
```mermaid
graph TD
    classDef client fill:#3b82f6,stroke:#1e40af,stroke-width:2px,color:#fff;
    classDef core fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef data fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef external fill:#6366f1,stroke:#4338ca,stroke-width:2px,color:#fff;

    %% Client Layer
    subgraph Client Endpoints
        A[React Web Dashboard]:::client
        B[React Native Mobile]:::client
        C[USSD Network Interface]:::client
    end

    %% API / Business Layer
    subgraph Core Backend Services
        D{FastAPI Gateway}:::core
        E[Auth & Identity Control]:::core
        F[Escrow Fintech Module]:::core
        G[Node IoT Gateway]:::core
    end

    %% Infrastructure
    subgraph Infrastructure
        DB[(PostgreSQL)]:::data
        RD[(Redis Cache)]:::data
    end

    A <-->|REST/WSS| D
    B <-->|REST| D
    C <-->|Telco API| D
    
    D --> E
    D --> F
    D --> G
    
    D <--> DB
    D <--> RD
```

### 3.2 Escrow Commerce Flow (DFD)
This sequence ensures neither party inherits risk during a transaction execution.
```mermaid
sequenceDiagram
    participant B as Merchant Buyer
    participant F as AgriTrust Platforms
    participant API as Core Backend
    participant EC as Mobile Money Escrow

    B->>F: Submit Purchase Offer
    F->>API: POST /transactions/initiate
    API->>API: Evaluate Transaction Integrity
    API->>EC: Process Mobile Money Fund Lock
    EC-->>API: Confirmation: Funds Secured
    API-->>F: Payment Successful. Farmer Dispatched.
```

### 3.3 Database Entity Design (ERD)
The underlying PostgreSQL database relies on strict schema validations to enforce referential security for financial logs.
```mermaid
erDiagram
    USERS {
        int id PK
        string phone_number UK
        string role "ADMIN, FARMER, BUYER, AGENT"
        float trust_score
    }
    LISTINGS {
        int id PK
        int farmer_id FK
        float price_per_unit
        string status "ACTIVE, SOLD"
    }
    TRANSACTIONS {
        int id PK
        int listing_id FK
        float total_amount
        string escrow_status "PENDING, LOCKED, DELIVERED, DISPUTED"
    }
    USERS ||--o{ LISTINGS : "creates"
    LISTINGS ||--o{ TRANSACTIONS : "locked in"
```

---

## 🏗️ 3. Sovereign Operational Fidelity ("Real Coded" Infrastructure)

Unlike generic marketplace templates, AgriTrust is engineered for high-fidelity technical oversight:

*   **Institutional Node Telemetry**: Every regional gateway (Harare, Mutare, etc.) is monitored via live SS7/API heartbeats.
*   **Secure Access Protocols**: Transitioned to secure, banking-standard **Numeric PIN-based Authentication** for rapid field access.
*   **Private Negotiation Hubs**: Trade commitments are securely sealed, keeping direct negotiations between farmers and commercial buyers isolated and recorded.
*   **Live Metrics Engine**: The dashboard features real-time telemetry demonstrating network latency and institutional build identifiers.
*   **Zero-AI Determinism**: The platform operates on fixed, auditable protocols. There is no non-deterministic AI behavior—only precise, automated trade execution governed by professional copy.

---

## 💻 4. Technical Stack

*   **Core Backend**: Python 3.12 (FastAPI, SQLAlchemy, Pydantic)
*   **Database**: PostgreSQL 16 (Relational Grade)
*   **Cache/Sessions**: Redis 7
*   **Web Dashboard**: React 18
*   **Styling & Design System**: Modern B2B Marketplace UI (AgriXchange-inspired palette: `#20963D` Action Green, `#000E2B` Institutional Navy)
*   **Typography**: `Noto Sans` (Body Data) & `Jost` (UI Components)
*   **Localization**: Professional Business English with localized regional references (Zero vernacular slang).
*   **Infrastructure**: Fully containerized Docker environment with automated node orchestration.

---

## 🚀 5. Getting Started (One-Command Deployment)

The entire platform is orchestrated via Docker Compose. This ensures all services (Database, Redis, Backend, Gateway, Dashboard, and Simulator) are launched in a consistent, professional environment.

### Step 5.1: Launch the Infrastructure
Ensure you have Docker and Docker Compose installed, then run:
```powershell
# In the project root
docker compose up -d --build
```

### Step 5.2: Access the Services
Once running, the following endpoints are available:
*   **Agent Web Dashboard**: `http://localhost:3000`
*   **Core API Gateway**: `http://localhost:8080`
*   **USSD Simulator**: `http://localhost:5000`
*   **IoT Node Gateway**: `http://localhost:3005`

### Step 5.3: Provision Demo Data
To preload the system with a complete agricultural data set (Farmers, Buyers, Listings):
1. Log into the Dashboard with the **Master Admin** account.
2. Click the `Sync Platform` button in the National Command Center.

---

## 🎯 6. User Roles & The "Perfect Loop" Demo

The system employs extremely rigid Role-Based Access Controls (RBAC). 

**Pre-Configured Demo Accounts:**
*(Authentication leverages secure Numeric PINs. Default accounts are listed below)*
| Role Assignment | Associated Account Name | Phone Number | Default PIN |
| :--- | :--- | :--- | :--- |
| **Admin** | MJ Admin | `0771234567` | `123456` |
| **Agent** | T. Miller | `0711234567` | `123456` |
| **Farmer**| Alex Johnson | `0781234567` | `123456` |
| **Buyer** | Bulk Industrial Buyer | `0791234567` | `123456` |

**Walkthrough (The Perfect Loop):**
1. Log into the `Web Dashboard` as the **Farmer**. Navigate to the Marketplace, and click `Add Listing`. List 500 units of Maize.
2. Log out, and log in as the **Buyer**. Filter the marketplace for Maize.
3. Select the Farmer's listing and initiate a transaction. The system triggers the Escrow deduction locally.
4. Log out, and log back in as the **Farmer**. In your "Orders" tab, observe that you have a shipment marked `ESCROW_LOCKED`. Deliver the goods. 
5. The **Buyer** confirms the delivery on their end. The system fully releases the Escrow funds into the Farmer's simulated Mobile Wallet and records System Revenue identically matching 1.5%.

---
⭐ *Engineered to empower modern agriculture through incorruptible code and operational excellence.*

🔗 [Connect with Mathew Mabira on LinkedIn](https://www.linkedin.com/in/mathew-mabira-24861632b)
