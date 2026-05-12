"""Domain exceptions for the Dispute bounded context."""
from __future__ import annotations


class DisputeDomainError(Exception):
    """Base exception for dispute domain errors."""
    pass


class InvalidDisputeTransition(DisputeDomainError):
    """Raised when an invalid status transition is attempted."""
    pass


class DisputeAlreadyResolved(DisputeDomainError):
    """Raised when attempting to modify a resolved dispute."""
    pass


class DisputeNotOpen(DisputeDomainError):
    """Raised when an action requires the dispute to be in OPEN state."""
    pass
