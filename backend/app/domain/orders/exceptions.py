"""Domain exceptions — translated to HTTP errors at the API edge, never inside the domain."""
from __future__ import annotations


class OrderDomainError(Exception):
    """Base class for all order-related domain errors."""


class InvalidStatusTransition(OrderDomainError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Invalid order status transition: {current} -> {target}")
        self.current = current
        self.target = target


class NotEscrowed(OrderDomainError):
    def __init__(self) -> None:
        super().__init__("Order is not in ESCROW_HELD state")


class InvalidHandoverCode(OrderDomainError):
    def __init__(self) -> None:
        super().__init__("Handover code is invalid or missing")


class UnauthorizedActor(OrderDomainError):
    def __init__(self, action: str) -> None:
        super().__init__(f"Actor not authorized to perform: {action}")
        self.action = action
