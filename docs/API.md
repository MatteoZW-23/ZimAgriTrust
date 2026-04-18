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
