"""Settlement domain service tests — pure, no DB."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.escrow.events import (
    EscrowRefunded,
    EscrowReleased,
    EscrowSplit,
)
from app.domain.escrow.exceptions import (
    CurrencyMismatch,
    SettlementMathError,
)
from app.domain.escrow.ledger import LedgerEntryType
from app.domain.escrow.plans import (
    DisputeSplitPlan,
    RefundPlan,
    ReleasePlan,
)
from app.domain.escrow.settlement import Settlement
from app.domain.escrow.wallet import Wallet
from app.domain.shared_kernel.identifiers import OrderId, UserId
from app.domain.shared_kernel.money import Currency, Money


def _wallet(pending: int = 0, available: int = 0) -> Wallet:
    return Wallet(
        user_id=UserId(uuid4()),
        currency=Currency.USD,
        available=Money(cents=available, currency=Currency.USD),
        pending=Money(cents=pending, currency=Currency.USD),
    )


def _money(c: int) -> Money:
    return Money(cents=c, currency=Currency.USD)


# -------------------- Plans --------------------

def test_release_plan_rejects_unbalanced_math():
    with pytest.raises(SettlementMathError):
        ReleasePlan(total=_money(1000), fee=_money(50), payout=_money(900))  # 950 != 1000


def test_release_plan_accepts_balanced_math():
    p = ReleasePlan(total=_money(1000), fee=_money(50), payout=_money(950))
    assert p.total.cents == 1000


def test_split_plan_rejects_unbalanced_math():
    with pytest.raises(SettlementMathError):
        DisputeSplitPlan(
            total=_money(1000),
            buyer_refund=_money(400),
            seller_payout=_money(400),
            fee=_money(100),  # sum 900
        )


def test_split_plan_balanced():
    p = DisputeSplitPlan(
        total=_money(1000),
        buyer_refund=_money(400),
        seller_payout=_money(550),
        fee=_money(50),
    )
    assert p.total.cents == 1000


# -------------------- Settlement.release --------------------

def test_settlement_release_moves_money_correctly():
    buyer = _wallet(pending=1000)
    seller = _wallet(available=0)
    plan = ReleasePlan(total=_money(1000), fee=_money(50), payout=_money(950))
    order_id = OrderId(uuid4())

    res = Settlement.release(order_id=order_id, buyer=buyer, seller=seller, plan=plan)

    assert buyer.pending.cents == 0
    assert seller.available.cents == 950
    types = {e.type for e in res.ledger_entries}
    assert types == {LedgerEntryType.ESCROW_RELEASE, LedgerEntryType.FEE}
    assert any(isinstance(e, EscrowReleased) for e in res.events)


# -------------------- Settlement.refund --------------------

def test_settlement_refund_returns_full_amount_to_buyer():
    buyer = _wallet(pending=1000, available=200)
    plan = RefundPlan(total=_money(1000))
    res = Settlement.refund(order_id=OrderId(uuid4()), buyer=buyer, plan=plan)
    assert buyer.pending.cents == 0
    assert buyer.available.cents == 1200
    assert any(isinstance(e, EscrowRefunded) for e in res.events)


# -------------------- Settlement.resolve_dispute --------------------

def test_settlement_split_distributes_correctly():
    buyer = _wallet(pending=1000, available=0)
    seller = _wallet(available=0)
    plan = DisputeSplitPlan(
        total=_money(1000),
        buyer_refund=_money(400),
        seller_payout=_money(550),
        fee=_money(50),
    )
    res = Settlement.resolve_dispute(
        order_id=OrderId(uuid4()), buyer=buyer, seller=seller, plan=plan,
    )
    assert buyer.pending.cents == 0
    assert buyer.available.cents == 400
    assert seller.available.cents == 550
    assert any(isinstance(e, EscrowSplit) for e in res.events)


def test_settlement_rejects_currency_mismatch():
    buyer = Wallet(
        user_id=UserId(uuid4()),
        currency=Currency.ZIG,
        available=Money(0, Currency.ZIG),
        pending=Money(1000, Currency.ZIG),
    )
    seller = _wallet()  # USD
    plan = ReleasePlan(total=_money(1000), fee=_money(0), payout=_money(1000))
    with pytest.raises(CurrencyMismatch):
        Settlement.release(order_id=OrderId(uuid4()), buyer=buyer, seller=seller, plan=plan)
