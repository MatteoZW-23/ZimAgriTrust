"""Ledger entry value object — produced by Settlement, persisted by infra."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.shared_kernel.identifiers import OrderId, UserId
from app.domain.shared_kernel.money import Money


class LedgerEntryType(str, Enum):
    ESCROW_HOLD = "ESCROW_HOLD"
    ESCROW_RELEASE = "ESCROW_RELEASE"
    REFUND = "REFUND"
    FEE = "FEE"
    ADJUSTMENT = "ADJUSTMENT"


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    order_id: OrderId
    user_id: UserId
    type: LedgerEntryType
    amount: Money
