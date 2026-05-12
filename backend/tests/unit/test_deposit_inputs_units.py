"""
Pure-function unit tests for the buyer-deposit and input-marketplace
helpers — no DB required.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.models.deposits import RecurrenceCadence
from app.services.deposit_automation_service import (
    _next_run,
    calculate_refund_fee,
)


# ---------------------------------------------------------------------------
# Refund fee
# ---------------------------------------------------------------------------

class TestRefundFee:
    def test_two_percent_under_cap(self):
        # $100 deposit → 2% = $2.00 (under $10 cap)
        assert calculate_refund_fee(100.0) == 2.0

    def test_capped_at_ten_dollars(self):
        # $1000 deposit → 2% = $20 capped to $10
        assert calculate_refund_fee(1000.0) == 10.0

    def test_zero(self):
        assert calculate_refund_fee(0) == 0.0

    def test_small_amount(self):
        # $5 deposit → 2% = $0.10
        assert calculate_refund_fee(5.0) == 0.10


# ---------------------------------------------------------------------------
# _next_run scheduling math
# ---------------------------------------------------------------------------

class TestNextRun:
    def test_weekly_jumps_at_least_one_day(self):
        base = datetime(2026, 5, 6, 12, 0, 0)  # Wednesday
        nxt = _next_run(RecurrenceCadence.WEEKLY, day_of_week=2, day_of_month=None, from_dt=base)
        # day_of_week=2 is Wednesday → must roll forward 7 days, never 0
        assert nxt > base
        assert (nxt - base).days >= 1

    def test_weekly_specific_dow(self):
        # Monday 2026-05-04
        base = datetime(2026, 5, 4, 9, 0, 0)
        nxt = _next_run(RecurrenceCadence.WEEKLY, day_of_week=4, day_of_month=None, from_dt=base)
        assert nxt.weekday() == 4  # Friday

    def test_biweekly_is_14_days(self):
        base = datetime(2026, 5, 6)
        nxt = _next_run(RecurrenceCadence.BIWEEKLY, day_of_week=None, day_of_month=None, from_dt=base)
        assert (nxt - base).days == 14

    def test_monthly_snaps_to_target_day(self):
        base = datetime(2026, 5, 6)
        nxt = _next_run(RecurrenceCadence.MONTHLY, day_of_week=None, day_of_month=15, from_dt=base)
        # ~30 days later, snapped to day 15 (or 28 max for safety)
        assert nxt.day == 15
        assert nxt > base

    def test_monthly_february_safe_for_day_30(self):
        # Day 30 requested but Feb only has 28 → must clamp to 28 (no ValueError)
        base = datetime(2026, 1, 30)
        nxt = _next_run(RecurrenceCadence.MONTHLY, day_of_week=None, day_of_month=30, from_dt=base)
        assert nxt.day <= 28


# ---------------------------------------------------------------------------
# Marketplace fee math (constants drawn from settings)
# ---------------------------------------------------------------------------

class TestInputMarketplaceFees:
    def test_total_breakdown(self):
        from app.core.config import settings

        subtotal = 200.0
        platform_fee = round(subtotal * settings.INPUT_PLATFORM_FEE_PERCENT, 2)
        escrow_fee = round(subtotal * settings.INPUT_ESCROW_FEE_PERCENT, 2)
        total = round(subtotal + platform_fee + escrow_fee, 2)
        seller_payout = round(subtotal - escrow_fee, 2)

        # Default: 2.5% platform + 0.5% escrow
        assert platform_fee == 5.00
        assert escrow_fee == 1.00
        assert total == 206.00
        assert seller_payout == 199.00

    def test_bulk_threshold_classification(self):
        from app.core.config import settings

        small = 499.99
        bulk = 500.0
        assert small < settings.INPUT_BULK_ORDER_MIN_USD
        assert bulk >= settings.INPUT_BULK_ORDER_MIN_USD


# ---------------------------------------------------------------------------
# Notification triggers must NEVER raise
# ---------------------------------------------------------------------------

class TestNotificationTriggersNeverRaise:
    def test_all_helpers_swallow_missing_phone(self):
        from app.services import notification_triggers as n

        # All of these should be no-ops when phone is None / blank
        n.deposit_completed(None, 50.0, "ecocash", "REF1")
        n.deposit_failed("", "timeout", "REF2")
        n.deposit_refund_processed(None, 49.0, 1.0)
        n.cash_collected_by_agent(None, "Alice", 100.0)
        n.input_listing_verified(None, "Maize seed")
        n.input_listing_rejected(None, "Maize seed", "missing cert")
        n.input_offer_received(None, "Maize seed", 100, 5.50)
        n.input_offer_accepted(None, "Maize seed", 550.0, "IN-ABCD")
        n.input_offer_rejected(None, "Maize seed", None)
        n.input_order_shipped(None, "IN-ABCD", "TRK-1")
        n.input_order_completed(None, "IN-ABCD", 549.0)
        n.input_listing_expiry_warning(None, "Maize seed", 7)
        n.input_listing_expired(None, "Maize seed")
        n.input_low_stock(None, "Maize seed", 3)
        n.input_listing_reported(None, "Maize seed", "fake")
        n.input_price_alert_hit(None, "Maize seed", 4.50, 5.00)
