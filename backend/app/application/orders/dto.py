"""Application-layer DTOs — boundary objects between presentation and use cases.

Pure data, no framework. Pydantic schemas live in the API layer; these
are stdlib-only so the application layer stays portable.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ConfirmDeliveryCommand:
    order_id: UUID
    actor_id: UUID
    handover_code: str | None


@dataclass(frozen=True, slots=True)
class GetOrderQuery:
    order_id: UUID
    actor_id: UUID
    actor_is_admin: bool = False


@dataclass(frozen=True, slots=True)
class OrderView:
    """Read-model returned by queries. Decoupled from ORM and from the
    domain entity (queries don't need invariants)."""
    id: UUID
    order_number: str
    buyer_id: UUID
    seller_id: UUID
    status: str
    total_amount_cents: int
    seller_payout_cents: int
    currency: str
    logistics_type: str
    handover_code_visible: str | None
    created_at: datetime
