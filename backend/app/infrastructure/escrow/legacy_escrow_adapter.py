"""EscrowPort adapter that delegates to the existing escrow_service.

Preserves the live money-movement behaviour while letting use cases
depend on the abstract port. When escrow_service is decomposed in a
future phase, only this adapter changes.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.escrow import EscrowPort
from app.domain.orders.entities import Order as DomainOrder
from app.models.transaction import Order as OrmOrder


class LegacyEscrowAdapter(EscrowPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def release_funds(self, order: DomainOrder) -> None:
        # Lazy import — keeps the import graph clean and avoids pulling
        # the legacy service into module-load time.
        from app.services.escrow_service import release_payment

        row = self._session.get(OrmOrder, order.id.value)
        if row is None:
            raise LookupError(f"Order {order.id} not found for escrow release")

        # release_payment commits internally and returns the updated row.
        # We accept that here; the use case treats this as the side-effect
        # boundary. Idempotency is the legacy service's responsibility.
        release_payment(self._session, row, handover_code=order.handover_code)
