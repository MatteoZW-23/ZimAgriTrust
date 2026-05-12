"""Escrow command DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ReleaseEscrowCommand:
    order_id: UUID


@dataclass(frozen=True, slots=True)
class RefundEscrowCommand:
    order_id: UUID


@dataclass(frozen=True, slots=True)
class ResolveDisputeCommand:
    order_id: UUID
    buyer_refund_cents: int
    seller_payout_cents: int
    fee_cents: int
