"""
ZimAgritrust Transport Dispute Service
Handles transport-related disputes including delivery issues, payment disputes, and driver conflicts.
Integrates with the existing dispute system for transport-specific workflows.
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

from app.models.transport import (
    TransportDispute,
    TransportDisputeEvidence,
    DisputeStatus as DBDisputeStatus,
    PaymentAllocation,
    AllocationStatus,
)
from app.models.transaction import Order
from app.models.user import User, UserRole
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


# ── Dispute Status Enum ─────────────────────────────────────────────────────

class DisputeStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


class DisputePriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class DisputeType(str, Enum):
    DELIVERY_DELAY = "DELIVERY_DELAY"
    DAMAGED_GOODS = "DAMAGED_GOODS"
    WRONG_GOODS = "WRONG_GOODS"
    PAYMENT_DISPUTE = "PAYMENT_DISPUTE"
    DRIVER_MISCONDUCT = "DRIVER_MISCONDUCT"
    TRANSPORT_FEE_DISPUTE = "TRANSPORT_FEE_DISPUTE"
    PICKUP_ISSUE = "PICKUP_ISSUE"
    DELIVERY_LOCATION_ISSUE = "DELIVERY_LOCATION_ISSUE"


# ── Dispute Data ───────────────────────────────────────────────────────────

@dataclass
class TransportDispute:
    """Transport dispute data"""
    order_id: uuid.UUID
    transport_request_id: Optional[uuid.UUID]
    delivery_id: Optional[uuid.UUID]
    raised_by: uuid.UUID
    dispute_type: DisputeType
    category: str
    subcategory: Optional[str]
    title: str
    description: str
    disputed_amount: Optional[float]
    currency: str = "USD"
    priority: DisputePriority = DisputePriority.NORMAL


# ── Transport Dispute Service ───────────────────────────────────────────────

class TransportDisputeService:
    """Manages transport-related disputes"""
    
    RESPONSE_DEADLINE_HOURS = 48
    RESOLUTION_DEADLINE_DAYS = 7
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_dispute(
        self,
        dispute: TransportDispute,
    ) -> Dict[str, Any]:
        """
        Create a new transport dispute.
        
        Holds relevant payments in escrow until resolution.
        """
        logger.info(
            f"Creating transport dispute: order={dispute.order_id}, "
            f"type={dispute.dispute_type.value}, amount={dispute.disputed_amount}"
        )
        
        # Insert into disputes table
        priority = self.calculate_dispute_priority(dispute.dispute_type, dispute.disputed_amount)
        
        new_dispute = TransportDispute(
            order_id=dispute.order_id,
            transport_request_id=dispute.transport_request_id,
            delivery_id=dispute.delivery_id,
            raised_by=dispute.raised_by,
            dispute_type=dispute.dispute_type.value,
            category=dispute.category,
            subcategory=dispute.subcategory,
            title=dispute.title,
            description=dispute.description,
            disputed_amount=dispute.disputed_amount,
            currency=dispute.currency,
            status=DBDisputeStatus.OPEN,
            priority=priority.value,
            response_due_at=datetime.utcnow() + timedelta(hours=self.RESPONSE_DEADLINE_HOURS),
            resolution_due_at=datetime.utcnow() + timedelta(days=self.RESOLUTION_DEADLINE_DAYS),
        )
        self.db.add(new_dispute)
        self.db.flush()
        
        # Hold relevant payments in escrow
        payment_allocations = self.db.query(PaymentAllocation).filter(
            PaymentAllocation.order_id == dispute.order_id,
            PaymentAllocation.status == AllocationStatus.PENDING
        ).all()
        
        for allocation in payment_allocations:
            allocation.status = AllocationStatus.HELD
            allocation.held_at = datetime.utcnow()
        
        self.db.commit()
        
        # Notify admin
        admin_users = self.db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])).all()
        for admin in admin_users:
            notification_service.send_notification(
                db=self.db,
                user_id=admin.id,
                notification_type="dispute_raised",
                title="New Transport Dispute",
                body=f"A transport dispute has been raised: {dispute.title}",
                data={"dispute_id": str(new_dispute.id)},
            )
        
        # Notify counterparty
        order = self.db.query(Order).filter(Order.id == dispute.order_id).first()
        if order:
            counterparty_id = order.buyer_id if dispute.raised_by == order.seller_id else order.seller_id
            notification_service.send_notification(
                db=self.db,
                user_id=counterparty_id,
                notification_type="dispute_raised",
                title="Transport Dispute Raised",
                body="A dispute has been raised regarding your order.",
                data={"dispute_id": str(new_dispute.id)},
            )
        
        return {
            "id": str(new_dispute.id),
            "order_id": str(dispute.order_id),
            "dispute_type": dispute.dispute_type.value,
            "status": new_dispute.status.value,
            "priority": new_dispute.priority.value,
            "created_at": new_dispute.created_at.isoformat(),
            "response_due_at": new_dispute.response_due_at.isoformat(),
            "resolution_due_at": new_dispute.resolution_due_at.isoformat(),
        }
    
    def add_evidence(
        self,
        dispute_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        evidence_type: str,
        file_url: str,
        file_name: str,
        file_size_bytes: int,
        file_mime_type: Optional[str],
        description: Optional[str],
    ) -> Dict[str, Any]:
        """
        Add evidence to a dispute.
        
        Evidence types: PHOTO, VIDEO, DOCUMENT, AUDIO, SCREENSHOT
        """
        logger.info(f"Adding evidence to dispute {dispute_id}: {evidence_type}")
        
        # Validate dispute exists
        dispute = self.db.query(TransportDispute).filter(
            TransportDispute.id == dispute_id
        ).first()
        
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        # Insert into dispute_evidence table
        evidence = TransportDisputeEvidence(
            dispute_id=dispute_id,
            uploaded_by=uploaded_by,
            evidence_type=evidence_type,
            file_url=file_url,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            file_mime_type=file_mime_type,
            description=description,
        )
        self.db.add(evidence)
        self.db.commit()
        
        # Notify admin of new evidence
        admin_users = self.db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])).all()
        for admin in admin_users:
            notification_service.send_notification(
                db=self.db,
                user_id=admin.id,
                notification_type="dispute_evidence_added",
                title="New Evidence Added to Dispute",
                body=f"New evidence has been added to dispute: {evidence_type}",
                data={"dispute_id": str(dispute_id)},
            )
        
        return {
            "id": str(evidence.id),
            "dispute_id": str(dispute_id),
            "evidence_type": evidence_type,
            "file_url": file_url,
            "created_at": evidence.created_at.isoformat(),
        }
    
    def escalate_dispute(
        self,
        dispute_id: uuid.UUID,
        escalated_by: uuid.UUID,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Escalate a dispute to higher priority or admin review.
        """
        logger.info(f"Escalating dispute {dispute_id} by {escalated_by}")
        
        # Validate dispute exists
        dispute = self.db.query(TransportDispute).filter(
            TransportDispute.id == dispute_id
        ).first()
        
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        # Update status to ESCALATED
        dispute.status = DBDisputeStatus.ESCALATED
        dispute.escalated_to_admin = True
        dispute.escalated_at = datetime.utcnow()
        dispute.escalation_level = dispute.escalation_level + 1
        dispute.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Notify admin
        admin_users = self.db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])).all()
        for admin in admin_users:
            notification_service.send_notification(
                db=self.db,
                user_id=admin.id,
                notification_type="dispute_escalated",
                title="Dispute Escalated",
                body=f"A dispute has been escalated: {reason}",
                data={"dispute_id": str(dispute_id)},
            )
        
        # Notify both parties
        order = self.db.query(Order).filter(Order.id == dispute.order_id).first()
        if order:
            notification_service.send_notification(
                db=self.db,
                user_id=order.buyer_id,
                notification_type="dispute_escalated",
                title="Dispute Escalated",
                body="Your dispute has been escalated to admin review.",
                data={"dispute_id": str(dispute_id)},
            )
            notification_service.send_notification(
                db=self.db,
                user_id=order.seller_id,
                notification_type="dispute_escalated",
                title="Dispute Escalated",
                body="A dispute has been escalated to admin review.",
                data={"dispute_id": str(dispute_id)},
            )
        
        return {
            "id": str(dispute_id),
            "status": dispute.status.value,
            "escalated_at": dispute.escalated_at.isoformat(),
            "reason": reason,
        }
    
    def resolve_dispute(
        self,
        dispute_id: uuid.UUID,
        resolved_by: uuid.UUID,
        resolution_type: str,
        resolution_amount: Optional[float],
        resolution_notes: str,
    ) -> Dict[str, Any]:
        """
        Resolve a dispute with a resolution.
        
        Resolution types:
        - FULL_REFUND: Full refund to buyer
        - PARTIAL_REFUND: Partial refund to buyer
        - NO_REFUND: No refund, dispute rejected
        - DRIVER_PENALTY: Driver penalized, refund to buyer
        - SPLIT_COST: Cost split between parties
        """
        logger.info(f"Resolving dispute {dispute_id}: {resolution_type}")
        
        # Validate dispute exists
        dispute = self.db.query(TransportDispute).filter(
            TransportDispute.id == dispute_id
        ).first()
        
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        # Validate resolver has permission
        resolver = self.db.query(User).filter(User.id == resolved_by).first()
        if not resolver or resolver.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        # Update status to RESOLVED
        dispute.status = DBDisputeStatus.RESOLVED
        dispute.resolution_type = resolution_type
        dispute.resolution_amount = resolution_amount
        dispute.resolution_notes = resolution_notes
        dispute.resolved_by = resolved_by
        dispute.resolved_at = datetime.utcnow()
        dispute.updated_at = datetime.utcnow()
        
        # Apply resolution
        if resolution_type in ["FULL_REFUND", "PARTIAL_REFUND"] and resolution_amount:
            # Process refunds (simplified - would use payment service)
            pass
        
        # Release held payments
        payment_allocations = self.db.query(PaymentAllocation).filter(
            PaymentAllocation.order_id == dispute.order_id,
            PaymentAllocation.status == AllocationStatus.HELD
        ).all()
        
        for allocation in payment_allocations:
            allocation.status = AllocationStatus.RELEASED
            allocation.released_at = datetime.utcnow()
        
        self.db.commit()
        
        # Notify both parties
        order = self.db.query(Order).filter(Order.id == dispute.order_id).first()
        if order:
            notification_service.send_notification(
                db=self.db,
                user_id=order.buyer_id,
                notification_type="dispute_resolved",
                title="Dispute Resolved",
                body=f"Your dispute has been resolved: {resolution_type}",
                data={"dispute_id": str(dispute_id)},
            )
            notification_service.send_notification(
                db=self.db,
                user_id=order.seller_id,
                notification_type="dispute_resolved",
                title="Dispute Resolved",
                body=f"A dispute has been resolved: {resolution_type}",
                data={"dispute_id": str(dispute_id)},
            )
        
        # Close dispute
        dispute.status = DBDisputeStatus.CLOSED
        dispute.closed_at = datetime.utcnow()
        self.db.commit()
        
        return {
            "id": str(dispute_id),
            "status": dispute.status.value,
            "resolved_at": dispute.resolved_at.isoformat(),
            "resolution_type": resolution_type,
            "resolution_amount": resolution_amount,
        }
    
    def close_dispute(
        self,
        dispute_id: uuid.UUID,
        closed_by: uuid.UUID,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Close a dispute without resolution (e.g., withdrawn by user).
        """
        logger.info(f"Closing dispute {dispute_id} by {closed_by}")
        
        # Validate dispute exists
        dispute = self.db.query(TransportDispute).filter(
            TransportDispute.id == dispute_id
        ).first()
        
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        # Update status to CLOSED
        dispute.status = DBDisputeStatus.CLOSED
        dispute.closed_at = datetime.utcnow()
        dispute.updated_at = datetime.utcnow()
        
        # Release held payments
        payment_allocations = self.db.query(PaymentAllocation).filter(
            PaymentAllocation.order_id == dispute.order_id,
            PaymentAllocation.status == AllocationStatus.HELD
        ).all()
        
        for allocation in payment_allocations:
            allocation.status = AllocationStatus.RELEASED
            allocation.released_at = datetime.utcnow()
        
        self.db.commit()
        
        # Notify both parties
        order = self.db.query(Order).filter(Order.id == dispute.order_id).first()
        if order:
            notification_service.send_notification(
                db=self.db,
                user_id=order.buyer_id,
                notification_type="dispute_closed",
                title="Dispute Closed",
                body=f"The dispute has been closed: {reason}",
                data={"dispute_id": str(dispute_id)},
            )
            notification_service.send_notification(
                db=self.db,
                user_id=order.seller_id,
                notification_type="dispute_closed",
                title="Dispute Closed",
                body=f"A dispute has been closed: {reason}",
                data={"dispute_id": str(dispute_id)},
            )
        
        return {
            "id": str(dispute_id),
            "status": dispute.status.value,
            "closed_at": dispute.closed_at.isoformat(),
            "reason": reason,
        }
    
    def get_dispute(
        self,
        dispute_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get dispute details including evidence.
        """
        # Query disputes table
        dispute = self.db.query(TransportDispute).filter(
            TransportDispute.id == dispute_id
        ).first()
        
        if not dispute:
            return None
        
        # Query dispute_evidence table
        evidence = self.db.query(TransportDisputeEvidence).filter(
            TransportDisputeEvidence.dispute_id == dispute_id
        ).order_by(TransportDisputeEvidence.created_at).all()
        
        # Return dispute with evidence list
        return {
            "id": str(dispute.id),
            "order_id": str(dispute.order_id),
            "transport_request_id": str(dispute.transport_request_id) if dispute.transport_request_id else None,
            "delivery_id": str(dispute.delivery_id) if dispute.delivery_id else None,
            "raised_by": str(dispute.raised_by),
            "dispute_type": dispute.dispute_type,
            "category": dispute.category,
            "subcategory": dispute.subcategory,
            "title": dispute.title,
            "description": dispute.description,
            "disputed_amount": float(dispute.disputed_amount) if dispute.disputed_amount else None,
            "currency": dispute.currency,
            "status": dispute.status.value,
            "priority": dispute.priority,
            "resolution_type": dispute.resolution_type,
            "resolution_amount": float(dispute.resolution_amount) if dispute.resolution_amount else None,
            "resolution_notes": dispute.resolution_notes,
            "resolved_by": str(dispute.resolved_by) if dispute.resolved_by else None,
            "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None,
            "escalated_to_admin": dispute.escalated_to_admin,
            "escalated_at": dispute.escalated_at.isoformat() if dispute.escalated_at else None,
            "escalation_level": dispute.escalation_level,
            "created_at": dispute.created_at.isoformat(),
            "updated_at": dispute.updated_at.isoformat(),
            "closed_at": dispute.closed_at.isoformat() if dispute.closed_at else None,
            "response_due_at": dispute.response_due_at.isoformat() if dispute.response_due_at else None,
            "resolution_due_at": dispute.resolution_due_at.isoformat() if dispute.resolution_due_at else None,
            "evidence": [
                {
                    "id": str(ev.id),
                    "uploaded_by": str(ev.uploaded_by),
                    "evidence_type": ev.evidence_type,
                    "file_url": ev.file_url,
                    "file_name": ev.file_name,
                    "file_size_bytes": ev.file_size_bytes,
                    "file_mime_type": ev.file_mime_type,
                    "description": ev.description,
                    "created_at": ev.created_at.isoformat(),
                }
                for ev in evidence
            ],
        }
    
    def get_user_disputes(
        self,
        user_id: uuid.UUID,
        status: Optional[DisputeStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all disputes for a user (as raiser or counterparty).
        """
        # Query disputes table
        query = self.db.query(TransportDispute).filter(
            TransportDispute.raised_by == user_id
        )
        
        # Filter by status if provided
        if status:
            query = query.filter(TransportDispute.status == DBDisputeStatus(status.value))
        
        disputes = query.order_by(TransportDispute.created_at.desc()).all()
        
        # Return disputes
        return [
            {
                "id": str(d.id),
                "order_id": str(d.order_id),
                "dispute_type": d.dispute_type,
                "status": d.status.value,
                "priority": d.priority,
                "created_at": d.created_at.isoformat(),
            }
            for d in disputes
        ]
    
    def get_transport_disputes(
        self,
        transport_request_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all disputes for a transport request.
        """
        # Query disputes table
        disputes = self.db.query(TransportDispute).filter(
            TransportDispute.transport_request_id == transport_request_id
        ).order_by(TransportDispute.created_at.desc()).all()
        
        # Return disputes
        return [
            {
                "id": str(d.id),
                "order_id": str(d.order_id),
                "dispute_type": d.dispute_type,
                "status": d.status.value,
                "priority": d.priority,
                "created_at": d.created_at.isoformat(),
            }
            for d in disputes
        ]
    
    def check_response_deadlines(self) -> int:
        """
        Check for disputes past response deadline.
        
        Escalate to admin if counterparty hasn't responded.
        This is typically run as a scheduled job.
        """
        logger.info("Checking dispute response deadlines")
        
        escalated_count = 0
        
        # Query disputes where status = OPEN and response_due_at < NOW
        overdue_disputes = self.db.query(TransportDispute).filter(
            TransportDispute.status == DBDisputeStatus.OPEN,
            TransportDispute.response_due_at < datetime.utcnow()
        ).all()
        
        # For each overdue dispute:
        for dispute in overdue_disputes:
            # Escalate to admin
            dispute.status = DBDisputeStatus.ESCALATED
            dispute.escalated_to_admin = True
            dispute.escalated_at = datetime.utcnow()
            dispute.escalation_level = dispute.escalation_level + 1
            dispute.updated_at = datetime.utcnow()
            escalated_count += 1
            
            # Notify admin
            admin_users = self.db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])).all()
            for admin in admin_users:
                notification_service.send_notification(
                    db=self.db,
                    user_id=admin.id,
                    notification_type="dispute_overdue",
                    title="Dispute Response Overdue",
                    body="A dispute has passed its response deadline.",
                    data={"dispute_id": str(dispute.id)},
                )
            
            # Notify both parties
            order = self.db.query(Order).filter(Order.id == dispute.order_id).first()
            if order:
                notification_service.send_notification(
                    db=self.db,
                    user_id=order.buyer_id,
                    notification_type="dispute_overdue",
                    title="Dispute Response Overdue",
                    body="Your dispute has passed its response deadline and has been escalated.",
                    data={"dispute_id": str(dispute.id)},
                )
                notification_service.send_notification(
                    db=self.db,
                    user_id=order.seller_id,
                    notification_type="dispute_overdue",
                    title="Dispute Response Overdue",
                    body="A dispute has passed its response deadline and has been escalated.",
                    data={"dispute_id": str(dispute.id)},
                )
        
        self.db.commit()
        
        return escalated_count
    
    def check_resolution_deadlines(self) -> int:
        """
        Check for disputes past resolution deadline.
        
        Auto-resolve or escalate to higher authority.
        This is typically run as a scheduled job.
        """
        logger.info("Checking dispute resolution deadlines")
        
        auto_resolved_count = 0
        
        # Query disputes where status = UNDER_REVIEW and resolution_due_at < NOW
        overdue_disputes = self.db.query(TransportDispute).filter(
            TransportDispute.status == DBDisputeStatus.UNDER_REVIEW,
            TransportDispute.resolution_due_at < datetime.utcnow()
        ).all()
        
        # For each overdue dispute:
        for dispute in overdue_disputes:
            # Apply default resolution (e.g., full refund)
            dispute.resolution_type = "FULL_REFUND"
            dispute.resolution_amount = dispute.disputed_amount
            dispute.resolution_notes = "Auto-resolved due to resolution deadline"
            dispute.status = DBDisputeStatus.RESOLVED
            dispute.resolved_at = datetime.utcnow()
            dispute.closed_at = datetime.utcnow()
            auto_resolved_count += 1
            
            # Release held payments
            payment_allocations = self.db.query(PaymentAllocation).filter(
                PaymentAllocation.order_id == dispute.order_id,
                PaymentAllocation.status == AllocationStatus.HELD
            ).all()
            
            for allocation in payment_allocations:
                allocation.status = AllocationStatus.RELEASED
                allocation.released_at = datetime.utcnow()
            
            # Notify both parties
            order = self.db.query(Order).filter(Order.id == dispute.order_id).first()
            if order:
                notification_service.send_notification(
                    db=self.db,
                    user_id=order.buyer_id,
                    notification_type="dispute_auto_resolved",
                    title="Dispute Auto-Resolved",
                    body="Your dispute has been auto-resolved with a full refund.",
                    data={"dispute_id": str(dispute.id)},
                )
                notification_service.send_notification(
                    db=self.db,
                    user_id=order.seller_id,
                    notification_type="dispute_auto_resolved",
                    title="Dispute Auto-Resolved",
                    body="A dispute has been auto-resolved with a full refund.",
                    data={"dispute_id": str(dispute.id)},
                )
        
        self.db.commit()
        
        return auto_resolved_count
    
    def calculate_dispute_priority(
        self,
        dispute_type: DisputeType,
        disputed_amount: Optional[float],
    ) -> DisputePriority:
        """
        Calculate dispute priority based on type and amount.
        """
        # High priority types
        if dispute_type in [DisputeType.DAMAGED_GOODS, DisputeType.DRIVER_MISCONDUCT]:
            return DisputePriority.HIGH
        
        # Urgent priority for high-value disputes
        if disputed_amount and disputed_amount > 500:
            return DisputePriority.URGENT
        
        # Normal priority for standard disputes
        return DisputePriority.NORMAL


# ── Transport-Specific Dispute Handlers ───────────────────────────────────────

class DeliveryDelayHandler:
    """Handles delivery delay disputes"""
    
    @staticmethod
    def validate_delay(
        actual_arrival: datetime,
        estimated_arrival: datetime,
        threshold_minutes: int = 60,
    ) -> bool:
        """Check if delay exceeds threshold"""
        delay = actual_arrival - estimated_arrival
        return delay.total_seconds() / 60 > threshold_minutes
    
    @staticmethod
    def calculate_compensation(
        delay_minutes: int,
        transport_fee: float,
    ) -> float:
        """Calculate compensation for delay (e.g., 10% of fee per hour)"""
        hours = delay_minutes / 60
        compensation_rate = 0.10  # 10% per hour
        return round(transport_fee * compensation_rate * hours, 2)


class DamagedGoodsHandler:
    """Handles damaged goods disputes"""
    
    @staticmethod
    def validate_damage_claim(
        evidence: List[Dict[str, Any]],
    ) -> tuple[bool, str]:
        """Validate damage claim based on evidence"""
        # TODO: Check for photo evidence
        # TODO: Check for timestamp within delivery window
        # TODO: Verify goods match order
        
        return True, "Valid"
    
    @staticmethod
    def calculate_refund(
        goods_value: float,
        damage_percentage: float,
    ) -> float:
        """Calculate refund based on damage percentage"""
        return round(goods_value * (damage_percentage / 100), 2)


class PaymentDisputeHandler:
    """Handles payment disputes"""
    
    @staticmethod
    def validate_payment_claim(
        order_id: uuid.UUID,
        disputed_amount: float,
        expected_amount: float,
    ) -> tuple[bool, str]:
        """Validate payment dispute claim"""
        if abs(disputed_amount - expected_amount) < 0.01:
            return False, "Amounts match - no dispute needed"
        
        return True, "Valid dispute"


# ── Helper Functions ─────────────────────────────────────────────────────────

def validate_dispute_type(dispute_type: str) -> bool:
    """Validate dispute type"""
    try:
        DisputeType(dispute_type)
        return True
    except ValueError:
        return False


def validate_dispute_priority(priority: str) -> bool:
    """Validate dispute priority"""
    try:
        DisputePriority(priority)
        return True
    except ValueError:
        return False


def generate_dispute_reference(dispute_id: uuid.UUID) -> str:
    """Generate human-readable dispute reference"""
    return f"DISP-{str(dispute_id)[:8].upper()}"
