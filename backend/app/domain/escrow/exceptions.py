"""Escrow domain exceptions."""
from __future__ import annotations


class EscrowDomainError(Exception):
    """Base class for all escrow-related domain errors."""


class InsufficientFunds(EscrowDomainError):
    def __init__(self, *, requested: int, available: int, currency: str) -> None:
        super().__init__(
            f"Insufficient funds: requested={requested} available={available} {currency}"
        )
        self.requested = requested
        self.available = available
        self.currency = currency


class SettlementMathError(EscrowDomainError):
    """Raised when a settlement plan's parts do not sum to the total."""


class CurrencyMismatch(EscrowDomainError):
    pass
