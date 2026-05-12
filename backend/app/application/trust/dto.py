"""Trust command DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RecomputeTrustCommand:
    buyer_id: UUID
    seller_id: UUID
