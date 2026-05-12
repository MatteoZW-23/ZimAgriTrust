"""Trust domain exceptions."""
from __future__ import annotations


class TrustDomainError(Exception):
    pass


class InvalidScore(TrustDomainError):
    pass


class UnsupportedRole(TrustDomainError):
    pass
