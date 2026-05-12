"""Unit tests for the Order aggregate. NO database, NO framework — pure Python."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.orders import (
    DeliveryConfirmed,
    EscrowReleased,
    InvalidHandoverCode,
    InvalidStatusTransition,
    LogisticsType,
    NotEscrowed,
    Order,
    OrderStatus,
)
from app.domain.orders.exceptions import UnauthorizedActor
from app.domain.shared_kernel.identifiers import OrderId, UserId
from app.domain.shared_kernel.money import Currency, Money


def _make_order(
    *,
    status: OrderStatus = OrderStatus.ESCROW_HELD,
    logistics: LogisticsType = LogisticsType.PLATFORM,
    handover_code: str | None = "ABC123",
) -> tuple[Order, UserId, UserId]:
    buyer = UserId(uuid4())
    seller = UserId(uuid4())
    order = Order(
        id=OrderId(uuid4()),
        buyer_id=buyer,
        seller_id=seller,
        order_number="ZAT-0001",
        total_amount=Money(cents=10_000, currency=Currency.USD),
        seller_payout=Money(cents=9_500, currency=Currency.USD),
        status=status,
        logistics_type=logistics,
        handover_code=handover_code,
        created_at=datetime.now(timezone.utc),
    )
    return order, buyer, seller


# ---------------------- confirm_delivery ----------------------

def test_confirm_delivery_happy_path_emits_event_and_transitions():
    order, buyer, _ = _make_order()

    order.confirm_delivery(actor_id=buyer, handover_code="ABC123")

    assert order.status == OrderStatus.DELIVERED
    events = order.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], DeliveryConfirmed)
    assert events[0].confirmed_by == buyer


def test_confirm_delivery_rejects_seller():
    order, _, seller = _make_order()
    with pytest.raises(UnauthorizedActor):
        order.confirm_delivery(actor_id=seller, handover_code="ABC123")


def test_confirm_delivery_requires_escrow_state():
    order, buyer, _ = _make_order(status=OrderStatus.PENDING)
    with pytest.raises(NotEscrowed):
        order.confirm_delivery(actor_id=buyer, handover_code="ABC123")


def test_confirm_delivery_rejects_wrong_handover_code():
    order, buyer, _ = _make_order(handover_code="REAL-CODE")
    with pytest.raises(InvalidHandoverCode):
        order.confirm_delivery(actor_id=buyer, handover_code="WRONG")


def test_confirm_delivery_rejects_missing_handover_code_for_platform_logistics():
    order, buyer, _ = _make_order(handover_code="ABC123")
    with pytest.raises(InvalidHandoverCode):
        order.confirm_delivery(actor_id=buyer, handover_code=None)


def test_confirm_delivery_self_logistics_does_not_require_handover_code():
    order, buyer, _ = _make_order(logistics=LogisticsType.SELF, handover_code=None)
    order.confirm_delivery(actor_id=buyer, handover_code=None)
    assert order.status == OrderStatus.DELIVERED


# ---------------------- mark_settled_after_release ----------------------

def test_mark_settled_after_release_from_delivered_emits_escrow_released():
    order, buyer, _ = _make_order()
    order.confirm_delivery(actor_id=buyer, handover_code="ABC123")
    order.pull_events()  # discard

    order.mark_settled_after_release()

    assert order.status == OrderStatus.SETTLED
    events = order.pull_events()
    assert any(isinstance(e, EscrowReleased) for e in events)


def test_mark_settled_after_release_rejects_pending():
    order, *_ = _make_order(status=OrderStatus.PENDING)
    with pytest.raises(InvalidStatusTransition):
        order.mark_settled_after_release()


def test_settled_is_terminal():
    order, buyer, _ = _make_order()
    order.confirm_delivery(actor_id=buyer, handover_code="ABC123")
    order.mark_settled_after_release()
    with pytest.raises(InvalidStatusTransition):
        order.mark_settled_after_release()


# ---------------------- Money invariants ----------------------

def test_money_rejects_negative():
    with pytest.raises(ValueError):
        Money(cents=-1, currency=Currency.USD)


def test_money_rejects_currency_mismatch():
    a = Money(cents=100, currency=Currency.USD)
    b = Money(cents=100, currency=Currency.ZIG)
    with pytest.raises(ValueError):
        _ = a + b
