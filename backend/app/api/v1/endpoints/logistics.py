"""
ZimAgritrust Logistics & Delivery API
Covers: trip marketplace, delivery lifecycle (9 states), agent/driver assignment.
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from sqlalchemy import desc
from app.api.deps import get_current_user, get_db, require_roles
from app.models.logistics import DeliveryMethod, LogisticsTrip, OrderDelivery
from app.models.user import User, UserRole
from app.models.transaction import Order
from app.models.driver import DriverJob
from app.schemas.logistics import LogisticsTripCreate, LogisticsTripResponse, TripManifest
from app.services.logistics_service import LogisticsService
import app.services.delivery_service as delivery_svc

router = APIRouter()
admin_router = APIRouter()

# ── Admin Fleet & Logistics Management ─────────────────────────────────────────

@admin_router.get("/requests")
def get_transport_requests(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    orders = db.query(Order).order_by(desc(Order.created_at)).limit(limit).all()
    return {
        "items": [
            {
                "id": str(o.id),
                "order_id": str(o.id),
                "status": o.status,
                "created_at": o.created_at,
                "buyer_id": o.buyer_id,
                "farmer_id": o.farmer_id,
                "transport_fee": o.transport_fee,
            }
            for o in orders
        ],
        "total": len(orders)
    }

@admin_router.get("/negotiations")
def get_transport_negotiations(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    return {"items": [], "total": 0}

@admin_router.get("/driver-assignments")
def get_driver_assignments(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    jobs = db.query(DriverJob).order_by(desc(DriverJob.created_at)).limit(limit).all()
    return {
        "items": [
            {
                "id": str(j.id),
                "driver_id": str(j.driver_id),
                "order_id": str(j.order_id),
                "status": j.status,
                "payout": j.driver_payout,
                "created_at": j.created_at,
            }
            for j in jobs
        ],
        "total": len(jobs)
    }

@admin_router.get("/disputes")
def get_transport_disputes(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    return {"items": [], "total": 0}



# ── Trip Marketplace ───────────────────────────────────────────────────────────

@router.get("/trips", response_model=list[LogisticsTripResponse])
def list_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(LogisticsTrip).all()


@router.post("/trips", response_model=LogisticsTripResponse)
def create_trip(
    payload: LogisticsTripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    trip = LogisticsTrip(driver_id=current_user.id, **payload.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.get("/trips/{trip_id}/manifest", response_model=TripManifest)
def get_manifest(
    trip_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    items = LogisticsService.get_trip_load_manifest(db, str(trip_id))
    return {"trip_id": trip_id, "items": items}


# ── Delivery Lifecycle ─────────────────────────────────────────────────────────

class SetMethodPayload(BaseModel):
    method: DeliveryMethod
    pickup_address: Optional[str] = None
    delivery_address: Optional[str] = None
    pickup_scheduled_at: Optional[datetime] = None

    @field_validator("method", mode="before")
    @classmethod
    def normalize_method(cls, value):
        if value == "PLATFORM":
            return DeliveryMethod.THIRD_PARTY
        return value


class AssignAgentPayload(BaseModel):
    agent_id: uuid.UUID


class AssignDriverPayload(BaseModel):
    driver_id: Optional[uuid.UUID] = None
    driver_name: Optional[str] = None
    vehicle_reg: Optional[str] = None


class ConfirmPickupPayload(BaseModel):
    photos: Optional[list] = []
    gps_verified: bool = False
    estimated_arrival_at: Optional[datetime] = None


class ConfirmDeliveryPayload(BaseModel):
    photos: Optional[list] = []
    gps_verified: bool = False


class DelayPayload(BaseModel):
    new_eta: Optional[datetime] = None


@router.get("/orders/{order_id}/delivery")
def get_delivery_status(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current delivery status and details for an order."""
    d = delivery_svc.get_delivery(db, order_id)
    return {
        "order_id": str(d.order_id),
        "status": d.status,
        "method": d.method,
        "pickup_scheduled_at": d.pickup_scheduled_at,
        "estimated_arrival_at": d.estimated_arrival_at,
        "delivered_at": d.delivered_at,
        "confirmed_at": d.confirmed_at,
        "inspection_deadline": d.inspection_deadline,
        "pickup_address": d.pickup_address,
        "delivery_address": d.delivery_address,
        "pickup_gps_verified": d.pickup_gps_verified,
        "delivery_gps_verified": d.delivery_gps_verified,
        "pickup_photos": d.pickup_photos or [],
        "delivery_photos": d.delivery_photos or [],
        "driver_name": d.driver_name,
        "vehicle_reg": d.vehicle_reg,
        "notes": d.notes,
    }


@router.post("/orders/{order_id}/delivery/method")
def set_delivery_method(
    order_id: uuid.UUID,
    payload: SetMethodPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Step 2 — Buyer or farmer selects delivery method."""
    d = delivery_svc.set_delivery_method(
        db, order_id,
        method=payload.method,
        pickup_address=payload.pickup_address,
        delivery_address=payload.delivery_address,
        pickup_scheduled_at=payload.pickup_scheduled_at,
    )
    return {"status": d.status, "method": d.method}


@router.post("/orders/{order_id}/delivery/assign-agent")
def assign_agent(
    order_id: uuid.UUID,
    payload: AssignAgentPayload,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin assigns a field agent to witness the delivery."""
    d = delivery_svc.assign_agent(db, order_id, payload.agent_id)
    return {"status": d.status, "agent_id": str(d.agent_id)}


@router.post("/orders/{order_id}/delivery/assign-driver")
def assign_driver(
    order_id: uuid.UUID,
    payload: AssignDriverPayload,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """Assign a third-party driver to the delivery."""
    d = delivery_svc.assign_driver(
        db, order_id,
        driver_id=payload.driver_id,
        driver_name=payload.driver_name,
        vehicle_reg=payload.vehicle_reg,
    )
    return {"status": d.status, "driver_name": d.driver_name}


@router.post("/orders/{order_id}/delivery/pickup-in-progress")
def pickup_in_progress(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    """Agent/driver marks themselves as en route to farm."""
    d = delivery_svc.mark_pickup_in_progress(db, order_id)
    return {"status": d.status}


@router.post("/orders/{order_id}/delivery/confirm-pickup")
def confirm_pickup(
    order_id: uuid.UUID,
    payload: ConfirmPickupPayload,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    """Step 3 — Agent confirms goods collected. Moves to IN_TRANSIT."""
    d = delivery_svc.confirm_pickup(
        db, order_id,
        photos=payload.photos,
        gps_verified=payload.gps_verified,
        estimated_arrival_at=payload.estimated_arrival_at,
    )
    return {"status": d.status, "estimated_arrival_at": d.estimated_arrival_at}


@router.post("/orders/{order_id}/delivery/delay")
def mark_delayed(
    order_id: uuid.UUID,
    payload: DelayPayload,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    """Mark delivery as delayed with updated ETA."""
    d = delivery_svc.mark_delayed(db, order_id, new_eta=payload.new_eta)
    return {"status": d.status, "new_eta": d.estimated_arrival_at}


@router.post("/orders/{order_id}/delivery/arrived")
def mark_arrived(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    """Step 5 — Driver/agent marks arrival at buyer location."""
    d = delivery_svc.mark_arrived(db, order_id)
    return {"status": d.status}


@router.post("/orders/{order_id}/delivery/confirm-delivery")
def confirm_delivery(
    order_id: uuid.UUID,
    payload: ConfirmDeliveryPayload,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    """Step 5 complete — Agent confirms goods handed over. Starts 24h inspection window."""
    d = delivery_svc.confirm_delivery(
        db, order_id,
        photos=payload.photos,
        gps_verified=payload.gps_verified,
    )
    return {
        "status": d.status,
        "delivered_at": d.delivered_at,
        "inspection_deadline": d.inspection_deadline,
    }


@router.post("/orders/{order_id}/delivery/confirm-receipt")
def confirm_receipt(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Step 6 — Buyer confirms receipt. Releases escrow to farmer."""
    d = delivery_svc.buyer_confirm_receipt(db, order_id, current_user.id)
    return {"status": d.status, "confirmed_at": d.confirmed_at}
