"""Value objects for the Dispute bounded context."""
from __future__ import annotations

from enum import Enum


class DisputeStatus(str, Enum):
    """Lifecycle states for a dispute."""
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    PROPOSED_OFFER = "proposed_offer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

    def can_transition_to(self, target: "DisputeStatus") -> bool:
        """Check if a transition is valid."""
        valid_transitions = {
            DisputeStatus.OPEN: {DisputeStatus.UNDER_REVIEW, DisputeStatus.CLOSED},
            DisputeStatus.UNDER_REVIEW: {DisputeStatus.PROPOSED_OFFER, DisputeStatus.ESCALATED, DisputeStatus.RESOLVED},
            DisputeStatus.PROPOSED_OFFER: {DisputeStatus.RESOLVED, DisputeStatus.UNDER_REVIEW},
            DisputeStatus.ESCALATED: {DisputeStatus.RESOLVED, DisputeStatus.CLOSED},
            DisputeStatus.RESOLVED: set(),  # Terminal state
            DisputeStatus.CLOSED: set(),  # Terminal state
        }
        return target in valid_transitions.get(self, set())
