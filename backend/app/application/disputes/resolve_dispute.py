"""ResolveDispute use case."""
from __future__ import annotations

from uuid import UUID

from app.application.disputes.dto import ResolveDisputeCommand
from app.application.ports.disputes import DisputeRepository
from app.application.ports.notifications import NotificationPort
from app.domain.shared_kernel.identifiers import DisputeId


class ResolveDispute:
    def __init__(
        self,
        repository: DisputeRepository,
        notifier: NotificationPort,
    ) -> None:
        self._repo = repository
        self._notifier = notifier

    def __call__(self, cmd: ResolveDisputeCommand) -> None:
        dispute_id = DisputeId(cmd.dispute_id)
        dispute = self._repo.get_by_id(dispute_id)

        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        # Resolve the dispute
        dispute.resolve(
            resolution=cmd.resolution,
            release_to_farmer=cmd.release_to_farmer,
        )

        # Persist
        self._repo.save(dispute)

        # Publish domain events
        for event in dispute.pull_events():
            self._notifier.publish(event)
