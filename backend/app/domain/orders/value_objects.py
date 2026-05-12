"""Order value objects (enums) — decoupled from ORM enum to allow safe evolution."""
from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    """
    Domain status. Note that the persistence layer's `OrderStatus` aliases
    CANCELLED -> REFUNDED for legacy DB reasons; the domain keeps them
    distinct conceptually. The mapper bridges the two.
    """
    PENDING = "PENDING"
    ESCROW_HELD = "ESCROW_HELD"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    SETTLED = "SETTLED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"


class LogisticsType(str, Enum):
    PLATFORM = "PLATFORM"
    THIRD_PARTY = "THIRD_PARTY"
    SELF = "SELF"
