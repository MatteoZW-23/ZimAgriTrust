"""SQLAlchemy adapter for LedgerPort — writes Transaction rows."""
from __future__ import annotations

from typing import Iterable

from sqlalchemy.orm import Session

from app.application.ports.ledger import LedgerPort
from app.domain.escrow.ledger import LedgerEntry, LedgerEntryType
from app.models.transaction import Transaction as OrmTransaction
from app.models.transaction import TransactionType as OrmTransactionType


_TYPE_MAP: dict[LedgerEntryType, OrmTransactionType] = {
    LedgerEntryType.ESCROW_HOLD: OrmTransactionType.ESCROW_HOLD,
    LedgerEntryType.ESCROW_RELEASE: OrmTransactionType.ESCROW_RELEASE,
    LedgerEntryType.REFUND: OrmTransactionType.REFUND,
    LedgerEntryType.FEE: OrmTransactionType.FEE,
    LedgerEntryType.ADJUSTMENT: OrmTransactionType.ADJUSTMENT,
}


class SqlAlchemyLedgerAdapter(LedgerPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, entries: Iterable[LedgerEntry]) -> None:
        for e in entries:
            self._session.add(OrmTransaction(
                order_id=e.order_id.value,
                user_id=e.user_id.value,
                type=_TYPE_MAP[e.type],
                amount=e.amount.major,
                currency=e.amount.currency.value,
                status="completed",
            ))
