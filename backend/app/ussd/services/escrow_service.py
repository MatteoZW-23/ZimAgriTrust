"""USSD Escrow Service."""
from __future__ import annotations
from typing import Any
import uuid

class USSDEscrowService:
    @staticmethod
    async def create_escrow(db: Any, buyer_id: str, seller_id: str, listing_id: str, qty: float, total: float) -> Any:
        from app.models.escrow import Escrow, EscrowStatus
        escrow = Escrow(
            id=uuid.uuid4(),
            buyer_id=buyer_id,
            seller_id=seller_id,
            listing_id=listing_id,
            quantity=qty,
            amount=total,
            status=EscrowStatus.AWAITING_PAYMENT,
        )
        db.add(escrow)
        db.commit()
        db.refresh(escrow)
        return escrow

ussd_escrow = USSDEscrowService()
