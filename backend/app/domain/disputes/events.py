"""Domain events for the Dispute bounded context."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from app.domain.disputes.value_objects import DisputeStatus


@dataclass(frozen=True, slots=True)
class DisputeCreated:
    dispute_id: UUID
    order_id: UUID
    raised_by: UUID
    dispute_type: str
    description: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DisputeResolved:
    dispute_id: UUID
    order_id: UUID
    resolution: str
    previous_status: DisputeStatus
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DisputeEscalated:
    dispute_id: UUID
    order_id: UUID
    escalated_by: UUID
    reason: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DisputeProposedOffer:
    dispute_id: UUID
    order_id: UUID
    discount_percent: float
    refund_amount: float
    proposed_by: UUID
    memo: str
    occurred_at: datetime
