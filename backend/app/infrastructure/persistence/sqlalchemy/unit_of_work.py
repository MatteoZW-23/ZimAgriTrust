"""SQLAlchemy adapter for UnitOfWork port."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.unit_of_work import UnitOfWork
from app.infrastructure.persistence.sqlalchemy.ledger_adapter import (
    SqlAlchemyLedgerAdapter,
)
from app.infrastructure.persistence.sqlalchemy.order_repository import (
    SqlAlchemyOrderRepository,
)
from app.infrastructure.persistence.sqlalchemy.wallet_repository import (
    SqlAlchemyWalletRepository,
)
from app.infrastructure.persistence.sqlalchemy.trust_repository import (
    SqlAlchemyTrustRepository,
)
from app.infrastructure.persistence.sqlalchemy.trust_history_reader import (
    SqlAlchemyTrustHistoryReader,
)
from app.infrastructure.persistence.sqlalchemy.dispute_repository import (
    SqlAlchemyDisputeRepository,
)
from app.infrastructure.persistence.sqlalchemy.dispute_reader import (
    SqlAlchemyDisputeReader,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    """
    Wraps a SQLAlchemy Session.

    Note: takes an externally-managed session (FastAPI's `get_db`
        self.disputes = SqlAlchemyDisputeRepository(session)
        self.dispute_reader = SqlAlchemyDisputeReader(session)
    generator owns the lifecycle) so transaction boundaries align with
    the request scope. `commit()` flushes to the same session FastAPI
    will close on exit.
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self.orders = SqlAlchemyOrderRepository(session)
        self.wallets = SqlAlchemyWalletRepository(session)
        self.ledger = SqlAlchemyLedgerAdapter(session)
        self.trust = SqlAlchemyTrustRepository(session)
        self.trust_history = SqlAlchemyTrustHistoryReader(session)
        self.disputes = SqlAlchemyDisputeRepository(session)
        self.dispute_reader = SqlAlchemyDisputeReader(session)

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
