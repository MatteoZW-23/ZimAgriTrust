"""
ZimAgritrust Transport Business Rule Engine
Enforces the core business rule: WHOEVER REQUESTS TRANSPORT = WHO PAYS FOR TRANSPORT

This service applies all 6 core business rules for transport payment responsibility.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.transport_pricing_service import (
    transport_pricing_engine,
    PricingFactors,
)
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


# ── Transport Modes Enum ───────────────────────────────────────────────────────

class TransportMode(str, Enum):
    PLATFORM_DELIVERY_BUYER_REQUESTED = "PLATFORM_DELIVERY_BUYER_REQUESTED"
    PLATFORM_DELIVERY_FARMER_REQUESTED = "PLATFORM_DELIVERY_FARMER_REQUESTED"
    SELF_PICKUP = "SELF_PICKUP"
    SELF_DELIVERY = "SELF_DELIVERY"
    NEGOTIATED_TRANSPORT = "NEGOTIATED_TRANSPORT"
    DEFERRED = "DEFERRED"


# ── Rule Result ───────────────────────────────────────────────────────────────

@dataclass
class RuleResult:
    """Result of applying a business rule"""
    success: bool
    transport_fee_payer: Optional[str]  # 'BUYER', 'FARMER', 'SPLIT', or None
    transport_fee: float
    driver_assignment: str  # 'AUTO_ASSIGNED', 'MANUAL', 'NONE'
    payment_allocations: list[Dict[str, Any]]
    notifications: list[Dict[str, Any]]
    error_message: Optional[str] = None


# ── Business Rule Engine ───────────────────────────────────────────────────────

class TransportRuleEngine:
    """Enforces transport payment business rules"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def apply_rules(
        self,
        order_id: uuid.UUID,
        requested_by: str,  # 'BUYER' or 'FARMER'
        mode: TransportMode,
        transport_request_data: Dict[str, Any],
    ) -> RuleResult:
        """
        Apply the appropriate business rule based on transport mode.
        
        Core Principle: WHOEVER REQUESTS TRANSPORT = WHO PAYS FOR TRANSPORT
        """
        logger.info(
            f"Applying transport rule for order {order_id}: "
            f"requested_by={requested_by}, mode={mode}"
        )
        
        try:
            if mode == TransportMode.PLATFORM_DELIVERY_BUYER_REQUESTED:
                return await self._apply_buyer_requested_delivery(
                    order_id, transport_request_data
                )
            elif mode == TransportMode.PLATFORM_DELIVERY_FARMER_REQUESTED:
                return await self._apply_farmer_requested_delivery(
                    order_id, transport_request_data
                )
            elif mode == TransportMode.SELF_PICKUP:
                return await self._apply_self_pickup(
                    order_id, transport_request_data
                )
            elif mode == TransportMode.SELF_DELIVERY:
                return await self._apply_self_delivery(
                    order_id, transport_request_data
                )
            elif mode == TransportMode.NEGOTIATED_TRANSPORT:
                return await self._apply_negotiated_transport(
                    order_id, requested_by, transport_request_data
                )
            elif mode == TransportMode.DEFERRED:
                return await self._apply_deferred_decision(
                    order_id, requested_by, transport_request_data
                )
            else:
                raise ValueError(f"Unknown transport mode: {mode}")
        except Exception as e:
            logger.error(f"Error applying transport rule: {e}")
            return RuleResult(
                success=False,
                transport_fee_payer=None,
                transport_fee=0.0,
                driver_assignment="NONE",
                payment_allocations=[],
                notifications=[],
                error_message=str(e),
            )
    
    async def _apply_buyer_requested_delivery(
        self,
        order_id: uuid.UUID,
        transport_data: Dict[str, Any],
    ) -> RuleResult:
        """
        RULE 1: Buyer Requested Delivery
        - Buyer pays transport fee
        - Transport fee added to buyer invoice
        - Farmer receives full goods payment minus platform fee
        - Driver assigned automatically
        """
        logger.info(f"Applying Rule 1: Buyer Requested Delivery for order {order_id}")
        
        # Calculate transport fee
        quote = await self._calculate_transport_quote(transport_data)
        
        # Create payment allocation
        allocation = {
            "order_id": str(order_id),
            "allocation_type": "TRANSPORT_FEE",
            "payer": "BUYER",
            "payee": "DRIVER",
            "amount": quote["total_amount"],
            "currency": "USD",
            "payment_method": "ESCROW",
        }
        
        # Create notifications
        notifications = [
            {
                "user_type": "BUYER",
                "type": "TRANSPORT_FEE_ASSIGNED",
                "title": "Transport Fee Assigned",
                "body": f"You will pay ${quote['total_amount']:.2f} for transport.",
                "data": {"transport_fee": quote["total_amount"]},
            },
            {
                "user_type": "FARMER",
                "type": "BUYER_REQUESTED_DELIVERY",
                "title": "Buyer Requested Delivery",
                "body": "The buyer has requested platform delivery for your order.",
                "data": {},
            },
        ]
        
        return RuleResult(
            success=True,
            transport_fee_payer="BUYER",
            transport_fee=quote["total_amount"],
            driver_assignment="AUTO_ASSIGNED",
            payment_allocations=[allocation],
            notifications=notifications,
        )
    
    async def _apply_farmer_requested_delivery(
        self,
        order_id: uuid.UUID,
        transport_data: Dict[str, Any],
    ) -> RuleResult:
        """
        RULE 2: Farmer Requested Delivery
        - Farmer pays transport fee
        - Transport fee deducted from farmer settlement
        - Buyer pays goods price only
        - Driver assigned automatically
        """
        logger.info(f"Applying Rule 2: Farmer Requested Delivery for order {order_id}")
        
        # Calculate transport fee
        quote = await self._calculate_transport_quote(transport_data)
        
        # Create payment allocation
        allocation = {
            "order_id": str(order_id),
            "allocation_type": "TRANSPORT_FEE",
            "payer": "FARMER",
            "payee": "DRIVER",
            "amount": quote["total_amount"],
            "currency": "USD",
            "payment_method": "ESCROW",
        }
        
        # Create notifications
        notifications = [
            {
                "user_type": "FARMER",
                "type": "TRANSPORT_FEE_DEDUCTED",
                "title": "Transport Fee Deducted",
                "body": f"${quote['total_amount']:.2f} will be deducted from your settlement for transport.",
                "data": {"transport_fee": quote["total_amount"]},
            },
            {
                "user_type": "BUYER",
                "type": "FARMER_PROVIDING_DELIVERY",
                "title": "Farmer Providing Delivery",
                "body": "The farmer will arrange delivery for your order.",
                "data": {},
            },
        ]
        
        return RuleResult(
            success=True,
            transport_fee_payer="FARMER",
            transport_fee=quote["total_amount"],
            driver_assignment="AUTO_ASSIGNED",
            payment_allocations=[allocation],
            notifications=notifications,
        )
    
    async def _apply_self_pickup(
        self,
        order_id: uuid.UUID,
        transport_data: Dict[str, Any],
    ) -> RuleResult:
        """
        RULE 3: Buyer Self Pickup
        - No platform logistics fee
        - Buyer handles collection
        - Pickup code required
        - Geolocation verification enabled
        """
        logger.info(f"Applying Rule 3: Buyer Self Pickup for order {order_id}")
        
        # Generate pickup code
        pickup_code = self._generate_pickup_code()
        
        # Create notifications
        notifications = [
            {
                "user_type": "BUYER",
                "type": "PICKUP_CODE_GENERATED",
                "title": "Pickup Code Generated",
                "body": f"Your pickup code is: {pickup_code}. Show this to the farmer.",
                "data": {"pickup_code": pickup_code},
            },
            {
                "user_type": "FARMER",
                "type": "BUYER_SELF_PICKUP_SCHEDULED",
                "title": "Buyer Self Pickup Scheduled",
                "body": "The buyer will collect the order directly.",
                "data": {"pickup_code": pickup_code},
            },
        ]
        
        return RuleResult(
            success=True,
            transport_fee_payer=None,
            transport_fee=0.0,
            driver_assignment="NONE",
            payment_allocations=[],
            notifications=notifications,
        )
    
    async def _apply_self_delivery(
        self,
        order_id: uuid.UUID,
        transport_data: Dict[str, Any],
    ) -> RuleResult:
        """
        RULE 4: Farmer Self Delivery
        - Farmer handles transport
        - Buyer receives ETA updates
        - Delivery verification required
        """
        logger.info(f"Applying Rule 4: Farmer Self Delivery for order {order_id}")
        
        # Create notifications
        notifications = [
            {
                "user_type": "FARMER",
                "type": "SELF_DELIVERY_INITIATED",
                "title": "Self Delivery Initiated",
                "body": "You will deliver the order directly to the buyer.",
                "data": {},
            },
            {
                "user_type": "BUYER",
                "type": "FARMER_DELIVERING_DIRECTLY",
                "title": "Farmer Delivering Directly",
                "body": "The farmer will deliver your order directly.",
                "data": {},
            },
        ]
        
        return RuleResult(
            success=True,
            transport_fee_payer=None,
            transport_fee=0.0,
            driver_assignment="NONE",
            payment_allocations=[],
            notifications=notifications,
        )
    
    async def _apply_negotiated_transport(
        self,
        order_id: uuid.UUID,
        requested_by: str,
        transport_data: Dict[str, Any],
    ) -> RuleResult:
        """
        RULE 5: Negotiated Transport
        - Both parties can propose terms
        - Support split payment
        - Support price adjustment negotiations
        - Maintain immutable negotiation history
        - Require explicit agreement from both parties
        """
        logger.info(f"Applying Rule 5: Negotiated Transport for order {order_id}")
        
        # Calculate initial quote as starting point
        quote = await self._calculate_transport_quote(transport_data)
        
        # Set negotiation expiry (72 hours)
        expires_at = datetime.utcnow() + timedelta(hours=72)
        
        # Create notifications
        notifications = [
            {
                "user_type": "BUYER",
                "type": "NEGOTIATION_STARTED",
                "title": "Transport Negotiation Started",
                "body": f"Negotiation for transport fee (${quote['total_amount']:.2f}) has started. You have 72 hours to agree.",
                "data": {
                    "initial_quote": quote,
                    "expires_at": expires_at.isoformat(),
                },
            },
            {
                "user_type": "FARMER",
                "type": "NEGOTIATION_STARTED",
                "title": "Transport Negotiation Started",
                "body": f"Negotiation for transport fee (${quote['total_amount']:.2f}) has started. You have 72 hours to agree.",
                "data": {
                    "initial_quote": quote,
                    "expires_at": expires_at.isoformat(),
                },
            },
        ]
        
        return RuleResult(
            success=True,
            transport_fee_payer=None,  # To be determined by negotiation
            transport_fee=quote["total_amount"],  # Initial quote
            driver_assignment="PENDING",  # Assignment after negotiation
            payment_allocations=[],  # To be created after agreement
            notifications=notifications,
        )
    
    async def _apply_deferred_decision(
        self,
        order_id: uuid.UUID,
        requested_by: str,
        transport_data: Dict[str, Any],
    ) -> RuleResult:
        """
        RULE 6: Deferred Decision
        - Counterparty chooses transport method
        - System applies requester-pays principle
        - 48-hour deadline for counterparty decision
        - Auto-assignment if no decision
        """
        logger.info(f"Applying Rule 6: Deferred Decision for order {order_id}")
        
        # Set decision deadline (48 hours)
        decision_deadline = datetime.utcnow() + timedelta(hours=48)
        
        # Determine counterparty
        counterparty = "FARMER" if requested_by == "BUYER" else "BUYER"
        
        # Create notifications
        notifications = [
            {
                "user_type": counterparty,
                "type": "TRANSPORT_DECISION_REQUIRED",
                "title": "Transport Decision Required",
                "body": f"The other party deferred the transport decision. You have 48 hours to choose a transport method.",
                "data": {
                    "decision_deadline": decision_deadline.isoformat(),
                    "requested_by": requested_by,
                },
            },
            {
                "user_type": requested_by,
                "type": "TRANSPORT_DEFERRED",
                "title": "Transport Decision Deferred",
                "body": f"You have deferred the transport decision. The {counterparty.lower()} will choose within 48 hours.",
                "data": {
                    "decision_deadline": decision_deadline.isoformat(),
                },
            },
        ]
        
        return RuleResult(
            success=True,
            transport_fee_payer=None,  # To be determined by counterparty
            transport_fee=0.0,
            driver_assignment="PENDING",
            payment_allocations=[],
            notifications=notifications,
        )
    
    async def _calculate_transport_quote(
        self,
        transport_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate transport quote using pricing engine"""
        factors = PricingFactors(
            distance_km=transport_data.get("distance_km", 0),
            vehicle_type=transport_data.get("vehicle_type", "van"),
            cargo_weight_kg=transport_data.get("cargo_weight_kg", 0),
            cargo_volume_m3=transport_data.get("cargo_volume_m3"),
            urgency_level=transport_data.get("urgency_level", "STANDARD"),
            fuel_multiplier=transport_data.get("fuel_multiplier", 1.0),
            road_accessibility=transport_data.get("road_accessibility", "GOOD"),
            weather_risk=transport_data.get("weather_risk", "LOW"),
            rural_accessibility_score=transport_data.get("rural_accessibility_score", 1.0),
            driver_availability=transport_data.get("driver_availability", "HIGH"),
            peak_demand_multiplier=transport_data.get("peak_demand_multiplier", 1.0),
            pickup_latitude=transport_data.get("pickup_latitude"),
            pickup_longitude=transport_data.get("pickup_longitude"),
            delivery_latitude=transport_data.get("delivery_latitude"),
            delivery_longitude=transport_data.get("delivery_longitude"),
        )
        
        return transport_pricing_engine.calculate_quote(factors, self.db)
    
    def _generate_pickup_code(self) -> str:
        """Generate a 6-digit pickup code"""
        import random
        return f"{random.randint(100000, 999999)}"
    
    async def process_negotiation_agreement(
        self,
        negotiation_id: uuid.UUID,
        final_payer: str,  # 'BUYER', 'FARMER', or 'SPLIT'
        final_amount: float,
        split_ratio: Optional[Dict[str, float]] = None,
    ) -> RuleResult:
        """
        Process the final agreement from negotiation.
        Create payment allocations based on agreed terms.
        """
        logger.info(
            f"Processing negotiation agreement: {negotiation_id}, "
            f"payer={final_payer}, amount={final_amount}"
        )
        
        allocations = []
        
        if final_payer == "BUYER":
            allocations.append({
                "allocation_type": "TRANSPORT_FEE",
                "payer": "BUYER",
                "payee": "DRIVER",
                "amount": final_amount,
                "currency": "USD",
                "payment_method": "ESCROW",
            })
        elif final_payer == "FARMER":
            allocations.append({
                "allocation_type": "TRANSPORT_FEE",
                "payer": "FARMER",
                "payee": "DRIVER",
                "amount": final_amount,
                "currency": "USD",
                "payment_method": "ESCROW",
            })
        elif final_payer == "SPLIT" and split_ratio:
            buyer_share = final_amount * split_ratio.get("buyer", 0.5)
            farmer_share = final_amount * split_ratio.get("farmer", 0.5)
            
            allocations.append({
                "allocation_type": "TRANSPORT_FEE",
                "payer": "BUYER",
                "payee": "DRIVER",
                "amount": buyer_share,
                "currency": "USD",
                "payment_method": "ESCROW",
            })
            allocations.append({
                "allocation_type": "TRANSPORT_FEE",
                "payer": "FARMER",
                "payee": "DRIVER",
                "amount": farmer_share,
                "currency": "USD",
                "payment_method": "ESCROW",
            })
        
        return RuleResult(
            success=True,
            transport_fee_payer=final_payer,
            transport_fee=final_amount,
            driver_assignment="AUTO_ASSIGNED",
            payment_allocations=allocations,
            notifications=[],
        )
    
    async def handle_deferred_deadline_expiry(
        self,
        order_id: uuid.UUID,
        original_requester: str,
    ) -> RuleResult:
        """
        Handle expiry of deferred decision deadline.
        Auto-assign responsibility to counterparty.
        """
        logger.info(f"Handling deferred deadline expiry for order {order_id}")
        
        counterparty = "FARMER" if original_requester == "BUYER" else "BUYER"
        
        # Default to platform delivery by counterparty
        mode = (
            TransportMode.PLATFORM_DELIVERY_FARMER_REQUESTED
            if counterparty == "FARMER"
            else TransportMode.PLATFORM_DELIVERY_BUYER_REQUESTED
        )
        
        notifications = [
            {
                "user_type": counterparty,
                "type": "TRANSPORT_RESPONSIBILITY_ASSIGNED",
                "title": "Transport Responsibility Assigned",
                "body": f"The decision deadline has passed. Platform delivery has been assigned to you.",
                "data": {"mode": mode.value},
            },
            {
                "user_type": original_requester,
                "type": "TRANSPORT_AUTO_ASSIGNED",
                "title": "Transport Auto Assigned",
                "body": f"The {counterparty.lower()} has been assigned transport responsibility.",
                "data": {"mode": mode.value},
            },
        ]
        
        return RuleResult(
            success=True,
            transport_fee_payer=counterparty,
            transport_fee=0.0,  # Will be calculated
            driver_assignment="AUTO_ASSIGNED",
            payment_allocations=[],
            notifications=notifications,
        )


# ── Helper Functions ───────────────────────────────────────────────────────────

def validate_transport_mode(mode: str) -> bool:
    """Validate transport mode"""
    try:
        TransportMode(mode)
        return True
    except ValueError:
        return False


def validate_requested_by(requested_by: str) -> bool:
    """Validate requested_by value"""
    return requested_by in ["BUYER", "FARMER"]
