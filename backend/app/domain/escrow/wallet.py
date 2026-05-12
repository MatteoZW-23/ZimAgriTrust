"""Wallet aggregate — per (user, currency) pair.

Models the actual financial primitive: every wallet has `available` and
`pending` (escrowed) balances. All operations enforce non-negativity,
currency consistency, and conservation of money.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.escrow.exceptions import (
    CurrencyMismatch,
    InsufficientFunds,
)
from app.domain.shared_kernel.identifiers import UserId
from app.domain.shared_kernel.money import Currency, Money


@dataclass
class Wallet:
    """One wallet per (user, currency)."""
    user_id: UserId
    currency: Currency
    available: Money
    pending: Money

    def __post_init__(self) -> None:
        if self.available.currency != self.currency or self.pending.currency != self.currency:
            raise CurrencyMismatch(
                f"Wallet currency {self.currency} differs from balances "
                f"(available={self.available.currency}, pending={self.pending.currency})"
            )

    # ---------------- internal guards ----------------

    def _expect_currency(self, m: Money) -> None:
        if m.currency != self.currency:
            raise CurrencyMismatch(
                f"Wallet currency {self.currency.value} != amount {m.currency.value}"
            )

    # ---------------- operations ----------------

    def hold(self, amount: Money) -> None:
        """Move `amount` from available -> pending. Raises if insufficient."""
        self._expect_currency(amount)
        if self.available.cents < amount.cents:
            raise InsufficientFunds(
                requested=amount.cents,
                available=self.available.cents,
                currency=self.currency.value,
            )
        self.available = self.available - amount
        self.pending = self.pending + amount

    def debit_pending(self, amount: Money) -> None:
        """Remove `amount` from pending. Used during settlement."""
        self._expect_currency(amount)
        if self.pending.cents < amount.cents:
            raise InsufficientFunds(
                requested=amount.cents,
                available=self.pending.cents,
                currency=self.currency.value,
            )
        self.pending = self.pending - amount

    def credit_available(self, amount: Money) -> None:
        """Add `amount` to available."""
        self._expect_currency(amount)
        self.available = self.available + amount

    def credit_pending(self, amount: Money) -> None:
        """Add `amount` to pending (used when refunding back into escrow)."""
        self._expect_currency(amount)
        self.pending = self.pending + amount

    def refund_pending(self, amount: Money) -> None:
        """Move `amount` from pending -> available (own wallet)."""
        self.debit_pending(amount)
        self.credit_available(amount)
