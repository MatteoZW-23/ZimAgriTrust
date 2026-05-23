"""
Escrow Simulation System
Simulates escrow holds, releases, disputes, and partial settlements
"""

import asyncio
import random
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from app.providers.mock.base_provider import PaymentStatus


class EscrowStatus(Enum):
    """Escrow status states"""
    PENDING = "pending"
    HELD = "held"
    RELEASED = "released"
    PARTIALLY_RELEASED = "partially_released"
    FROZEN = "frozen"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class DisputeStatus(Enum):
    """Dispute status states"""
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


@dataclass
class EscrowHold:
    """Escrow hold record"""
    escrow_id: str
    order_id: str
    buyer_id: str
    seller_id: str
    amount: float
    currency: str
    status: EscrowStatus
    held_at: datetime
    release_deadline: datetime
    released_at: Optional[datetime] = None
    released_amount: float = 0
    frozen_at: Optional[datetime] = None
    dispute_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "escrow_id": self.escrow_id,
            "order_id": self.order_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "held_at": self.held_at.isoformat(),
            "release_deadline": self.release_deadline.isoformat(),
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "released_amount": self.released_amount,
            "frozen_at": self.frozen_at.isoformat() if self.frozen_at else None,
            "dispute_id": self.dispute_id,
            "metadata": self.metadata
        }


@dataclass
class Dispute:
    """Dispute record"""
    dispute_id: str
    escrow_id: str
    order_id: str
    raised_by: str
    reason: str
    description: str
    status: DisputeStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dispute_id": self.dispute_id,
            "escrow_id": self.escrow_id,
            "order_id": self.order_id,
            "raised_by": self.raised_by,
            "reason": self.reason,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution": self.resolution,
            "metadata": self.metadata
        }


class EscrowSimulator:
    """
    Escrow simulation system
    Simulates escrow holds, releases, disputes, and partial settlements
    """
    
    def __init__(self):
        self._escrow_holds: Dict[str, EscrowHold] = {}
        self._disputes: Dict[str, Dispute] = {}
        
        # Configuration
        self.default_hold_duration_hours = 168  # 7 days
        self.auto_release_enabled = True
        self.dispute_review_hours = 24
        
    async def hold_escrow(
        self,
        order_id: str,
        buyer_id: str,
        seller_id: str,
        amount: float,
        currency: str,
        hold_duration_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EscrowHold:
        """
        Hold funds in escrow for an order
        Returns escrow hold record
        """
        escrow_id = f"ESC_{uuid.uuid4().hex[:16]}"
        hold_duration = hold_duration_hours or self.default_hold_duration_hours
        release_deadline = datetime.utcnow() + timedelta(hours=hold_duration)
        
        escrow = EscrowHold(
            escrow_id=escrow_id,
            order_id=order_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            amount=amount,
            currency=currency,
            status=EscrowStatus.HELD,
            held_at=datetime.utcnow(),
            release_deadline=release_deadline,
            metadata=metadata
        )
        
        self._escrow_holds[escrow_id] = escrow
        return escrow
    
    async def release_escrow(
        self,
        escrow_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> EscrowHold:
        """
        Release escrow funds to seller
        Returns updated escrow hold record
        """
        escrow = self._escrow_holds.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow not found: {escrow_id}")
        
        if escrow.status == EscrowStatus.FROZEN:
            raise ValueError(f"Escrow is frozen due to dispute: {escrow_id}")
        
        if escrow.status in [EscrowStatus.RELEASED, EscrowStatus.REFUNDED]:
            raise ValueError(f"Escrow already {escrow.status.value}: {escrow_id}")
        
        release_amount = amount or escrow.amount
        escrow.released_amount += release_amount
        escrow.released_at = datetime.utcnow()
        
        if escrow.released_amount >= escrow.amount:
            escrow.status = EscrowStatus.RELEASED
        else:
            escrow.status = EscrowStatus.PARTIALLY_RELEASED
        
        if reason:
            if not escrow.metadata:
                escrow.metadata = {}
            escrow.metadata["release_reason"] = reason
        
        return escrow
    
    async def refund_escrow(
        self,
        escrow_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> EscrowHold:
        """
        Refund escrow funds to buyer
        Returns updated escrow hold record
        """
        escrow = self._escrow_holds.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow not found: {escrow_id}")
        
        if escrow.status == EscrowStatus.FROZEN:
            raise ValueError(f"Escrow is frozen due to dispute: {escrow_id}")
        
        if escrow.status in [EscrowStatus.RELEASED, EscrowStatus.REFUNDED]:
            raise ValueError(f"Escrow already {escrow.status.value}: {escrow_id}")
        
        escrow.status = EscrowStatus.REFUNDED
        escrow.released_at = datetime.utcnow()
        
        if reason:
            if not escrow.metadata:
                escrow.metadata = {}
            escrow.metadata["refund_reason"] = reason
        
        return escrow
    
    async def freeze_escrow(
        self,
        escrow_id: str,
        reason: str
    ) -> EscrowHold:
        """
        Freeze escrow due to dispute
        Returns updated escrow hold record
        """
        escrow = self._escrow_holds.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow not found: {escrow_id}")
        
        escrow.status = EscrowStatus.FROZEN
        escrow.frozen_at = datetime.utcnow()
        
        if not escrow.metadata:
            escrow.metadata = {}
        escrow.metadata["freeze_reason"] = reason
        
        return escrow
    
    async def unfreeze_escrow(
        self,
        escrow_id: str,
        reason: Optional[str] = None
    ) -> EscrowHold:
        """
        Unfreeze escrow after dispute resolution
        Returns updated escrow hold record
        """
        escrow = self._escrow_holds.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow not found: {escrow_id}")
        
        if escrow.status != EscrowStatus.FROZEN:
            raise ValueError(f"Escrow not frozen: {escrow_id}")
        
        escrow.status = EscrowStatus.HELD
        escrow.frozen_at = None
        
        if reason:
            if not escrow.metadata:
                escrow.metadata = {}
            escrow.metadata["unfreeze_reason"] = reason
        
        return escrow
    
    async def raise_dispute(
        self,
        escrow_id: str,
        order_id: str,
        raised_by: str,
        reason: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dispute:
        """
        Raise a dispute on an escrow hold
        Returns dispute record
        """
        escrow = self._escrow_holds.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow not found: {escrow_id}")
        
        dispute_id = f"DSP_{uuid.uuid4().hex[:16]}"
        
        dispute = Dispute(
            dispute_id=dispute_id,
            escrow_id=escrow_id,
            order_id=order_id,
            raised_by=raised_by,
            reason=reason,
            description=description,
            status=DisputeStatus.OPEN,
            created_at=datetime.utcnow(),
            metadata=metadata
        )
        
        self._disputes[dispute_id] = dispute
        
        # Freeze escrow
        await self.freeze_escrow(escrow_id, f"Dispute raised: {dispute_id}")
        escrow.dispute_id = dispute_id
        
        return dispute
    
    async def resolve_dispute(
        self,
        dispute_id: str,
        resolution: str,
        release_to_buyer: bool = False,
        release_amount: Optional[float] = None
    ) -> Dispute:
        """
        Resolve a dispute
        Returns updated dispute record
        """
        dispute = self._disputes.get(dispute_id)
        if not dispute:
            raise ValueError(f"Dispute not found: {dispute_id}")
        
        dispute.status = DisputeStatus.RESOLVED
        dispute.resolved_at = datetime.utcnow()
        dispute.resolution = resolution
        
        # Unfreeze escrow
        escrow = self._escrow_holds.get(dispute.escrow_id)
        if escrow:
            await self.unfreeze_escrow(dispute.escrow_id, f"Dispute resolved: {dispute_id}")
            
            # Release funds based on resolution
            if release_to_buyer:
                await self.refund_escrow(dispute.escrow_id, release_amount, resolution)
            else:
                await self.release_escrow(dispute.escrow_id, release_amount, resolution)
        
        return dispute
    
    async def process_auto_releases(self) -> List[EscrowHold]:
        """
        Process automatic releases for expired escrow holds
        Returns list of released escrow holds
        """
        if not self.auto_release_enabled:
            return []
        
        now = datetime.utcnow()
        expired_escrows = [
            e for e in self._escrow_holds.values()
            if e.status == EscrowStatus.HELD
            and e.release_deadline <= now
            and e.status != EscrowStatus.FROZEN
        ]
        
        released = []
        for escrow in expired_escrows:
            try:
                released_escrow = await self.release_escrow(
                    escrow.escrow_id,
                    reason="Automatic release after deadline"
                )
                released.append(released_escrow)
            except Exception:
                # Log error but continue with other escrows
                pass
        
        return released
    
    def get_escrow(self, escrow_id: str) -> Optional[EscrowHold]:
        """Get escrow hold by ID"""
        return self._escrow_holds.get(escrow_id)
    
    def get_escrow_by_order(self, order_id: str) -> Optional[EscrowHold]:
        """Get escrow hold by order ID"""
        for escrow in self._escrow_holds.values():
            if escrow.order_id == order_id:
                return escrow
        return None
    
    def get_escrows_by_status(self, status: EscrowStatus) -> List[EscrowHold]:
        """Get escrow holds by status"""
        return [e for e in self._escrow_holds.values() if e.status == status]
    
    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get dispute by ID"""
        return self._disputes.get(dispute_id)
    
    def get_disputes_by_status(self, status: DisputeStatus) -> List[Dispute]:
        """Get disputes by status"""
        return [d for d in self._disputes.values() if d.status == status]
    
    def get_escrow_stats(self) -> Dict[str, Any]:
        """Get escrow statistics"""
        total = len(self._escrow_holds)
        if total == 0:
            return {"total": 0, "held": 0, "released": 0, "frozen": 0, "total_amount": 0}
        
        held = len(self.get_escrows_by_status(EscrowStatus.HELD))
        released = len(self.get_escrows_by_status(EscrowStatus.RELEASED))
        partially_released = len(self.get_escrows_by_status(EscrowStatus.PARTIALLY_RELEASED))
        frozen = len(self.get_escrows_by_status(EscrowStatus.FROZEN))
        refunded = len(self.get_escrows_by_status(EscrowStatus.REFUNDED))
        
        total_amount = sum(e.amount for e in self._escrow_holds.values())
        held_amount = sum(e.amount for e in self.get_escrows_by_status(EscrowStatus.HELD))
        released_amount = sum(e.released_amount for e in self._escrow_holds.values())
        
        return {
            "total": total,
            "held": held,
            "released": released,
            "partially_released": partially_released,
            "frozen": frozen,
            "refunded": refunded,
            "total_amount": total_amount,
            "held_amount": held_amount,
            "released_amount": released_amount
        }
    
    def get_dispute_stats(self) -> Dict[str, Any]:
        """Get dispute statistics"""
        total = len(self._disputes)
        if total == 0:
            return {"total": 0, "open": 0, "resolved": 0, "under_review": 0}
        
        open_count = len(self.get_disputes_by_status(DisputeStatus.OPEN))
        under_review = len(self.get_disputes_by_status(DisputeStatus.UNDER_REVIEW))
        resolved = len(self.get_disputes_by_status(DisputeStatus.RESOLVED))
        escalated = len(self.get_disputes_by_status(DisputeStatus.ESCALATED))
        
        return {
            "total": total,
            "open": open_count,
            "under_review": under_review,
            "resolved": resolved,
            "escalated": escalated,
            "resolution_rate": (resolved / total) * 100
        }
    
    def clear_escrows(self) -> None:
        """Clear all escrow holds"""
        self._escrow_holds.clear()
    
    def clear_disputes(self) -> None:
        """Clear all disputes"""
        self._disputes.clear()


# Global escrow simulator instance
escrow_simulator = EscrowSimulator()
