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
    
    # TODO: Create transport_request record in database
    # TODO: Create payment_allocations records
    # TODO: Send notifications
    
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
    # TODO: Query transport_requests table
    # TODO: Return current status, mode, payer, fee
    
    return {
        "order_id": str(order_id),
        "status": "PENDING",
        "mode": None,
        "transport_fee_payer": None,
        "transport_fee": 0.0,
        "driver_assigned": False,
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
    # TODO: Validate transport_request exists
    # TODO: Validate quote exists and is valid
    # TODO: Update transport_request status to ACCEPTED
    # TODO: Create payment allocations
    # TODO: Trigger driver assignment if platform delivery
    # TODO: Send notifications
    
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
    # TODO: Validate transport_request exists
    # TODO: Update transport_request mode to DEFERRED
    # TODO: Set decision deadline (48 hours)
    # TODO: Notify counterparty
    # TODO: Schedule deadline check
    
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
    # TODO: Validate order exists and is in appropriate state
    # TODO: Create transport_negotiation record
    # TODO: Set expiry (72 hours)
    # TODO: Send notifications to both parties
    # TODO: Return negotiation ID
    
    return {
        "success": True,
        "negotiation_id": str(uuid.uuid4()),
        "expires_at": (datetime.utcnow() + timedelta(hours=72)).isoformat(),
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
    # TODO: Validate negotiation exists and is active
    # TODO: Create negotiation_message record
    # TODO: Update negotiation status if needed
    # TODO: Notify counterparty
    # TODO: Check for agreement (both parties accepted same terms)
    
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
    # TODO: Validate negotiation exists and is active
    # TODO: Check if both parties have accepted
    # TODO: If both accepted, process agreement
    # TODO: Create payment allocations
    # TODO: Trigger driver assignment
    # TODO: Send notifications
    
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
    # TODO: Query transport_negotiations table
    # TODO: Query negotiation_messages table
    # TODO: Return negotiation state and messages
    
    return {
        "negotiation_id": str(negotiation_id),
        "status": "INITIATED",
        "messages": [],
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
    # TODO: Validate transport_request exists
    # TODO: Find available driver
    # TODO: Create driver_assignment record
    # TODO: Update transport_request status
    # TODO: Notify driver
    # TODO: Notify buyer/farmer
    
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
    # TODO: Query drivers table for available drivers
    # TODO: Filter by location, capacity, vehicle type
    # TODO: Sort by rating and distance
    # TODO: Return list of available drivers
    
    return {
        "drivers": [],
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
    # TODO: Validate delivery exists
    # TODO: Verify pickup code if provided
    # TODO: Update delivery status to PICKED_UP
    # TODO: Record pickup photo
    # TODO: Notify buyer/farmer
    # TODO: Start tracking
    
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
    # TODO: Validate delivery exists
    # TODO: Verify delivery code if provided
    # TODO: Update delivery status to DELIVERED
    # TODO: Record proof of delivery
    # TODO: Trigger payment settlement
    # TODO: Notify buyer/farmer
    # TODO: Notify driver
    
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
    # TODO: Validate delivery exists
    # TODO: Create dispute record
    # TODO: Link to delivery
    # TODO: Notify admin
    # TODO: Notify counterparty
    # TODO: Hold payment in escrow
    
    return {
        "success": True,
        "dispute_id": str(uuid.uuid4()),
        "message": "Dispute raised",
    }


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
    # TODO: Validate delivery exists
    # TODO: Create delivery_tracking record
    # TODO: Update delivery current location
    # TODO: Calculate ETA if needed
    # TODO: Notify buyer/farmer of location update
    
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
    # TODO: Query delivery_tracking table
    # TODO: Return location history
    # TODO: Include timestamps
    
    return {
        "delivery_id": str(delivery_id),
        "tracking_points": [],
    }
