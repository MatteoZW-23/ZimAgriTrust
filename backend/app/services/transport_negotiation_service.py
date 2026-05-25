"""
ZimAgritrust Transport Negotiation Service
Manages transport fee negotiations between buyers and farmers.
Supports real-time chat, structured offers, split payments, and agreement tracking.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.transport import (
    TransportNegotiation,
    NegotiationMessage,
    NegotiationStatus as DBNegotiationStatus,
    MessageType as DBMessageType,
    PaymentAllocation,
    AllocationType,
    AllocationStatus,
)
from app.models.transaction import Order
from app.models.user import User, UserRole
from app.services.notification_service import notification_service

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
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.NEGOTIATION_TIMEOUT_HOURS)
        
        # Insert into transport_negotiations table
        negotiation = TransportNegotiation(
            order_id=order_id,
            initiator_id=initiator_id,
            counterparty_id=counterparty_id,
            status=DBNegotiationStatus.INITIATED,
            expires_at=expires_at,
        )
        self.db.add(negotiation)
        self.db.flush()
        
        # Create initial system message with quote
        system_message = NegotiationMessage(
            negotiation_id=negotiation.id,
            sender_id=initiator_id,
            message_type=DBMessageType.SYSTEM,
            content=f"Negotiation started. Initial quote: ${initial_quote.get('amount', 0):.2f}",
            structured_offer=initial_quote,
        )
        self.db.add(system_message)
        
        self.db.commit()
        
        # Send notifications to both parties
        notification_service.send_notification(
            db=self.db,
            user_id=counterparty_id,
            notification_type="negotiation_started",
            title="Transport Fee Negotiation Started",
            body="A transport fee negotiation has been initiated.",
            data={"negotiation_id": str(negotiation.id)},
        )
        
        # Schedule expiry check (would use Celery in production)
        
        return {
            "id": str(negotiation.id),
            "order_id": str(order_id),
            "initiator_id": str(initiator_id),
            "counterparty_id": str(counterparty_id),
            "status": negotiation.status.value,
            "initiated_at": negotiation.initiated_at.isoformat(),
            "expires_at": negotiation.expires_at.isoformat(),
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
        
        # Validate negotiation exists and is active
        negotiation = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.id == negotiation_id
        ).first()
        
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        if negotiation.status not in [DBNegotiationStatus.INITIATED, DBNegotiationStatus.COUNTER_OFFER]:
            raise HTTPException(status_code=400, detail="Negotiation is not active")
        
        if negotiation.expires_at < datetime.now(timezone.utc):
            negotiation.status = DBNegotiationStatus.EXPIRED
            self.db.commit()
            raise HTTPException(status_code=400, detail="Negotiation has expired")
        
        # Validate sender is participant
        if sender_id not in [negotiation.initiator_id, negotiation.counterparty_id]:
            raise HTTPException(status_code=403, detail="Sender is not a participant in this negotiation")
        
        # Insert into negotiation_messages table
        message = NegotiationMessage(
            negotiation_id=negotiation.id,
            sender_id=sender_id,
            message_type=DBMessageType(message_type.value),
            content=content,
            structured_offer=structured_offer,
        )
        self.db.add(message)
        
        # Update negotiation status if offer/acceptance/rejection
        if message_type in [MessageType.OFFER, MessageType.COUNTER_OFFER]:
            negotiation.status = DBNegotiationStatus.COUNTER_OFFER
        elif message_type == MessageType.ACCEPTANCE:
            negotiation.status = DBNegotiationStatus.ACCEPTED
        elif message_type == MessageType.REJECTION:
            negotiation.status = DBNegotiationStatus.COUNTER_OFFER
        
        negotiation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # Notify counterparty via WebSocket
        counterparty_id = negotiation.counterparty_id if sender_id == negotiation.initiator_id else negotiation.initiator_id
        notification_service.send_notification(
            db=self.db,
            user_id=counterparty_id,
            notification_type="negotiation_message",
            title=f"New {message_type.value} in Negotiation",
            body=content,
            data={"negotiation_id": str(negotiation.id)},
        )
        
        # Check for agreement (both accepted same terms)
        if message_type == MessageType.ACCEPTANCE:
            # Check if both parties have accepted (simplified logic)
            acceptance_count = self.db.query(NegotiationMessage).filter(
                NegotiationMessage.negotiation_id == negotiation_id,
                NegotiationMessage.message_type == DBMessageType.ACCEPTANCE
            ).count()
            
            if acceptance_count >= 2:
                negotiation.status = DBNegotiationStatus.ACCEPTED
                negotiation.completed_at = datetime.now(timezone.utc)
                self.db.commit()
        
        return {
            "id": str(message.id),
            "negotiation_id": str(negotiation_id),
            "sender_id": str(sender_id),
            "message_type": message_type.value,
            "content": content,
            "structured_offer": structured_offer,
            "created_at": message.created_at.isoformat(),
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
        
        # Validate negotiation exists and is active
        negotiation = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.id == negotiation_id
        ).first()
        
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        if negotiation.status not in [DBNegotiationStatus.INITIATED, DBNegotiationStatus.COUNTER_OFFER]:
            raise HTTPException(status_code=400, detail="Negotiation is not active")
        
        # Get latest offer
        latest_offer = self.db.query(NegotiationMessage).filter(
            NegotiationMessage.negotiation_id == negotiation_id,
            NegotiationMessage.message_type.in_([DBMessageType.OFFER, DBMessageType.COUNTER_OFFER])
        ).order_by(NegotiationMessage.created_at.desc()).first()
        
        # Create acceptance message
        acceptance_message = NegotiationMessage(
            negotiation_id=negotiation.id,
            sender_id=sender_id,
            message_type=DBMessageType.ACCEPTANCE,
            content="Offer accepted",
        )
        self.db.add(acceptance_message)
        
        # Check if both parties have accepted
        acceptance_count = self.db.query(NegotiationMessage).filter(
            NegotiationMessage.negotiation_id == negotiation_id,
            NegotiationMessage.message_type == DBMessageType.ACCEPTANCE
        ).count()
        
        # If both accepted, resolve negotiation
        if acceptance_count >= 2:
            negotiation.status = DBNegotiationStatus.ACCEPTED
            negotiation.completed_at = datetime.now(timezone.utc)
            
            if latest_offer and latest_offer.structured_offer:
                negotiation.final_payer = latest_offer.structured_offer.get("payer")
                negotiation.final_amount = latest_offer.structured_offer.get("amount")
                negotiation.split_ratio = latest_offer.structured_offer.get("split_ratio")
                
                # Create payment allocations
                if negotiation.final_amount:
                    payment_allocation = PaymentAllocation(
                        order_id=negotiation.order_id,
                        allocation_type=AllocationType.TRANSPORT_FEE,
                        payer=negotiation.final_payer or "BUYER",
                        payee="PLATFORM",
                        amount=negotiation.final_amount,
                        status=AllocationStatus.PENDING,
                    )
                    self.db.add(payment_allocation)
            
            # Trigger driver assignment (simplified - would use driver matching service)
            # Send notifications
            notification_service.send_notification(
                db=self.db,
                user_id=negotiation.counterparty_id if sender_id == negotiation.initiator_id else negotiation.initiator_id,
                notification_type="negotiation_accepted",
                title="Transport Negotiation Accepted",
                body="Both parties have accepted the transport fee offer.",
                data={"negotiation_id": str(negotiation.id)},
            )
        
        self.db.commit()
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.ACCEPTED.value,
            "accepted_at": datetime.now(timezone.utc).isoformat(),
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
        
        # Validate negotiation exists and is active
        negotiation = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.id == negotiation_id
        ).first()
        
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        if negotiation.status not in [DBNegotiationStatus.INITIATED, DBNegotiationStatus.COUNTER_OFFER]:
            raise HTTPException(status_code=400, detail="Negotiation is not active")
        
        # Send rejection message
        rejection_message = NegotiationMessage(
            negotiation_id=negotiation.id,
            sender_id=sender_id,
            message_type=DBMessageType.REJECTION,
            content=reason or "Offer rejected",
        )
        self.db.add(rejection_message)
        
        # Update negotiation status
        negotiation.status = DBNegotiationStatus.COUNTER_OFFER
        negotiation.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Notify counterparty
        counterparty_id = negotiation.counterparty_id if sender_id == negotiation.initiator_id else negotiation.initiator_id
        notification_service.send_notification(
            db=self.db,
            user_id=counterparty_id,
            notification_type="negotiation_rejected",
            title="Offer Rejected in Negotiation",
            body=reason or "Your offer has been rejected.",
            data={"negotiation_id": str(negotiation.id)},
        )
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.COUNTER_OFFER.value,
            "rejected_at": datetime.now(timezone.utc).isoformat(),
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
        
        # Validate negotiation exists
        negotiation = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.id == negotiation_id
        ).first()
        
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        # Validate sender is participant
        if sender_id not in [negotiation.initiator_id, negotiation.counterparty_id]:
            raise HTTPException(status_code=403, detail="Sender is not a participant in this negotiation")
        
        # Update negotiation status to CANCELLED
        negotiation.status = DBNegotiationStatus.CANCELLED
        negotiation.updated_at = datetime.now(timezone.utc)
        
        # Send system message
        system_message = NegotiationMessage(
            negotiation_id=negotiation.id,
            sender_id=sender_id,
            message_type=DBMessageType.SYSTEM,
            content=reason or "Negotiation cancelled by participant",
        )
        self.db.add(system_message)
        
        self.db.commit()
        
        # Notify both parties
        notification_service.send_notification(
            db=self.db,
            user_id=negotiation.counterparty_id if sender_id == negotiation.initiator_id else negotiation.initiator_id,
            notification_type="negotiation_cancelled",
            title="Transport Negotiation Cancelled",
            body=reason or "The negotiation has been cancelled.",
            data={"negotiation_id": str(negotiation.id)},
        )
        
        # Trigger deferred decision flow (would update transport request to DEFERRED mode)
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.CANCELLED.value,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        }
    
    def get_negotiation(
        self,
        negotiation_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get negotiation details and message history.
        """
        # Query transport_negotiations table
        negotiation = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.id == negotiation_id
        ).first()
        
        if not negotiation:
            return None
        
        # Query negotiation_messages table
        messages = self.db.query(NegotiationMessage).filter(
            NegotiationMessage.negotiation_id == negotiation_id
        ).order_by(NegotiationMessage.created_at).all()
        
        # Return negotiation state and messages
        return {
            "id": str(negotiation.id),
            "order_id": str(negotiation.order_id),
            "initiator_id": str(negotiation.initiator_id),
            "counterparty_id": str(negotiation.counterparty_id),
            "status": negotiation.status.value,
            "initiated_at": negotiation.initiated_at.isoformat(),
            "expires_at": negotiation.expires_at.isoformat(),
            "completed_at": negotiation.completed_at.isoformat() if negotiation.completed_at else None,
            "final_payer": negotiation.final_payer,
            "final_amount": float(negotiation.final_amount) if negotiation.final_amount else None,
            "split_ratio": negotiation.split_ratio,
            "messages": [
                {
                    "id": str(msg.id),
                    "sender_id": str(msg.sender_id),
                    "message_type": msg.message_type.value,
                    "content": msg.content,
                    "structured_offer": msg.structured_offer,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
        }
    
    def get_user_negotiations(
        self,
        user_id: uuid.UUID,
        status: Optional[NegotiationStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all negotiations for a user.
        """
        # Query transport_negotiations table
        query = self.db.query(TransportNegotiation).filter(
            (TransportNegotiation.initiator_id == user_id) |
            (TransportNegotiation.counterparty_id == user_id)
        )
        
        # Filter by status if provided
        if status:
            query = query.filter(TransportNegotiation.status == DBNegotiationStatus(status.value))
        
        negotiations = query.order_by(TransportNegotiation.created_at.desc()).all()
        
        # Return negotiations
        return [
            {
                "id": str(neg.id),
                "order_id": str(neg.order_id),
                "initiator_id": str(neg.initiator_id),
                "counterparty_id": str(neg.counterparty_id),
                "status": neg.status.value,
                "initiated_at": neg.initiated_at.isoformat(),
                "expires_at": neg.expires_at.isoformat(),
            }
            for neg in negotiations
        ]
    
    def check_expired_negotiations(self) -> int:
        """
        Check for expired negotiations and handle them.
        
        This is typically run as a scheduled job.
        """
        logger.info("Checking for expired negotiations")
        
        expired_count = 0
        
        # Query negotiations where expires_at < NOW and status = INITIATED/COUNTER_OFFER
        expired_negotiations = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.expires_at < datetime.now(timezone.utc),
            TransportNegotiation.status.in_([DBNegotiationStatus.INITIATED, DBNegotiationStatus.COUNTER_OFFER])
        ).all()
        
        # Update status to EXPIRED
        for negotiation in expired_negotiations:
            negotiation.status = DBNegotiationStatus.EXPIRED
            negotiation.updated_at = datetime.now(timezone.utc)
            expired_count += 1
            
            # Escalate to admin
            negotiation.escalated_to_admin = True
            negotiation.escalated_at = datetime.now(timezone.utc)
            
            # Send notifications
            notification_service.send_notification(
                db=self.db,
                user_id=negotiation.initiator_id,
                notification_type="negotiation_expired",
                title="Transport Negotiation Expired",
                body="Your transport fee negotiation has expired.",
                data={"negotiation_id": str(negotiation.id)},
            )
            notification_service.send_notification(
                db=self.db,
                user_id=negotiation.counterparty_id,
                notification_type="negotiation_expired",
                title="Transport Negotiation Expired",
                body="The transport fee negotiation has expired.",
                data={"negotiation_id": str(negotiation.id)},
            )
            
            # Trigger deferred decision flow (would update transport request)
        
        self.db.commit()
        
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
        
        # Update negotiation status to ADMIN_REVIEW
        negotiation = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.id == negotiation_id
        ).first()
        
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        negotiation.status = DBNegotiationStatus.ADMIN_REVIEW
        negotiation.escalated_to_admin = True
        negotiation.escalated_at = datetime.now(timezone.utc)
        negotiation.escalated_by = escalated_by
        negotiation.updated_at = datetime.now(timezone.utc)
        
        # Send system message
        system_message = NegotiationMessage(
            negotiation_id=negotiation.id,
            sender_id=escalated_by,
            message_type=DBMessageType.SYSTEM,
            content=f"Escalated to admin: {reason}",
        )
        self.db.add(system_message)
        
        self.db.commit()
        
        # Notify admin
        admin_users = self.db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])).all()
        for admin in admin_users:
            notification_service.send_notification(
                db=self.db,
                user_id=admin.id,
                notification_type="negotiation_escalated",
                title="Negotiation Escalated to Admin",
                body=f"A transport negotiation has been escalated: {reason}",
                data={"negotiation_id": str(negotiation.id)},
            )
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.ADMIN_REVIEW.value,
            "escalated_at": datetime.now(timezone.utc).isoformat(),
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
        
        # Validate admin has permission
        admin = self.db.query(User).filter(User.id == admin_id).first()
        if not admin or admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        negotiation = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.id == negotiation_id
        ).first()
        
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        # Update negotiation status to RESOLVED
        negotiation.status = DBNegotiationStatus.RESOLVED
        negotiation.completed_at = datetime.now(timezone.utc)
        negotiation.admin_resolution = resolution.get("notes", "")
        negotiation.updated_at = datetime.now(timezone.utc)
        
        # Apply resolution (payer, amount, split)
        negotiation.final_payer = resolution.get("payer")
        negotiation.final_amount = resolution.get("amount")
        negotiation.split_ratio = resolution.get("split_ratio")
        
        # Create payment allocations
        if negotiation.final_amount:
            payment_allocation = PaymentAllocation(
                order_id=negotiation.order_id,
                allocation_type=AllocationType.TRANSPORT_FEE,
                payer=negotiation.final_payer or "BUYER",
                payee="PLATFORM",
                amount=negotiation.final_amount,
                status=AllocationStatus.PENDING,
            )
            self.db.add(payment_allocation)
        
        self.db.commit()
        
        # Trigger driver assignment (simplified)
        # Send notifications to all parties
        notification_service.send_notification(
            db=self.db,
            user_id=negotiation.initiator_id,
            notification_type="negotiation_resolved",
            title="Negotiation Resolved by Admin",
            body=f"The negotiation has been resolved: {resolution.get('notes', '')}",
            data={"negotiation_id": str(negotiation.id)},
        )
        notification_service.send_notification(
            db=self.db,
            user_id=negotiation.counterparty_id,
            notification_type="negotiation_resolved",
            title="Negotiation Resolved by Admin",
            body=f"The negotiation has been resolved: {resolution.get('notes', '')}",
            data={"negotiation_id": str(negotiation.id)},
        )
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": NegotiationStatus.RESOLVED.value,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolution": resolution,
        }
    
    def get_negotiation_summary(
        self,
        negotiation_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Get a summary of the negotiation state.
        """
        # Query negotiation
        negotiation = self.db.query(TransportNegotiation).filter(
            TransportNegotiation.id == negotiation_id
        ).first()
        
        if not negotiation:
            return {
                "negotiation_id": str(negotiation_id),
                "status": "NOT_FOUND",
                "message_count": 0,
                "latest_offer": None,
                "time_remaining_hours": 0,
            }
        
        # Get latest offer
        latest_offer = self.db.query(NegotiationMessage).filter(
            NegotiationMessage.negotiation_id == negotiation_id,
            NegotiationMessage.message_type.in_([DBMessageType.OFFER, DBMessageType.COUNTER_OFFER])
        ).order_by(NegotiationMessage.created_at.desc()).first()
        
        # Count messages
        message_count = self.db.query(NegotiationMessage).filter(
            NegotiationMessage.negotiation_id == negotiation_id
        ).count()
        
        # Calculate time remaining
        time_remaining = calculate_time_remaining(negotiation.expires_at)
        
        # Return summary
        return {
            "negotiation_id": str(negotiation.id),
            "status": negotiation.status.value,
            "message_count": message_count,
            "latest_offer": latest_offer.structured_offer if latest_offer else None,
            "time_remaining_hours": time_remaining["remaining_hours"],
            "time_remaining_minutes": time_remaining["remaining_minutes"],
            "expired": time_remaining["expired"],
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
    now = datetime.now(timezone.utc)
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
