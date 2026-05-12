"""Settlement plans — immutable, self-validating value objects.

Each plan asserts that `payout + fee + refund = total` so callers cannot
construct an internally-inconsistent settlement. The Settlement service
trusts the plan once constructed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from app.domain.escrow.exceptions import SettlementMathError
from app.domain.shared_kernel.money import Money


def _zero_like(m: Money) -> Money:
    return Money(cents=0, currency=m.currency)


@dataclass(frozen=True, slots=True)
class ReleasePlan:
    """Happy path: full release to seller, fee retained as platform revenue."""
    total: Money
    fee: Money
    payout: Money

    def __post_init__(self) -> None:
        if self.fee.currency != self.total.currency or self.payout.currency != self.total.currency:
            raise SettlementMathError("Mixed currencies in ReleasePlan")
        if self.payout.cents + self.fee.cents != self.total.cents:
            raise SettlementMathError(
                f"payout + fee != total ({self.payout.cents} + {self.fee.cents} "
                f"!= {self.total.cents})"
            )


@dataclass(frozen=True, slots=True)
class RefundPlan:
    """Full refund: 100% returned to buyer, no fee."""
    total: Money

    def __post_init__(self) -> None:
        if self.total.cents <= 0:
            raise SettlementMathError("RefundPlan total must be > 0")


@dataclass(frozen=True, slots=True)
class DisputeSplitPlan:
    """Mediated split: buyer gets refund, seller gets payout, platform takes fee."""
    total: Money
    buyer_refund: Money
    seller_payout: Money
    fee: Money

    def __post_init__(self) -> None:
        currencies = {
            self.total.currency,
            self.buyer_refund.currency,
            self.seller_payout.currency,
            self.fee.currency,
        }
        if len(currencies) > 1:
            raise SettlementMathError(f"Mixed currencies in DisputeSplitPlan: {currencies}")
        s = self.buyer_refund.cents + self.seller_payout.cents + self.fee.cents
        if s != self.total.cents:
            raise SettlementMathError(
                f"refund + payout + fee != total ({s} != {self.total.cents})"
            )


SettlementPlan = Union[ReleasePlan, RefundPlan, DisputeSplitPlan]
