"""Order aggregate root — enforces lifecycle invariants in pure Python."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from app.domain.orders.events import (
    DeliveryConfirmed,
    DomainEvent,
    EscrowReleased,
)
from app.domain.orders.exceptions import (
    InvalidHandoverCode,
    InvalidStatusTransition,
    NotEscrowed,
    UnauthorizedActor,
)
from app.domain.orders.value_objects import LogisticsType, OrderStatus
from app.domain.shared_kernel.identifiers import OrderId, UserId
from app.domain.shared_kernel.money import Money

# Allowed status transitions. Single source of truth; mapper enforces no
# illegal state ever lands in the DB.
_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PENDING:     frozenset({OrderStatus.ESCROW_HELD, OrderStatus.REFUNDED}),
    OrderStatus.ESCROW_HELD: frozenset({OrderStatus.DELIVERED, OrderStatus.DISPUTED, OrderStatus.REFUNDED}),
    OrderStatus.DELIVERED:   frozenset({OrderStatus.COMPLETED, OrderStatus.DISPUTED}),
    OrderStatus.COMPLETED:   frozenset({OrderStatus.SETTLED}),
    OrderStatus.DISPUTED:    frozenset({OrderStatus.SETTLED, OrderStatus.REFUNDED}),
    OrderStatus.SETTLED:     frozenset(),  # terminal
    OrderStatus.REFUNDED:    frozenset(),  # terminal
}


@dataclass
class Order:
    """
    Aggregate root for the order lifecycle.

    Holds only data + invariants needed to make transition decisions.
    Excludes ORM relationships (listing, offer, disputes) — those are
    queried through ports if a use case needs them.
    """
    id: OrderId
    buyer_id: UserId
    seller_id: UserId
    order_number: str
    total_amount: Money
    seller_payout: Money
    status: OrderStatus
    logistics_type: LogisticsType
    handover_code: str | None
    created_at: datetime

    # Domain events accumulated during a command; the application layer
    # is responsible for dispatching + clearing them post-commit.
    _events: List[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    # ---------------- invariants ----------------

    def _transition_to(self, target: OrderStatus) -> None:
        if target not in _TRANSITIONS[self.status]:
            raise InvalidStatusTransition(self.status.value, target.value)
        self.status = target

    # ---------------- commands ----------------

    def confirm_delivery(self, *, actor_id: UserId, handover_code: str | None) -> None:
        """
        Buyer confirms goods received. Validates:
          - actor is the buyer
          - order is currently in escrow
          - handover code matches (only required when platform/3rd-party logistics)
        Transitions ESCROW_HELD -> DELIVERED and emits domain events.
        """
        if actor_id != self.buyer_id:
            raise UnauthorizedActor("confirm_delivery")

        if self.status != OrderStatus.ESCROW_HELD:
            raise NotEscrowed()

        # Handover code is mandatory for non-self logistics.
        if self.logistics_type in (LogisticsType.PLATFORM, LogisticsType.THIRD_PARTY):
            if not handover_code or handover_code.strip() != (self.handover_code or "").strip():
                raise InvalidHandoverCode()

        self._transition_to(OrderStatus.DELIVERED)
        now = datetime.now(timezone.utc)
        self._events.append(DeliveryConfirmed(occurred_at=now, order_id=self.id, confirmed_by=actor_id))

    def mark_settled_after_release(self) -> None:
        """
        Mark the order COMPLETED -> SETTLED after escrow funds have been
        physically released by the infrastructure adapter (escrow service).
        """
        if self.status == OrderStatus.DELIVERED:
            self._transition_to(OrderStatus.COMPLETED)
        if self.status != OrderStatus.COMPLETED:
            raise InvalidStatusTransition(self.status.value, OrderStatus.SETTLED.value)
        self._transition_to(OrderStatus.SETTLED)
        self._events.append(EscrowReleased(
            occurred_at=datetime.now(timezone.utc),
            order_id=self.id,
            seller_id=self.seller_id,
            seller_payout=self.seller_payout,
        ))

    # ---------------- event helpers ----------------

    def pull_events(self) -> list[DomainEvent]:
        """Return and clear accumulated events. Called by the application layer post-commit."""
        events, self._events = list(self._events), []
        return events
