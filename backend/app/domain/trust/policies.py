"""Trust scoring policies — weights + pure recompute function.

Faithful port of the legacy formulas in `services/trust_service.py`:

  Buyer:
    score = base
          + successful_orders * w.successful_action
          + (successful_orders // 5) * w.milestone_5
          - disputes * 12
          - failed_orders * 10
          - leakage_penalty

  Farmer:
    score = base
          + successful_orders * w.successful_action
          + (successful_orders // 5) * w.milestone_5
          - disputes * 10
          + min(listings_count, 5)
          - leakage_penalty

  result = clamp(score, 0..100)

Leakage penalty is computed by the infrastructure (history reader) and
passed in as a precomputed value so this layer stays pure.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.trust.exceptions import UnsupportedRole
from app.domain.trust.value_objects import Role, TrustScore


@dataclass(frozen=True, slots=True)
class TrustWeights:
    successful_action: int
    milestone_5: int
    dispute_penalty: int
    failed_order_penalty: int  # buyer-only; ignored for farmer (set 0)


# Legacy defaults from `verification_service.TRUST_SCORES`.
BUYER_WEIGHTS = TrustWeights(
    successful_action=2,
    milestone_5=0,
    dispute_penalty=12,
    failed_order_penalty=10,
)

FARMER_WEIGHTS = TrustWeights(
    successful_action=2,
    milestone_5=10,
    dispute_penalty=10,
    failed_order_penalty=0,
)


@dataclass(frozen=True, slots=True)
class TrustHistory:
    """Snapshot of the user's history relevant to trust scoring.

    Constructed by the infrastructure layer from the database. Domain
    receives a frozen value object and never queries.
    """
    successful_orders: int
    disputes: int
    failed_orders: int = 0           # buyer only
    listings_count: int = 0          # farmer only
    leakage_penalty: float = 0.0


def recompute(*, role: Role, base: int, history: TrustHistory) -> TrustScore:
    """Pure recompute. Returns a clamped TrustScore."""
    if role == Role.BUYER:
        w = BUYER_WEIGHTS
        score = (
            base
            + history.successful_orders * w.successful_action
            + (history.successful_orders // 5) * w.milestone_5
            - history.disputes * w.dispute_penalty
            - history.failed_orders * w.failed_order_penalty
            - history.leakage_penalty
        )
    elif role == Role.FARMER:
        w = FARMER_WEIGHTS
        score = (
            base
            + history.successful_orders * w.successful_action
            + (history.successful_orders // 5) * w.milestone_5
            - history.disputes * w.dispute_penalty
            + min(history.listings_count, 5)
            - history.leakage_penalty
        )
    else:
        raise UnsupportedRole(f"Trust recompute not defined for role: {role}")

    return TrustScore.clamp(score)
