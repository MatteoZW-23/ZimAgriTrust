"""Settlement domain service — pure orchestration of money movement.

Given a plan + the affected wallets, mutates the wallets and returns
ledger entries + domain events. Performs zero I/O. Caller (application
layer) decides when/how to persist and dispatch.

Invariants enforced:
  - All parties share a currency.
  - Sufficient funds in pending balance to satisfy the plan total.
  - Total = sum of parts (validated inside each plan's __post_init__).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple

from app.domain.escrow.events import (
    EscrowRefunded,
    EscrowReleased,
    EscrowSplit,
)
from app.domain.escrow.exceptions import CurrencyMismatch
from app.domain.escrow.ledger import LedgerEntry, LedgerEntryType
from app.domain.escrow.plans import (
    DisputeSplitPlan,
    RefundPlan,
    ReleasePlan,
)
from app.domain.escrow.wallet import Wallet
from app.domain.shared_kernel.identifiers import OrderId


class SettlementResult(NamedTuple):
    ledger_entries: list[LedgerEntry]
    events: list[object]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _check_currency(*wallets: Wallet, plan_currency) -> None:
    currencies = {w.currency for w in wallets} | {plan_currency}
    if len(currencies) > 1:
        raise CurrencyMismatch(f"Mixed currencies in settlement: {currencies}")


class Settlement:
    """Pure functions. No state. No I/O."""

    @staticmethod
    def release(
        *,
        order_id: OrderId,
        buyer: Wallet,
        seller: Wallet,
        plan: ReleasePlan,
    ) -> SettlementResult:
        _check_currency(buyer, seller, plan_currency=plan.total.currency)

        # Money movements: buyer pending -> seller available; fee disappears
        # from circulation (recorded as platform revenue in the ledger).
        buyer.debit_pending(plan.total)
        seller.credit_available(plan.payout)

        ledger = [
            LedgerEntry(order_id, seller.user_id, LedgerEntryType.ESCROW_RELEASE, plan.payout),
            LedgerEntry(order_id, buyer.user_id, LedgerEntryType.FEE, plan.fee),
        ]
        events = [EscrowReleased(
            order_id=order_id,
            occurred_at=_now(),
            seller_id=seller.user_id,
            payout=plan.payout,
            fee=plan.fee,
        )]
        return SettlementResult(ledger_entries=ledger, events=events)

    @staticmethod
    def refund(
        *,
        order_id: OrderId,
        buyer: Wallet,
        plan: RefundPlan,
    ) -> SettlementResult:
        _check_currency(buyer, plan_currency=plan.total.currency)

        # buyer pending -> buyer available, full amount.
        buyer.refund_pending(plan.total)

        ledger = [
            LedgerEntry(order_id, buyer.user_id, LedgerEntryType.REFUND, plan.total),
        ]
        events = [EscrowRefunded(
            order_id=order_id,
            occurred_at=_now(),
            buyer_id=buyer.user_id,
            amount=plan.total,
        )]
        return SettlementResult(ledger_entries=ledger, events=events)

    @staticmethod
    def resolve_dispute(
        *,
        order_id: OrderId,
        buyer: Wallet,
        seller: Wallet,
        plan: DisputeSplitPlan,
    ) -> SettlementResult:
        _check_currency(buyer, seller, plan_currency=plan.total.currency)

        # Drain buyer's pending in one go; redistribute according to plan.
        buyer.debit_pending(plan.total)
        if plan.buyer_refund.cents > 0:
            buyer.credit_available(plan.buyer_refund)
        if plan.seller_payout.cents > 0:
            seller.credit_available(plan.seller_payout)
        # plan.fee is platform revenue — captured only in the ledger.

        ledger: list[LedgerEntry] = []
        if plan.buyer_refund.cents > 0:
            ledger.append(LedgerEntry(order_id, buyer.user_id, LedgerEntryType.REFUND, plan.buyer_refund))
        if plan.seller_payout.cents > 0:
            ledger.append(LedgerEntry(order_id, seller.user_id, LedgerEntryType.ESCROW_RELEASE, plan.seller_payout))
        if plan.fee.cents > 0:
            ledger.append(LedgerEntry(order_id, buyer.user_id, LedgerEntryType.FEE, plan.fee))

        events = [EscrowSplit(
            order_id=order_id,
            occurred_at=_now(),
            buyer_id=buyer.user_id,
            seller_id=seller.user_id,
            buyer_refund=plan.buyer_refund,
            seller_payout=plan.seller_payout,
            fee=plan.fee,
        )]
        return SettlementResult(ledger_entries=ledger, events=events)
