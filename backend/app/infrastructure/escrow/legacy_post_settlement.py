"""PostSettlementPort adapter — bridges to legacy fan-out side effects.

This is *not* the long-term home for these handlers (trust scoring and
driver settlement should each become their own bounded contexts that
react to domain events). It is a strict-parity bridge so the new escrow
use cases preserve all current behaviour.
"""
from __future__ import annotations

import logging
import os
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.post_settlement import PostSettlementPort

_log = logging.getLogger(__name__)


class LegacyPostSettlementAdapter(PostSettlementPort):
    def __init__(self, session: Session, trust_use_case=None) -> None:
        self._session = session
        self._trust_use_case = trust_use_case
        self._trust_use_domain = os.getenv("TRUST_USE_DOMAIN", "false").lower() == "true"

    # -------- on_release: driver payout + trust score updates --------

    def on_release(self, order_id: UUID) -> None:
        # Lazy imports to keep import graph clean.
        from app.models.transaction import Order as OrmOrder

        order = self._session.get(OrmOrder, order_id)
        if order is None:
            return

        # Driver settlement (third-party logistics).
        if order.driver_payout and order.driver_payout > 0:
            try:
                from app.models.driver import DriverJob
                from app.services.transport_service import settle_driver_payout
                job = self._session.query(DriverJob).filter(
                    DriverJob.order_id == order.id,
                    DriverJob.status == "DELIVERED",
                ).first()
                if job:
                    settle_driver_payout(self._session, job)
            except Exception as e:  # pragma: no cover
                _log.error("Driver payout failed for order %s: %s", order.id, e)

        # Trust scoring.
        if self._trust_use_domain and self._trust_use_case:
            try:
                from app.application.trust.dto import RecomputeTrustCommand
                cmd = RecomputeTrustCommand(
                    buyer_id=order.buyer_id,
                    seller_id=order.seller_id,
                )
                self._trust_use_case(cmd)
            except Exception as e:  # pragma: no cover
                _log.error("Domain trust update failed for order %s: %s", order.id, e)
        else:
            try:
                from app.services.trust_service import update_scores_after_success
                update_scores_after_success(self._session, order)
            except Exception as e:  # pragma: no cover
                _log.error("Legacy trust update failed for order %s: %s", order.id, e)

    def on_refund(self, order_id: UUID) -> None:
        # Legacy refund_payment had no fan-out beyond the audit ledger.
        return

    def on_dispute_resolved(self, order_id: UUID) -> None:
        # Legacy resolve_dispute had no fan-out beyond the audit ledger.
        return
