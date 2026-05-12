"""ResolveDispute use case — replaces escrow_service.resolve_dispute."""
from __future__ import annotations

from app.application.escrow.dto import ResolveDisputeCommand
from app.application.escrow.release_escrow import (
    OrderNotFound,
    WalletNotFound,
    _force_status,
)
from app.application.ports.notifications import NotificationPort
from app.application.ports.post_settlement import PostSettlementPort
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.escrow.plans import DisputeSplitPlan
from app.domain.escrow.settlement import Settlement
from app.domain.orders.exceptions import InvalidStatusTransition
from app.domain.orders.value_objects import OrderStatus
from app.domain.shared_kernel.identifiers import OrderId
from app.domain.shared_kernel.money import Money


class ResolveDispute:
    def __init__(
        self,
        uow: UnitOfWork,
        notifier: NotificationPort,
        post_settlement: PostSettlementPort,
    ) -> None:
        self._uow = uow
        self._notifier = notifier
        self._post_settlement = post_settlement

    def __call__(self, cmd: ResolveDisputeCommand) -> None:
        with self._uow:
            order = self._uow.orders.get(OrderId(cmd.order_id))
            if order is None:
                raise OrderNotFound(str(cmd.order_id))
            if order.status != OrderStatus.DISPUTED:
                raise InvalidStatusTransition(order.status.value, OrderStatus.SETTLED.value)

            currency = order.total_amount.currency
            buyer = self._uow.wallets.get(order.buyer_id, currency)
            seller = self._uow.wallets.get(order.seller_id, currency)
            if buyer is None or seller is None:
                raise WalletNotFound(f"order={cmd.order_id}")

            plan = DisputeSplitPlan(
                total=order.total_amount,
                buyer_refund=Money(cents=cmd.buyer_refund_cents, currency=currency),
                seller_payout=Money(cents=cmd.seller_payout_cents, currency=currency),
                fee=Money(cents=cmd.fee_cents, currency=currency),
            )

            result = Settlement.resolve_dispute(
                order_id=order.id,
                buyer=buyer,
                seller=seller,
                plan=plan,
            )

            self._uow.wallets.save(buyer)
            self._uow.wallets.save(seller)
            self._uow.ledger.append(result.ledger_entries)

            _force_status(order, OrderStatus.SETTLED)
            self._uow.orders.save(order)
            self._uow.commit()

            try:
                self._post_settlement.on_dispute_resolved(cmd.order_id)
            except Exception:  # pragma: no cover
                import logging
                logging.exception("post-settlement on_dispute_resolved failed for order %s", cmd.order_id)

            for event in result.events:
                self._notifier.publish(event)
