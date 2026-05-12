"""
Withdrawal limits, fees, and rate enforcement.

Tier rules (see WithdrawalLimit table; defaults from config):
  - UNVERIFIED: $50/day,  $200/week
  - VERIFIED:   $500/day, $2,000/week
  - TRUSTED:    $1,000/day, $5,000/week (requires trust_score >= 80)

Fee:  1% (capped at $5)
Min:  $5
Rate: max 3 withdrawals per user per day
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.security import UserTier, WithdrawalLimit
from app.models.transaction import Transaction, TransactionType
from app.models.user import User


# ---------------------------------------------------------------------------
# Tier resolution
# ---------------------------------------------------------------------------

def resolve_user_tier(user: User) -> UserTier:
    if not user:
        return UserTier.UNVERIFIED
    trust = int(getattr(user, "trust_score", 0) or 0)
    is_verified = bool(
        getattr(user, "is_phone_verified", False)
        and getattr(user, "is_id_verified", False)
    )
    if trust >= settings.TIER_TRUSTED_MIN_TRUST_SCORE and is_verified:
        return UserTier.TRUSTED
    if is_verified:
        return UserTier.VERIFIED
    return UserTier.UNVERIFIED


def get_tier_limits(db: Session, tier: UserTier) -> dict[str, float]:
    """Read tier limits from DB (with config fallback)."""
    row = db.query(WithdrawalLimit).filter(WithdrawalLimit.user_tier == tier).first()
    if row:
        return {
            "daily": float(row.daily_limit),
            "weekly": float(row.weekly_limit),
            "monthly": float(row.monthly_limit),
            "per_txn": float(row.per_transaction_limit),
        }
    # Config fallback
    fallback = {
        UserTier.UNVERIFIED: (settings.TIER_UNVERIFIED_DAILY, settings.TIER_UNVERIFIED_WEEKLY),
        UserTier.VERIFIED:   (settings.TIER_VERIFIED_DAILY,   settings.TIER_VERIFIED_WEEKLY),
        UserTier.TRUSTED:    (settings.TIER_TRUSTED_DAILY,    settings.TIER_TRUSTED_WEEKLY),
    }[tier]
    daily, weekly = fallback
    return {"daily": daily, "weekly": weekly, "monthly": weekly * 4, "per_txn": daily}


# ---------------------------------------------------------------------------
# Fee calculation
# ---------------------------------------------------------------------------

def calculate_fee(amount: float) -> float:
    raw = amount * settings.WITHDRAWAL_FEE_PERCENT
    return round(min(raw, settings.WITHDRAWAL_FEE_CAP), 2)


# ---------------------------------------------------------------------------
# Usage queries
# ---------------------------------------------------------------------------

def _sum_withdrawals_since(db: Session, user_id, since: datetime) -> float:
    total = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.WITHDRAWAL,
            Transaction.status != "failed",
            Transaction.created_at >= since,
        )
        .scalar()
    )
    return float(total or 0.0)


def _count_withdrawals_since(db: Session, user_id, since: datetime) -> int:
    return int(
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.WITHDRAWAL,
            Transaction.status != "failed",
            Transaction.created_at >= since,
        )
        .scalar()
        or 0
    )


def get_withdrawal_usage(db: Session, user: User) -> dict[str, float | int]:
    now = datetime.now(timezone.utc)
    day_start = now - timedelta(days=1)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    return {
        "today_amount": _sum_withdrawals_since(db, user.id, day_start),
        "week_amount": _sum_withdrawals_since(db, user.id, week_start),
        "month_amount": _sum_withdrawals_since(db, user.id, month_start),
        "today_count": _count_withdrawals_since(db, user.id, day_start),
    }


# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------

def check_withdrawal(
    db: Session,
    *,
    user: User,
    amount: float,
    currency: str = "USD",
) -> dict:
    """
    Run ALL pre-flight checks. Raises HTTPException(400) on violation.
    Returns a quote on success: {amount, fee, net, tier, limits, usage}.

    Side-effect free — caller is responsible for actually executing the withdrawal.
    """
    if amount is None or amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")
    if currency != "USD":
        # Tier limits configured in USD; explicit reject avoids silent miscalculation
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only USD withdrawals supported")
    if amount < settings.WITHDRAWAL_MIN_AMOUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum withdrawal is ${settings.WITHDRAWAL_MIN_AMOUNT:.2f}",
        )

    tier = resolve_user_tier(user)
    limits = get_tier_limits(db, tier)
    usage = get_withdrawal_usage(db, user)

    if amount > limits["per_txn"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount exceeds per-transaction limit of ${limits['per_txn']:.2f} for tier {tier.value}",
        )
    if usage["today_amount"] + amount > limits["daily"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Daily limit exceeded: ${usage['today_amount']:.2f} used / "
                f"${limits['daily']:.2f} cap"
            ),
        )
    if usage["week_amount"] + amount > limits["weekly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Weekly limit exceeded: ${usage['week_amount']:.2f} used / "
                f"${limits['weekly']:.2f} cap"
            ),
        )
    if usage["today_count"] >= settings.WITHDRAWALS_PER_DAY_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum {settings.WITHDRAWALS_PER_DAY_MAX} withdrawals per day reached",
        )

    fee = calculate_fee(amount)
    net = round(amount - fee, 2)

    return {
        "amount": round(amount, 2),
        "fee": fee,
        "net": net,
        "currency": currency,
        "tier": tier.value,
        "limits": limits,
        "usage": usage,
    }


# ---------------------------------------------------------------------------
# Structuring detection helper (used by fraud_detection_service too)
# ---------------------------------------------------------------------------

def is_structuring_amount(amount: float, daily_limit: float) -> bool:
    """True if amount is suspiciously close to (but under) the daily limit."""
    if daily_limit <= 0:
        return False
    gap = (daily_limit - amount) / daily_limit
    return 0 <= gap <= settings.FRAUD_STRUCTURING_GAP_PERCENT
