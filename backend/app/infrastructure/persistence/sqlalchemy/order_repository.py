"""SQLAlchemy adapter for OrderRepository port."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.repositories import OrderRepository
from app.domain.orders.entities import Order as DomainOrder
from app.domain.shared_kernel.identifiers import OrderId
from app.infrastructure.persistence.sqlalchemy.mappers import (
    apply_to_orm,
    to_domain,
)
from app.models.transaction import Order as OrmOrder


class SqlAlchemyOrderRepository(OrderRepository):
    """
    Identity-map aware repository.

    Loaded ORM rows are tracked in `_identity_map` so a subsequent `save`
    mutates the same row, keeping SQLAlchemy's change-tracking working.
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._identity_map: dict[OrderId, OrmOrder] = {}

    def get(self, order_id: OrderId) -> DomainOrder | None:
        row = self._session.get(OrmOrder, order_id.value)
        if row is None:
            return None
        self._identity_map[order_id] = row
        return to_domain(row)

    def save(self, order: DomainOrder) -> None:
        row = self._identity_map.get(order.id)
        if row is None:
            # Re-fetch defensively — every save must flow through a prior get
            # for this aggregate's lifecycle, but we tolerate the alternative.
            row = self._session.get(OrmOrder, order.id.value)
            if row is None:
                raise LookupError(f"Order {order.id} disappeared mid-transaction")
        apply_to_orm(order, row)
        self._session.add(row)
