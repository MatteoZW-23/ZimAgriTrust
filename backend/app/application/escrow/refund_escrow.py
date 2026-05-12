"""RefundEscrow use case — replaces escrow_service.refund_payment."""
from __future__ import annotations

from app.application.escrow.dto import RefundEscrowCommand
from app.application.escrow.release_escrow import (
    OrderNotFound,
    WalletNotFound,
    _force_status,
)
from app.application.ports.notifications import NotificationPort
from app.application.ports.post_settlement import PostSettlementPort
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.escrow.plans import RefundPlan
from app.domain.escrow.settlement import Settlement
from app.domain.orders.exceptions import InvalidStatusTransition
from app.domain.orders.value_objects import OrderStatus
from app.domain.shared_kernel.identifiers import OrderId

_REFUNDABLE = frozenset({OrderStatus.ESCROW_HELD, OrderStatus.DISPUTED})


class RefundEscrow:
    def __init__(
        self,
        uow: UnitOfWork,
        notifier: NotificationPort,
        post_settlement: PostSettlementPort,
    ) -> None:
        self._uow = uow
        self._notifier = notifier
        self._post_settlement = post_settlement

    def __call__(self, cmd: RefundEscrowCommand) -> None:
        with self._uow:
            order = self._uow.orders.get(OrderId(cmd.order_id))
            if order is None:
                raise OrderNotFound(str(cmd.order_id))
            if order.status not in _REFUNDABLE:
                raise InvalidStatusTransition(order.status.value, OrderStatus.REFUNDED.value)

            buyer = self._uow.wallets.get(order.buyer_id, order.total_amount.currency)
            if buyer is None:
                raise WalletNotFound(f"order={cmd.order_id} buyer")

            plan = RefundPlan(total=order.total_amount)
            result = Settlement.refund(order_id=order.id, buyer=buyer, plan=plan)

            self._uow.wallets.save(buyer)
            self._uow.ledger.append(result.ledger_entries)

            _force_status(order, OrderStatus.REFUNDED)
            self._uow.orders.save(order)
            self._uow.commit()

            try:
                self._post_settlement.on_refund(cmd.order_id)
            except Exception:  # pragma: no cover
                import logging
                logging.exception("post-settlement on_refund failed for order %s", cmd.order_id)

            for event in result.events:
                self._notifier.publish(event)
