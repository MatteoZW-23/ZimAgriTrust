"""GetOrder query handler — read-only, no transaction needed."""
from __future__ import annotations

from app.application.orders.dto import GetOrderQuery, OrderView
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.orders.entities import Order
from app.domain.orders.exceptions import UnauthorizedActor
from app.domain.shared_kernel.identifiers import OrderId, UserId


class OrderNotFound(Exception):
    pass


class GetOrder:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def __call__(self, query: GetOrderQuery) -> OrderView:
        with self._uow:
            order = self._uow.orders.get(OrderId(query.order_id))
            if order is None:
                raise OrderNotFound(str(query.order_id))

            actor = UserId(query.actor_id)
            if not query.actor_is_admin and actor not in (order.buyer_id, order.seller_id):
                raise UnauthorizedActor("get_order")

            return _to_view(order, actor_is_buyer_or_admin=query.actor_is_admin or actor == order.buyer_id)


def _to_view(order: Order, *, actor_is_buyer_or_admin: bool) -> OrderView:
    return OrderView(
        id=order.id.value,
        order_number=order.order_number,
        buyer_id=order.buyer_id.value,
        seller_id=order.seller_id.value,
        status=order.status.value,
        total_amount_cents=order.total_amount.cents,
        seller_payout_cents=order.seller_payout.cents,
        currency=order.total_amount.currency.value,
        logistics_type=order.logistics_type.value,
        # Handover code only revealed to buyer / admin, never seller.
        handover_code_visible=order.handover_code if actor_is_buyer_or_admin else None,
        created_at=order.created_at,
    )
