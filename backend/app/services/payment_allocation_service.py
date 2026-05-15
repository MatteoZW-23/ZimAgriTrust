"""
ZimAgritrust Payment Allocation Service
Manages payment allocations for transport fees, goods payments, and platform fees.
Ensures proper allocation based on business rules (requester-pays principle).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Allocation Types ───────────────────────────────────────────────────────────

class AllocationType(str, Enum):
    GOODS_PAYMENT = "GOODS_PAYMENT"
    TRANSPORT_FEE = "TRANSPORT_FEE"
    PLATFORM_FEE = "PLATFORM_FEE"
    REFUND = "REFUND"


class AllocationStatus(str, Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    RELEASED = "RELEASED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, Enum):
    ESCROW = "ESCROW"
    WALLET = "WALLET"
    STRIPE = "STRIPE"
    PAYNOW = "PAYNOW"
    CASH = "CASH"


# ── Allocation Data ───────────────────────────────────────────────────────────

@dataclass
class PaymentAllocation:
    """Payment allocation data"""
    order_id: uuid.UUID
    transport_request_id: Optional[uuid.UUID]
    allocation_type: AllocationType
    payer: str  # 'BUYER', 'FARMER', 'PLATFORM'
    payee: str  # 'FARMER', 'DRIVER', 'PLATFORM', 'BUYER'
    amount: float
    currency: str = "USD"
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None


# ── Payment Allocation Service ───────────────────────────────────────────────

class PaymentAllocationService:
    """Manages payment allocations for transport system"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_allocation(
        self,
        allocation: PaymentAllocation,
    ) -> Dict[str, Any]:
        """
        Create a payment allocation record.
        
        This records who pays what amount to whom.
        """
        logger.info(
            f"Creating payment allocation: {allocation.allocation_type.value}, "
            f"payer={allocation.payer}, payee={allocation.payee}, amount={allocation.amount}"
        )
        
        # TODO: Insert into payment_allocations table
        # TODO: Generate payment reference if not provided
        # TODO: Set initial status to PENDING
        
        allocation_id = uuid.uuid4()
        
        return {
            "id": str(allocation_id),
            "order_id": str(allocation.order_id),
            "allocation_type": allocation.allocation_type.value,
            "payer": allocation.payer,
            "payee": allocation.payee,
            "amount": allocation.amount,
            "currency": allocation.currency,
            "payment_method": allocation.payment_method.value if allocation.payment_method else None,
            "status": AllocationStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
        }
    
    def hold_in_escrow(
        self,
        allocation_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Hold payment in escrow.
        
        This is typically done when goods payment is received but delivery is pending.
        """
        logger.info(f"Holding allocation {allocation_id} in escrow")
        
        # TODO: Update payment_allocations status to HELD
        # TODO: Set held_at timestamp
        # TODO: Integrate with escrow service
        
        return {
            "id": str(allocation_id),
            "status": AllocationStatus.HELD.value,
            "held_at": datetime.utcnow().isoformat(),
        }
    
    def release_allocation(
        self,
        allocation_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Release payment from escrow to payee.
        
        This is done when delivery is confirmed and conditions are met.
        """
        logger.info(f"Releasing allocation {allocation_id}")
        
        # TODO: Update payment_allocations status to RELEASED
        # TODO: Set released_at timestamp
        # TODO: Execute actual payment transfer
        # TODO: Integrate with wallet service or payment gateway
        
        return {
            "id": str(allocation_id),
            "status": AllocationStatus.RELEASED.value,
            "released_at": datetime.utcnow().isoformat(),
        }
    
    def refund_allocation(
        self,
        allocation_id: uuid.UUID,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Refund a payment allocation.
        
        This is done when a dispute is resolved in favor of the payer.
        """
        logger.info(f"Refunding allocation {allocation_id}: {reason}")
        
        # TODO: Update payment_allocations status to REFUNDED
        # TODO: Set refunded_at timestamp
        # TODO: Execute refund to original payer
        # TODO: Record refund reason
        
        return {
            "id": str(allocation_id),
            "status": AllocationStatus.REFUNDED.value,
            "refunded_at": datetime.utcnow().isoformat(),
            "refund_reason": reason,
        }
    
    def create_transport_fee_allocations(
        self,
        order_id: uuid.UUID,
        transport_request_id: uuid.UUID,
        transport_fee: float,
        payer: str,  # 'BUYER', 'FARMER', or 'SPLIT'
        split_ratio: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create transport fee payment allocations based on payer.
        
        Core Business Rule: WHOEVER REQUESTS TRANSPORT = WHO PAYS FOR TRANSPORT
        """
        logger.info(
            f"Creating transport fee allocations for order {order_id}: "
            f"payer={payer}, amount={transport_fee}"
        )
        
        allocations = []
        
        if payer == "BUYER":
            # Buyer pays full transport fee to driver
            allocation = PaymentAllocation(
                order_id=order_id,
                transport_request_id=transport_request_id,
                allocation_type=AllocationType.TRANSPORT_FEE,
                payer="BUYER",
                payee="DRIVER",
                amount=transport_fee,
                payment_method=PaymentMethod.ESCROW,
            )
            allocations.append(self.create_allocation(allocation))
        
        elif payer == "FARMER":
            # Farmer pays full transport fee to driver
            allocation = PaymentAllocation(
                order_id=order_id,
                transport_request_id=transport_request_id,
                allocation_type=AllocationType.TRANSPORT_FEE,
                payer="FARMER",
                payee="DRIVER",
                amount=transport_fee,
                payment_method=PaymentMethod.ESCROW,
            )
            allocations.append(self.create_allocation(allocation))
        
        elif payer == "SPLIT" and split_ratio:
            # Split payment between buyer and farmer
            buyer_share = transport_fee * split_ratio.get("buyer", 0.5)
            farmer_share = transport_fee * split_ratio.get("farmer", 0.5)
            
            buyer_allocation = PaymentAllocation(
                order_id=order_id,
                transport_request_id=transport_request_id,
                allocation_type=AllocationType.TRANSPORT_FEE,
                payer="BUYER",
                payee="DRIVER",
                amount=buyer_share,
                payment_method=PaymentMethod.ESCROW,
            )
            allocations.append(self.create_allocation(buyer_allocation))
            
            farmer_allocation = PaymentAllocation(
                order_id=order_id,
                transport_request_id=transport_request_id,
                allocation_type=AllocationType.TRANSPORT_FEE,
                payer="FARMER",
                payee="DRIVER",
                amount=farmer_share,
                payment_method=PaymentMethod.ESCROW,
            )
            allocations.append(self.create_allocation(farmer_allocation))
        
        return allocations
    
    def create_goods_payment_allocation(
        self,
        order_id: uuid.UUID,
        goods_amount: float,
        platform_fee: float,
    ) -> List[Dict[str, Any]]:
        """
        Create goods payment and platform fee allocations.
        
        Buyer pays goods amount + platform fee.
        Farmer receives goods amount - platform fee.
        Platform receives platform fee.
        """
        logger.info(
            f"Creating goods payment allocations for order {order_id}: "
            f"goods={goods_amount}, platform_fee={platform_fee}"
        )
        
        allocations = []
        
        # Buyer pays goods amount to farmer (via escrow)
        goods_allocation = PaymentAllocation(
            order_id=order_id,
            transport_request_id=None,
            allocation_type=AllocationType.GOODS_PAYMENT,
            payer="BUYER",
            payee="FARMER",
            amount=goods_amount,
            payment_method=PaymentMethod.ESCROW,
        )
        allocations.append(self.create_allocation(goods_allocation))
        
        # Platform fee allocation (buyer pays to platform)
        if platform_fee > 0:
            platform_allocation = PaymentAllocation(
                order_id=order_id,
                transport_request_id=None,
                allocation_type=AllocationType.PLATFORM_FEE,
                payer="BUYER",
                payee="PLATFORM",
                amount=platform_fee,
                payment_method=PaymentMethod.ESCROW,
            )
            allocations.append(self.create_allocation(platform_allocation))
        
        return allocations
    
    def get_order_allocations(
        self,
        order_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all payment allocations for an order.
        """
        # TODO: Query payment_allocations table
        # TODO: Filter by order_id
        # TODO: Return all allocations with status
        
        return []
    
    def get_user_allocations(
        self,
        user_id: uuid.UUID,
        role: str,  # 'payer' or 'payee'
    ) -> List[Dict[str, Any]]:
        """
        Get all payment allocations for a user as payer or payee.
        """
        # TODO: Query payment_allocations table
        # TODO: Filter by payer or payee
        # TODO: Return allocations
        
        return []
    
    def calculate_total_payer_amount(
        self,
        order_id: uuid.UUID,
        payer: str,
    ) -> float:
        """
        Calculate total amount a payer needs to pay for an order.
        """
        allocations = self.get_order_allocations(order_id)
        
        total = sum(
            a["amount"] for a in allocations
            if a["payer"] == payer and a["status"] != AllocationStatus.REFUNDED.value
        )
        
        return round(total, 2)
    
    def calculate_total_payee_amount(
        self,
        order_id: uuid.UUID,
        payee: str,
    ) -> float:
        """
        Calculate total amount a payee will receive for an order.
        """
        allocations = self.get_order_allocations(order_id)
        
        total = sum(
            a["amount"] for a in allocations
            if a["payee"] == payee and a["status"] == AllocationStatus.RELEASED.value
        )
        
        return round(total, 2)


# ── Helper Functions ───────────────────────────────────────────────────────────

def validate_payer(payer: str) -> bool:
    """Validate payer value"""
    return payer in ["BUYER", "FARMER", "PLATFORM"]


def validate_payee(payee: str) -> bool:
    """Validate payee value"""
    return payee in ["FARMER", "DRIVER", "PLATFORM", "BUYER"]


def validate_split_ratio(split_ratio: Dict[str, float]) -> bool:
    """Validate split ratio sums to 1.0"""
    if not split_ratio:
        return False
    
    total = sum(split_ratio.values())
    return abs(total - 1.0) < 0.01  # Allow small floating point errors
