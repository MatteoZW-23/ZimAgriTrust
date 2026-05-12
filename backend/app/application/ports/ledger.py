"""LedgerPort — append-only ledger writer."""
from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable

from app.domain.escrow.ledger import LedgerEntry


@runtime_checkable
class LedgerPort(Protocol):
    def append(self, entries: Iterable[LedgerEntry]) -> None: ...
