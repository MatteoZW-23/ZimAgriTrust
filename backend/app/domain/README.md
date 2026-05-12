# Clean Architecture — domain / application / infrastructure

This subtree introduces clean architecture into the AgriTrust backend
**without breaking the existing service-oriented codebase**. New endpoints
are exposed at `/api/v1/transactions/v2/...` and run alongside the
legacy ones until parity is verified.

## Layers (dependency direction is one-way, inward)

```
api  ─┐
      ├──> application ──> domain
infra ─┘            (ports)
```

- **`app/domain/`** — pure Python. No SQLAlchemy, no FastAPI, no Pydantic.
  Holds aggregates (`Order`), value objects (`Money`, `OrderStatus`),
  events (`DeliveryConfirmed`, `EscrowReleased`) and exceptions.
  All lifecycle invariants live here.

- **`app/application/`** — use cases (`ConfirmDelivery`, `GetOrder`) that
  orchestrate aggregates and side-effects. Defines abstract **ports**
  (`OrderRepository`, `UnitOfWork`, `NotificationPort`, `EscrowPort`).
  Imports only from `app.domain`.

- **`app/infrastructure/`** — concrete adapters that implement ports:
  `SqlAlchemyOrderRepository`, `SqlAlchemyUnitOfWork`,
  `LegacyEscrowAdapter` (delegates to existing `escrow_service`),
  `LoggingNotifier`.

- **`app/api/v1/dependencies.py`** — composition root. The single place
  where adapters are wired into use cases via FastAPI `Depends`.

## Enforcement

`backend/.importlinter` makes the dependency rule a CI check:

```bash
docker compose exec backend pip install -r requirements-dev.txt
docker compose exec backend lint-imports
```

Any commit that imports SQLAlchemy from `app.domain` or FastAPI from
`app.application` fails the build.

## Tests

Pure-domain unit tests run in milliseconds and never touch a DB:

```bash
docker compose exec backend pytest tests/unit/domain -v
```

## Migration plan (this is Step 1 of 5)

1. ✅ **Order** aggregate — `confirm-delivery` use case (this commit).
2. ⏳ **Escrow** aggregate — extract money movement out of `escrow_service`.
3. ⏳ **Trust** aggregate — score updates as domain events.
4. ⏳ **Disputes** aggregate.
5. ⏳ Decompose `whatsapp_service.py` (125 KB) into a separate process
   behind Redis Streams.

After Step 1 the legacy `confirm-delivery` endpoint will be deprecated;
remove only after frontend migration to v2.
