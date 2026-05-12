# ZimAgriTrust Security And Portal Boundaries

This project uses strict role separation. Public users, drivers, agents, and admins do not share the same login path.

## Portal Map

| Portal | Route | Allowed Roles | Auth Path | Device |
| --- | --- | --- | --- | --- |
| Public website | `/` | Guest, Farmer, Buyer, Driver browsing public content | None for browsing | Web |
| Farmer/Buyer app | `/app/*` | `FARMER`, `BUYER` | `/api/v1/auth/app/login` | Web, Android, iOS |
| Driver app | mobile app only | `TRANSPORTER` | `/api/v1/auth/driver/login` | Android, iOS |
| Agent portal | `/agent/*` | `AGENT` | `/api/v1/agent/login`, `/api/v1/agent/verify-mfa` | Web only |
| Admin portal | `/admin/*` | `ADMIN`, `SUPER_ADMIN`, `REGIONAL_MANAGER` | `/api/v1/admin/login`, `/api/v1/admin/verify-mfa` | Web only |

## Backend Enforcement

- Role validation happens on the backend before a token is issued.
- Shared `/auth/login` and `/auth/verify-login-2fa` are disabled for staff and return `410 Gone`.
- Public registration only accepts farmer, buyer, and transporter accounts.
- Privileged accounts must be created or approved from the admin side.
- Backend dependencies validate token status, user status, role, session activity, and revoked sessions on protected requests.
- Driver endpoints require `TRANSPORTER`.
- Agent portal endpoints require `AGENT`.
- Admin endpoints accept admin-family roles only.

## Token And Session Policy

- Access token lifetime: 60 minutes.
- Refresh token lifetime: 7 days.
- Web clients receive HTTP-only cookies.
- Local Docker HTTP uses non-secure cookies when `FORCE_HTTPS=false`.
- Production must set `FORCE_HTTPS=true` behind TLS.
- Mobile apps store tokens in Expo SecureStore.
- USSD sessions remain separate and should expire after 2 minutes.

## Current Security Features Implemented

- Separate login endpoints for public app, driver app, agent portal, and admin portal.
- MFA-required flow for admin and agent portals.
- Server-side portal routing metadata in auth responses.
- Soft-delete/anonymization for users to preserve transaction, agent, driver, audit, and dispute history.
- Admin action audit logging for user status and soft-delete operations.
- Role-specific frontend redirects and access-denied screens.
- Docker environment defaults for 60-minute access tokens and 7-day refresh tokens.

## Production Requirements Still Needed Before Launch

- Configure real SMS provider credentials for OTP delivery.
- Configure WhatsApp Business API credentials and webhook verification.
- Configure EcoCash and OneMoney merchant credentials.
- Configure email provider credentials for receipts, security alerts, and reports.
- Add CAPTCHA provider after repeated login failures.
- Add biometric unlock prompts on mobile after first verified login.
- Enforce TLS at the load balancer or reverse proxy.
- Run database migrations in production before deployment.
- Perform a third-party security review and payment compliance review before handling real escrow money.

## Migration

Run Alembic migrations after deploying the backend:

```powershell
docker compose exec backend alembic upgrade head
```

The migration `0022_security_portal_boundaries.py` expands `users.phone_number` so soft-deleted anonymized users no longer fail on PostgreSQL length constraints.
