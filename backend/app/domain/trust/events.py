"""Trust domain events."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.shared_kernel.identifiers import UserId
from app.domain.trust.value_objects import Role, TrustScore


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class TrustScoreUpdated:
    user_id: UserId
    role: Role
    previous: TrustScore
    new: TrustScore
    delta: int
    reason: str
    triggered_by: str
    occurred_at: datetime
