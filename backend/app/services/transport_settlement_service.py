"""
ZimAgritrust Transport Settlement Service
Handles settlement calculations and payouts for transport payments.
Ensures proper distribution based on business rules (requester-pays principle).
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


# ── Settlement Types ─────────────────────────────────────────────────────────

class SettlementType(str, Enum):
    FARMER_PAYOUT = "FARMER_PAYOUT"
    DRIVER_PAYOUT = "DRIVER_PAYOUT"
    BUYER_REFUND = "BUYER_REFUND"


class SettlementStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PayoutMethod(str, Enum):
    WALLET = "WALLET"
    BANK_TRANSFER = "BANK_TRANSFER"
    MOBILE_MONEY = "MOBILE_MONEY"


# ── Settlement Data ─────────────────────────────────────────────────────────

@dataclass
class Settlement:
    """Settlement data"""
    order_id: uuid.UUID
    user_id: uuid.UUID
    settlement_type: SettlementType
    gross_amount: float
    deductions: Dict[str, float]
    net_amount: float
    currency: str = "USD"
    goods_amount: Optional[float] = None
    transport_amount: Optional[float] = None
    platform_fee_amount: Optional[float] = None
    other_deductions: float = 0.0
    payout_method: PayoutMethod = PayoutMethod.WALLET
    payout_reference: Optional[str] = None


# ── Transport Settlement Service ─────────────────────────────────────────────

class TransportSettlementService:
    """Manages transport-specific settlements"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_farmer_settlement(
        self,
        order_id: uuid.UUID,
        farmer_id: uuid.UUID,
        goods_amount: float,
        platform_fee: float,
        transport_fee_paid_by_farmer: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate farmer settlement.
        
        Formula:
        Net = Goods Amount - Platform Fee - Transport Fee (if farmer paid)
        """
        logger.info(
            f"Calculating farmer settlement for order {order_id}: "
            f"goods={goods_amount}, platform_fee={platform_fee}, "
            f"transport_fee={transport_fee_paid_by_farmer}"
        )
        
        gross_amount = goods_amount
        deductions = {
            "platform_fee": platform_fee,
        }
        
        if transport_fee_paid_by_farmer > 0:
            deductions["transport_fee"] = transport_fee_paid_by_farmer
        
        total_deductions = sum(deductions.values())
        net_amount = gross_amount - total_deductions
        
        settlement = Settlement(
            order_id=order_id,
            user_id=farmer_id,
            settlement_type=SettlementType.FARMER_PAYOUT,
            gross_amount=gross_amount,
            deductions=deductions,
            net_amount=net_amount,
            goods_amount=goods_amount,
            transport_amount=transport_fee_paid_by_farmer if transport_fee_paid_by_farmer > 0 else None,
            platform_fee_amount=platform_fee,
        )
        
        return self._create_settlement_record(settlement)
    
    def calculate_driver_settlement(
        self,
        order_id: uuid.UUID,
        driver_id: uuid.UUID,
        transport_fee: float,
        platform_commission: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate driver settlement.
        
        Formula:
        Net = Transport Fee - Platform Commission
        """
        logger.info(
            f"Calculating driver settlement for order {order_id}: "
            f"transport_fee={transport_fee}, platform_commission={platform_commission}"
        )
        
        gross_amount = transport_fee
        deductions = {
            "platform_commission": platform_commission,
        }
        
        total_deductions = sum(deductions.values())
        net_amount = gross_amount - total_deductions
        
        settlement = Settlement(
            order_id=order_id,
            user_id=driver_id,
            settlement_type=SettlementType.DRIVER_PAYOUT,
            gross_amount=gross_amount,
            deductions=deductions,
            net_amount=net_amount,
            transport_amount=transport_fee,
            platform_fee_amount=platform_commission,
        )
        
        return self._create_settlement_record(settlement)
    
    def calculate_buyer_refund(
        self,
        order_id: uuid.UUID,
        buyer_id: uuid.UUID,
        refund_amount: float,
        refund_reason: str,
    ) -> Dict[str, Any]:
        """
        Calculate buyer refund.
        
        Used when disputes are resolved in buyer's favor or order is cancelled.
        """
        logger.info(
            f"Calculating buyer refund for order {order_id}: "
            f"amount={refund_amount}, reason={refund_reason}"
        )
        
        gross_amount = refund_amount
        deductions = {}
        net_amount = refund_amount
        
        settlement = Settlement(
            order_id=order_id,
            user_id=buyer_id,
            settlement_type=SettlementType.BUYER_REFUND,
            gross_amount=gross_amount,
            deductions=deductions,
            net_amount=net_amount,
            other_deductions=0.0,
        )
        
        return self._create_settlement_record(settlement)
    
    def process_settlement(
        self,
        settlement_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Process a settlement - execute the actual payout.
        """
        logger.info(f"Processing settlement {settlement_id}")
        
        # TODO: Query settlements table
        # TODO: Update status to PROCESSING
        # TODO: Execute payout based on payout_method
        # TODO: Integrate with wallet service or payment gateway
        # TODO: Update status to COMPLETED or FAILED
        # TODO: Handle retries on failure
        
        return {
            "id": str(settlement_id),
            "status": SettlementStatus.PROCESSING.value,
            "processed_at": datetime.utcnow().isoformat(),
        }
    
    def process_order_settlements(
        self,
        order_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Process all settlements for an order after delivery confirmation.
        
        This is called when delivery is confirmed and all conditions are met.
        """
        logger.info(f"Processing all settlements for order {order_id}")
        
        settlements = []
        
        # TODO: Query order details
        # TODO: Determine transport fee payer
        # TODO: Calculate farmer settlement
        # TODO: Calculate driver settlement (if platform delivery)
        # TODO: Process all settlements
        # TODO: Send notifications
        
        return settlements
    
    def retry_failed_settlements(
        self,
        max_retries: int = 3,
    ) -> int:
        """
        Retry failed settlements with exponential backoff.
        
        This is typically run as a scheduled job.
        """
        logger.info("Retrying failed settlements")
        
        retry_count = 0
        
        # TODO: Query settlements with status FAILED
        # TODO: Filter by retry_count < max_retries
        # TODO: Check if next_retry_at has passed
        # TODO: Process settlement
        # TODO: Update retry_count and next_retry_at on failure
        
        return retry_count
    
    def _create_settlement_record(
        self,
        settlement: Settlement,
    ) -> Dict[str, Any]:
        """
        Create a settlement record in the database.
        """
        # TODO: Insert into settlements table
        # TODO: Generate payout reference if not provided
        # TODO: Set initial status to PENDING
        
        settlement_id = uuid.uuid4()
        
        return {
            "id": str(settlement_id),
            "order_id": str(settlement.order_id),
            "user_id": str(settlement.user_id),
            "settlement_type": settlement.settlement_type.value,
            "gross_amount": settlement.gross_amount,
            "deductions": settlement.deductions,
            "net_amount": settlement.net_amount,
            "currency": settlement.currency,
            "goods_amount": settlement.goods_amount,
            "transport_amount": settlement.transport_amount,
            "platform_fee_amount": settlement.platform_fee_amount,
            "other_deductions": settlement.other_deductions,
            "payout_method": settlement.payout_method.value,
            "payout_reference": settlement.payout_reference,
            "status": SettlementStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
        }
    
    def get_settlement(
        self,
        settlement_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get settlement details.
        """
        # TODO: Query settlements table
        # TODO: Return settlement details
        
        return None
    
    def get_user_settlements(
        self,
        user_id: uuid.UUID,
        settlement_type: Optional[SettlementType] = None,
        status: Optional[SettlementStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all settlements for a user.
        """
        # TODO: Query settlements table
        # TODO: Filter by user_id, type, status
        # TODO: Return settlements
        
        return []
    
    def get_order_settlements(
        self,
        order_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all settlements for an order.
        """
        # TODO: Query settlements table
        # TODO: Filter by order_id
        # TODO: Return settlements
        
        return []


# ── Helper Functions ─────────────────────────────────────────────────────────

def calculate_retry_delay(retry_count: int) -> int:
    """
    Calculate retry delay in seconds using exponential backoff.
    
    Formula: 2^retry_count * 60 (minimum 60 seconds, maximum 1 hour)
    """
    delay = min(2 ** retry_count * 60, 3600)
    return delay


def validate_settlement_amount(amount: float) -> bool:
    """Validate settlement amount is positive"""
    return amount > 0


def validate_deductions(deductions: Dict[str, float]) -> bool:
    """Validate all deductions are non-negative"""
    return all(v >= 0 for v in deductions.values())
