"""Dispute ports."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.disputes.entities import Dispute
from app.domain.shared_kernel.identifiers import DisputeId, OrderId, UserId


@runtime_checkable
class DisputeRepository(Protocol):
    def save(self, dispute: Dispute) -> None:
        """Persist dispute aggregate."""
        ...

    def get_by_id(self, dispute_id: DisputeId) -> Dispute | None:
        """Load dispute by ID."""
        ...

    def get_by_order(self, order_id: OrderId) -> Dispute | None:
        """Load dispute by order ID (at most one)."""
        ...


@runtime_checkable
class DisputeReader(Protocol):
    def exists_for_order(self, order_id: OrderId) -> bool:
        """Check if a dispute already exists for the order."""
        ...
