"""
ZimAgritrust Driver API
Covers: registration, job management, rating, admin controls.
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.driver import Driver, DriverJob, DriverStatus
from app.models.listing import LogisticsType
from app.models.logistics import OrderDelivery, DeliveryStatus
from app.models.transaction import Order, OrderStatus
from app.models.user import User, UserRole, UserStatus
from app.services import transport_service

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class DriverRegisterPayload(BaseModel):
    vehicle_reg: str
    vehicle_type: Optional[str] = None
    vehicle_capacity_kg: float = 1000.0
    license_number: str
    current_district: Optional[str] = None


class TransportQuotePayload(BaseModel):
    scenario: LogisticsType
    distance_km: float = 0.0
    waiting_blocks: int = 0
    premium_matching: bool = False


class DecisionTreePayload(BaseModel):
    order_total: float
    buyer_has_vehicle: bool = False
    farmer_has_vehicle: bool = False
    buyer_willing_to_pay_transport: bool = True


class AssignDriverPayload(BaseModel):
    order_id: uuid.UUID
    origin_district: str
    distance_km: float
    platform_fleet_only: bool = False


class RateDriverPayload(BaseModel):
    job_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    note: Optional[str] = None


class UpdateDeliveryStatusPayload(BaseModel):
    status: str


# ── Helper: resolve Driver from current user ────────────────────────────────

def _get_driver(db: Session, user: User) -> Driver:
    if user.role != UserRole.TRANSPORTER:
        raise HTTPException(status_code=403, detail="Driver APIs are restricted to driver accounts.")
    driver = db.query(Driver).filter(Driver.user_id == user.id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Not registered as a driver")
    return driver


# ── Self-registration (new driver, no account yet) ────────────────────────────

@router.post("/self-register", summary="New driver self-registration with document upload")
async def self_register_driver(
    authorization: str = Form(..., description="Bearer temp_token from OTP verify"),
    phone_number: str = Form(...),
    pin: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    address: str = Form(...),
    vehicle_type: str = Form(...),
    plate_number: str = Form(...),
    vehicle_model: Optional[str] = Form(None),
    vehicle_year: Optional[str] = Form(None),
    national_id_front: Optional[UploadFile] = File(None),
    national_id_back: Optional[UploadFile] = File(None),
    license_front: Optional[UploadFile] = File(None),
    license_back: Optional[UploadFile] = File(None),
    vehicle_registration: Optional[UploadFile] = File(None),
    vehicle_photo: Optional[UploadFile] = File(None),
    profile_photo: Optional[UploadFile] = File(None),
    live_selfie: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Complete driver self-registration. Requires a valid temp_token issued by
    /auth/driver/verify-otp. Creates a PENDING_VERIFICATION User + Driver record.
    """
    # ── Validate temp token ─────────────────────────────────────────────────
    token = authorization.replace("Bearer ", "").strip()
    try:
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if claims.get("scope") != "driver_registration":
            raise HTTPException(status_code=403, detail="Invalid registration token scope.")
        token_phone = claims.get("sub", "")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired registration token.")

    if token_phone != phone_number:
        raise HTTPException(status_code=403, detail="Token phone number does not match submitted phone.")

    # ── Check for duplicate ─────────────────────────────────────────────────
    existing = db.query(User).filter(User.phone_number == phone_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this phone number already exists.")

    # ── Create User ─────────────────────────────────────────────────────────
    user = User(
        phone_number=phone_number,
        full_name=f"{first_name} {last_name}",
        password_hash=get_password_hash(pin),
        ussd_pin_hash=get_password_hash(pin),
        role=UserRole.TRANSPORTER,
        status=UserStatus.PENDING_VERIFICATION,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()  # get user.id without committing

    # ── Create Driver record ────────────────────────────────────────────────
    driver = Driver(
        user_id=user.id,
        vehicle_reg=plate_number,
        vehicle_type=vehicle_type,
        license_number=f"PENDING-{plate_number}",
        current_district=address,
        status=DriverStatus.PENDING_REVIEW,
    )
    db.add(driver)
    db.commit()
    db.refresh(user)
    db.refresh(driver)

    return {
        "status": "PENDING_APPROVAL",
        "user_id": str(user.id),
        "driver_id": str(driver.id),
        "message": (
            "Your application has been submitted. "
            "An admin will review your documents within 24–48 hours. "
            "You will be notified via SMS when approved."
        ),
    }


# ── Driver registration (existing TRANSPORTER user) ───────────────────────────

@router.post("/register")
def register_driver(
    payload: DriverRegisterPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Driver accounts can submit vehicle details for admin approval."""
    if current_user.role != UserRole.TRANSPORTER:
        raise HTTPException(status_code=403, detail="Use the driver mobile app with a driver account.")
    existing = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already registered as a driver")

    driver = Driver(
        user_id=current_user.id,
        vehicle_reg=payload.vehicle_reg,
        vehicle_type=payload.vehicle_type,
        vehicle_capacity_kg=payload.vehicle_capacity_kg,
        license_number=payload.license_number,
        current_district=payload.current_district,
        status=DriverStatus.PENDING_REVIEW,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return {"id": str(driver.id), "status": driver.status, "message": "Application submitted. Pending admin review."}


@router.get("/me")
def get_my_driver_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    driver = _get_driver(db, current_user)
    return {
        "id": str(driver.id),
        "status": driver.status,
        "vehicle_reg": driver.vehicle_reg,
        "vehicle_type": driver.vehicle_type,
        "vehicle_capacity_kg": driver.vehicle_capacity_kg,
        "avg_rating": driver.avg_rating,
        "total_deliveries": driver.total_deliveries,
        "warning_count": driver.warning_count,
        "license_verified": driver.license_verified,
        "insurance_verified": driver.insurance_verified,
        "background_cleared": driver.background_cleared,
    }


@router.get("/me/jobs")
def get_my_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    driver = _get_driver(db, current_user)
    jobs = db.query(DriverJob).filter(DriverJob.driver_id == driver.id).order_by(DriverJob.created_at.desc()).all()
    return [
        {
            "id": str(j.id),
            "order_id": str(j.order_id),
            "status": j.status,
            "distance_km": j.distance_km,
            "total_transport_fee": j.total_transport_fee,
            "driver_payout": j.driver_payout,
            "buyer_rating": j.buyer_rating,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]


# ── Job acceptance ─────────────────────────────────────────────────────────────

@router.post("/jobs/{job_id}/accept")
def accept_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_driver(db, current_user)
    job = transport_service.driver_accept_job(db, job_id, current_user.id)
    return {"status": job.status, "accepted_at": job.accepted_at}


@router.post("/jobs/{job_id}/reject")
def reject_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_driver(db, current_user)
    new_job = transport_service.driver_reject_job(db, job_id, current_user.id)
    return {"reassigned": new_job is not None}


# ── Transport quote & decision tree ───────────────────────────────────────────

@router.post("/quote")
def get_transport_quote(payload: TransportQuotePayload):
    """Returns a full fee breakdown for a given scenario and distance."""
    return transport_service.calculate_transport_fee(
        scenario=payload.scenario,
        distance_km=payload.distance_km,
        waiting_blocks=payload.waiting_blocks,
        premium_matching=payload.premium_matching,
    )


@router.post("/recommend-scenario")
def recommend_scenario(payload: DecisionTreePayload):
    """
    Decision tree — returns the recommended logistics scenario
    based on buyer/farmer capabilities and order value.
    """
    scenario = transport_service.recommend_scenario(
        order_total=payload.order_total,
        buyer_has_vehicle=payload.buyer_has_vehicle,
        farmer_has_vehicle=payload.farmer_has_vehicle,
        buyer_willing_to_pay_transport=payload.buyer_willing_to_pay_transport,
    )
    fee = transport_service.calculate_transport_fee(scenario=scenario)
    return {"recommended_scenario": scenario, "fee_breakdown": fee}


# ── Mobile App Endpoints ───────────────────────────────────────────────────────

@router.get("/profile")
def get_driver_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full driver profile for mobile app (alias for /me with extra user info)."""
    driver = _get_driver(db, current_user)
    return {
        "id": str(driver.id),
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "status": driver.status,
        "vehicle_reg": driver.vehicle_reg,
        "vehicle_type": driver.vehicle_type,
        "carrying_capacity_kg": driver.vehicle_capacity_kg,
        "operating_district": driver.current_district,
        "rating": driver.avg_rating,
        "total_deliveries": driver.total_deliveries,
        "successful_deliveries": driver.successful_deliveries,
        "license_verified": driver.license_verified,
        "insurance_verified": driver.insurance_verified,
        "background_cleared": driver.background_cleared,
        "created_at": driver.created_at.isoformat() if driver.created_at else None,
    }


@router.get("/jobs/available")
def get_available_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List jobs available for this driver to accept (PENDING status, not yet assigned)."""
    driver = _get_driver(db, current_user)
    if driver.status != DriverStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Driver account is not active")

    jobs = (
        db.query(DriverJob)
        .filter(DriverJob.status == "PENDING", DriverJob.driver_id.is_(None))
        .order_by(DriverJob.created_at.desc())
        .limit(50)
        .all()
    )

    result = []
    for j in jobs:
        order = j.order
        listing = order.listing if order else None
        result.append({
            "id": str(j.id),
            "order_id": str(j.order_id),
            "pickup_location": listing.location_district if listing else (order.seller.district if order and order.seller else "Unknown"),
            "delivery_location": order.buyer.district if order and order.buyer else "Unknown",
            "distance_km": j.distance_km or 0,
            "weight_kg": order.quantity * 1000 if order else 0,
            "crop_type": listing.product_type if listing else "Cargo",
            "payment_amount": round(j.driver_payout or j.total_transport_fee or 0, 2),
            "currency": order.currency if order else "USD",
            "status": "available",
            "created_at": j.created_at.isoformat() if j.created_at else None,
        })
    return result


@router.get("/deliveries")
def get_my_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all deliveries assigned to this driver."""
    driver = _get_driver(db, current_user)

    jobs = (
        db.query(DriverJob)
        .filter(DriverJob.driver_id == driver.id)
        .order_by(DriverJob.created_at.desc())
        .all()
    )

    result = []
    for j in jobs:
        order = j.order
        listing = order.listing if order else None

        delivery = db.query(OrderDelivery).filter(OrderDelivery.order_id == j.order_id).first()

        status_map = {
            "PENDING": "pending",
            "ACCEPTED": "pending",
            "PICKUP_DONE": "picked_up",
            "IN_TRANSIT": "in_transit",
            "DELIVERED": "delivered",
            "PAID": "completed",
        }

        result.append({
            "id": str(j.id),
            "order_id": str(j.order_id),
            "pickup_location": delivery.pickup_address if delivery else (listing.location_district if listing else "Unknown"),
            "delivery_location": delivery.delivery_address if delivery else "Unknown",
            "status": status_map.get(j.status, "pending"),
            "crop_type": listing.product_type if listing else "Cargo",
            "weight_kg": order.quantity * 1000 if order else 0,
            "payment_amount": round(j.driver_payout or j.total_transport_fee or 0, 2),
            "distance_km": j.distance_km or 0,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        })
    return result


@router.patch("/deliveries/{delivery_id}/status")
def update_delivery_status(
    delivery_id: uuid.UUID,
    payload: UpdateDeliveryStatusPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a delivery's status (called from driver mobile app)."""
    driver = _get_driver(db, current_user)

    job = db.query(DriverJob).filter(
        DriverJob.id == delivery_id,
        DriverJob.driver_id == driver.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Delivery not found")

    VALID_TRANSITIONS = {
        "ACCEPTED": ["PICKUP_DONE"],
        "PICKUP_DONE": ["IN_TRANSIT"],
        "IN_TRANSIT": ["DELIVERED"],
    }
    allowed = VALID_TRANSITIONS.get(job.status, [])
    new_status = payload.status.upper()
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {job.status} to {new_status}. Allowed: {allowed}",
        )

    job.status = new_status
    if new_status == "DELIVERED":
        job.completed_at = datetime.utcnow()

    delivery = db.query(OrderDelivery).filter(OrderDelivery.order_id == job.order_id).first()
    if delivery:
        delivery_status_map = {
            "PICKUP_DONE": DeliveryStatus.PICKUP_COMPLETED,
            "IN_TRANSIT": DeliveryStatus.IN_TRANSIT,
            "DELIVERED": DeliveryStatus.DELIVERED,
        }
        if new_status in delivery_status_map:
            delivery.status = delivery_status_map[new_status]
            if new_status == "DELIVERED":
                delivery.delivered_at = datetime.utcnow()

    db.commit()
    return {"status": job.status, "updated": True}


@router.get("/earnings")
def get_driver_earnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Earnings summary for the driver mobile app."""
    driver = _get_driver(db, current_user)

    all_jobs = db.query(DriverJob).filter(DriverJob.driver_id == driver.id).all()

    total = sum(j.driver_payout or 0 for j in all_jobs if j.status in ("DELIVERED", "PAID"))
    pending = sum(j.driver_payout or 0 for j in all_jobs if j.status in ("ACCEPTED", "PICKUP_DONE", "IN_TRANSIT"))

    now = datetime.utcnow()
    this_week = sum(
        j.driver_payout or 0 for j in all_jobs
        if j.status in ("DELIVERED", "PAID") and j.completed_at and (now - j.completed_at).days <= 7
    )
    this_month = sum(
        j.driver_payout or 0 for j in all_jobs
        if j.status in ("DELIVERED", "PAID") and j.completed_at and j.completed_at.month == now.month and j.completed_at.year == now.year
    )
    today = sum(
        j.driver_payout or 0 for j in all_jobs
        if j.status in ("DELIVERED", "PAID") and j.completed_at and j.completed_at.date() == now.date()
    )

    paid_out = sum(j.driver_payout or 0 for j in all_jobs if j.status == "PAID")
    available = total - paid_out

    return {
        "total": round(total, 2),
        "available": round(available, 2),
        "pending": round(pending, 2),
        "this_week": round(this_week, 2),
        "this_month": round(this_month, 2),
        "today": round(today, 2),
        "completed_deliveries": driver.total_deliveries,
        "currency": "USD",
    }


# ── Rating ─────────────────────────────────────────────────────────────────────

@router.post("/rate")
def rate_driver(
    payload: RateDriverPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Buyer rates a driver after delivery."""
    job = transport_service.rate_driver(db, payload.job_id, current_user.id, payload.rating, payload.note)
    return {"job_id": str(job.id), "rating": job.buyer_rating, "driver_avg": job.driver.avg_rating if job.driver else None}


# ── Admin controls ─────────────────────────────────────────────────────────────

@router.get("/admin/all")
def list_all_drivers(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    drivers = db.query(Driver).order_by(Driver.created_at.desc()).all()
    return [
        {
            "id": str(d.id),
            "user_id": str(d.user_id),
            "name": d.user.full_name if d.user else "N/A",
            "phone": d.user.phone_number if d.user else "N/A",
            "vehicle_reg": d.vehicle_reg,
            "status": d.status,
            "avg_rating": d.avg_rating,
            "total_deliveries": d.total_deliveries,
            "warning_count": d.warning_count,
            "license_verified": d.license_verified,
            "insurance_verified": d.insurance_verified,
            "background_cleared": d.background_cleared,
        }
        for d in drivers
    ]


@router.post("/admin/{driver_id}/approve")
def approve_driver(
    driver_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.status = DriverStatus.ACTIVE
    driver.license_verified = True
    driver.background_cleared = True
    driver.registration_fee_paid = True
    db.commit()

    # F#285 — driver approval email (best-effort).
    try:
        from app.services.email_service import email_service
        owner = db.query(User).filter(User.id == driver.user_id).first()
        if owner and owner.email:
            email_service.send_template(
                "email.driver_approval",
                to=owner.email,
                context={
                    "name": owner.full_name,
                    "tier": getattr(driver, "tier", None) or "New",
                },
            )
    except Exception:  # noqa: BLE001
        pass

    return {"status": driver.status}


@router.post("/admin/{driver_id}/suspend")
def suspend_driver(
    driver_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.status = DriverStatus.SUSPENDED
    db.commit()
    return {"status": driver.status}


@router.post("/admin/{driver_id}/reactivate")
def reactivate_driver(
    driver_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    driver = transport_service.reactivate_driver(db, driver_id)
    return {"status": driver.status}


@router.post("/admin/assign-driver")
def admin_assign_driver(
    payload: AssignDriverPayload,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin manually triggers driver auto-assignment for an order."""
    from app.models.transaction import Order
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    job = transport_service.auto_assign_driver(
        db, order,
        origin_district=payload.origin_district,
        distance_km=payload.distance_km,
        platform_fleet_only=payload.platform_fleet_only,
    )
    if not job:
        raise HTTPException(status_code=404, detail="No available drivers in that district")

    return {
        "job_id": str(job.id),
        "driver_payout": job.driver_payout,
        "platform_commission": job.platform_commission,
        "total_transport_fee": job.total_transport_fee,
    }
