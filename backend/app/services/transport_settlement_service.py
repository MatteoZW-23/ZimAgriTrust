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

from app.models.transport import (
    Settlement,
    SettlementStatus as DBSettlementStatus,
    PaymentAllocation,
    AllocationStatus,
    DriverAssignment,
    TransportRequest,
)
from app.models.transaction import Order
from app.models.user import User, UserRole
from app.services.notification_service import notification_service

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
        
        # Query settlements table
        settlement = self.db.query(Settlement).filter(
            Settlement.id == settlement_id
        ).first()
        
        if not settlement:
            raise HTTPException(status_code=404, detail="Settlement not found")
        
        if settlement.status != DBSettlementStatus.PENDING:
            raise HTTPException(status_code=400, detail="Settlement is not in PENDING status")
        
        # Update status to PROCESSING
        settlement.status = DBSettlementStatus.PROCESSING
        settlement.processed_at = datetime.utcnow()
        self.db.commit()
        
        # Execute payout based on payout_method
        try:
            # Integrate with wallet service or payment gateway (simplified)
            if settlement.payout_method == "WALLET":
                # Would call wallet service to credit user wallet
                pass
            elif settlement.payout_method == "BANK_TRANSFER":
                # Would call payment gateway for bank transfer
                pass
            elif settlement.payout_method == "MOBILE_MONEY":
                # Would call mobile money API
                pass
            
            # Update status to COMPLETED
            settlement.status = DBSettlementStatus.COMPLETED
            settlement.completed_at = datetime.utcnow()
            self.db.commit()
            
            # Send notification
            notification_service.send_notification(
                db=self.db,
                user_id=settlement.user_id,
                notification_type="settlement_completed",
                title="Settlement Completed",
                body=f"Your settlement of ${settlement.net_amount:.2f} has been processed.",
                data={"settlement_id": str(settlement.id)},
            )
            
        except Exception as e:
            # Update status to FAILED
            settlement.status = DBSettlementStatus.FAILED
            settlement.retry_count = (settlement.retry_count or 0) + 1
            settlement.next_retry_at = datetime.utcnow() + timedelta(seconds=calculate_retry_delay(settlement.retry_count))
            settlement.error_message = str(e)
            self.db.commit()
            
            # Handle retries on failure (would be handled by scheduled job)
            logger.error(f"Settlement {settlement_id} failed: {e}")
            raise
        
        return {
            "id": str(settlement.id),
            "status": settlement.status.value,
            "processed_at": settlement.processed_at.isoformat() if settlement.processed_at else None,
            "completed_at": settlement.completed_at.isoformat() if settlement.completed_at else None,
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
        
        # Query order details
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Determine transport fee payer
        payment_allocations = self.db.query(PaymentAllocation).filter(
            PaymentAllocation.order_id == order_id,
            PaymentAllocation.allocation_type == "TRANSPORT_FEE"
        ).all()
        
        transport_fee_payer = None
        transport_fee = 0.0
        for allocation in payment_allocations:
            if allocation.payer:
                transport_fee_payer = allocation.payer
                transport_fee = allocation.amount
        
        # Calculate farmer settlement
        platform_fee = order.total_amount * 0.05  # 5% platform fee
        transport_fee_paid_by_farmer = transport_fee if transport_fee_payer == "FARMER" else 0.0
        
        farmer_settlement = self.calculate_farmer_settlement(
            order_id=order_id,
            farmer_id=order.seller_id,
            goods_amount=order.total_amount,
            platform_fee=platform_fee,
            transport_fee_paid_by_farmer=transport_fee_paid_by_farmer,
        )
        settlements.append(farmer_settlement)
        
        # Calculate driver settlement (if platform delivery)
        driver_assignment = self.db.query(DriverAssignment).filter(
            DriverAssignment.transport_request_id.in_(
                self.db.query(TransportRequest.id).filter(TransportRequest.order_id == order_id)
            )
        ).first()
        
        if driver_assignment and driver_assignment.status == "COMPLETED":
            driver_settlement = self.calculate_driver_settlement(
                order_id=order_id,
                driver_id=driver_assignment.driver_id,
                transport_fee=driver_assignment.transport_fee,
                platform_commission=driver_assignment.platform_commission,
            )
            settlements.append(driver_settlement)
        
        # Process all settlements
        for settlement_data in settlements:
            settlement_id = uuid.UUID(settlement_data["id"])
            try:
                self.process_settlement(settlement_id)
            except Exception as e:
                logger.error(f"Failed to process settlement {settlement_id}: {e}")
        
        # Send notifications
        notification_service.send_notification(
            db=self.db,
            user_id=order.seller_id,
            notification_type="settlements_processed",
            title="Order Settlements Processed",
            body="Your order settlements have been processed.",
            data={"order_id": str(order_id)},
        )
        
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
        
        # Query settlements with status FAILED
        failed_settlements = self.db.query(Settlement).filter(
            Settlement.status == DBSettlementStatus.FAILED,
            (Settlement.retry_count < max_retries) | (Settlement.retry_count.is_(None))
        ).all()
        
        for settlement in failed_settlements:
            # Check if next_retry_at has passed
            if settlement.next_retry_at and settlement.next_retry_at > datetime.utcnow():
                continue
            
            # Process settlement
            try:
                self.process_settlement(settlement.id)
                retry_count += 1
            except Exception as e:
                # Update retry_count and next_retry_at on failure
                settlement.retry_count = (settlement.retry_count or 0) + 1
                settlement.next_retry_at = datetime.utcnow() + timedelta(seconds=calculate_retry_delay(settlement.retry_count))
                settlement.error_message = str(e)
                self.db.commit()
                logger.error(f"Retry failed for settlement {settlement.id}: {e}")
        
        return retry_count
        
        return retry_count
    
    def _create_settlement_record(
        self,
        settlement: Settlement,
    ) -> Dict[str, Any]:
        """
        Create a settlement record in the database.
        """
        # Insert into settlements table
        db_settlement = Settlement(
            order_id=settlement.order_id,
            user_id=settlement.user_id,
            settlement_type=settlement.settlement_type.value,
            gross_amount=settlement.gross_amount,
            deductions=settlement.deductions,
            net_amount=settlement.net_amount,
            currency=settlement.currency,
            goods_amount=settlement.goods_amount,
            transport_amount=settlement.transport_amount,
            platform_fee_amount=settlement.platform_fee_amount,
            other_deductions=settlement.other_deductions,
            payout_method=settlement.payout_method.value,
            payout_reference=settlement.payout_reference,
            status=DBSettlementStatus.PENDING,
        )
        self.db.add(db_settlement)
        self.db.flush()
        
        # Generate payout reference if not provided
        if not db_settlement.payout_reference:
            db_settlement.payout_reference = f"STL-{str(db_settlement.id)[:8].upper()}"
        
        self.db.commit()
        
        return {
            "id": str(db_settlement.id),
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
            "payout_reference": db_settlement.payout_reference,
            "status": db_settlement.status.value,
            "created_at": db_settlement.created_at.isoformat(),
        }
    
    def get_settlement(
        self,
        settlement_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get settlement details.
        """
        # Query settlements table
        settlement = self.db.query(Settlement).filter(
            Settlement.id == settlement_id
        ).first()
        
        if not settlement:
            return None
        
        # Return settlement details
        return {
            "id": str(settlement.id),
            "order_id": str(settlement.order_id),
            "user_id": str(settlement.user_id),
            "settlement_type": settlement.settlement_type,
            "gross_amount": float(settlement.gross_amount),
            "deductions": settlement.deductions,
            "net_amount": float(settlement.net_amount),
            "currency": settlement.currency,
            "goods_amount": float(settlement.goods_amount) if settlement.goods_amount else None,
            "transport_amount": float(settlement.transport_amount) if settlement.transport_amount else None,
            "platform_fee_amount": float(settlement.platform_fee_amount) if settlement.platform_fee_amount else None,
            "other_deductions": float(settlement.other_deductions) if settlement.other_deductions else 0.0,
            "payout_method": settlement.payout_method,
            "payout_reference": settlement.payout_reference,
            "status": settlement.status.value,
            "retry_count": settlement.retry_count,
            "error_message": settlement.error_message,
            "created_at": settlement.created_at.isoformat(),
            "processed_at": settlement.processed_at.isoformat() if settlement.processed_at else None,
            "completed_at": settlement.completed_at.isoformat() if settlement.completed_at else None,
            "next_retry_at": settlement.next_retry_at.isoformat() if settlement.next_retry_at else None,
        }
    
    def get_user_settlements(
        self,
        user_id: uuid.UUID,
        settlement_type: Optional[SettlementType] = None,
        status: Optional[SettlementStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all settlements for a user.
        """
        # Query settlements table
        query = self.db.query(Settlement).filter(Settlement.user_id == user_id)
        
        # Filter by type, status
        if settlement_type:
            query = query.filter(Settlement.settlement_type == settlement_type.value)
        if status:
            query = query.filter(Settlement.status == DBSettlementStatus(status.value))
        
        settlements = query.order_by(Settlement.created_at.desc()).all()
        
        # Return settlements
        return [
            {
                "id": str(s.id),
                "order_id": str(s.order_id),
                "settlement_type": s.settlement_type,
                "net_amount": float(s.net_amount),
                "status": s.status.value,
                "created_at": s.created_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in settlements
        ]
    
    def get_order_settlements(
        self,
        order_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all settlements for an order.
        """
        # Query settlements table
        settlements = self.db.query(Settlement).filter(
            Settlement.order_id == order_id
        ).order_by(Settlement.created_at.desc()).all()
        
        # Return settlements
        return [
            {
                "id": str(s.id),
                "user_id": str(s.user_id),
                "settlement_type": s.settlement_type,
                "net_amount": float(s.net_amount),
                "status": s.status.value,
                "created_at": s.created_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in settlements
        ]


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
