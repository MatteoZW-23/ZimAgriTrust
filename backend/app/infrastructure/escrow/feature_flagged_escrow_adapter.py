"""Feature-flagged EscrowPort adapter.

Switches between:
  - LegacyEscrowAdapter (calls services.escrow_service.release_payment)
  - The new domain-driven ReleaseEscrow use case

Toggle via env var:  ESCROW_USE_DOMAIN=true

Both paths produce identical observable effects (wallet movements +
ledger entries + trust/driver fan-out). The new path additionally:
  - runs in a single DB transaction (atomic);
  - validates `payout + fee == total` via ReleasePlan;
  - emits structured domain events.
"""
from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session

from app.application.escrow import ReleaseEscrow, ReleaseEscrowCommand
from app.application.ports.escrow import EscrowPort
from app.domain.orders.entities import Order as DomainOrder
from app.infrastructure.escrow.legacy_escrow_adapter import LegacyEscrowAdapter
from app.infrastructure.escrow.legacy_post_settlement import (
    LegacyPostSettlementAdapter,
)
from app.infrastructure.notifications import LoggingNotifier
from app.infrastructure.persistence.sqlalchemy import SqlAlchemyUnitOfWork

_log = logging.getLogger(__name__)


def _flag_enabled() -> bool:
    return os.getenv("ESCROW_USE_DOMAIN", "false").strip().lower() in {"1", "true", "yes", "on"}


class FeatureFlaggedEscrowAdapter(EscrowPort):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._legacy = LegacyEscrowAdapter(session)

    def release_funds(self, order: DomainOrder) -> None:
        if not _flag_enabled():
            _log.debug("ESCROW_USE_DOMAIN=off — using legacy path for order %s", order.id)
            self._legacy.release_funds(order)
            return

        _log.info("ESCROW_USE_DOMAIN=on — using domain ReleaseEscrow for order %s", order.id)
        # Build a fresh UoW + use case scoped to this same DB session.
        # Note: this UoW will commit() inside; the outer ConfirmDelivery
        # use case's own UoW will then commit() again — that second
        # commit is a no-op because no further changes were made.
        uow = SqlAlchemyUnitOfWork(self._session)
        use_case = ReleaseEscrow(
            uow=uow,
            notifier=LoggingNotifier(),
            post_settlement=LegacyPostSettlementAdapter(self._session),
        )
        use_case(ReleaseEscrowCommand(order_id=order.id.value))
