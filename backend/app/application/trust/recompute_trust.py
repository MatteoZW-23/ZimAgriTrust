"""RecomputeTrustAfterSettlement use case — replaces trust_service.update_scores_after_success.

Recomputes buyer and seller trust scores after a successful settlement
using the pure domain formula. Triggers milestone events for first
transactions via the port.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.application.trust.dto import RecomputeTrustCommand
from app.application.ports.notifications import NotificationPort
from app.application.ports.trust import (
    TrustHistoryReader,
    TrustMilestonePort,
    TrustRepository,
)
from app.domain.shared_kernel.identifiers import UserId
from app.domain.trust.events import TrustScoreUpdated
from app.domain.trust.policies import recompute
from app.domain.trust.value_objects import Role


class RecomputeTrustAfterSettlement:
    def __init__(
        self,
        history_reader: TrustHistoryReader,
        repository: TrustRepository,
        milestone: TrustMilestonePort,
        notifier: NotificationPort,
    ) -> None:
        self._reader = history_reader
        self._repo = repository
        self._milestone = milestone
        self._notifier = notifier

    def __call__(self, cmd: RecomputeTrustCommand) -> None:
        buyer_id = UserId(cmd.buyer_id)
        seller_id = UserId(cmd.seller_id)

        # Rebuyer
        buyer_role = self._reader.role_of(buyer_id)
        if buyer_role in (Role.BUYER, Role.FARMER, Role.AGENT):
            self._recompute_one(buyer_id, buyer_role)
            # First-transaction milestone
            if self._reader.completed_count(buyer_id, as_buyer=True) == 1:
                self._milestone.on_first_transaction(buyer_id)

        # Reseller
        seller_role = self._reader.role_of(seller_id)
        if seller_role in (Role.BUYER, Role.FARMER, Role.AGENT):
            self._recompute_one(seller_id, seller_role)
            if self._reader.completed_count(seller_id, as_buyer=False) == 1:
                self._milestone.on_first_transaction(seller_id)

    def _recompute_one(self, user_id: UserId, role: Role) -> None:
        previous = self._repo.current_score(user_id)
        base = self._reader.base_score(user_id)
        history = self._reader.read(user_id, role)
        new = recompute(role=role, base=base, history=history)
        delta = new.value - previous.value

        if delta == 0:
            return  # No change, skip write

        self._repo.save(
            user_id=user_id,
            role=role,
            previous=previous,
            new=new,
            reason="settlement_recompute",
            triggered_by="system",
        )

        event = TrustScoreUpdated(
            user_id=user_id,
            role=role,
            previous=previous,
            new=new,
            delta=delta,
            reason="settlement_recompute",
            triggered_by="system",
            occurred_at=datetime.now(timezone.utc),
        )
        self._notifier.publish(event)
