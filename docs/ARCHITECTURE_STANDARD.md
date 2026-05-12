# 🏛️ ZimAgriTrust — Standard Architecture

> **Status:** Authoritative. All new code must follow this layout. Existing code is migrated incrementally per `docs/SYSTEM_ROADMAP.md`.
> **Source:** Formalizes the layered Clean-Architecture migration described in `backend/app/domain/README.md`.

---

## 1. PRINCIPLES

1. **Dependencies point inward.** UI → application → domain. Infrastructure plugs in via interfaces. The compiler/linter (`backend/.importlinter`) enforces this.
2. **Domain is pure Python.** No SQLAlchemy. No FastAPI. No Pydantic. No HTTP. No Redis. Aggregates are testable in milliseconds.
3. **Application defines ports; infrastructure provides adapters.** Use cases never know whether persistence is Postgres, in-memory, or a file.
4. **One source of truth per concept.** A notification template lives in `services/notifications/registry.py` and nowhere else; a price formula lives in one place; a trust delta is computed in one service.
5. **Spec traceability.** Every implemented spec function carries a `# F#NNN` comment. CI greps for missing IDs.

---

## 2. THE LAYERS

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              api  (FastAPI)                             │
│      thin controllers — translate HTTP → command/query → response       │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ depends on
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   application  (use cases & ports)                      │
│  ConfirmDelivery, CreateDispute, ApplyForLoan, …                        │
│  Defines abstract ports: OrderRepository, NotificationPort, EscrowPort  │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ depends on
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            domain  (pure)                               │
│  Aggregates (Order, Dispute, Loan), value objects (Money, OrderStatus), │
│  domain events (DeliveryConfirmed), domain exceptions                   │
└─────────────────────────────────────────────────────────────────────────┘
                           ▲ implemented by
                           │
┌─────────────────────────────────────────────────────────────────────────┐
│                infrastructure  (adapters, drivers, IO)                  │
│  SqlAlchemyOrderRepository, RedisRateLimiter, SendGridEmailAdapter,     │
│  TwilioSmsAdapter, EcoCashClient, LegacyEscrowAdapter (transitional)    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.1 `app/domain/`
- **What lives here:** `entities/` (aggregates), `value_objects.py`, `events.py`, `exceptions.py`.
- **What never lives here:** `from sqlalchemy`, `from fastapi`, `from pydantic`, `from app.models`, `from app.api`.
- **Tests:** `tests/unit/domain/test_*.py`. No `db` fixture. Run in <1 s.

### 2.2 `app/application/`
- **What lives here:** one use case per file (e.g. `application/loans/apply_for_loan.py`), DTOs (`dto.py`), abstract ports (`ports/`).
- **What never lives here:** SQLAlchemy queries, HTTP handlers, Pydantic models.
- **Allowed imports:** `app.domain.*` + standard library + `typing`/`dataclasses`.
- **Tests:** `tests/unit/application/test_*.py` with **fakes** for every port.

### 2.3 `app/infrastructure/`
- **What lives here:** concrete adapters that implement `application/ports/*` interfaces. SQLAlchemy repositories, Redis clients, email/SMS providers, third-party HTTP clients.
- **Allowed imports:** anything.
- **Tests:** `tests/integration/infrastructure/test_*.py` with real DB / Redis (Docker).

### 2.4 `app/api/`
- **What lives here:** thin FastAPI routers. The composition root `app/api/v1/dependencies.py` wires concrete adapters into use cases via `Depends`.
- **What endpoints do:**
  1. Parse request → command DTO
  2. Call exactly one use case (or query)
  3. Map result → response schema
  4. Map domain exceptions → HTTP errors
- **No business logic in endpoints.** Anything else belongs in a use case.

### 2.5 `app/services/` (legacy / utility)
- **Status:** transitional + miscellaneous.
- **Two valid uses:**
  1. **Cross-cutting utilities** that don't belong in domain (e.g. `notifications/registry.py`, `email_service.py`, `sms_service.py`, `cache_service.py`). These stay.
  2. **Legacy business services** (`escrow_service.py`, `dispute_service.py`, `transaction_service.py`, `trust_service.py`) that are gradually migrated into `application/` + `domain/`. **No new business logic should be added here**; new code goes straight into the DDD layout.

### 2.6 `app/models/`
- **Role:** SQLAlchemy ORM models. Used by infrastructure repositories. Not imported by domain or application.
- **Naming:** one aggregate root per file. Sub-entities can live alongside if always loaded with the root.

### 2.7 `app/schemas/`
- **Role:** Pydantic request/response schemas. Used by api/ only.
- **Rule:** never used as DTOs in application/. Application has its own dataclass DTOs.

### 2.8 `app/core/`
- **Role:** truly global concerns: config, security primitives, middleware, password validator, rate-limit settings.

---

## 3. NEW CODE CHECKLIST

When adding a feature, follow this order:

1. **Domain first** — write the aggregate / value object / exceptions. Test it in isolation.
2. **Application** — write the use case + ports it needs. Test with fakes.
3. **Schema** — define request/response Pydantic models in `app/schemas/`.
4. **Infrastructure** — implement the ports against real DB / Redis / HTTP. Integration-test.
5. **API** — write the FastAPI router calling the use case. End-to-end test the happy path.
6. **Notifications** — add a row in `services/notifications/registry.py` with the spec ID. Never inline strings.
7. **Migration** — add an Alembic revision. Never edit existing migrations.
8. **Spec marker** — add `# F#NNN` comment near the entry point.

---

## 4. NAMING CONVENTIONS

| Element | Pattern | Example |
|---|---|---|
| Use case class | `VerbNoun` | `ApplyForLoan`, `ConfirmDelivery`, `RaiseDispute` |
| Use case file | `verb_noun.py` | `apply_for_loan.py` |
| Command DTO | `VerbNounCommand` | `ApplyForLoanCommand` |
| Query DTO | `VerbNounQuery` | `GetOrderQuery` |
| Read-model | `NounView` | `OrderView` |
| Port (interface) | `NounRepository`, `NounPort` | `LoanRepository`, `EmailPort` |
| SQLAlchemy model | `Noun` (singular) | `Loan`, `Order`, `User` |
| Pydantic request | `NounAction` or `NounCreate/Update` | `LoanApplyRequest`, `ListingCreate` |
| Pydantic response | `NounResponse` | `LoanResponse` |
| Endpoint module | plural noun | `loans.py`, `listings.py` |
| Endpoint path | kebab-case | `/loans/{id}/admin/assign-agent` |
| Spec marker | `F#NNN` | `# F#338 — submit a loan application` |

---

## 5. DEPENDENCY RULES (enforced by import-linter)

```ini
# backend/.importlinter
[importlinter]
root_packages = app

[importlinter:contract:layered]
name = Layered architecture
type = layers
layers =
    app.api
    app.application
    app.domain
ignore_imports =
    app.api.deps -> app.models     # (transitional, until repositories cover all reads)

[importlinter:contract:domain-purity]
name = Domain has no infrastructure
type = forbidden
source_modules = app.domain
forbidden_modules =
    sqlalchemy
    fastapi
    pydantic
    redis
    app.models
    app.infrastructure
    app.api
    app.services
```

CI runs `lint-imports` on every PR. A failed contract blocks merge.

---

## 6. TESTING PYRAMID

```
        ╱╲          E2E (FastAPI TestClient + real DB)        ── slow, few
       ╱──╲         tests/integration/ — one per feature
      ╱────╲        Integration (infrastructure adapters)      ── medium
     ╱──────╲       tests/integration/infrastructure/
    ╱────────╲      Application (use cases + fakes)            ── many
   ╱──────────╲     tests/unit/application/
  ╱────────────╲    Domain (pure)                              ── most, fastest
 ╱──────────────╲   tests/unit/domain/
```

- **Domain tests** must run with `pytest tests/unit/domain` in <1 s and need no fixtures.
- **Application tests** use hand-written fake ports — no `unittest.mock` for protocol implementations.
- **Integration tests** spin up Postgres + Redis via `docker compose`.
- **E2E** tests hit `TestClient(app)` and run a small but representative slice.

---

## 7. CURRENT MIGRATION STATE

| Aggregate | Domain | Application | API uses DDD? |
|---|:---:|:---:|:---:|
| Order | ✅ | ✅ | partial — `/transactions/v2/*` does, v1 still uses `transaction_service` |
| Escrow | ✅ | ✅ | partial — feature-flagged adapter |
| Dispute | ✅ | ✅ | partial — `disputes.py` uses use cases for create/resolve |
| Trust | ✅ | ✅ | partial — `recompute_trust` use case wired in escrow flow |
| Loan (new) | 🔴 not yet | 🔴 in `services/loan_service.py` | — current implementation is in legacy services, scheduled for migration in Sprint 7 |
| Listing | 🔴 | 🔴 | — currently service-oriented |
| WhatsApp | 🔴 | 🔴 | — single 127 KB module; planned to be extracted into a separate process behind Redis Streams |

Legend: ✅ done · 🔴 not started

---

## 8. WHAT TO DO ABOUT `loan_service.py`

The loan module created in Sprint 1 lives in `services/loan_service.py` because we needed it shipped fast. It already follows clean separation (domain logic in the service, no HTTP concerns), so the migration is mechanical:

1. Move pure logic (`_amortize_monthly_payment`, status transitions) into `app/domain/loans/`.
2. Wrap it with use cases in `app/application/loans/` (`ApplyForLoan`, `RepayLoan`, `ApproveLoan`, `RejectLoan`, …).
3. Implement `LoanRepository` in `app/infrastructure/persistence/sqlalchemy/loan_repository.py`.
4. Have `app/api/v1/endpoints/loans.py` call the use cases instead of `loan_service` directly.
5. Delete `services/loan_service.py`.

This is tracked as a Sprint-7-prerequisite item.

---

## 9. ENFORCEMENT IN PRACTICE

| Rule | Enforced by |
|---|---|
| Domain purity | `import-linter` (CI) |
| Spec coverage | `make spec-coverage` greps `# F#NNN` markers (planned in roadmap F0.5) |
| No circular imports | `import-linter` (CI) |
| Style | `ruff check` + `ruff format` (existing) |
| Type-safety | `mypy app/domain app/application` (strict for these layers) |
| Notification templates | Module-level `assert len(TEMPLATES) == 43` in `notifications/registry.py` |

---

## 10. ADOPTING THIS STANDARD

For PRs that **add** new code: follow the new-code checklist (§3). New code lives in the DDD layout from day one.

For PRs that **modify** legacy code: do not introduce more legacy patterns. If the change is more than a small tweak, take the opportunity to migrate that module to DDD as part of the PR.

For PRs that **delete** code: see `docs/DEAD_CODE_AUDIT.md` for the safe-deletion list.
