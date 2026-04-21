# Architecture Overview

## The AgriTrust Platform
AgriTrust is a highly modular, event-driven national agricultural platform. 

### Key Components
1. **Backend API (FastAPI)**: Heavy-lifting system core. Connects to PostgreSQL and Redis.
2. **Node Gateway**: Real-time aggregation node for national data. 
3. **Agent Dashboard (React/Vite)**: Comprehensive UI for staff, admins, farmers, and buyers. 
4. **Notebook Scheduler**: Automated data science pipeline for training and inferencing models. 
5. **USSD Simulator**: A gateway mockup for SMS/USSD unstructured supplementary service data.

### Data Flow
1. User logs in via the dashboard or USSD.
2. Backend API routes state updates and triggers database transactions. 
3. Machine Learning Scheduler routinely sweeps PostgreSQL data to detect anomalies or predict market prices.
4. Redis caches common routes for velocity.
# AgriTrust API Documentation

## Base URL
`/api/v1`

## Authentication
All endpoints require a Bearer token received via `/auth/login`.

## Domains
* **Auth**: `/auth/register`, `/auth/login`
* **Market**: `/market` (prices, analytics, forecasts)
* **Listings**: `/listings` (supply creation, browse)
* **Transactions**: `/transactions` (orders, invoices)
* **Admin/Governance**: `/admin` (overview, disputes, KYC)

## Security
Endpoints are strictly protected based on Role-Based Access Control (`ADMIN`, `AGENT`, `FARMER`, `BUYER`).
Requests use signature validation and are audited.
