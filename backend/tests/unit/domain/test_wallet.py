"""Wallet aggregate unit tests — pure, no DB."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.escrow.exceptions import CurrencyMismatch, InsufficientFunds
from app.domain.escrow.wallet import Wallet
from app.domain.shared_kernel.identifiers import UserId
from app.domain.shared_kernel.money import Currency, Money


def _wallet(*, available: int = 10_000, pending: int = 0, currency: Currency = Currency.USD) -> Wallet:
    return Wallet(
        user_id=UserId(uuid4()),
        currency=currency,
        available=Money(cents=available, currency=currency),
        pending=Money(cents=pending, currency=currency),
    )


def test_hold_moves_funds_available_to_pending():
    w = _wallet(available=10_000)
    w.hold(Money(cents=3_000, currency=Currency.USD))
    assert w.available.cents == 7_000
    assert w.pending.cents == 3_000


def test_hold_rejects_insufficient_funds():
    w = _wallet(available=100)
    with pytest.raises(InsufficientFunds):
        w.hold(Money(cents=200, currency=Currency.USD))


def test_hold_rejects_currency_mismatch():
    w = _wallet(currency=Currency.USD)
    with pytest.raises(CurrencyMismatch):
        w.hold(Money(cents=100, currency=Currency.ZIG))


def test_debit_pending_rejects_overdraft():
    w = _wallet(pending=500)
    with pytest.raises(InsufficientFunds):
        w.debit_pending(Money(cents=600, currency=Currency.USD))


def test_refund_pending_round_trips():
    w = _wallet(available=0, pending=5_000)
    w.refund_pending(Money(cents=5_000, currency=Currency.USD))
    assert w.available.cents == 5_000
    assert w.pending.cents == 0


def test_wallet_rejects_currency_mismatch_at_construction():
    with pytest.raises(CurrencyMismatch):
        Wallet(
            user_id=UserId(uuid4()),
            currency=Currency.USD,
            available=Money(cents=0, currency=Currency.ZIG),
            pending=Money(cents=0, currency=Currency.USD),
        )
