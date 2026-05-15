"""
ZimAgritrust Transport Negotiation Service
Manages transport fee negotiations between buyers and farmers.
Supports real-time chat, structured offers, split payments, and agreement tracking.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Negotiation Status Enum ─────────────────────────────────────────────────

class NegotiationStatus(str, Enum):
    INITIATED = "INITIATED"
    COUNTER_OFFER = "COUNTER_OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ADMIN_REVIEW = "ADMIN_REVIEW"
    RESOLVED = "RESOLVED"


class MessageType(str, Enum):
    TEXT = "TEXT"
    OFFER = "OFFER"
    COUNTER_OFFER = "COUNTER_OFFER"
    ACCEPTANCE = "ACCEPTANCE"
    REJECTION = "REJECTION"
    SYSTEM = "SYSTEM"


# ── Negotiation Data ───────────────────────────────────────────────────────

@dataclass
class NegotiationMessage:
    """Negotiation message data"""
    negotiation_id: uuid.UUID
    sender_id: uuid.UUID
    message_type: MessageType
    content: str
    structured_offer: Optional[Dict[str, Any]] = None


@dataclass
class NegotiationOffer:
    """Negotiation offer data"""
    payer: str  # 'BUYER', 'FARMER', or 'SPLIT'
    amount: float
    split_ratio: Optional[Dict[str, float]] = None  # For split: {"buyer": 0.6, "farmer": 0.4}


# ── Transport Negotiation Service ───────────────────────────────────────────

class TransportNegotiationService:
    """Manages transport fee negotiations"""
    
    NEGOTIATION_TIMEOUT_HOURS = 72
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_negotiation(
        self,
        order_id: uuid.UUID,
        initiator_id: uuid.UUID,
        counterparty_id: uuid.UUID,
        initial_quote: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Start a new transport fee negotiation.
        
        Creates negotiation record with 72-hour expiry.
        """
        logger.info(
            f"Starting negotiation for order {order_id}: "
            f"initiator={initiator_id}, counterparty={counterparty_id}"
        )
        
        negotiation_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=self.NEGOTIATION_TIMEOUT_HOURS)
        
        # TODO: Insert into transport_negotiations table
        # TODO: Create initial system message with quote
        # TODO: Send notifications to both parties
        # TODO: Schedule expiry check
        
        return {
            "id": str(negotiation_id),
            "order_id": str(order_id),
            "initiator_id": str(initiator_id),
            "counterparty_id": str(counterparty_id),
            "status": NegotiationStatus.INITIATED.value,
            "initiated_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "initial_quote": initial_quote,
        }
    
    def send_message(
        self,
        negotiation_id: uuid.UUID,
        sender_id: uuid.UUID,
        message_type: MessageType,
        content: str,
        structured_offer: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a message in the negotiation.
        
        Can be text, offer, counter-offer, acceptance, or rejection.
        """
        logger.info(
            f"Sending message in negotiation {negotiation_id}: "
            f"type={message_type.value}, sender={sender_id}"
        )
        
        # TODO: Validate negotiation exists and is active
        # TODO: Validate sender is participant
        # TODO: Insert into negotiation_messages table
        # TODO: Update negotiation status if offer/acceptance/rejection
        # TODO: Notify counterparty via WebSocket
        # TODO: Check for agreement (both accepted same terms)
        
        message_id = uuid.uuid4()
        
        return {
            "id": str(message_id),
            "negotiation_id": str(negotiation_id),
            "sender_id": str(sender_id),
            "message_type": message_type.value,
            "content": content,
            "structured_offer": structured_offer,
            "created_at": datetime.utcnow().isoformat(),
        }
    
    def submit_offer(
        self,
        negotiation_id: uuid.UUID,
        sender_id: uuid.UUID,
        offer: NegotiationOffer,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a structured offer in the negotiation.
        """
        logger.info(
            f"Submitting offer in negotiation {negotiation_id}: "
            f"payer={offer.payer}, amount={offer.amount}"
        )
        
        # Validate offer
        if offer.payer not in ["BUYER", "FARMER", "SPLIT"]:
            raise HTTPException(status_code=400, detail="Invalid payer. Must be BUYER, FARMER, or SPLIT")
        
        if offer.payer == "SPLIT" and not offer.split_ratio:
            raise HTTPException(status_code=400, detail="Split ratio required for split payment")
        
        if offer.payer == "SPLIT" and offer.split_ratio:
            total = sum(offer.split_ratio.values())
            if abs(total - 1.0) > 0.01:
                raise HTTPException(status_code=400, detail="Split ratio must sum to 1.0")
        
        structured_offer = {
            "payer": offer.payer,
            "amount": offer.amount,
            "split_ratio": offer.split_ratio,
        }
        
        # Send as counter-offer message
        return self.send_message(
            negotiation_id=negotiation_id,
            sender_id=sender_id,
            message_type=MessageType.COUNTER_OFFER,
            content=message or f"Offer: ${offer.amount:.2f} paid by {offer.payer}",
            structured_offer=structured_offer,
        )
    
    def accept_offer(
        self,
        negotiation_id: uuid.UUID,
        sender_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Accept the current offer in the negotiation.
        
        If both parties have accepted the same terms, the negotiation is resolved.
        """
        logger.info(f"Accepting offer in negotiation {negotiation_id} by {sender_id}")
        
        # TODO: Validate negotiation exists and is active
        # TODO: Get latest offer
        # TODO: Check if both parties have accepted
        # TODO: If both accepted, resolve negotiation
        # TODO: Create payment allocations
        # TODO: Trigger driver assignment
        # TODO: Send notifications
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.ACCEPTED.value,
            "accepted_at": datetime.utcnow().isoformat(),
        }
    
    def reject_offer(
        self,
        negotiation_id: uuid.UUID,
        sender_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reject the current offer in the negotiation.
        
        Negotiation continues with counter-party able to submit new offer.
        """
        logger.info(f"Rejecting offer in negotiation {negotiation_id} by {sender_id}")
        
        # TODO: Validate negotiation exists and is active
        # TODO: Send rejection message
        # TODO: Update negotiation status
        # TODO: Notify counterparty
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.COUNTER_OFFER.value,
            "rejected_at": datetime.utcnow().isoformat(),
            "reason": reason,
        }
    
    def cancel_negotiation(
        self,
        negotiation_id: uuid.UUID,
        sender_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel the negotiation entirely.
        
        Transport decision is deferred to counterparty.
        """
        logger.info(f"Cancelling negotiation {negotiation_id} by {sender_id}")
        
        # TODO: Validate negotiation exists
        # TODO: Validate sender is participant
        # TODO: Update negotiation status to CANCELLED
        # TODO: Send system message
        # TODO: Notify both parties
        # TODO: Trigger deferred decision flow
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.CANCELLED.value,
            "cancelled_at": datetime.utcnow().isoformat(),
            "reason": reason,
        }
    
    def get_negotiation(
        self,
        negotiation_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get negotiation details and message history.
        """
        # TODO: Query transport_negotiations table
        # TODO: Query negotiation_messages table
        # TODO: Return negotiation state and messages
        
        return None
    
    def get_user_negotiations(
        self,
        user_id: uuid.UUID,
        status: Optional[NegotiationStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all negotiations for a user.
        """
        # TODO: Query transport_negotiations table
        # TODO: Filter where user_id is initiator or counterparty
        # TODO: Filter by status if provided
        # TODO: Return negotiations
        
        return []
    
    def check_expired_negotiations(self) -> int:
        """
        Check for expired negotiations and handle them.
        
        This is typically run as a scheduled job.
        """
        logger.info("Checking for expired negotiations")
        
        expired_count = 0
        
        # TODO: Query negotiations where expires_at < NOW and status = INITIATED/COUNTER_OFFER
        # TODO: Update status to EXPIRED
        # TODO: Escalate to admin
        # TODO: Send notifications
        # TODO: Trigger deferred decision flow
        
        return expired_count
    
    def escalate_to_admin(
        self,
        negotiation_id: uuid.UUID,
        escalated_by: uuid.UUID,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Escalate negotiation to admin for resolution.
        """
        logger.info(f"Escalating negotiation {negotiation_id} to admin")
        
        # TODO: Update negotiation status to ADMIN_REVIEW
        # TODO: Set escalated flags
        # TODO: Notify admin
        # TODO: Send system message
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.ADMIN_REVIEW.value,
            "escalated_at": datetime.utcnow().isoformat(),
        }
    
    def resolve_negotiation(
        self,
        negotiation_id: uuid.UUID,
        admin_id: uuid.UUID,
        resolution: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Admin resolves a stalled negotiation.
        """
        logger.info(f"Admin resolving negotiation {negotiation_id}")
        
        # TODO: Validate admin has permission
        # TODO: Update negotiation status to RESOLVED
        # TODO: Apply resolution (payer, amount, split)
        # TODO: Create payment allocations
        # TODO: Trigger driver assignment
        # TODO: Send notifications to all parties
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.RESOLVED.value,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution": resolution,
        }
    
    def get_negotiation_summary(
        self,
        negotiation_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Get a summary of the negotiation state.
        """
        # TODO: Query negotiation
        # TODO: Get latest offer
        # TODO: Count messages
        # TODO: Calculate time remaining
        # TODO: Return summary
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": "INITIATED",
            "message_count": 0,
            "latest_offer": None,
            "time_remaining_hours": 72,
        }


# ── Helper Functions ─────────────────────────────────────────────────────────

def validate_split_ratio(split_ratio: Dict[str, float]) -> bool:
    """Validate split ratio sums to 1.0"""
    if not split_ratio:
        return False
    
    total = sum(split_ratio.values())
    return abs(total - 1.0) < 0.01


def calculate_time_remaining(expires_at: datetime) -> Dict[str, Any]:
    """Calculate time remaining until expiry"""
    now = datetime.utcnow()
    remaining = expires_at - now
    
    if remaining.total_seconds() <= 0:
        return {
            "remaining_hours": 0,
            "remaining_minutes": 0,
            "expired": True,
        }
    
    return {
        "remaining_hours": int(remaining.total_seconds() // 3600),
        "remaining_minutes": int((remaining.total_seconds() % 3600) // 60),
        "expired": False,
    }
