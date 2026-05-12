"""SQLAlchemy adapter for TrustRepository."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.trust import TrustRepository
from app.domain.shared_kernel.identifiers import UserId
from app.domain.trust.events import TrustScoreUpdated
from app.domain.trust.value_objects import Role, TrustScore
from app.models.user import TrustScoreEvent as OrmTrustScoreEvent
from app.models.user import User as OrmUser


class SqlAlchemyTrustRepository(TrustRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def current_score(self, user_id: UserId) -> TrustScore:
        row = self._session.get(OrmUser, user_id.value)
        if row is None:
            raise LookupError(f"User {user_id} not found")
        return TrustScore(row.trust_score)

    def save(
        self,
        *,
        user_id: UserId,
        role: Role,
        previous: TrustScore,
        new: TrustScore,
        reason: str,
        triggered_by: str,
    ) -> None:
        row = self._session.get(OrmUser, user_id.value)
        if row is None:
            raise LookupError(f"User {user_id} not found")
        row.trust_score = new.value
        self._session.add(row)

        event = OrmTrustScoreEvent(
            user_id=user_id.value,
            previous_score=previous.value,
            new_score=new.value,
            delta=new.value - previous.value,
            reason=reason,
            triggered_by=triggered_by,
        )
        self._session.add(event)
