"""Escrow port — abstracts the wallet/ledger side-effect from the domain.

The domain owns lifecycle invariants; physically moving money is
infrastructure. This port is the seam between them.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.orders.entities import Order


@runtime_checkable
class EscrowPort(Protocol):
    def release_funds(self, order: Order) -> None:
        """Credit seller wallet, write ledger entries, etc. Idempotent."""
        ...
