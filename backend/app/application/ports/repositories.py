"""Repository ports — abstract interfaces, implemented by infrastructure adapters."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.orders.entities import Order
from app.domain.shared_kernel.identifiers import OrderId


@runtime_checkable
class OrderRepository(Protocol):
    """Persistence-agnostic interface for the Order aggregate."""

    def get(self, order_id: OrderId) -> Order | None: ...

    def save(self, order: Order) -> None:
        """Persist new or modified Order. UoW is responsible for the commit."""
        ...
