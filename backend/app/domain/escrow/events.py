"""Escrow domain events."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.shared_kernel.identifiers import OrderId, UserId
from app.domain.shared_kernel.money import Money


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class _EscrowEvent:
    order_id: OrderId
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class EscrowHeld(_EscrowEvent):
    buyer_id: UserId
    amount: Money


@dataclass(frozen=True, slots=True)
class EscrowReleased(_EscrowEvent):
    seller_id: UserId
    payout: Money
    fee: Money


@dataclass(frozen=True, slots=True)
class EscrowRefunded(_EscrowEvent):
    buyer_id: UserId
    amount: Money


@dataclass(frozen=True, slots=True)
class EscrowSplit(_EscrowEvent):
    buyer_id: UserId
    seller_id: UserId
    buyer_refund: Money
    seller_payout: Money
    fee: Money
