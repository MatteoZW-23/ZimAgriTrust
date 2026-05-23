"""
ZimAgritrust Transport Payment API
Implements the transport request, pricing, and payment responsibility endpoints.
Core Business Rule: WHOEVER REQUESTS TRANSPORT = WHO PAYS FOR TRANSPORT
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.models.transport import (
    TransportRequest,
    TransportQuote,
    TransportNegotiation,
    NegotiationMessage,
    DriverAssignment,
    Delivery,
    DeliveryTracking,
    PaymentAllocation,
    TransportMode as DBTransportMode,
    TransportRequestStatus,
    TransportQuoteStatus,
    NegotiationStatus as DBNegotiationStatus,
    MessageType,
    AssignmentStatus,
    DeliveryStatus,
    TrackingStatus,
    AllocationType,
    AllocationStatus,
)
from app.models.driver import Driver
from app.models.transaction import Order
from app.services.transport_pricing_service import (
    transport_pricing_engine,
    PricingFactors,
    get_vehicle_types,
    estimate_delivery_time,
)
from app.services.transport_rule_engine import (
    TransportRuleEngine,
    TransportMode,
    validate_transport_mode,
    validate_requested_by,
)
from app.services.notification_service import notification_service

router = APIRouter()


# ── Request/Response Schemas ─────────────────────────────────────────────────

class TransportRequestCreate(BaseModel):
    """Request to initiate transport"""
    order_id: uuid.UUID
    requested_by: str = Field(..., description="'BUYER' or 'FARMER'")
    mode: str = Field(..., description="Transport mode")
    
    # Pickup details
    pickup_address: str
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    pickup_contact_name: Optional[str] = None
    pickup_contact_phone: Optional[str] = None
    
    # Delivery details
    delivery_address: str
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    delivery_contact_name: Optional[str] = None
    delivery_contact_phone: Optional[str] = None
    
    # Cargo details
    cargo_weight_kg: float = Field(..., gt=0)
    cargo_volume_m3: Optional[float] = None
    cargo_description: Optional[str] = None
    special_handling: Optional[list[str]] = None
    
    # Timing
    preferred_pickup_time: Optional[datetime] = None
    preferred_delivery_time: Optional[datetime] = None
    urgency_level: str = Field(default="STANDARD", regex="^(STANDARD|URGENT|EXPEDITED)$")
    
    # Vehicle preferences
    preferred_vehicle_type: Optional[str] = None
    vehicle_requirements: Optional[list[str]] = None


class TransportQuoteRequest(BaseModel):
    """Request to calculate transport quote"""
    distance_km: float = Field(..., ge=0)
    vehicle_type: str = Field(..., regex="^(motorcycle|car|van|truck)$")
    cargo_weight_kg: float = Field(..., gt=0)
    cargo_volume_m3: Optional[float] = None
    urgency_level: str = Field(default="STANDARD", regex="^(STANDARD|URGENT|EXPEDITED)$")
    fuel_multiplier: float = Field(default=1.0, ge=0.5, le=2.0)
    road_accessibility: str = Field(default="GOOD", regex="^(EXCELLENT|GOOD|FAIR|POOR)$")
    weather_risk: str = Field(default="LOW", regex="^(LOW|MODERATE|HIGH|SEVERE)$")
    rural_accessibility_score: float = Field(default=1.0, ge=1.0, le=5.0)
    driver_availability: str = Field(default="HIGH", regex="^(HIGH|MEDIUM|LOW|CRITICAL)$")
    peak_demand_multiplier: float = Field(default=1.0, ge=1.0, le=2.0)
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None


class TransportAcceptPayload(BaseModel):
    """Accept transport request"""
    transport_request_id: uuid.UUID
    quote_id: Optional[uuid.UUID] = None


class TransportDeferPayload(BaseModel):
    """Defer transport decision"""
    transport_request_id: uuid.UUID
    reason: Optional[str] = None


class NegotiationOfferPayload(BaseModel):
    """Submit negotiation offer"""
    negotiation_id: uuid.UUID
    payer: str = Field(..., regex="^(BUYER|FARMER|SPLIT)$")
    amount: float = Field(..., gt=0)
    split_ratio: Optional[Dict[str, float]] = None  # For split payments: {"buyer": 0.6, "farmer": 0.4}
    message: Optional[str] = None


class NegotiationAcceptPayload(BaseModel):
    """Accept negotiation offer"""
    negotiation_id: uuid.UUID


# ── Transport Request Endpoints ────────────────────────────────────────────────

@router.post("/request")
async def request_transport(
    payload: TransportRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Request transport for an order.
    
    Core Business Rule: WHOEVER REQUESTS TRANSPORT = WHO PAYS FOR TRANSPORT
    
    This endpoint:
    1. Validates the transport request
    2. Applies the appropriate business rule based on mode
    3. Creates payment allocations
    4. Sends notifications to all parties
    """
    # Validate inputs
    if not validate_requested_by(payload.requested_by):
        raise HTTPException(status_code=400, detail="Invalid requested_by. Must be 'BUYER' or 'FARMER'")
    
    if not validate_transport_mode(payload.mode):
        raise HTTPException(status_code=400, detail="Invalid transport mode")
    
    # Verify user can make this request
    if payload.requested_by == "BUYER" and current_user.role != UserRole.BUYER:
        raise HTTPException(status_code=403, detail="Only buyers can request buyer-paid transport")
    
    if payload.requested_by == "FARMER" and current_user.role != UserRole.FARMER:
        raise HTTPException(status_code=403, detail="Only farmers can request farmer-paid transport")
    
    # Calculate distance if coordinates provided
    distance_km = 0.0
    if (payload.pickup_latitude and payload.pickup_longitude and
        payload.delivery_latitude and payload.delivery_longitude):
        distance_km = transport_pricing_engine.estimate_distance(
            payload.pickup_latitude,
            payload.pickup_longitude,
            payload.delivery_latitude,
            payload.delivery_longitude,
        )
    
    # Prepare transport data for rule engine
    transport_data = {
        "distance_km": distance_km,
        "vehicle_type": payload.preferred_vehicle_type or "van",
        "cargo_weight_kg": payload.cargo_weight_kg,
        "cargo_volume_m3": payload.cargo_volume_m3,
        "urgency_level": payload.urgency_level,
        "pickup_latitude": payload.pickup_latitude,
        "pickup_longitude": payload.pickup_longitude,
        "delivery_latitude": payload.delivery_latitude,
        "delivery_longitude": payload.delivery_longitude,
    }
    
    # Apply business rule
    rule_engine = TransportRuleEngine(db)
    result = await rule_engine.apply_rules(
        order_id=payload.order_id,
        requested_by=payload.requested_by,
        mode=TransportMode(payload.mode),
        transport_request_data=transport_data,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message or "Failed to process transport request")
    
    # Create transport_request record in database
    transport_request = TransportRequest(
        order_id=payload.order_id,
        requested_by=payload.requested_by,
        mode=DBTransportMode(payload.mode),
        pickup_address=payload.pickup_address,
        pickup_latitude=payload.pickup_latitude,
        pickup_longitude=payload.pickup_longitude,
        pickup_contact_name=payload.pickup_contact_name,
        pickup_contact_phone=payload.pickup_contact_phone,
        delivery_address=payload.delivery_address,
        delivery_latitude=payload.delivery_latitude,
        delivery_longitude=payload.delivery_longitude,
        delivery_contact_name=payload.delivery_contact_name,
        delivery_contact_phone=payload.delivery_contact_phone,
        cargo_weight=payload.cargo_weight_kg,
        cargo_volume=payload.cargo_volume_m3,
        cargo_description=payload.cargo_description,
        special_handling=payload.special_handling,
        preferred_pickup_time=payload.preferred_pickup_time,
        preferred_delivery_time=payload.preferred_delivery_time,
        urgency_level=payload.urgency_level,
        preferred_vehicle_type=payload.preferred_vehicle_type,
        vehicle_requirements=payload.vehicle_requirements,
        status=TransportRequestStatus.PRICED,
        created_by=current_user.id,
    )
    db.add(transport_request)
    db.flush()
    
    # Create payment_allocations records
    for allocation in result.payment_allocations:
        payment_allocation = PaymentAllocation(
            order_id=payload.order_id,
            transport_request_id=transport_request.id,
            allocation_type=AllocationType(allocation["allocation_type"]),
            payer=allocation["payer"],
            payee=allocation["payee"],
            amount=allocation["amount"],
            currency=allocation.get("currency", "USD"),
            status=AllocationStatus.PENDING,
        )
        db.add(payment_allocation)
    
    db.commit()
    
    # Send notifications
    for notification in result.notifications:
        await notification_service.send_notification(
            db=db,
            user_id=notification["user_id"],
            notification_type=notification["type"],
            title=notification["title"],
            body=notification["body"],
            data=notification.get("data", {}),
        )
    
    return {
        "success": True,
        "transport_fee_payer": result.transport_fee_payer,
        "transport_fee": result.transport_fee,
        "driver_assignment": result.driver_assignment,
        "payment_allocations": result.payment_allocations,
        "notifications_queued": len(result.notifications),
    }


@router.get("/status/{order_id}")
def get_transport_status(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current transport status for an order.
    """
    # Query transport_requests table
    transport_request = db.query(TransportRequest).filter(
        TransportRequest.order_id == order_id
    ).first()
    
    if not transport_request:
        raise HTTPException(status_code=404, detail="Transport request not found")
    
    # Return current status, mode, payer, fee
    return {
        "order_id": str(order_id),
        "status": transport_request.status.value,
        "mode": transport_request.mode.value,
        "transport_fee_payer": transport_request.requested_by if transport_request.mode in [DBTransportMode.PLATFORM_DELIVERY_BUYER_REQUESTED, DBTransportMode.PLATFORM_DELIVERY_FARMER_REQUESTED] else None,
        "transport_fee": 0.0,  # Would need to calculate from payment_allocations
        "driver_assigned": db.query(DriverAssignment).filter(
            DriverAssignment.transport_request_id == transport_request.id,
            DriverAssignment.status == AssignmentStatus.ACCEPTED
        ).first() is not None,
    }


@router.post("/accept")
async def accept_transport(
    payload: TransportAcceptPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept a transport request with a specific quote.
    """
    # Validate transport_request exists
    transport_request = db.query(TransportRequest).filter(
        TransportRequest.id == payload.transport_request_id
    ).first()
    
    if not transport_request:
        raise HTTPException(status_code=404, detail="Transport request not found")
    
    # Validate quote exists and is valid
    if payload.quote_id:
        quote = db.query(TransportQuote).filter(
            TransportQuote.id == payload.quote_id,
            TransportQuote.transport_request_id == payload.transport_request_id,
            TransportQuote.status == TransportQuoteStatus.ACTIVE
        ).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found or expired")
        
        if quote.valid_until < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Quote has expired")
    
    # Update transport_request status to ACCEPTED
    transport_request.status = TransportRequestStatus.ACCEPTED
    transport_request.decision_made_at = datetime.utcnow()
    transport_request.decision_made_by = current_user.role.value
    
    # Create payment allocations
    if payload.quote_id:
        payment_allocation = PaymentAllocation(
            order_id=transport_request.order_id,
            transport_request_id=transport_request.id,
            allocation_type=AllocationType.TRANSPORT_FEE,
            payer=transport_request.requested_by,
            payee="PLATFORM",
            amount=quote.total_amount,
            currency=quote.currency,
            status=AllocationStatus.HELD,
        )
        db.add(payment_allocation)
    
    # Trigger driver assignment if platform delivery
    if transport_request.mode in [DBTransportMode.PLATFORM_DELIVERY_BUYER_REQUESTED, DBTransportMode.PLATFORM_DELIVERY_FARMER_REQUESTED]:
        # Auto-assign driver (simplified - in production would use driver matching algorithm)
        available_driver = db.query(Driver).filter(
            Driver.status == "active",
            Driver.vehicle_capacity_kg >= transport_request.cargo_weight
        ).first()
        
        if available_driver:
            driver_assignment = DriverAssignment(
                transport_request_id=transport_request.id,
                driver_id=available_driver.id,
                assigned_by="AUTO",
                status=AssignmentStatus.ASSIGNED,
                vehicle_type=transport_request.preferred_vehicle_type or "van",
                vehicle_registration=available_driver.vehicle_reg,
                transport_fee=quote.total_amount if payload.quote_id else 0.0,
                driver_earnings=quote.total_amount * 0.8 if payload.quote_id else 0.0,
                platform_commission=quote.total_amount * 0.2 if payload.quote_id else 0.0,
            )
            db.add(driver_assignment)
    
    db.commit()
    
    # Send notifications
    await notification_service.send_notification(
        db=db,
        user_id=current_user.id,
        notification_type="transport_accepted",
        title="Transport Request Accepted",
        body="Your transport request has been accepted.",
        data={"transport_request_id": str(payload.transport_request_id)},
    )
    
    return {
        "success": True,
        "message": "Transport request accepted",
    }


@router.post("/defer")
async def defer_transport(
    payload: TransportDeferPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Defer transport decision to counterparty.
    """
    # Validate transport_request exists
    transport_request = db.query(TransportRequest).filter(
        TransportRequest.id == payload.transport_request_id
    ).first()
    
    if not transport_request:
        raise HTTPException(status_code=404, detail="Transport request not found")
    
    # Update transport_request mode to DEFERRED
    transport_request.mode = DBTransportMode.DEFERRED
    transport_request.decision_deadline = datetime.utcnow() + timedelta(hours=48)
    transport_request.status = TransportRequestStatus.PENDING
    
    db.commit()
    
    # Notify counterparty
    order = db.query(Order).filter(Order.id == transport_request.order_id).first()
    if order:
        counterparty_id = order.buyer_id if transport_request.requested_by == "FARMER" else order.seller_id
        await notification_service.send_notification(
            db=db,
            user_id=counterparty_id,
            notification_type="transport_deferred",
            title="Transport Decision Deferred",
            body=f"Transport decision has been deferred. Please respond within 48 hours.",
            data={"transport_request_id": str(payload.transport_request_id)},
        )
    
    # Schedule deadline check (would use Celery in production)
    
    return {
        "success": True,
        "message": "Transport decision deferred",
        "decision_deadline": (datetime.utcnow() + timedelta(hours=48)).isoformat(),
    }


# ── Pricing Endpoints ───────────────────────────────────────────────────────

@router.post("/calculate")
def calculate_transport_fee(
    payload: TransportQuoteRequest,
):
    """
    Calculate transport fee based on pricing factors.
    Returns complete breakdown with all components.
    """
    factors = PricingFactors(
        distance_km=payload.distance_km,
        vehicle_type=payload.vehicle_type,
        cargo_weight_kg=payload.cargo_weight_kg,
        cargo_volume_m3=payload.cargo_volume_m3,
        urgency_level=payload.urgency_level,
        fuel_multiplier=payload.fuel_multiplier,
        road_accessibility=payload.road_accessibility,
        weather_risk=payload.weather_risk,
        rural_accessibility_score=payload.rural_accessibility_score,
        driver_availability=payload.driver_availability,
        peak_demand_multiplier=payload.peak_demand_multiplier,
        pickup_latitude=payload.pickup_latitude,
        pickup_longitude=payload.pickup_longitude,
        delivery_latitude=payload.delivery_latitude,
        delivery_longitude=payload.delivery_longitude,
    )
    
    quote = transport_pricing_engine.calculate_quote(factors)
    
    # Calculate estimated delivery time
    delivery_time = estimate_delivery_time(
        payload.distance_km,
        payload.vehicle_type,
        payload.urgency_level,
    )
    
    return {
        **quote,
        "estimated_delivery_time": delivery_time,
    }


@router.get("/vehicles")
def get_available_vehicles():
    """
    Get available vehicle types with pricing information.
    """
    return {
        "vehicles": get_vehicle_types(),
    }


@router.post("/estimate-distance")
def estimate_distance(
    pickup_lat: float,
    pickup_lon: float,
    delivery_lat: float,
    delivery_lon: float,
):
    """
    Estimate distance between two points using Haversine formula.
    In production, this would use Google Maps Distance Matrix API.
    """
    distance_km = transport_pricing_engine.estimate_distance(
        pickup_lat, pickup_lon, delivery_lat, delivery_lon
    )
    
    return {
        "distance_km": distance_km,
        "pickup": {"latitude": pickup_lat, "longitude": pickup_lon},
        "delivery": {"latitude": delivery_lat, "longitude": delivery_lon},
    }


# ── Negotiation Endpoints ────────────────────────────────────────────────────

@router.post("/negotiations/start")
async def start_negotiation(
    order_id: uuid.UUID,
    initial_offer: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a transport fee negotiation.
    """
    # Validate order exists and is in appropriate state
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Determine counterparty
    counterparty_id = order.buyer_id if current_user.id == order.seller_id else order.seller_id
    
    # Create transport_negotiation record
    negotiation = TransportNegotiation(
        order_id=order_id,
        initiator_id=current_user.id,
        counterparty_id=counterparty_id,
        status=DBNegotiationStatus.INITIATED,
        expires_at=datetime.utcnow() + timedelta(hours=72),
    )
    
    if initial_offer:
        negotiation.final_amount = initial_offer
        negotiation.final_payer = current_user.role.value if current_user.role in [UserRole.BUYER, UserRole.FARMER] else "BUYER"
    
    db.add(negotiation)
    db.flush()
    
    # Create initial system message with quote
    if initial_offer:
        message = NegotiationMessage(
            negotiation_id=negotiation.id,
            sender_id=current_user.id,
            message_type=MessageType.OFFER,
            content=f"Initial offer: ${initial_offer}",
            structured_offer={"amount": initial_offer, "payer": negotiation.final_payer},
        )
        db.add(message)
    
    db.commit()
    
    # Send notifications to both parties
    await notification_service.send_notification(
        db=db,
        user_id=counterparty_id,
        notification_type="transport_negotiation_started",
        title="Transport Fee Negotiation Started",
        body="A transport fee negotiation has been initiated.",
        data={"negotiation_id": str(negotiation.id)},
    )
    
    return {
        "success": True,
        "negotiation_id": str(negotiation.id),
        "expires_at": negotiation.expires_at.isoformat(),
    }


@router.post("/negotiations/offer")
async def submit_negotiation_offer(
    payload: NegotiationOfferPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a counter-offer in transport negotiation.
    """
    # Validate negotiation exists and is active
    negotiation = db.query(TransportNegotiation).filter(
        TransportNegotiation.id == payload.negotiation_id
    ).first()
    
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    
    if negotiation.status not in [DBNegotiationStatus.INITIATED, DBNegotiationStatus.COUNTER_OFFER]:
        raise HTTPException(status_code=400, detail="Negotiation is not active")
    
    if negotiation.expires_at < datetime.utcnow():
        negotiation.status = DBNegotiationStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=400, detail="Negotiation has expired")
    
    # Create negotiation_message record
    message = NegotiationMessage(
        negotiation_id=negotiation.id,
        sender_id=current_user.id,
        message_type=MessageType.COUNTER_OFFER if payload.message else MessageType.OFFER,
        content=payload.message or f"Offer: ${payload.amount} by {payload.payer}",
        structured_offer={
            "payer": payload.payer,
            "amount": payload.amount,
            "split_ratio": payload.split_ratio,
        },
    )
    db.add(message)
    
    # Update negotiation status
    negotiation.status = DBNegotiationStatus.COUNTER_OFFER
    negotiation.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Notify counterparty
    await notification_service.send_notification(
        db=db,
        user_id=negotiation.counterparty_id if current_user.id == negotiation.initiator_id else negotiation.initiator_id,
        notification_type="transport_negotiation_offer",
        title="New Offer in Transport Negotiation",
        body="A new offer has been submitted.",
        data={"negotiation_id": str(negotiation.id)},
    )
    
    return {
        "success": True,
        "message": "Offer submitted",
    }


@router.post("/negotiations/accept")
async def accept_negotiation(
    payload: NegotiationAcceptPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept the current negotiation offer.
    """
    # Validate negotiation exists and is active
    negotiation = db.query(TransportNegotiation).filter(
        TransportNegotiation.id == payload.negotiation_id
    ).first()
    
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    
    if negotiation.status not in [DBNegotiationStatus.INITIATED, DBNegotiationStatus.COUNTER_OFFER]:
        raise HTTPException(status_code=400, detail="Negotiation is not active")
    
    # Create acceptance message
    message = NegotiationMessage(
        negotiation_id=negotiation.id,
        sender_id=current_user.id,
        message_type=MessageType.ACCEPTANCE,
        content="Offer accepted",
    )
    db.add(message)
    
    # Check if both parties have accepted (simplified - in production would track acceptances per party)
    # For now, mark as accepted and process
    negotiation.status = DBNegotiationStatus.ACCEPTED
    negotiation.completed_at = datetime.utcnow()
    
    # If both accepted, process agreement
    if negotiation.final_amount and negotiation.final_payer:
        # Create payment allocations
        payment_allocation = PaymentAllocation(
            order_id=negotiation.order_id,
            allocation_type=AllocationType.TRANSPORT_FEE,
            payer=negotiation.final_payer,
            payee="PLATFORM",
            amount=negotiation.final_amount,
            status=AllocationStatus.PENDING,
        )
        db.add(payment_allocation)
        
        # Trigger driver assignment if platform delivery
        transport_request = db.query(TransportRequest).filter(
            TransportRequest.order_id == negotiation.order_id
        ).first()
        
        if transport_request and transport_request.mode in [DBTransportMode.PLATFORM_DELIVERY_BUYER_REQUESTED, DBTransportMode.PLATFORM_DELIVERY_FARMER_REQUESTED]:
            available_driver = db.query(Driver).filter(
                Driver.status == "active"
            ).first()
            
            if available_driver:
                driver_assignment = DriverAssignment(
                    transport_request_id=transport_request.id,
                    driver_id=available_driver.id,
                    assigned_by="AUTO",
                    status=AssignmentStatus.ASSIGNED,
                    vehicle_type=transport_request.preferred_vehicle_type or "van",
                    vehicle_registration=available_driver.vehicle_reg,
                    transport_fee=negotiation.final_amount,
                    driver_earnings=negotiation.final_amount * 0.8,
                    platform_commission=negotiation.final_amount * 0.2,
                )
                db.add(driver_assignment)
    
    db.commit()
    
    # Send notifications
    await notification_service.send_notification(
        db=db,
        user_id=negotiation.counterparty_id if current_user.id == negotiation.initiator_id else negotiation.initiator_id,
        notification_type="transport_negotiation_accepted",
        title="Transport Negotiation Accepted",
        body="The transport fee negotiation has been accepted.",
        data={"negotiation_id": str(negotiation.id)},
    )
    
    return {
        "success": True,
        "message": "Negotiation accepted",
    }


@router.get("/negotiations/{negotiation_id}")
def get_negotiation(
    negotiation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get negotiation details and message history.
    """
    # Query transport_negotiations table
    negotiation = db.query(TransportNegotiation).filter(
        TransportNegotiation.id == negotiation_id
    ).first()
    
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    
    # Query negotiation_messages table
    messages = db.query(NegotiationMessage).filter(
        NegotiationMessage.negotiation_id == negotiation_id
    ).order_by(NegotiationMessage.created_at).all()
    
    # Return negotiation state and messages
    return {
        "negotiation_id": str(negotiation.id),
        "status": negotiation.status.value,
        "initiator_id": str(negotiation.initiator_id),
        "counterparty_id": str(negotiation.counterparty_id),
        "final_payer": negotiation.final_payer,
        "final_amount": float(negotiation.final_amount) if negotiation.final_amount else None,
        "split_ratio": negotiation.split_ratio,
        "expires_at": negotiation.expires_at.isoformat() if negotiation.expires_at else None,
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


# ── Driver Assignment Endpoints ───────────────────────────────────────────────

@router.post("/drivers/assign")
async def assign_driver(
    transport_request_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Manually assign a driver to a transport request (admin only).
    """
    # Validate transport_request exists
    transport_request = db.query(TransportRequest).filter(
        TransportRequest.id == transport_request_id
    ).first()
    
    if not transport_request:
        raise HTTPException(status_code=404, detail="Transport request not found")
    
    # Find available driver
    available_driver = db.query(Driver).filter(
        Driver.status == "active",
        Driver.vehicle_capacity_kg >= transport_request.cargo_weight
    ).first()
    
    if not available_driver:
        raise HTTPException(status_code=404, detail="No available drivers found")
    
    # Create driver_assignment record
    driver_assignment = DriverAssignment(
        transport_request_id=transport_request.id,
        driver_id=available_driver.id,
        assigned_by="MANUAL",
        assigned_by_user_id=_.id,
        status=AssignmentStatus.ASSIGNED,
        vehicle_type=transport_request.preferred_vehicle_type or "van",
        vehicle_registration=available_driver.vehicle_reg,
        transport_fee=0.0,  # Would calculate from transport_request
        driver_earnings=0.0,
        platform_commission=0.0,
    )
    db.add(driver_assignment)
    
    # Update transport_request status
    transport_request.status = TransportRequestStatus.ASSIGNED
    
    db.commit()
    
    # Notify driver
    await notification_service.send_notification(
        db=db,
        user_id=available_driver.user_id,
        notification_type="driver_assignment",
        title="New Driver Assignment",
        body="You have been assigned to a new transport request.",
        data={"transport_request_id": str(transport_request_id)},
    )
    
    # Notify buyer/farmer
    order = db.query(Order).filter(Order.id == transport_request.order_id).first()
    if order:
        await notification_service.send_notification(
            db=db,
            user_id=order.buyer_id,
            notification_type="driver_assigned",
            title="Driver Assigned",
            body="A driver has been assigned to your order.",
            data={"transport_request_id": str(transport_request_id)},
        )
        await notification_service.send_notification(
            db=db,
            user_id=order.seller_id,
            notification_type="driver_assigned",
            title="Driver Assigned",
            body="A driver has been assigned to your order.",
            data={"transport_request_id": str(transport_request_id)},
        )
    
    return {
        "success": True,
        "message": "Driver assigned",
    }


@router.get("/drivers/available")
def get_available_drivers(
    pickup_latitude: float,
    pickup_longitude: float,
    required_capacity_kg: float,
    vehicle_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Get available drivers near pickup location (admin only).
    """
    # Query drivers table for available drivers
    drivers_query = db.query(Driver).filter(
        Driver.status == "active",
        Driver.vehicle_capacity_kg >= required_capacity_kg
    )
    
    # Filter by vehicle type if specified
    if vehicle_type:
        drivers_query = drivers_query.filter(Driver.vehicle_type == vehicle_type)
    
    # Filter by location (simplified - in production would use geospatial query)
    # Sort by rating and distance
    drivers = drivers_query.order_by(Driver.avg_rating.desc()).limit(20).all()
    
    # Return list of available drivers
    return {
        "drivers": [
            {
                "id": str(driver.id),
                "user_id": str(driver.user_id),
                "vehicle_reg": driver.vehicle_reg,
                "vehicle_type": driver.vehicle_type,
                "vehicle_capacity_kg": driver.vehicle_capacity_kg,
                "avg_rating": driver.avg_rating,
                "total_deliveries": driver.total_deliveries,
                "current_district": driver.current_district,
            }
            for driver in drivers
        ],
    }


# ── Delivery Endpoints ───────────────────────────────────────────────────────

@router.post("/delivery/confirm-pickup")
async def confirm_pickup(
    delivery_id: uuid.UUID,
    pickup_code: Optional[str] = None,
    photo_url: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirm pickup by driver.
    """
    # Validate delivery exists
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # Verify pickup code if provided
    if pickup_code and delivery.pickup_code != pickup_code:
        raise HTTPException(status_code=400, detail="Invalid pickup code")
    
    # Update delivery status to PICKED_UP
    delivery.status = DeliveryStatus.PICKED_UP
    delivery.pickup_confirmed_at = datetime.utcnow()
    delivery.pickup_confirmed_by = current_user.id
    delivery.pickup_photo_url = photo_url
    
    db.commit()
    
    # Notify buyer/farmer
    order = db.query(Order).filter(Order.id == delivery.order_id).first()
    if order:
        await notification_service.send_notification(
            db=db,
            user_id=order.buyer_id,
            notification_type="pickup_confirmed",
            title="Pickup Confirmed",
            body="Your order has been picked up by the driver.",
            data={"delivery_id": str(delivery_id)},
        )
        await notification_service.send_notification(
            db=db,
            user_id=order.seller_id,
            notification_type="pickup_confirmed",
            title="Pickup Confirmed",
            body="Your order has been picked up by the driver.",
            data={"delivery_id": str(delivery_id)},
        )
    
    # Start tracking (tracking points will be added via location updates)
    
    return {
        "success": True,
        "message": "Pickup confirmed",
    }


@router.post("/delivery/confirm-delivery")
async def confirm_delivery(
    delivery_id: uuid.UUID,
    delivery_code: Optional[str] = None,
    photo_url: Optional[str] = None,
    signature_url: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirm delivery by driver.
    """
    # Validate delivery exists
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # Verify delivery code if provided
    if delivery_code and delivery.delivery_code != delivery_code:
        raise HTTPException(status_code=400, detail="Invalid delivery code")
    
    # Update delivery status to DELIVERED
    delivery.status = DeliveryStatus.DELIVERED
    delivery.delivery_confirmed_at = datetime.utcnow()
    delivery.delivery_confirmed_by = current_user.id
    delivery.delivery_photo_url = photo_url
    delivery.delivery_signature_url = signature_url
    delivery.proof_of_delivery_url = photo_url
    delivery.actual_arrival_time = datetime.utcnow()
    
    # Complete driver assignment
    if delivery.driver_assignment:
        delivery.driver_assignment.status = AssignmentStatus.COMPLETED
        delivery.driver_assignment.completed_at = datetime.utcnow()
    
    db.commit()
    
    # Trigger payment settlement (simplified - would use payment service)
    # This would release held payments and create settlements
    
    # Notify buyer/farmer
    order = db.query(Order).filter(Order.id == delivery.order_id).first()
    if order:
        await notification_service.send_notification(
            db=db,
            user_id=order.buyer_id,
            notification_type="delivery_confirmed",
            title="Delivery Confirmed",
            body="Your order has been delivered successfully.",
            data={"delivery_id": str(delivery_id)},
        )
        await notification_service.send_notification(
            db=db,
            user_id=order.seller_id,
            notification_type="delivery_confirmed",
            title="Delivery Confirmed",
            body="Your order has been delivered successfully.",
            data={"delivery_id": str(delivery_id)},
        )
    
    # Notify driver
    if delivery.driver_assignment:
        await notification_service.send_notification(
            db=db,
            user_id=delivery.driver_assignment.driver.user_id,
            notification_type="delivery_completed",
            title="Delivery Completed",
            body="The delivery has been completed successfully.",
            data={"delivery_id": str(delivery_id)},
        )
    
    return {
        "success": True,
        "message": "Delivery confirmed",
    }


@router.post("/delivery/dispute")
async def raise_delivery_dispute(
    delivery_id: uuid.UUID,
    dispute_type: str,
    description: str,
    disputed_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Raise a dispute for a delivery.
    """
    # Validate delivery exists
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # Create dispute record
    from app.models.transport import TransportDispute
    
    dispute = TransportDispute(
        order_id=delivery.order_id,
        delivery_id=delivery.id,
        raised_by=current_user.id,
        dispute_type=dispute_type,
        category="DELIVERY",
        title=f"Delivery Dispute - {dispute_type}",
        description=description,
        disputed_amount=disputed_amount,
        status=TransportDisputeStatus.OPEN,
        response_due_at=datetime.utcnow() + timedelta(hours=48),
    )
    db.add(dispute)
    db.flush()
    
    # Update delivery status
    delivery.status = DeliveryStatus.DISPUTED
    
    db.commit()
    
    # Notify admin
    admin_users = db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])).all()
    for admin in admin_users:
        await notification_service.send_notification(
            db=db,
            user_id=admin.id,
            notification_type="dispute_raised",
            title="New Delivery Dispute",
            body=f"A delivery dispute has been raised: {dispute_type}",
            data={"dispute_id": str(dispute.id)},
        )
    
    # Notify counterparty
    order = db.query(Order).filter(Order.id == delivery.order_id).first()
    if order:
        counterparty_id = order.buyer_id if current_user.id == order.seller_id else order.seller_id
        await notification_service.send_notification(
            db=db,
            user_id=counterparty_id,
            notification_type="dispute_raised",
            title="Delivery Dispute Raised",
            body="A dispute has been raised regarding your delivery.",
            data={"dispute_id": str(dispute.id)},
        )
    
    # Hold payment in escrow (would update payment allocations status to HELD)
    
    return {
        "success": True,
        "dispute_id": str(uuid.uuid4()),
        "message": "Dispute raised",
    }

dispte
# ── Tracking Endpoints ───────────────────────────────────────────────────────

@router.post("/tracking/location")
async def update_driver_location(
    delivery_id: uuid.UUID,
    latitude: float,
    longitude: float,
    accuracy_meters: Optional[float] = None,
    speed_kmh: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update driver location for real-time tracking.
    """
    # Validate delivery exists
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # Get driver from delivery
    driver_id = None
    if delivery.driver_assignment:
        driver_id = delivery.driver_assignment.driver_id
    
    if not driver_id:
        raise HTTPException(status_code=400, detail="No driver assigned to this delivery")
    
    # Create delivery_tracking record
    tracking_point = DeliveryTracking(
        delivery_id=delivery.id,
        driver_id=driver_id,
        latitude=latitude,
        longitude=longitude,
        accuracy_meters=accuracy_meters,
        speed_kmh=speed_kmh,
        status=TrackingStatus.MOVING if speed_kmh and speed_kmh > 0 else TrackingStatus.STOPPED,
    )
    db.add(tracking_point)
    
    # Update delivery current location
    delivery.current_latitude = latitude
    delivery.current_longitude = longitude
    delivery.last_location_update_at = datetime.utcnow()
    
    db.commit()
    
    # Calculate ETA if needed (simplified - would use routing service)
    # Notify buyer/farmer of location update
    order = db.query(Order).filter(Order.id == delivery.order_id).first()
    if order:
        await notification_service.send_notification(
            db=db,
            user_id=order.buyer_id,
            notification_type="location_update",
            title="Driver Location Updated",
            body="Your driver's location has been updated.",
            data={"delivery_id": str(delivery_id), "latitude": latitude, "longitude": longitude},
        )
    
    return {
        "success": True,
        "message": "Location updated",
    }


@router.get("/tracking/{delivery_id}")
def get_tracking_history(
    delivery_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get tracking history for a delivery.
    """
    # Query delivery_tracking table
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    tracking_points = db.query(DeliveryTracking).filter(
        DeliveryTracking.delivery_id == delivery_id
    ).order_by(DeliveryTracking.recorded_at).limit(100).all()
    
    # Return location history with timestamps
    return {
        "delivery_id": str(delivery_id),
        "tracking_points": [
            {
                "id": str(point.id),
                "latitude": float(point.latitude),
                "longitude": float(point.longitude),
                "accuracy_meters": float(point.accuracy_meters) if point.accuracy_meters else None,
                "speed_kmh": float(point.speed_kmh) if point.speed_kmh else None,
                "status": point.status.value,
                "recorded_at": point.recorded_at.isoformat(),
            }
            for point in tracking_points
        ],
    }
    
    return {
        "delivery_id": str(delivery_id),
        "tracking_points": [],
