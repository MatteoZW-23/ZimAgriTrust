"""Trust value objects."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.trust.exceptions import InvalidScore


class Role(str, Enum):
    """Domain-local roles relevant to trust scoring.

    Mirrors the legacy `UserRole` enum's string values for buyer / farmer /
    agent. Other roles (admin, transporter) are not trust-scored.
    """
    BUYER = "buyer"
    FARMER = "farmer"
    AGENT = "agent"


_MIN, _MAX = 0, 100


@dataclass(frozen=True, slots=True)
class TrustScore:
    """Integer score in [0, 100]. Self-validating."""
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise InvalidScore(f"TrustScore must be int, got {type(self.value).__name__}")
        if not (_MIN <= self.value <= _MAX):
            raise InvalidScore(f"TrustScore out of range: {self.value}")

    @classmethod
    def clamp(cls, raw: float | int) -> "TrustScore":
        """Round half-even and clamp into [0, 100]. Convenience for formula output."""
        rounded = int(round(raw))
        return cls(max(_MIN, min(_MAX, rounded)))

    def with_delta(self, delta: int) -> "TrustScore":
        return TrustScore.clamp(self.value + delta)
