"""CreateDispute use case."""
from __future__ import annotations

from uuid import UUID

from app.application.disputes.dto import CreateDisputeCommand
from app.application.ports.disputes import DisputeReader, DisputeRepository
from app.application.ports.notifications import NotificationPort
from app.domain.disputes.entities import Dispute
from app.domain.shared_kernel.identifiers import DisputeId, OrderId, UserId


class CreateDispute:
    def __init__(
        self,
        repository: DisputeRepository,
        reader: DisputeReader,
        notifier: NotificationPort,
    ) -> None:
        self._repo = repository
        self._reader = reader
        self._notifier = notifier

    def __call__(self, cmd: CreateDisputeCommand) -> Dispute:
        order_id = OrderId(cmd.order_id)
        raised_by = UserId(cmd.raised_by)

        # Check if dispute already exists for this order
        if self._reader.exists_for_order(order_id):
            raise ValueError(f"Dispute already exists for order {order_id}")

        # Create dispute aggregate
        dispute = Dispute.create(
            dispute_id=DisputeId(UUID()),
            order_id=order_id,
            raised_by=raised_by,
            dispute_type=cmd.dispute_type,
            description=cmd.description,
        )

        # Persist
        self._repo.save(dispute)

        # Publish domain events
        for event in dispute.pull_events():
            self._notifier.publish(event)

        return dispute
