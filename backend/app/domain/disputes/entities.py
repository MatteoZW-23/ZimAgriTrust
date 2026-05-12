"""Dispute aggregate root."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from app.domain.disputes.events import (
    DisputeCreated,
    DisputeEscalated,
    DisputeProposedOffer,
    DisputeResolved,
)
from app.domain.disputes.exceptions import DisputeAlreadyResolved, DisputeNotOpen, InvalidDisputeTransition
from app.domain.disputes.value_objects import DisputeStatus
from app.domain.shared_kernel.identifiers import DisputeId, OrderId, UserId


@dataclass(slots=True)
class Dispute:
    """Aggregate root for dispute management.

    Enforces valid status transitions and emits domain events.
    """
    id: DisputeId
    order_id: OrderId
    raised_by: UserId
    dispute_type: str
    description: str
    status: DisputeStatus = DisputeStatus.OPEN
    agent_assigned: UserId | None = None
    resolution: str | None = None
    proposed_discount: float = 0.0
    proposed_refund_amount: float = 0.0
    buyer_accepted: bool = False
    seller_accepted: bool = False
    agent_resolution_memo: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _events: list = field(default_factory=list, init=False, repr=False)

    @classmethod
    def create(
        cls,
        dispute_id: DisputeId,
        order_id: OrderId,
        raised_by: UserId,
        dispute_type: str,
        description: str,
    ) -> Dispute:
        """Create a new dispute."""
        dispute = cls(
            id=dispute_id,
            order_id=order_id,
            raised_by=raised_by,
            dispute_type=dispute_type,
            description=description,
        )
        dispute._events.append(
            DisputeCreated(
                dispute_id=dispute_id.value,
                order_id=order_id.value,
                raised_by=raised_by.value,
                dispute_type=dispute_type,
                description=description,
                occurred_at=dispute.created_at,
            )
        )
        return dispute

    def assign_agent(self, agent_id: UserId) -> None:
        """Assign an agent to review the dispute."""
        if self.status != DisputeStatus.OPEN:
            raise DisputeNotOpen("Can only assign agent to OPEN disputes")
        self.agent_assigned = agent_id
        self._transition_to(DisputeStatus.UNDER_REVIEW)

    def propose_offer(
        self,
        discount_percent: float,
        refund_amount: float,
        proposed_by: UserId,
        memo: str,
    ) -> None:
        """Propose a settlement offer."""
        if self.status != DisputeStatus.UNDER_REVIEW:
            raise InvalidDisputeTransition(f"Cannot propose offer from {self.status}")
        if not (0 <= discount_percent <= 100):
            raise ValueError("Discount percent must be between 0 and 100")
        if refund_amount < 0:
            raise ValueError("Refund amount must be non-negative")

        self.proposed_discount = discount_percent
        self.proposed_refund_amount = refund_amount
        self.agent_resolution_memo = memo
        self._transition_to(DisputeStatus.PROPOSED_OFFER)

        self._events.append(
            DisputeProposedOffer(
                dispute_id=self.id.value,
                order_id=self.order_id.value,
                discount_percent=discount_percent,
                refund_amount=refund_amount,
                proposed_by=proposed_by.value,
                memo=memo,
                occurred_at=datetime.now(timezone.utc),
            )
        )

    def accept_offer(self, *, as_buyer: bool) -> None:
        """Accept the proposed offer."""
        if self.status != DisputeStatus.PROPOSED_OFFER:
            raise InvalidDisputeTransition(f"Cannot accept offer from {self.status}")

        if as_buyer:
            self.buyer_accepted = True
        else:
            self.seller_accepted = True

        # If both accepted, auto-resolve
        if self.buyer_accepted and self.seller_accepted:
            self.resolve(
                resolution=f"Mutual agreement: {self.proposed_discount}% discount",
                release_to_farmer=False,
            )

    def reject_offer(self) -> None:
        """Reject the proposed offer and return to review."""
        if self.status != DisputeStatus.PROPOSED_OFFER:
            raise InvalidDisputeTransition(f"Cannot reject offer from {self.status}")

        self.buyer_accepted = False
        self.seller_accepted = False
        self.proposed_discount = 0.0
        self.proposed_refund_amount = 0.0
        self._transition_to(DisputeStatus.UNDER_REVIEW)

    def resolve(self, resolution: str, release_to_farmer: bool) -> None:
        """Resolve the dispute with a final decision."""
        if self.status in (DisputeStatus.RESOLVED, DisputeStatus.CLOSED):
            raise DisputeAlreadyResolved(f"Dispute is already {self.status}")

        previous_status = self.status
        self.resolution = resolution
        self._transition_to(DisputeStatus.RESOLVED)

        self._events.append(
            DisputeResolved(
                dispute_id=self.id.value,
                order_id=self.order_id.value,
                resolution=resolution,
                previous_status=previous_status,
                occurred_at=datetime.now(timezone.utc),
            )
        )

    def escalate(self, escalated_by: UserId, reason: str) -> None:
        """Escalate the dispute to higher authority."""
        if self.status not in (DisputeStatus.UNDER_REVIEW, DisputeStatus.PROPOSED_OFFER):
            raise InvalidDisputeTransition(f"Cannot escalate from {self.status}")

        previous_status = self.status
        self._transition_to(DisputeStatus.ESCALATED)

        self._events.append(
            DisputeEscalated(
                dispute_id=self.id.value,
                order_id=self.order_id.value,
                escalated_by=escalated_by.value,
                reason=reason,
                occurred_at=datetime.now(timezone.utc),
            )
        )

    def close(self) -> None:
        """Close the dispute without resolution."""
        if self.status not in (DisputeStatus.OPEN, DisputeStatus.ESCALATED):
            raise InvalidDisputeTransition(f"Cannot close from {self.status}")

        self._transition_to(DisputeStatus.CLOSED)

    def _transition_to(self, target: DisputeStatus) -> None:
        """Internal transition validation."""
        if not self.status.can_transition_to(target):
            raise InvalidDisputeTransition(
                f"Cannot transition from {self.status} to {target}"
            )
        self.status = target

    def pull_events(self) -> list:
        """Pull and clear domain events."""
        events = self._events[:]
        self._events.clear()
        return events
