"""Money value object — integer-cents, immutable, currency-checked."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Currency(str, Enum):
    USD = "USD"
    ZIG = "ZIG"  # Zimbabwe Gold — actual currency used by wallet_service.


@dataclass(frozen=True, slots=True)
class Money:
    """
    Money is stored in integer minor units (cents) to avoid float drift.
    All arithmetic is currency-safe; mixing currencies raises.
    """
    cents: int
    currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.cents, int):
            raise TypeError("Money.cents must be int (minor units)")
        if self.cents < 0:
            raise ValueError("Money cannot be negative")

    @classmethod
    def from_major(cls, amount: float | str, currency: Currency | str) -> "Money":
        """Construct from major units (e.g. 12.50 USD). Rounds banker's rounding."""
        cur = Currency(currency) if isinstance(currency, str) else currency
        # Use string conversion to avoid binary float artefacts.
        from decimal import Decimal, ROUND_HALF_EVEN
        d = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        return cls(cents=int(d * 100), currency=cur)

    @property
    def major(self) -> float:
        return self.cents / 100

    def _check_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"Currency mismatch: {self.currency.value} vs {other.currency.value}"
            )

    def __add__(self, other: "Money") -> "Money":
        self._check_same_currency(other)
        return Money(self.cents + other.cents, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check_same_currency(other)
        if other.cents > self.cents:
            raise ValueError("Subtraction would yield negative Money")
        return Money(self.cents - other.cents, self.currency)

    def __str__(self) -> str:
        return f"{self.currency.value} {self.major:.2f}"
