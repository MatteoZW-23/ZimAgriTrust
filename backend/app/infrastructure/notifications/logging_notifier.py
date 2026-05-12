"""Default NotificationPort adapter — logs events.

Will be replaced with a Redis Streams / RabbitMQ adapter in Phase 2;
the use case never changes.
"""
from __future__ import annotations

import logging

from app.application.ports.notifications import NotificationPort
from app.domain.orders.events import DomainEvent

_log = logging.getLogger("agritrust.events")


class LoggingNotifier(NotificationPort):
    def publish(self, event: DomainEvent) -> None:
        _log.info(
            "DOMAIN_EVENT | %s | %s",
            type(event).__name__,
            event,
        )
