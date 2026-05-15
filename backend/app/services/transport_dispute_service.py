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
        
        # TODO: Insert into disputes table
        # TODO: Hold relevant payments in escrow
        # TODO: Set response deadline (48 hours)
        # TODO: Set resolution deadline (7 days)
        # TODO: Notify admin
        # TODO: Notify counterparty
        # TODO: Determine priority based on type and amount
        
        dispute_id = uuid.uuid4()
        response_due_at = datetime.utcnow() + timedelta(hours=self.RESPONSE_DEADLINE_HOURS)
        resolution_due_at = datetime.utcnow() + timedelta(days=self.RESOLUTION_DEADLINE_DAYS)
        
        return {
            "id": str(dispute_id),
            "order_id": str(dispute.order_id),
            "dispute_type": dispute.dispute_type.value,
            "status": DisputeStatus.OPEN.value,
            "priority": dispute.priority.value,
            "created_at": datetime.utcnow().isoformat(),
            "response_due_at": response_due_at.isoformat(),
            "resolution_due_at": resolution_due_at.isoformat(),
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
        
        # TODO: Validate dispute exists
        # TODO: Insert into dispute_evidence table
        # TODO: Notify admin of new evidence
        
        evidence_id = uuid.uuid4()
        
        return {
            "id": str(evidence_id),
            "dispute_id": str(dispute_id),
            "evidence_type": evidence_type,
            "file_url": file_url,
            "created_at": datetime.utcnow().isoformat(),
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
        
        # TODO: Validate dispute exists
        # TODO: Update status to ESCALATED
        # TODO: Increment escalation level
        # TODO: Set escalated_at
        # TODO: Notify admin
        # TODO: Notify both parties
        
        return {
            "id": str(dispute_id),
            "status": DisputeStatus.ESCALATED.value,
            "escalated_at": datetime.utcnow().isoformat(),
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
        
        # TODO: Validate dispute exists
        # TODO: Validate resolver has permission
        # TODO: Update status to RESOLVED
        # TODO: Set resolved_at and resolved_by
        # TODO: Apply resolution:
        #   - Process refunds if applicable
        #   - Release held payments
        #   - Apply penalties if applicable
        # TODO: Notify both parties
        # TODO: Close dispute
        
        return {
            "id": str(dispute_id),
            "status": DisputeStatus.RESOLVED.value,
            "resolved_at": datetime.utcnow().isoformat(),
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
        
        # TODO: Validate dispute exists
        # TODO: Update status to CLOSED
        # TODO: Set closed_at
        # TODO: Release held payments
        # TODO: Notify both parties
        
        return {
            "id": str(dispute_id),
            "status": DisputeStatus.CLOSED.value,
            "closed_at": datetime.utcnow().isoformat(),
            "reason": reason,
        }
    
    def get_dispute(
        self,
        dispute_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get dispute details including evidence.
        """
        # TODO: Query disputes table
        # TODO: Query dispute_evidence table
        # TODO: Return dispute with evidence list
        
        return None
    
    def get_user_disputes(
        self,
        user_id: uuid.UUID,
        status: Optional[DisputeStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all disputes for a user (as raiser or counterparty).
        """
        # TODO: Query disputes table
        # TODO: Filter where raised_by = user_id or counterparty = user_id
        # TODO: Filter by status if provided
        # TODO: Return disputes
        
        return []
    
    def get_transport_disputes(
        self,
        transport_request_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all disputes for a transport request.
        """
        # TODO: Query disputes table
        # TODO: Filter by transport_request_id
        # TODO: Return disputes
        
        return []
    
    def check_response_deadlines(self) -> int:
        """
        Check for disputes past response deadline.
        
        Escalate to admin if counterparty hasn't responded.
        This is typically run as a scheduled job.
        """
        logger.info("Checking dispute response deadlines")
        
        escalated_count = 0
        
        # TODO: Query disputes where:
        #   - status = OPEN
        #   - response_due_at < NOW
        # TODO: For each overdue dispute:
        #   - Escalate to admin
        #   - Notify admin
        #   - Notify both parties
        
        return escalated_count
    
    def check_resolution_deadlines(self) -> int:
        """
        Check for disputes past resolution deadline.
        
        Auto-resolve or escalate to higher authority.
        This is typically run as a scheduled job.
        """
        logger.info("Checking dispute resolution deadlines")
        
        auto_resolved_count = 0
        
        # TODO: Query disputes where:
        #   - status = UNDER_REVIEW
        #   - resolution_due_at < NOW
        # TODO: For each overdue dispute:
        #   - Apply default resolution (e.g., full refund)
        #   - Notify both parties
        #   - Close dispute
        
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
