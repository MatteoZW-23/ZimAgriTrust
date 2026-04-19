# AgriTrust: National Agricultural Marketplace

AgriTrust is a production-grade digital marketplace designed for Zimbabwe's agricultural sector. It connects rural farmers directly with commercial buyers through a secure, telecom-integrated platform.

## Key Features

*   **USSD Integration (`*123#`)**: Full marketplace accessibility for users with basic feature phones. No data connection required for farmers.
*   **Secure Escrow Payments**: Automated fund locking and release system (compatible with EcoCash and Mobile Money) to ensure payment security for both parties.
*   **Regional Agent Network**: Verified field agents provide logistical support, quality verification, and dispute resolution.
*   **Price Transparency**: Real-time market price monitoring and historical trend analysis to ensure fair trade.
*   **Identity & Trust**: Comprehensive KYC verification and performance-based trust ratings for all participants.

## Project Architecture

The system is built on a scalable, modular architecture:

*   **`backend/`**: FastAPI-based core services (Auth, Escrow, Marketplace, USSD Gateway).
*   **`dashboard/`**: React-based administrative control center for agents and HQ staff.
*   **`research/`**: Data analysis and modeling tools for market forecasting and risk management.
*   **`ussd-simulator/`**: Testing environment for GSM network interactions.

## Technical Specifications

*   **Backend**: Python 3.12, FastAPI, SQLAlchemy
*   **Database**: PostgreSQL 16 (Primary Ledger) & Redis (Cache)
*   **Frontend**: React 18, Professional UI with dark/light mode support
*   **Infrastructure**: Fully containerized Docker orchestration

## Quick Start

Deploy the entire stack with a single command:

```powershell
docker-compose up -d --build
```

Access points after launch:
*   **Management Dashboard**: `http://localhost:3000`
*   **System API**: `http://localhost:8080`
*   **USSD Test Tool**: `http://localhost:5000`

---

*AgriTrust is engineered for operational excellence and market integrity.*

🔗 [Developed by Mathew Mabira](https://www.linkedin.com/in/mathew-mabira-24861632b)
