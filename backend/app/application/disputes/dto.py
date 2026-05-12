"""DTOs for dispute use cases."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateDisputeCommand:
    order_id: UUID
    raised_by: UUID
    dispute_type: str
    description: str


@dataclass(frozen=True, slots=True)
class ResolveDisputeCommand:
    dispute_id: UUID
    resolution: str
    release_to_farmer: bool


@dataclass(frozen=True, slots=True)
class EscalateDisputeCommand:
    dispute_id: UUID
    escalated_by: UUID
    reason: str
