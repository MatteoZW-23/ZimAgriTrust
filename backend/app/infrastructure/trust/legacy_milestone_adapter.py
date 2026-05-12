"""LegacyMilestoneAdapter — bridges to verification_service.record_first_transaction.

The legacy milestone logic lives in verification_service. This adapter
preserves that behaviour without dragging it into the domain.
"""
from __future__ import annotations

from sqlalchemy.orm import Session
from uuid import UUID

from app.application.ports.trust import TrustMilestonePort


class LegacyMilestoneAdapter(TrustMilestonePort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def on_first_transaction(self, user_id: UUID) -> None:
        from app.models.user import User as OrmUser
        from app.services.verification_service import verification_service

        user = self._session.get(OrmUser, user_id)
        if user:
            verification_service.record_first_transaction(self._session, user)
