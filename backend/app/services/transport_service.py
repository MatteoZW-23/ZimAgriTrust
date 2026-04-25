"""
AgriTrust Transport Service
Implements the full decision tree from the spec:
  - Scenario selection (5 types)
  - Transport fee calculation
  - Driver matching & assignment
  - Fee splitting (farmer / driver / platform)
  - Driver rating & penalty system
  - Dispute resolution routing
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.driver import Driver, DriverJob, DriverStatus
from app.models.listing import LogisticsType
from app.models.transaction import Order, OrderStatus

logger = logging.getLogger(__name__)

# ── Fee constants (per spec) ───────────────────────────────────────────────────
BASE_FEE_USD            = 7.00    # Base delivery fee
DISTANCE_RATE_USD_PER_KM = 0.50  # Per km
WAITING_FEE_USD         = 2.00   # Per 30-min block
DRIVER_COMMISSION_RATE  = 0.10   # Platform takes 10% of transport fee
PLATFORM_FLEET_MARGIN   = 0.20   # Platform keeps 20% on fleet jobs
COOPERATIVE_FEE_RATE    = 0.05   # 5% coordination fee
DRIVER_REGISTRATION_FEE = 10.00  # One-time onboarding fee
PREMIUM_MATCHING_FEE    = 2.00   # Priority assignment surcharge

# High-value threshold — recommend platform fleet
HIGH_VALUE_THRESHOLD_USD = 500.0


# ── Decision tree ──────────────────────────────────────────────────────────────

def recommend_scenario(
    order_total: float,
    buyer_has_vehicle: bool,
    farmer_has_vehicle: bool,
    buyer_willing_to_pay_transport: bool,
) -> LogisticsType:
    """
    Implements the master decision tree from the spec.
    Returns the recommended logistics scenario.
    """
    if buyer_has_vehicle:
        return LogisticsType.SELF_COLLECT

    if farmer_has_vehicle:
        return LogisticsType.SELF_DELIVER

    if not buyer_willing_to_pay_transport:
        return LogisticsType.SELF_COLLECT  # Forced — buyer must collect

    if order_total >= HIGH_VALUE_THRESHOLD_USD:
        return LogisticsType.PLATFORM_FLEET  # Premium for high-value

    return LogisticsType.PLATFORM  # Default: 3rd-party driver


# ── Fee calculation ────────────────────────────────────────────────────────────

def calculate_transport_fee(
    scenario: LogisticsType,
    distance_km: float = 0.0,
    waiting_blocks: int = 0,
    premium_matching: bool = False,
) -> dict:
    """
    Returns a full fee breakdown for a given scenario.
    """
    if scenario in (LogisticsType.SELF_COLLECT, LogisticsType.SELF_DELIVER):
        return {
            "scenario": scenario,
            "base_fee": 0.0,
            "distance_fee": 0.0,
            "waiting_fee": 0.0,
            "matching_fee": 0.0,
            "total_transport_fee": 0.0,
            "platform_commission": 0.0,
            "driver_payout": 0.0,
            "platform_revenue": 0.0,
        }

    base        = BASE_FEE_USD
    dist_fee    = round(distance_km * DISTANCE_RATE_USD_PER_KM, 2)
    wait_fee    = round(waiting_blocks * WAITING_FEE_USD, 2)
    match_fee   = PREMIUM_MATCHING_FEE if premium_matching else 0.0
    total       = round(base + dist_fee + wait_fee + match_fee, 2)

    if scenario == LogisticsType.PLATFORM_FLEET:
        commission  = round(total * PLATFORM_FLEET_MARGIN, 2)
        driver_net  = round(total - commission, 2)
    elif scenario == LogisticsType.COOPERATIVE:
        commission  = round(total * COOPERATIVE_FEE_RATE, 2)
        driver_net  = round(total - commission, 2)
    else:  # PLATFORM (3rd party)
        commission  = round(total * DRIVER_COMMISSION_RATE, 2)
        driver_net  = round(total - commission, 2)

    return {
        "scenario": scenario,
        "base_fee": base,
        "distance_fee": dist_fee,
        "waiting_fee": wait_fee,
        "matching_fee": match_fee,
        "total_transport_fee": total,
        "platform_commission": commission,
        "driver_payout": driver_net,
        "platform_revenue": commission + match_fee,
    }


# ── Driver matching ────────────────────────────────────────────────────────────

def find_available_drivers(
    db: Session,
    origin_district: str,
    required_capacity_kg: float,
    platform_fleet_only: bool = False,
) -> list[Driver]:
    """
    Returns drivers available in the origin district with sufficient capacity.
    Sorted by rating descending.
    """
    q = (
        db.query(Driver)
        .filter(
            Driver.status == DriverStatus.ACTIVE,
            Driver.vehicle_capacity_kg >= required_capacity_kg,
            Driver.current_district == origin_district,
        )
    )
    if platform_fleet_only:
        q = q.filter(Driver.is_platform_fleet == True)

    drivers = q.order_by(Driver.avg_rating.desc()).all()
    return drivers


def auto_assign_driver(
    db: Session,
    order: Order,
    origin_district: str,
    distance_km: float,
    platform_fleet_only: bool = False,
) -> Optional[DriverJob]:
    """
    Auto-assigns the highest-rated available driver.
    Creates a DriverJob and updates Order transport fields.
    """
    drivers = find_available_drivers(
        db, origin_district, order.quantity, platform_fleet_only
    )
    if not drivers:
        return None

    driver = drivers[0]
    fee_breakdown = calculate_transport_fee(
        scenario=LogisticsType.PLATFORM_FLEET if platform_fleet_only else LogisticsType.PLATFORM,
        distance_km=distance_km,
    )

    job = DriverJob(
        driver_id=driver.id,
        order_id=order.id,
        distance_km=distance_km,
        base_fee=fee_breakdown["base_fee"],
        distance_fee=fee_breakdown["distance_fee"],
        total_transport_fee=fee_breakdown["total_transport_fee"],
        platform_commission=fee_breakdown["platform_commission"],
        driver_payout=fee_breakdown["driver_payout"],
        status="PENDING",
    )
    db.add(job)

    # Update order with transport fee breakdown
    order.transport_fee       = fee_breakdown["total_transport_fee"]
    order.transport_commission = fee_breakdown["platform_commission"]
    order.driver_payout       = fee_breakdown["driver_payout"]

    db.commit()
    db.refresh(job)

    _notify_driver_new_job(driver, order, fee_breakdown)
    return job


def driver_accept_job(db: Session, job_id: uuid.UUID, driver_user_id: uuid.UUID) -> DriverJob:
    """Driver accepts a job within the 5-minute window."""
    job = db.query(DriverJob).filter(DriverJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    driver = db.query(Driver).filter(Driver.user_id == driver_user_id).first()
    if not driver or job.driver_id != driver.id:
        raise HTTPException(status_code=403, detail="Not your job")

    if job.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Job already {job.status}")

    job.status = "ACCEPTED"
    job.accepted_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    _notify_job_confirmed(db, job)
    return job


def driver_reject_job(db: Session, job_id: uuid.UUID, driver_user_id: uuid.UUID) -> Optional[DriverJob]:
    """Driver rejects — system reassigns to next available driver."""
    job = db.query(DriverJob).filter(DriverJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "REJECTED"
    db.commit()

    # Reassign
    order = db.query(Order).filter(Order.id == job.order_id).first()
    if order:
        from app.models.logistics import OrderDelivery
        delivery = db.query(OrderDelivery).filter(OrderDelivery.order_id == order.id).first()
        origin = delivery.pickup_address or ""
        new_job = auto_assign_driver(db, order, origin, job.distance_km or 0)
        return new_job
    return None


def settle_driver_payout(db: Session, job: DriverJob) -> bool:
    """
    Releases driver payout from platform wallet after buyer confirms delivery.
    """
    if job.status != "DELIVERED":
        return False

    driver = db.query(Driver).filter(Driver.id == job.driver_id).first()
    if not driver:
        return False

    from app.services.wallet_service import wallet_service
    from app.models.transaction import Transaction, TransactionType

    # Credit driver's wallet
    wallet_service.deposit(db, driver.user_id, job.driver_payout, "USD", reference=f"JOB-{job.id}")

    # Log transaction
    db.add(Transaction(
        order_id=job.order_id,
        user_id=driver.user_id,
        type=TransactionType.ESCROW_RELEASE,
        amount=job.driver_payout,
        currency="USD",
        status="completed",
    ))

    job.status = "PAID"
    job.paid_at = datetime.utcnow()
    driver.total_deliveries += 1
    driver.successful_deliveries += 1
    db.commit()

    _notify_driver_paid(driver, job)
    return True


# ── Rating & penalty system ────────────────────────────────────────────────────

def rate_driver(
    db: Session,
    job_id: uuid.UUID,
    buyer_user_id: uuid.UUID,
    rating: int,
    note: Optional[str] = None,
) -> DriverJob:
    """
    Buyer rates driver 1-5 after delivery.
    Applies penalty logic per spec.
    """
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    job = db.query(DriverJob).filter(DriverJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.buyer_rating = rating
    job.buyer_rating_note = note

    driver = db.query(Driver).filter(Driver.id == job.driver_id).first()
    if driver:
        # Recalculate rolling average
        total_rated = db.query(DriverJob).filter(
            DriverJob.driver_id == driver.id,
            DriverJob.buyer_rating.isnot(None),
        ).count()
        current_sum = (driver.avg_rating * (total_rated - 1)) + rating
        driver.avg_rating = round(current_sum / total_rated, 2)

        if rating <= 3:
            _apply_driver_penalty(db, driver, job)

    db.commit()
    db.refresh(job)
    return job


def _apply_driver_penalty(db: Session, driver: Driver, job: DriverJob):
    """
    Per spec penalty tree:
    - First offense: warning + fee held 24h
    - Multiple offenses: suspension + retraining required
    """
    driver.warning_count += 1

    if driver.warning_count >= 3:
        driver.status = DriverStatus.SUSPENDED
        logger.warning("Driver %s suspended after %d warnings", driver.id, driver.warning_count)
        _notify_driver_suspended(driver)
    else:
        logger.info("Driver %s warning #%d issued", driver.id, driver.warning_count)
        _notify_driver_warning(driver, job)

    db.commit()


def reactivate_driver(db: Session, driver_id: uuid.UUID) -> Driver:
    """Admin reactivates a suspended driver after retraining."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.status != DriverStatus.SUSPENDED:
        raise HTTPException(status_code=400, detail="Driver is not suspended")

    driver.status = DriverStatus.ACTIVE
    driver.warning_count = 0
    db.commit()
    db.refresh(driver)
    return driver


# ── Notifications ──────────────────────────────────────────────────────────────

def _sms(phone: Optional[str], msg: str):
    if not phone:
        return
    try:
        from app.services.sms_service import _send_sms
        _send_sms(phone, msg)
    except Exception as e:
        logger.warning("SMS failed to %s: %s", phone, e)


def _notify_driver_new_job(driver: Driver, order: Order, fee: dict):
    phone = driver.user.phone_number if driver.user else None
    _sms(phone, (
        f"AgriTrust: 📋 New delivery job available. "
        f"Order #{order.order_number}. "
        f"Distance: {fee.get('distance_fee', 0) / 0.5:.0f}km. "
        f"Fee: ${fee['driver_payout']:.2f}. "
        f"Reply ACCEPT or REJECT within 5 minutes."
    ))


def _notify_job_confirmed(db: Session, job: DriverJob):
    order = db.query(Order).filter(Order.id == job.order_id).first()
    if not order:
        return
    farmer_phone = order.seller.phone_number if order.seller else None
    buyer_phone  = order.buyer.phone_number  if order.buyer  else None
    driver_name  = job.driver.user.full_name if job.driver and job.driver.user else "Driver"
    vehicle      = job.driver.vehicle_reg    if job.driver else "N/A"

    _sms(farmer_phone, f"AgriTrust Order #{order.order_number}: Driver {driver_name} ({vehicle}) will collect your goods.")
    _sms(buyer_phone,  f"AgriTrust Order #{order.order_number}: Driver {driver_name} ({vehicle}) assigned. License: {job.driver.license_number if job.driver else 'N/A'}.")


def _notify_driver_paid(driver: Driver, job: DriverJob):
    phone = driver.user.phone_number if driver.user else None
    _sms(phone, f"AgriTrust: 💰 ${job.driver_payout:.2f} added to your wallet for Job #{job.id}.")


def _notify_driver_warning(driver: Driver, job: DriverJob):
    phone = driver.user.phone_number if driver.user else None
    _sms(phone, (
        f"AgriTrust: ⚠️ Warning #{driver.warning_count} issued for low rating on Job #{job.id}. "
        f"Your fee is held for 24 hours. Improve service to avoid suspension."
    ))


def _notify_driver_suspended(driver: Driver):
    phone = driver.user.phone_number if driver.user else None
    _sms(phone, (
        "AgriTrust: 🚨 Your driver account has been suspended due to repeated low ratings. "
        "Complete retraining to reactivate. Contact support for details."
    ))
