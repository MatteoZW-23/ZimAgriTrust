"""Notification port — adapters publish to bus, queue, log, etc."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.orders.events import DomainEvent


@runtime_checkable
class NotificationPort(Protocol):
    def publish(self, event: DomainEvent) -> None: ...
