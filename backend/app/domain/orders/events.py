"""Order domain events — pure data, dispatched by the application layer."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.shared_kernel.identifiers import OrderId, UserId
from app.domain.shared_kernel.money import Money


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class DomainEvent:
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DeliveryConfirmed(DomainEvent):
    order_id: OrderId
    confirmed_by: UserId


@dataclass(frozen=True, slots=True)
class EscrowReleased(DomainEvent):
    order_id: OrderId
    seller_id: UserId
    seller_payout: Money
