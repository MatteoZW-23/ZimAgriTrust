"""Trust ports."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.shared_kernel.identifiers import UserId
from app.domain.trust.policies import TrustHistory
from app.domain.trust.value_objects import Role, TrustScore


@runtime_checkable
class TrustHistoryReader(Protocol):
    def read(self, user_id: UserId, role: Role) -> TrustHistory: ...

    def base_score(self, user_id: UserId) -> int:
        """Verification-derived starting score (e.g. KYC tier)."""
        ...

    def role_of(self, user_id: UserId) -> Role | None:
        """None if user is not a trust-scored role."""
        ...

    def completed_count(self, user_id: UserId, *, as_buyer: bool) -> int:
        """Number of COMPLETED orders for the user (used for first-tx milestone)."""
        ...


@runtime_checkable
class TrustRepository(Protocol):
    def current_score(self, user_id: UserId) -> TrustScore: ...

    def save(
        self,
        *,
        user_id: UserId,
        role: Role,
        previous: TrustScore,
        new: TrustScore,
        reason: str,
        triggered_by: str,
    ) -> None:
        """Persist new score + append audit event."""
        ...


@runtime_checkable
class TrustMilestonePort(Protocol):
    def on_first_transaction(self, user_id: UserId) -> None: ...
