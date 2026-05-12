"""Pure-math tests for the loan service.

We test only the side-effect-free helpers (`calculate_repayment`,
`_amortize_monthly_payment`) so the suite stays DB-free.
"""
import pytest

from backend.app.services.loan_service import (
    LoanService,
    _amortize_monthly_payment,
)


def test_zero_interest_uses_simple_division():
    pay = _amortize_monthly_payment(1200.0, 0.0, 12)
    assert pay == pytest.approx(100.0, rel=1e-3)


def test_amortization_matches_known_value():
    # $1000 @ 12% APR, 12 months → ≈ $88.85/mo
    pay = _amortize_monthly_payment(1000.0, 0.12, 12)
    assert pay == pytest.approx(88.85, abs=0.05)


def test_amortization_invalid_term():
    with pytest.raises(ValueError):
        _amortize_monthly_payment(1000, 0.1, 0)


def test_calculate_repayment_returns_full_breakdown():
    res = LoanService.calculate_repayment(amount_usd=2000.0, annual_rate=0.18, term_months=24)
    assert res["amount_usd"] == 2000.0
    assert res["term_months"] == 24
    assert res["monthly_payment_usd"] > 0
    assert res["total_repayment_usd"] >= res["amount_usd"]
    assert res["total_interest_usd"] == pytest.approx(
        res["total_repayment_usd"] - res["amount_usd"], abs=0.01
    )


def test_zero_rate_total_equals_principal():
    res = LoanService.calculate_repayment(amount_usd=600.0, annual_rate=0.0, term_months=6)
    assert res["monthly_payment_usd"] == pytest.approx(100.0, abs=0.01)
    # With zero rate the total equals principal (within rounding).
    assert res["total_repayment_usd"] == pytest.approx(600.0, abs=0.05)
    assert res["total_interest_usd"] == pytest.approx(0.0, abs=0.05)
