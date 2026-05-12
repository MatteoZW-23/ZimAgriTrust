"""ConfirmDelivery use case — orchestrates domain transition + escrow release."""
from __future__ import annotations

from app.application.orders.dto import ConfirmDeliveryCommand
from app.application.ports.escrow import EscrowPort
from app.application.ports.notifications import NotificationPort
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.shared_kernel.identifiers import OrderId, UserId


class OrderNotFound(Exception):
    pass


class ConfirmDelivery:
    """
    Use case: buyer confirms delivery of an escrowed order.

    Steps:
      1. Load aggregate inside UoW.
      2. Domain enforces invariants (state transition, handover code, actor).
      3. Infrastructure releases funds via the escrow port.
      4. Aggregate transitions to SETTLED and emits EscrowReleased event.
      5. UoW commits; events are then dispatched (post-commit, at-least-once
         via the notification port — full outbox lives in infra).
    """

    def __init__(
        self,
        uow: UnitOfWork,
        escrow: EscrowPort,
        notifier: NotificationPort,
    ) -> None:
        self._uow = uow
        self._escrow = escrow
        self._notifier = notifier

    def __call__(self, cmd: ConfirmDeliveryCommand) -> None:
        with self._uow:
            order = self._uow.orders.get(OrderId(cmd.order_id))
            if order is None:
                raise OrderNotFound(str(cmd.order_id))

            # 1. Domain transition (ESCROW_HELD -> DELIVERED) + invariants.
            order.confirm_delivery(
                actor_id=UserId(cmd.actor_id),
                handover_code=cmd.handover_code,
            )

            # 2. Infrastructure side-effect: release funds. The adapter is
            #    expected to be idempotent and to honour the same DB
            #    transaction as the UoW.
            self._escrow.release_funds(order)

            # 3. Move aggregate to terminal SETTLED state.
            order.mark_settled_after_release()

            self._uow.orders.save(order)
            self._uow.commit()

            # 4. Post-commit dispatch. (For a full system this would be
            #    a transactional outbox + relay; here the notifier is the
            #    seam that can be swapped without touching the use case.)
            for event in order.pull_events():
                self._notifier.publish(event)
