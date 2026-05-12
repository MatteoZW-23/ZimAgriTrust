"""Strongly-typed identifier wrappers — prevent passing a UserId where an OrderId is expected."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class _UuidId:
    value: UUID

    def __str__(self) -> str:  # pragma: no cover
        return str(self.value)


class OrderId(_UuidId):
    pass


class UserId(_UuidId):
    pass


class DisputeId(_UuidId):
    pass


class LoanId(_UuidId):
    pass


class LoanProductId(_UuidId):
    pass


class LoanRepaymentId(_UuidId):
    pass
