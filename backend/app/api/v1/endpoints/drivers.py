"""
ZimAgritrust Driver API
Covers: registration, job management, rating, admin controls.
"""
import uuid
import os
import shutil
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.driver import Driver, DriverJob, DriverStatus
from app.models.listing import LogisticsType
from app.models.logistics import OrderDelivery, DeliveryStatus
from app.models.transaction import Order, OrderStatus
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import Token, UserLogin
from app.services import transport_service
from app.services.portal_auth_service import DRIVER_ROLES, login_with_pin

# ── Document storage ──────────────────────────────────────────────────────────
DRIVER_UPLOAD_DIR = "uploads/driver_documents"
os.makedirs(DRIVER_UPLOAD_DIR, exist_ok=True)

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE_MB = 10


def _save_driver_file(file: UploadFile, driver_id: str, slot: str) -> Optional[str]:
    """Save a driver document file and return the stored path."""
    if not file or not file.filename:
        return None
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed.")

    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "application/pdf": "pdf"}
    ext = ext_map.get(file.content_type or "image/jpeg", "jpg")
    filename = f"{driver_id}_{slot}_{uuid.uuid4().hex[:12]}.{ext}"
    dest = os.path.join(DRIVER_UPLOAD_DIR, filename)

    # Path traversal defense
    real_dest = os.path.realpath(dest)
    real_upload = os.path.realpath(DRIVER_UPLOAD_DIR)
    if not real_dest.startswith(real_upload):
        raise HTTPException(status_code=400, detail="Invalid upload path.")

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size_mb = os.path.getsize(dest) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        os.remove(dest)
        raise HTTPException(status_code=400, detail=f"File too large ({size_mb:.1f} MB). Max {MAX_SIZE_MB} MB.")

    return dest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=Token)
async def login_driver_alias(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Token:
    try:
        return await login_with_pin(
            db=db,
            request=request,
            response=response,
            phone_number=payload.phone_number,
            pin=payload.password,
            allowed_roles=DRIVER_ROLES,
            portal_name="driver",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Driver login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Driver login failed")


# Global OPTIONS handler for all routes in this router
@router.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight for all routes"""
    return {"status": "ok"}


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





class ProfileUpdatePayload(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class VehicleUpdatePayload(BaseModel):
    vehicle_type: Optional[str] = None
    vehicle_reg: Optional[str] = None
    vehicle_capacity_kg: Optional[int] = None
    vehicle_color: Optional[str] = None


class ChangePinPayload(BaseModel):
    current_pin: str
    new_pin: str


class SettingsUpdatePayload(BaseModel):
    push_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    job_alerts: Optional[bool] = None
    earnings_alerts: Optional[bool] = None


class PrivacyUpdatePayload(BaseModel):
    share_location_delivery: Optional[bool] = None
    phone_visibility: Optional[bool] = None
    data_sharing_consent: Optional[bool] = None


# ── Helper: resolve Driver from current user ────────────────────────────────

def _get_driver(db: Session, user: User, enforce_active: bool = False) -> Driver:
    if user.role != UserRole.DRIVER:
        raise HTTPException(status_code=403, detail="Driver APIs are restricted to driver accounts.")
    driver = db.query(Driver).filter(Driver.user_id == user.id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Not registered as a driver")
    if enforce_active and driver.status != DriverStatus.ACTIVE:
        raise HTTPException(
            status_code=403, 
            detail=f"Action forbidden. Your account status is: {driver.status}. Please wait for admin approval."
        )
    return driver


# ── Self-registration (new driver, no account yet) ────────────────────────────

@router.post("/self-register", summary="New driver self-registration with document upload")
async def self_register_driver(
    authorization: str = Form(None, description="Bearer temp_token from OTP verify"),
    phone_number: str = Form(None),
    pin: str = Form(None),
    first_name: str = Form(None),
    last_name: str = Form(None),
    date_of_birth: str = Form(None),
    address: str = Form(None),
    vehicle_type: str = Form(None),
    plate_number: str = Form(None),
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
    # Log received fields for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"DRIVER SELF-REGISTER - Received fields: authorization={bool(authorization)}, phone_number={phone_number}, pin={bool(pin)}, first_name={first_name}, last_name={last_name}, vehicle_type={vehicle_type}, plate_number={plate_number}")

    # ── Validate required fields ───────────────────────────────────────────────
    if not authorization:
        raise HTTPException(status_code=422, detail="authorization is required")
    if not phone_number:
        raise HTTPException(status_code=422, detail="phone_number is required")
    if not pin:
        raise HTTPException(status_code=422, detail="pin is required")
    if not first_name:
        raise HTTPException(status_code=422, detail="first_name is required")
    if not last_name:
        raise HTTPException(status_code=422, detail="last_name is required")
    if not date_of_birth:
        raise HTTPException(status_code=422, detail="date_of_birth is required")
    if not address:
        raise HTTPException(status_code=422, detail="address is required")
    if not vehicle_type:
        raise HTTPException(status_code=422, detail="vehicle_type is required")
    if not plate_number:
        raise HTTPException(status_code=422, detail="plate_number is required")

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
        role=UserRole.DRIVER,
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
        vehicle_model=vehicle_model,
        vehicle_year=vehicle_year,
        license_number=f"PENDING-{plate_number}",
        current_district=address,
        status=DriverStatus.PENDING_REVIEW,
    )
    db.add(driver)
    db.flush()  # get driver.id

    # ── Save uploaded documents ─────────────────────────────────────────────
    driver_id_str = str(driver.id)
    doc_slots = {
        "national_id_front": national_id_front,
        "national_id_back": national_id_back,
        "license_front": license_front,
        "license_back": license_back,
        "vehicle_registration": vehicle_registration,
        "vehicle_photo": vehicle_photo,
        "profile_photo": profile_photo,
        "live_selfie": live_selfie,
    }
    saved_docs = {}
    for slot, file in doc_slots.items():
        if file and file.filename:
            try:
                path = _save_driver_file(file, driver_id_str, slot)
                if path:
                    saved_docs[slot] = path
            except Exception as e:
                logger.warning(f"Failed to save {slot}: {e}")

    # Store document paths on driver record
    driver.doc_national_id_front = saved_docs.get("national_id_front")
    driver.doc_national_id_back = saved_docs.get("national_id_back")
    driver.doc_license_front = saved_docs.get("license_front")
    driver.doc_license_back = saved_docs.get("license_back")
    driver.doc_vehicle_registration = saved_docs.get("vehicle_registration")
    driver.doc_vehicle_photo = saved_docs.get("vehicle_photo")
    driver.doc_profile_photo = saved_docs.get("profile_photo")
    driver.doc_live_selfie = saved_docs.get("live_selfie")

    db.commit()
    db.refresh(user)
    db.refresh(driver)

    return {
        "status": "PENDING_APPROVAL",
        "user_id": str(user.id),
        "driver_id": str(driver.id),
        "documents_received": list(saved_docs.keys()),
        "message": (
            "Your application has been submitted. "
            "An admin will review your documents within 24–48 hours. "
            "You will be notified via SMS when approved."
        ),
    }


# ── Step-by-step Registration Aliases (Requested by user) ────────────────────

@router.post("/register/otp")
async def register_otp(payload: dict, db: Session = Depends(get_db)):
    """Alias for /auth/driver/request-otp"""
    from app.api.v1.endpoints.portal_auth import driver_request_otp, DriverOtpRequest
    return await driver_request_otp(DriverOtpRequest(phone_number=payload.get("phone")), db)


@router.post("/register/verify")
async def register_verify(payload: dict, db: Session = Depends(get_db)):
    """Alias for /auth/driver/verify-otp"""
    from app.api.v1.endpoints.portal_auth import driver_verify_otp, DriverOtpVerify
    return await driver_verify_otp(DriverOtpVerify(phone_number=payload.get("phone"), otp=payload.get("otp")), db)


@router.post("/register/pin")
async def register_pin(payload: dict):
    """Store PIN in local state (frontend handles this, backend is one-shot)"""
    return {"success": True, "message": "PIN validated locally"}


@router.post("/register/personal")
async def register_personal(payload: dict):
    return {"success": True}


@router.post("/register/vehicle")
async def register_vehicle(payload: dict):
    return {"success": True}


@router.post("/register/submit")
async def register_submit(payload: dict):
    return {"success": True, "status": "pending", "message": "Please use the one-shot self-register endpoint for final submission"}


# ── Driver registration (existing DRIVER user) ───────────────────────────

@router.options("/register")
async def register_driver_options(request: Request):
    """Handle CORS preflight for register"""
    return {"status": "ok"}


@router.post("/register")
def register_driver(
    payload: DriverRegisterPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Driver accounts can submit vehicle details for admin approval."""
    if current_user.role != UserRole.DRIVER:
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
@router.get("/profile")
def get_my_driver_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    driver = _get_driver(db, current_user)
    # Use User model for name and phone fields
    full_name = getattr(current_user, "full_name", getattr(driver, "user", None).full_name if getattr(driver, "user", None) else None)
    phone_number = getattr(current_user, "phone_number", getattr(driver, "user", None).phone_number if getattr(driver, "user", None) else None)
    return {
        "id": str(driver.id),
            "full_name": full_name,
            "phone_number": phone_number,
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
            "address": driver.current_district,
            "email": getattr(current_user, "email", ""),
        }


@router.put("/me")
def update_profile(
    payload: ProfileUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    driver = _get_driver(db, current_user)
    if payload.full_name:
        driver.name = payload.full_name
        current_user.full_name = payload.full_name
    if payload.address:
        driver.current_district = payload.address
    if payload.phone_number:
        driver.phone = payload.phone_number
        current_user.phone_number = payload.phone_number
    if payload.email:
        current_user.email = payload.email
        
    db.commit()
    return {"success": True, "message": "Profile updated successfully"}


@router.put("/profile")
def update_driver_profile_alias(
    payload: ProfileUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_profile(payload=payload, db=db, current_user=current_user)


@router.put("/me/vehicle")
def update_vehicle(
    payload: VehicleUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    driver = _get_driver(db, current_user)
    if payload.vehicle_type:
        driver.vehicle_type = payload.vehicle_type
    if payload.vehicle_reg:
        driver.vehicle_reg = payload.vehicle_reg
    if payload.vehicle_capacity_kg:
        driver.vehicle_capacity_kg = payload.vehicle_capacity_kg
    if payload.vehicle_color:
        driver.vehicle_color = payload.vehicle_color
        
    db.commit()
    return {"success": True, "message": "Vehicle info updated successfully"}


@router.post("/me/change-pin")
def change_pin(
    payload: ChangePinPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_hash = current_user.ussd_pin_hash or current_user.password_hash
    if not current_hash or not verify_password(payload.current_pin, current_hash):
        raise HTTPException(status_code=400, detail="Invalid current PIN")
    
    hashed = get_password_hash(payload.new_pin)
    current_user.ussd_pin_hash = hashed
    current_user.password_hash = hashed
    db.commit()
    return {"success": True, "message": "PIN changed successfully"}


@router.post("/change-pin")
def change_pin_alias(
    payload: ChangePinPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return change_pin(payload=payload, db=db, current_user=current_user)


@router.get("/me/settings")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # In a real app, these would be in a driver_settings table
    # For now, we'll return defaults or store them in a JSON field if available
    return {
        "push_notifications": True,
        "sms_notifications": True,
        "email_notifications": False,
        "job_alerts": True,
        "earnings_alerts": True,
        "share_location_delivery": True,
        "phone_visibility": True,
        "data_sharing_consent": True
    }


@router.get("/settings")
def get_settings_alias(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_settings(db=db, current_user=current_user)


@router.put("/me/settings")
def update_settings(
    payload: SettingsUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Mock update
    return {"success": True, "message": "Settings updated"}


@router.put("/settings")
def update_settings_alias(
    payload: SettingsUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_settings(payload=payload, db=db, current_user=current_user)


@router.post("/me/settings/privacy")
def update_privacy(
    payload: PrivacyUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Mock update
    return {"success": True, "message": "Privacy settings updated"}


@router.delete("/me/data")
def delete_driver_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    driver = _get_driver(db, current_user)
    # Perform soft delete or data anonymization
    driver.status = DriverStatus.TERMINATED
    db.commit()
    return {"success": True, "message": "Data deletion request submitted"}


@router.delete("/data")
def delete_driver_data_alias(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delete_driver_data(db=db, current_user=current_user)


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
    _get_driver(db, current_user, enforce_active=True)
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
            "vehicle_type": d.vehicle_type,
            "status": d.status,
            "avg_rating": d.avg_rating,
            "total_deliveries": d.total_deliveries,
            "warning_count": d.warning_count,
            "license_verified": d.license_verified,
            "insurance_verified": d.insurance_verified,
            "background_cleared": d.background_cleared,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            # Document availability flags
            "has_national_id_front": bool(getattr(d, "doc_national_id_front", None)),
            "has_national_id_back": bool(getattr(d, "doc_national_id_back", None)),
            "has_license_front": bool(getattr(d, "doc_license_front", None)),
            "has_license_back": bool(getattr(d, "doc_license_back", None)),
            "has_vehicle_registration": bool(getattr(d, "doc_vehicle_registration", None)),
            "has_vehicle_photo": bool(getattr(d, "doc_vehicle_photo", None)),
            "has_profile_photo": bool(getattr(d, "doc_profile_photo", None)),
            "has_live_selfie": bool(getattr(d, "doc_live_selfie", None)),
            # Document URLs for admin review
            "doc_national_id_front": f"/drivers/admin/{d.id}/document/national_id_front" if getattr(d, "doc_national_id_front", None) else None,
            "doc_national_id_back": f"/drivers/admin/{d.id}/document/national_id_back" if getattr(d, "doc_national_id_back", None) else None,
            "doc_license_front": f"/drivers/admin/{d.id}/document/license_front" if getattr(d, "doc_license_front", None) else None,
            "doc_license_back": f"/drivers/admin/{d.id}/document/license_back" if getattr(d, "doc_license_back", None) else None,
            "doc_vehicle_registration": f"/drivers/admin/{d.id}/document/vehicle_registration" if getattr(d, "doc_vehicle_registration", None) else None,
            "doc_vehicle_photo": f"/drivers/admin/{d.id}/document/vehicle_photo" if getattr(d, "doc_vehicle_photo", None) else None,
            "doc_profile_photo": f"/drivers/admin/{d.id}/document/profile_photo" if getattr(d, "doc_profile_photo", None) else None,
            "doc_live_selfie": f"/drivers/admin/{d.id}/document/live_selfie" if getattr(d, "doc_live_selfie", None) else None,
        }
        for d in drivers
    ]


@router.get("/admin/{driver_id}/document/{slot}")
def get_driver_document(
    driver_id: uuid.UUID,
    slot: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Serve a driver's uploaded document file to admin reviewers."""
    valid_slots = [
        "national_id_front", "national_id_back", "license_front", "license_back",
        "vehicle_registration", "vehicle_photo", "profile_photo", "live_selfie"
    ]
    if slot not in valid_slots:
        raise HTTPException(status_code=400, detail="Invalid document slot")

    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    path = getattr(driver, f"doc_{slot}", None)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Document not found")

    return FileResponse(path)


@router.post("/admin/{driver_id}/approve")
def approve_driver(
    driver_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.status = DriverStatus.ACTIVE
    driver.license_verified = True
    driver.background_cleared = True
    driver.registration_fee_paid = True
    try:
        driver.reviewed_by = uuid.UUID(str(admin.id))
    except ValueError:
        driver.reviewed_by = None
    driver.reviewed_at = datetime.utcnow()
    db.commit()

    # Notify driver
    try:
        from app.services.notification_service import NotificationService
        owner = db.query(User).filter(User.id == driver.user_id).first()
        if owner:
            import asyncio
            asyncio.create_task(
                NotificationService._notify_both_channels(
                    owner.phone_number,
                    f"✅ *Driver Application Approved!*\n\n"
                    f"Hello {owner.full_name}, your driver application has been approved.\n\n"
                    f"🚚 You can now log in to the ZimAgriTrust Driver App and start accepting jobs.\n\n"
                    f"Welcome to the fleet!"
                )
            )
    except Exception:
        pass

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


@router.post("/admin/{driver_id}/reject")
def reject_driver(
    driver_id: uuid.UUID,
    note: str = Form(..., description="Reason for rejection — sent to driver"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin rejects a driver application with a reason."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.status != DriverStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail=f"Driver is already {driver.status}")

    driver.status = DriverStatus.TERMINATED
    driver.rejection_note = note
    try:
        driver.reviewed_by = uuid.UUID(str(admin.id))
    except ValueError:
        driver.reviewed_by = None
    driver.reviewed_at = datetime.utcnow()
    db.commit()

    # Notify driver
    try:
        from app.services.notification_service import NotificationService
        owner = db.query(User).filter(User.id == driver.user_id).first()
        if owner:
            import asyncio
            asyncio.create_task(
                NotificationService._notify_both_channels(
                    owner.phone_number,
                    f"❌ *Driver Application Rejected*\n\n"
                    f"Hello {owner.full_name}, your driver application was not approved.\n\n"
                    f"*Reason:* {note}\n\n"
                    f"Please contact support or reapply with the correct documents."
                )
            )
    except Exception:
        pass

    return {"status": driver.status, "note": note}


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


# ── Additional Mobile App Endpoints ───────────────────────────────────────────

class LocationUpdatePayload(BaseModel):
    latitude: float
    longitude: float
    job_id: Optional[uuid.UUID] = None
    timestamp: Optional[str] = None


class AvailabilityPayload(BaseModel):
    is_available: bool


class WithdrawPayload(BaseModel):
    amount: float = Field(..., gt=0)
    method: str = Field(..., pattern="^(ecocash|onemoney|bank)$")


class NegotiatePayload(BaseModel):
    counter_offer: float = Field(..., gt=0)


class PickupProofPayload(BaseModel):
    photo_base64: str


class DeliveryProofPayload(BaseModel):
    photo_base64: str
    signature_base64: str


@router.post("/location")
def update_driver_location(
    payload: LocationUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update driver's current location (called from mobile app)."""
    driver = _get_driver(db, current_user)
    driver.current_lat = payload.latitude
    driver.current_lon = payload.longitude
    db.commit()
    return {"success": True, "timestamp": payload.timestamp or datetime.utcnow().isoformat()}


@router.post("/availability")
def update_driver_availability(
    payload: AvailabilityPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle driver online/offline status."""
    driver = _get_driver(db, current_user)
    if driver.status != DriverStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Driver account is not active")
    
    # Store availability in a separate field or use status
    # For now, we'll use a simple approach - could add is_available field to Driver model
    driver.current_district = driver.current_district  # Trigger update
    db.commit()
    return {"success": True, "is_available": payload.is_available}


@router.post("/earnings/withdraw")
def withdraw_earnings(
    payload: WithdrawPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request withdrawal of available earnings."""
    driver = _get_driver(db, current_user)
    
    # Calculate available balance
    all_jobs = db.query(DriverJob).filter(DriverJob.driver_id == driver.id).all()
    total = sum(j.driver_payout or 0 for j in all_jobs if j.status in ("DELIVERED", "PAID"))
    paid_out = sum(j.driver_payout or 0 for j in all_jobs if j.status == "PAID")
    available = total - paid_out
    
    if payload.amount > available:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Available: ${available:.2f}")
    
    if payload.amount < 5:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is $5")
    
    # Create withdrawal record (would need a Withdrawal model in production)
    # For now, just return success
    return {
        "success": True,
        "amount": payload.amount,
        "method": payload.method,
        "reference": f"WD-{uuid.uuid4().hex[:12].upper()}",
        "status": "processing",
    }


@router.post("/jobs/{job_id}/negotiate")
def negotiate_job_fare(
    job_id: uuid.UUID,
    payload: NegotiatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a counter-offer for a job's transport fee."""
    driver = _get_driver(db, current_user)
    
    job = db.query(DriverJob).filter(
        DriverJob.id == job_id,
        DriverJob.status == "PENDING",
        DriverJob.driver_id.is_(None)
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not available for negotiation")
    
    # Store negotiation (would need a Negotiation model in production)
    # For now, just return the counter-offer as accepted for demo
    job.total_transport_fee = payload.counter_offer
    job.driver_payout = payload.counter_offer * 0.9  # 90% to driver
    db.commit()
    
    return {
        "success": True,
        "new_fee": payload.counter_offer,
        "driver_payout": job.driver_payout,
    }


@router.post("/jobs/{job_id}/pickup")
def confirm_pickup(
    job_id: uuid.UUID,
    payload: PickupProofPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm pickup with photo proof."""
    driver = _get_driver(db, current_user)
    
    job = db.query(DriverJob).filter(
        DriverJob.id == job_id,
        DriverJob.driver_id == driver.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in ("ACCEPTED", "PICKUP_DONE"):
        raise HTTPException(status_code=400, detail="Job cannot be picked up in current status")
    
    job.status = "PICKUP_DONE"
    job.accepted_at = job.accepted_at or datetime.utcnow()
    
    # Update delivery status
    delivery = db.query(OrderDelivery).filter(OrderDelivery.order_id == job.order_id).first()
    if delivery:
        delivery.status = DeliveryStatus.PICKUP_COMPLETED
        delivery.pickup_at = datetime.utcnow()
    
    db.commit()
    return {"success": True, "status": job.status}


@router.post("/jobs/{job_id}/deliver")
def confirm_delivery(
    job_id: uuid.UUID,
    payload: DeliveryProofPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm delivery with photo and signature proof."""
    driver = _get_driver(db, current_user)
    
    job = db.query(DriverJob).filter(
        DriverJob.id == job_id,
        DriverJob.driver_id == driver.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "PICKUP_DONE":
        raise HTTPException(status_code=400, detail="Job must be picked up before delivery")
    
    job.status = "DELIVERED"
    job.completed_at = datetime.utcnow()
    
    # Update delivery status
    delivery = db.query(OrderDelivery).filter(OrderDelivery.order_id == job.order_id).first()
    if delivery:
        delivery.status = DeliveryStatus.DELIVERED
        delivery.delivered_at = datetime.utcnow()
    
    # Update driver stats
    driver.total_deliveries += 1
    driver.successful_deliveries += 1
    
    db.commit()
    
    return {
        "success": True,
        "status": job.status,
        "earnings": job.driver_payout,
    }
