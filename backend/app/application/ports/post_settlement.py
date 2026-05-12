"""PostSettlementPort — fan-out side effects after a successful settlement.

Currently bridges to legacy `trust_service.update_scores_after_success`
and `transport_service.settle_driver_payout`. As those are migrated to
proper bounded-context handlers, this port shrinks.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class PostSettlementPort(Protocol):
    def on_release(self, order_id: UUID) -> None: ...
    def on_refund(self, order_id: UUID) -> None: ...
    def on_dispute_resolved(self, order_id: UUID) -> None: ...
