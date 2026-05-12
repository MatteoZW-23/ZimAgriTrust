"""SQLAlchemy adapter for DisputeReader."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.disputes import DisputeReader
from app.domain.shared_kernel.identifiers import OrderId
from app.models.dispute import Dispute as OrmDispute


class SqlAlchemyDisputeReader(DisputeReader):
    def __init__(self, session: Session) -> None:
        self._session = session

    def exists_for_order(self, order_id: OrderId) -> bool:
        return self._session.query(OrmDispute).filter(
            OrmDispute.order_id == order_id.value
        ).first() is not None
