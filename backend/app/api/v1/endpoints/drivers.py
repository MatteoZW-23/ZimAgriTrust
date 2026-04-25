"""
AgriTrust Driver API
Covers: registration, job management, rating, admin controls.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.driver import Driver, DriverJob, DriverStatus
from app.models.listing import LogisticsType
from app.models.user import User, UserRole
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


# ── Driver registration ────────────────────────────────────────────────────────

@router.post("/register")
def register_driver(
    payload: DriverRegisterPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Any user can register as a driver. Requires admin approval."""
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
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Not registered as a driver")
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
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Not registered as a driver")
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
    job = transport_service.driver_accept_job(db, job_id, current_user.id)
    return {"status": job.status, "accepted_at": job.accepted_at}


@router.post("/jobs/{job_id}/reject")
def reject_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
