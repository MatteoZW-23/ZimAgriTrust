# 🛣️ ZimAgriTrust – Implementation Roadmap

> **Source of truth:** `docs/SYSTEM_SPECIFICATION.md` (348 functions). Coverage measured in `docs/SYSTEM_GAP_ANALYSIS.md` (current: ~58% complete, 28% partial, 14% missing).
>
> **Operating principle:** The platform is largely scaffolded. The roadmap is therefore **completion-oriented**, not greenfield. Every phase closes specific spec function IDs.
>
> **Cadence:** 2-week sprints. Each sprint closes a deliverable + tests + docs.
>
> **Generated:** 2026-05-05

---

## PHASE 0 – FOUNDATION AUDIT (Week 1, parallel to all)

**Goal:** Make the existing implementation traceable and testable.

| Task | Spec IDs | Owner area | Output |
|---|---|---|---|
| F0.1 Confirm trust score deltas match spec | 26–31 | backend/services/trust_service | Patch + unit test |
| F0.2 Audit USSD menu vs spec numbering | 198–219 | backend/services/ussd_service | Compliance report + patches |
| F0.3 Inventory WhatsApp commands vs spec | 220–244 | backend/services/whatsapp_service | Command registry doc |
| F0.4 Inventory existing notification templates | 245–287 | backend/services | `notifications/templates.py` registry mapped to spec IDs |
| F0.5 Add `make spec-coverage` script | – | tooling | Generates coverage table from grep of `# F#NNN` markers |

**Exit criteria:** Every implemented function carries a `# F#NNN` traceability comment. Coverage tool runs in CI.

---

## PHASE 1 – P0 COMPLETION (Sprints 1–2)

### Sprint 1 – Listings CRUD + Email Service

**Listings completion** (closes #52, #53, #54, #56, #57, #58, #89, #92, #94)

| Task | Endpoint / file | Spec |
|---|---|---|
| 1.1 `GET /listings/{id}` (single detail) | `endpoints/listings.py` | #89 |
| 1.2 `PUT /listings/{id}` (edit) | same | #53 |
| 1.3 `DELETE /listings/{id}` (delete) | same | #54 |
| 1.4 `POST /listings/{id}/photos` + `DELETE /listings/{id}/photos/{idx}` | + `media_service` | #52 |
| 1.5 `GET /listings/{id}/stats` (views, offers, conversion) | + counter in middleware | #56 |
| 1.6 `POST /listings/{id}/boost` ($2 fee, premium flag) | + `revenue_service` | #57, #229 |
| 1.7 `POST /listings/{id}/expire` + cron job | + scheduler | #58 |
| 1.8 `POST /users/me/saved-listings/{id}` + `DELETE` + `GET` | new `users` router | #92 |
| 1.9 `POST /listings/{id}/report` (abuse) | + admin queue | #94 |
| 1.10 `GET /listings/search` add `min_quantity`, `max_quantity`, `sort_by` params | existing | #87, #88 |

**Email service** (closes 10 templates + #297, #303)

| Task | File | Spec |
|---|---|---|
| 1.11 `app/services/email_service.py` (SendGrid + AWS SES dual provider, retry+queue) | new | 32-equiv for email |
| 1.12 Jinja templates `app/templates/email/*.html` (10 templates) | new | 278–287 |
| 1.13 Wire receipts → email on payment release | `escrow_service` | #297 |
| 1.14 `GET /wallet/statement.pdf` (monthly) + email delivery | `wallet_service` + new pdf util | #303 |

**Sprint 1 exit:** Listings CRUD complete. Email service live. All 10 email templates send via test endpoint.

---

### Sprint 2 – Driver Real-Time + Notifications Registry

**Driver real-time** (closes #124, #129, #132, #134, #333, #334, #335)

| Task | File | Spec |
|---|---|---|
| 2.1 `POST /drivers/me/online` + `POST /drivers/me/offline` (status toggle in Redis) | `drivers.py` + `cache_service` | #124, #129 |
| 2.2 WebSocket `/ws/drivers/{driver_id}/location` (push GPS to subscribed buyers) | new `app/api/v1/ws/` | #333 |
| 2.3 ETA calculator (`logistics_service.compute_eta`) using haversine + avg speed | `logistics_service` | #334 |
| 2.4 Delay alert generator (cron compares ETA vs actuals → SMS/WhatsApp) | + scheduler | #335 |
| 2.5 Photo upload on pickup/delivery confirmation | `drivers.py` `update_delivery_status` | #132, #134 |
| 2.6 Signature capture endpoint (base64 PNG) | same | #134 |

**Notification template registry** (closes 245–287 traceability)

| Task | File | Spec |
|---|---|---|
| 2.7 `app/services/notifications/registry.py` enumerating 43 templates with `(spec_id, channel, key, payload_schema)` | new | 245–287 |
| 2.8 Refactor `sms_service`, `whatsapp_service`, `email_service` to source from registry | refactor | – |
| 2.9 `GET /admin/notifications/templates` (admin can preview/edit) | `admin/notifications.py` | #193 |
| 2.10 `POST /admin/notifications/broadcast` (multi-channel) | same | #193 |

**Sprint 2 exit:** Driver online/offline live. Live tracking via WS demoable. All 43 notifications registered and sourced from one registry.

---

## PHASE 2 – P1 COMPLETION (Sprints 3–4)

### Sprint 3 – Public Website Decomposition + Farming Tools

**Public website pages** (closes #42, #43, #44 + cleanup of 35–41)

| Task | File | Spec |
|---|---|---|
| 3.1 Split `apps/public-website/src/App.jsx` into `pages/Home`, `HowItWorks`, `Pricing`, `About` | refactor | 35–41 |
| 3.2 New page `pages/HelpCenter.jsx` with searchable FAQs (markdown-driven) | new | #42 |
| 3.3 New page `pages/Terms.jsx` | new | #43 |
| 3.4 New page `pages/Privacy.jsx` | new | #44 |
| 3.5 Add React Router; SEO meta per page | refactor | – |
| 3.6 Pull homepage market snapshot from `/market/summary` | wire | #36 |

**Farming tools** (closes #78–81, #79, #275)

| Task | File | Spec |
|---|---|---|
| 3.7 Weather integration (OpenWeatherMap) `services/weather_service.py` + `/weather` endpoint | new | #79, #223 |
| 3.8 `services/farming_tips_service.py` + content store + `/farming/tips` endpoint | new | #78 |
| 3.9 Planting calendar dataset + `/farming/calendar` | new | #80 |
| 3.10 Fertilizer calculator endpoint `/farming/fertilizer-calc` | new | #81 |
| 3.11 Frontend Farmer Dashboard – farming tools card | `user-mobile` | #78–81 |
| 3.12 Weather alert template + cron trigger on storm warnings | notifications | #275 |

**Sprint 3 exit:** Public website is multi-page. Farming tools live and visible in farmer dashboard.

---

### Sprint 4 – Price Alerts + Listing UX + Buyer Offer Mgmt

**Price alerts** (closes #49, #274)

| Task | File | Spec |
|---|---|---|
| 4.1 `models/price_alert.py` (user_id, crop, threshold, direction) | new | #49 |
| 4.2 `POST/GET/DELETE /market/alerts` | new | #49 |
| 4.3 Cron checks alerts vs latest price → WhatsApp (with chart) | scheduler + `whatsapp_service` | #274 |

**Buyer offer mgmt** (closes #97, #98)

| Task | File | Spec |
|---|---|---|
| 4.4 `GET /offers/sent` (buyer-side) | listings/offers | #97 |
| 4.5 `POST /offers/{id}/cancel` | same | #98 |

**Frontend polish for farmer/buyer flows** (#56, #92 in UI)

| Task | Spec |
|---|---|
| 4.6 Listing stats UI (My Listings) | #56 |
| 4.7 Saved listings UI (Marketplace) | #92 |
| 4.8 Report listing modal | #94 |

**Sprint 4 exit:** Price alerts live with WhatsApp delivery. Buyer offer management UI complete.

---

## PHASE 3 – P2 COMPLETION (Sprints 5–6)

### Sprint 5 – Driver App Polish + Cooperative Transport + Tier Engine

**Driver app** (closes #119, #125 map, #127, signature)

| Task | File | Spec |
|---|---|---|
| 5.1 Live selfie + handwritten date verification (computer vision) | `verification_service` | #119 |
| 5.2 Driver app map view of available jobs (Mapbox/Google) | `driver-mobile/src/screens/JobsScreen` | #125 |
| 5.3 Fare negotiation counter flow | `drivers.py` + screen | #127 |
| 5.4 Real-time delivery tracking screen consumes WS | `DeliveryTrackingScreen` | #333 |

**Cooperative transport** (closes #332)

| Task | File | Spec |
|---|---|---|
| 5.5 `models/cooperative_trip.py` linking multiple orders to one driver/vehicle | new | #332 |
| 5.6 `POST /logistics/cooperative-trip` matching algo | `logistics_service` | #332 |

**Driver tier engine** (closes #321–328)

| Task | File | Spec |
|---|---|---|
| 5.7 `services/driver_tier_service.py` evaluating tier transitions nightly | new | #321–324 |
| 5.8 Bonus calculator (peak hour, volume, tier, rating) | `agent_earnings_service` analog for drivers | #325–328 |
| 5.9 Driver earnings screen shows tier + bonus breakdown | `EarningsScreen` | #135 |

**Sprint 5 exit:** Drivers see tier progression, bonus breakdown. Cooperative trips bookable.

---

### Sprint 6 – Agent Portal Decomposition + WhatsApp Polish

**Agent portal** (closes 139–162 UX gaps)

| Task | File | Spec |
|---|---|---|
| 6.1 Split `apps/agent-portal/src/App.jsx` into routed screens: Dashboard, VerificationForm, DisputeResolution, TrainingAcademy | refactor | 27–30 (frontend) |
| 6.2 Agent leaderboard / ranking page | new | #162 |
| 6.3 `/agents/performance` returns structured stats | backend | #161 |
| 6.4 GPS-tagged photo upload (capture EXIF) | verification flow | #154 |

**WhatsApp polish**

| Task | Spec |
|---|---|
| 6.5 `forecast`, `trending` commands | #221, #222 |
| 6.6 `weather [location]` (uses weather_service) | #223 |
| 6.7 `boost [id]` → payment intent | #229 |

**Sprint 6 exit:** Agent portal fully separated. WhatsApp commands match spec §3.9.

---

## PHASE 4 – P3 COMPLETION (Sprints 7–9)

### Sprint 7 – Loan Module Foundation (closes 337–344)

| Task | File | Spec |
|---|---|---|
| 7.1 `models/loan.py` (Loan, LoanProduct, LoanRepayment, LoanPurpose) + migration | new | #337–348 |
| 7.2 `services/loan_service.py` (eligibility, calc, lifecycle) | new | #337, #340 |
| 7.3 Endpoints: `GET /loans/eligibility`, `GET /loans/products`, `POST /loans/apply`, `GET /loans/me`, `GET /loans/{id}`, `POST /loans/{id}/repay` | new router | #337–343 |
| 7.4 Disbursement to wallet on approval | `wallet_service` | #344 |
| 7.5 Frontend Loan screens (farmer) | `user-mobile` | – |

### Sprint 8 – Loan Verification & Approval (closes 345–348)

| Task | File | Spec |
|---|---|---|
| 8.1 Agent loan verification task type | `agent_assignment` | #345, #346 |
| 8.2 `POST /agents/loans/{id}/verify` (purpose + viability) | new | #345, #346 |
| 8.3 Admin loan approval UI + `POST /admin/loans/{id}/approve` and `/reject` | admin/users analog | #347, #348 |
| 8.4 Loan reminder cron (WhatsApp + SMS) | scheduler | #277 (loan reminder) |

### Sprint 9 – Reporting, PDF Pipeline, Auto-Withdrawal

| Task | File | Spec |
|---|---|---|
| 9.1 Unified PDF generator `app/services/pdf_service.py` (WeasyPrint or reportlab) | new | #197, #303, #320 |
| 9.2 Daily/weekly/monthly reports as PDF + email | scheduler | #194–197 |
| 9.3 Auto-withdrawal config `users.auto_withdraw_threshold` + cron | `wallet_service` | #304 |
| 9.4 Pending transactions filter | `wallet_service` | #302 |

**Phase 4 exit:** All 348 spec functions are at minimum 🟡; ≥95% are ✅.

---

## PHASE 5 – HARDENING (Sprint 10)

| Task | Spec area |
|---|---|
| 10.1 Security audit: JWT lifetimes, rate limits, MFA on admin, OTP expiry | §4.7 |
| 10.2 Encryption-at-rest verification (AES-256) | §4.7 |
| 10.3 Audit log completeness review | §4.7 |
| 10.4 USSD 2-min session timeout enforcement | §4.7 |
| 10.5 OTP 5-min expiry, 3-attempt lock | §4.7 |
| 10.6 End-to-end test suite covering one trace per spec category | – |
| 10.7 Load test: 1k concurrent USSD, 10k WhatsApp/min | – |

---

## CROSS-CUTTING TRACKS (run continuously)

- **Tests:** Every endpoint added must ship with a pytest + a frontend screen test where applicable.
- **Migrations:** Alembic revisions for every schema change; never edit existing migrations.
- **Docs:** Update `docs/SYSTEM_GAP_ANALYSIS.md` coverage table at end of each sprint.
- **Traceability:** Comment every implemented spec function with `# F#NNN` (Python) or `// F#NNN` (JS).
- **CI:** `make spec-coverage` must run on every PR; fail if coverage drops.

---

## TIMELINE SUMMARY

| Phase | Sprints | Weeks | Functions closed |
|---|---|---|---|
| 0. Foundation audit | – | 1 | traceability only |
| 1. P0 completion | 1–2 | 2–4 | ~30 closures |
| 2. P1 completion | 3–4 | 5–8 | ~25 closures |
| 3. P2 completion | 5–6 | 9–12 | ~25 closures |
| 4. P3 completion | 7–9 | 13–18 | ~30 closures (loans + reports) |
| 5. Hardening | 10 | 19–20 | quality gate |
| **Total** | **10 sprints** | **~20 weeks** | **all 348 covered** |

---

## RISK REGISTER

| Risk | Mitigation |
|---|---|
| WhatsApp service complexity (127 KB single file) | Decompose into command modules in Phase 0 |
| USSD compliance drift | F0.2 audit + regression tests with real session traces |
| Email provider lock-in | Dual-provider design (SendGrid + SES) from day 1 |
| Loan module regulatory exposure | Legal review before Sprint 7 launch |
| Live GPS scaling | Use Redis pub/sub, not direct WS broadcast, from day 1 |

---

## IMMEDIATE NEXT STEP (Sprint 1, Day 1)

Begin with **Listings CRUD completion** — it is the highest-leverage P0 gap, blocks farmer/buyer UX, and is mechanical work. See `docs/SYSTEM_GAP_ANALYSIS.md` §5 priority list.
