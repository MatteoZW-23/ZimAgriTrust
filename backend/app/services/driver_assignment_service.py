"""
ZimAgritrust Driver Assignment Service
Manages driver assignment, availability, and dispatching for transport requests.
Integrates with the existing driver system and transport pricing.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Assignment Status Enum ─────────────────────────────────────────────────────

class AssignmentStatus(str, Enum):
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class AssignmentType(str, Enum):
    SYSTEM = "SYSTEM"
    ADMIN = "ADMIN"
    MANUAL = "MANUAL"


# ── Driver Availability ─────────────────────────────────────────────────────

@dataclass
class DriverCriteria:
    """Criteria for driver selection"""
    required_capacity_kg: float
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    pickup_district: Optional[str] = None
    vehicle_type: Optional[str] = None
    max_distance_km: Optional[float] = None


@dataclass
class DriverAssignment:
    """Driver assignment data"""
    transport_request_id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_type: str
    vehicle_registration: str
    transport_fee: float
    platform_commission: float
    driver_earnings: float
    estimated_distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    route_polyline: Optional[str] = None
    assigned_by: AssignmentType = AssignmentType.SYSTEM
    assigned_by_user_id: Optional[uuid.UUID] = None


# ── Driver Assignment Service ────────────────────────────────────────────────

class DriverAssignmentService:
    """Manages driver assignment and dispatching"""
    
    RESPONSE_TIMEOUT_MINUTES = 5
    MAX_REASSIGNMENT_ATTEMPTS = 3
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_available_drivers(
        self,
        criteria: DriverCriteria,
    ) -> List[Dict[str, Any]]:
        """
        Find available drivers matching criteria.
        
        Returns sorted by rating and proximity.
        """
        logger.info(
            f"Finding available drivers: capacity={criteria.required_capacity_kg}kg, "
            f"vehicle_type={criteria.vehicle_type}, district={criteria.pickup_district}"
        )
        
        from app.models.driver import Driver, DriverStatus
        
        # Query drivers table
        query = self.db.query(Driver).filter(
            Driver.status == DriverStatus.ACTIVE,
            Driver.vehicle_capacity_kg >= criteria.required_capacity_kg,
            Driver.is_available == True
        )
        
        # Filter by district if specified
        if criteria.pickup_district:
            query = query.filter(Driver.current_district == criteria.pickup_district)
        
        # Filter by vehicle type if specified
        if criteria.vehicle_type:
            query = query.filter(Driver.vehicle_type == criteria.vehicle_type)
        
        drivers = query.all()
        
        # Calculate distance if coordinates provided
        driver_results = []
        for driver in drivers:
            distance_km = None
            if criteria.pickup_latitude and criteria.pickup_longitude and driver.current_latitude and driver.current_longitude:
                distance_km = calculate_distance(
                    criteria.pickup_latitude, criteria.pickup_longitude,
                    driver.current_latitude, driver.current_longitude
                )
            
            # Filter by max_distance_km if specified
            if criteria.max_distance_km and distance_km and distance_km > criteria.max_distance_km:
                continue
            
            # Calculate driver score
            score = calculate_driver_score(
                {
                    "avg_rating": driver.avg_rating,
                    "success_rate": driver.successful_deliveries / driver.total_deliveries if driver.total_deliveries > 0 else 1.0
                },
                distance_km
            )
            
            driver_results.append({
                "id": str(driver.id),
                "user_id": str(driver.user_id),
                "vehicle_type": driver.vehicle_type,
                "vehicle_registration": driver.vehicle_reg,
                "vehicle_capacity_kg": driver.vehicle_capacity_kg,
                "avg_rating": driver.avg_rating,
                "total_deliveries": driver.total_deliveries,
                "successful_deliveries": driver.successful_deliveries,
                "current_latitude": driver.current_latitude,
                "current_longitude": driver.current_longitude,
                "distance_km": distance_km,
                "score": score
            })
        
        # Sort by score DESC
        driver_results.sort(key=lambda x: x["score"], reverse=True)
        
        return driver_results
    
    def auto_assign_driver(
        self,
        transport_request_id: uuid.UUID,
        criteria: DriverCriteria,
        transport_quote: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Automatically assign the best available driver.
        
        Uses algorithm to select optimal driver based on:
        - Rating
        - Proximity
        - Vehicle type match
        - Availability
        """
        logger.info(f"Auto-assigning driver for transport request {transport_request_id}")
        
        # Find available drivers
        available_drivers = self.find_available_drivers(criteria)
        
        if not available_drivers:
            logger.warning("No available drivers found")
            return None
        
        # Select best driver (first in sorted list)
        best_driver = available_drivers[0]
        
        # Calculate driver earnings
        transport_fee = transport_quote["total_amount"]
        platform_commission = transport_fee * 0.10  # 10% platform commission
        driver_earnings = transport_fee - platform_commission
        
        # Create assignment
        assignment = DriverAssignment(
            transport_request_id=transport_request_id,
            driver_id=best_driver["id"],
            vehicle_type=best_driver["vehicle_type"],
            vehicle_registration=best_driver["vehicle_registration"],
            transport_fee=transport_fee,
            platform_commission=platform_commission,
            driver_earnings=driver_earnings,
            estimated_distance_km=transport_quote.get("distance_km"),
            estimated_duration_minutes=transport_quote.get("estimated_minutes"),
            assigned_by=AssignmentType.SYSTEM,
        )
        
        return self.create_assignment(assignment)
    
    def manual_assign_driver(
        self,
        transport_request_id: uuid.UUID,
        driver_id: uuid.UUID,
        assigned_by_user_id: uuid.UUID,
        transport_quote: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Manually assign a specific driver (admin action).
        """
        logger.info(
            f"Manual driver assignment: request={transport_request_id}, "
            f"driver={driver_id}, by={assigned_by_user_id}"
        )
        
        from app.models.driver import Driver, DriverStatus
        
        # Validate driver exists and is active
        driver = self.db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        if driver.status != DriverStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Driver is not active")
        if not driver.is_available:
            raise HTTPException(status_code=400, detail="Driver is not available")
        
        # Validate driver has sufficient capacity
        required_capacity = transport_quote.get("required_capacity_kg", 0)
        if driver.vehicle_capacity_kg < required_capacity:
            raise HTTPException(status_code=400, detail="Driver has insufficient capacity")
        
        # Calculate driver earnings
        transport_fee = transport_quote["total_amount"]
        platform_commission = transport_fee * 0.10
        driver_earnings = transport_fee - platform_commission
        
        assignment = DriverAssignment(
            transport_request_id=transport_request_id,
            driver_id=driver_id,
            vehicle_type=driver.vehicle_type,
            vehicle_registration=driver.vehicle_reg,
            transport_fee=transport_fee,
            platform_commission=platform_commission,
            driver_earnings=driver_earnings,
            assigned_by=AssignmentType.ADMIN,
            assigned_by_user_id=assigned_by_user_id,
        )
        
        result = self.create_assignment(assignment)
        
        # Notify driver
        try:
            from app.services.notification_service import notification_service
            if driver.user:
                notification_service._send_sms(
                    driver.user.phone_number,
                    f"ZimAgritrust: You have been manually assigned to transport request #{transport_request_id}. Fee: ${driver_earnings:.2f}"
                )
        except Exception as e:
            logger.warning(f"Failed to notify driver: {e}")
        
        return result
    
    def create_assignment(
        self,
        assignment: DriverAssignment,
    ) -> Dict[str, Any]:
        """
        Create a driver assignment record.
        """
        logger.info(
            f"Creating driver assignment: driver={assignment.driver_id}, "
            f"fee=${assignment.transport_fee:.2f}"
        )
        
        from app.models.driver import DriverJob, DriverJobStatus
        from app.models.transaction import Order
        
        # Get the order from transport_request_id
        order = self.db.query(Order).filter(Order.id == assignment.transport_request_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Transport request (order) not found")
        
        # Create DriverJob record
        job = DriverJob(
            driver_id=assignment.driver_id,
            order_id=assignment.transport_request_id,
            distance_km=assignment.estimated_distance_km or 0,
            base_fee=assignment.transport_fee * 0.5,  # Base fee portion
            distance_fee=assignment.transport_fee * 0.3,  # Distance fee portion
            total_transport_fee=assignment.transport_fee,
            platform_commission=assignment.platform_commission,
            driver_payout=assignment.driver_earnings,
            status=DriverJobStatus.PENDING,
            assigned_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Update order with transport fee breakdown
        order.transport_fee = assignment.transport_fee
        order.transport_commission = assignment.platform_commission
        order.driver_payout = assignment.driver_earnings
        self.db.commit()
        
        # Send notification to driver
        try:
            from app.services.notification_service import notification_service
            driver = self.db.query(Driver).filter(Driver.id == assignment.driver_id).first()
            if driver and driver.user:
                notification_service._send_sms(
                    driver.user.phone_number,
                    f"ZimAgritrust: 📋 New delivery job available. Order #{order.order_number}. Distance: {assignment.estimated_distance_km or 0}km. Fee: ${assignment.driver_earnings:.2f}. Reply ACCEPT or REJECT within 5 minutes."
                )
        except Exception as e:
            logger.warning(f"Failed to notify driver: {e}")
        
        # Send notification to buyer/farmer
        try:
            from app.services.notification_service import notification_service
            if order.buyer:
                notification_service._send_sms(
                    order.buyer.phone_number,
                    f"ZimAgritrust: Driver assigned to order #{order.order_number}. Transport fee: ${assignment.transport_fee:.2f}"
                )
            if order.seller:
                notification_service._send_sms(
                    order.seller.phone_number,
                    f"ZimAgritrust: Driver assigned to order #{order.order_number}. Pickup scheduled."
                )
        except Exception as e:
            logger.warning(f"Failed to notify buyer/farmer: {e}")
        
        return {
            "id": str(job.id),
            "transport_request_id": str(assignment.transport_request_id),
            "driver_id": str(assignment.driver_id),
            "vehicle_type": assignment.vehicle_type,
            "vehicle_registration": assignment.vehicle_registration,
            "transport_fee": assignment.transport_fee,
            "platform_commission": assignment.platform_commission,
            "driver_earnings": assignment.driver_earnings,
            "estimated_distance_km": assignment.estimated_distance_km,
            "estimated_duration_minutes": assignment.estimated_duration_minutes,
            "status": AssignmentStatus.ASSIGNED.value,
            "assigned_at": job.assigned_at.isoformat() if job.assigned_at else datetime.now(timezone.utc).isoformat(),
            "assigned_by": assignment.assigned_by.value,
        }
    
    def accept_assignment(
        self,
        assignment_id: uuid.UUID,
        driver_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Driver accepts a job assignment.
        
        Must be accepted within RESPONSE_TIMEOUT_MINUTES.
        """
        logger.info(f"Driver {driver_id} accepting assignment {assignment_id}")
        
        from app.models.driver import DriverJob, DriverJobStatus, Driver
        
        # Validate assignment exists
        job = self.db.query(DriverJob).filter(DriverJob.id == assignment_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Validate assignment belongs to driver
        if job.driver_id != driver_id:
            raise HTTPException(status_code=403, detail="Not your job")
        
        # Validate assignment status is ASSIGNED
        if job.status != DriverJobStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Job already {job.status.value}")
        
        # Check if within timeout window
        if job.assigned_at:
            time_elapsed = datetime.now(timezone.utc) - job.assigned_at
            if time_elapsed.total_seconds() > self.RESPONSE_TIMEOUT_MINUTES * 60:
                raise HTTPException(status_code=400, detail="Assignment timed out")
        
        # Update status to ACCEPTED
        job.status = DriverJobStatus.ACCEPTED
        job.accepted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        
        # Notify buyer/farmer
        try:
            from app.services.notification_service import notification_service
            driver = self.db.query(Driver).filter(Driver.id == driver_id).first()
            if job.order:
                if job.order.buyer:
                    notification_service._send_sms(
                        job.order.buyer.phone_number,
                        f"ZimAgritrust: Driver {driver.user.full_name if driver and driver.user else 'Driver'} has accepted order #{job.order.order_number}. Pickup scheduled."
                    )
                if job.order.seller:
                    notification_service._send_sms(
                        job.order.seller.phone_number,
                        f"ZimAgritrust: Driver {driver.user.full_name if driver and driver.user else 'Driver'} accepted order #{job.order.order_number}. Will collect goods soon."
                    )
        except Exception as e:
            logger.warning(f"Failed to notify buyer/farmer: {e}")
        
        # Create delivery record
        try:
            from app.models.logistics import OrderDelivery
            delivery = OrderDelivery(
                order_id=job.order_id,
                driver_id=driver_id,
                status="ASSIGNED",
                assigned_at=datetime.now(timezone.utc),
            )
            self.db.add(delivery)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to create delivery record: {e}")
        
        return {
            "id": str(assignment_id),
            "status": AssignmentStatus.ACCEPTED.value,
            "accepted_at": job.accepted_at.isoformat() if job.accepted_at else datetime.now(timezone.utc).isoformat(),
        }
    
    def reject_assignment(
        self,
        assignment_id: uuid.UUID,
        driver_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Driver rejects a job assignment.
        
        System attempts to reassign to next available driver.
        """
        logger.info(f"Driver {driver_id} rejecting assignment {assignment_id}: {reason}")
        
        from app.models.driver import DriverJob, DriverJobStatus
        from app.models.transaction import Order
        from app.models.logistics import OrderDelivery
        
        # Validate assignment exists
        job = self.db.query(DriverJob).filter(DriverJob.id == assignment_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Validate assignment belongs to driver
        if job.driver_id != driver_id:
            raise HTTPException(status_code=403, detail="Not your job")
        
        # Update status to REJECTED
        job.status = DriverJobStatus.REJECTED
        job.driver_rejection_reason = reason
        job.rejected_at = datetime.now(timezone.utc)
        job.reassignment_attempts = (job.reassignment_attempts or 0) + 1
        self.db.commit()
        
        # Attempt reassignment
        order = self.db.query(Order).filter(Order.id == job.order_id).first()
        if order and job.reassignment_attempts < self.MAX_REASSIGNMENT_ATTEMPTS:
            try:
                from app.models.logistics import OrderDelivery
                delivery = self.db.query(OrderDelivery).filter(OrderDelivery.order_id == order.id).first()
                if delivery:
                    pickup_district = delivery.pickup_address or ""
                    criteria = DriverCriteria(
                        required_capacity_kg=order.quantity or 100,
                        pickup_district=pickup_district[:50] if pickup_district else None,
                    )
                    transport_quote = {
                        "total_amount": job.total_transport_fee,
                        "distance_km": job.distance_km,
                    }
                    new_job = self.auto_assign_driver(order.id, criteria, transport_quote)
                    if new_job:
                        logger.info(f"Reassigned job {assignment_id} to driver {new_job['driver_id']}")
                        return {
                            "id": str(assignment_id),
                            "status": AssignmentStatus.REJECTED.value,
                            "rejected_at": job.rejected_at.isoformat() if job.rejected_at else datetime.now(timezone.utc).isoformat(),
                            "reason": reason,
                            "reassigned_to": new_job.get("driver_id"),
                        }
            except Exception as e:
                logger.warning(f"Reassignment failed: {e}")
        
        # If max attempts reached, escalate to admin
        if job.reassignment_attempts >= self.MAX_REASSIGNMENT_ATTEMPTS:
            logger.warning(f"Max reassignment attempts reached for job {assignment_id}, escalating to admin")
            # TODO: Implement admin escalation notification
        
        return {
            "id": str(assignment_id),
            "status": AssignmentStatus.REJECTED.value,
            "rejected_at": job.rejected_at.isoformat() if job.rejected_at else datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        }
    
    def cancel_assignment(
        self,
        assignment_id: uuid.UUID,
        cancelled_by_user_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel a driver assignment (admin action).
        """
        logger.info(f"Cancelling assignment {assignment_id} by {cancelled_by_user_id}")
        
        from app.models.driver import DriverJob, DriverJobStatus, Driver
        from app.models.transaction import Order
        
        # Validate assignment exists
        job = self.db.query(DriverJob).filter(DriverJob.id == assignment_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update status to CANCELLED
        job.status = DriverJobStatus.CANCELLED
        job.cancelled_at = datetime.now(timezone.utc)
        job.cancelled_by = cancelled_by_user_id
        job.cancellation_reason = reason
        self.db.commit()
        
        # Notify driver
        try:
            from app.services.notification_service import notification_service
            driver = self.db.query(Driver).filter(Driver.id == job.driver_id).first()
            if driver and driver.user:
                notification_service._send_sms(
                    driver.user.phone_number,
                    f"ZimAgritrust: Your job assignment has been cancelled. Reason: {reason or 'Admin action'}."
                )
        except Exception as e:
            logger.warning(f"Failed to notify driver: {e}")
        
        # Notify buyer/farmer
        try:
            from app.services.notification_service import notification_service
            if job.order:
                if job.order.buyer:
                    notification_service._send_sms(
                        job.order.buyer.phone_number,
                        f"ZimAgritrust: Driver assignment cancelled for order #{job.order.order_number}. Reason: {reason or 'Admin action'}."
                    )
                if job.order.seller:
                    notification_service._send_sms(
                        job.order.seller.phone_number,
                        f"ZimAgritrust: Driver assignment cancelled for order #{job.order.order_number}. Reason: {reason or 'Admin action'}."
                    )
        except Exception as e:
            logger.warning(f"Failed to notify buyer/farmer: {e}")
        
        # Attempt reassignment if needed
        if job.order and reason != "driver_unavailable":
            try:
                from app.models.logistics import OrderDelivery
                delivery = self.db.query(OrderDelivery).filter(OrderDelivery.order_id == job.order.id).first()
                if delivery:
                    pickup_district = delivery.pickup_address or ""
                    criteria = DriverCriteria(
                        required_capacity_kg=job.order.quantity or 100,
                        pickup_district=pickup_district[:50] if pickup_district else None,
                    )
                    transport_quote = {
                        "total_amount": job.total_transport_fee,
                        "distance_km": job.distance_km,
                    }
                    new_job = self.auto_assign_driver(job.order.id, criteria, transport_quote)
                    if new_job:
                        logger.info(f"Reassigned cancelled job {assignment_id} to driver {new_job['driver_id']}")
            except Exception as e:
                logger.warning(f"Reassignment after cancel failed: {e}")
        
        return {
            "id": str(assignment_id),
            "status": AssignmentStatus.CANCELLED.value,
            "cancelled_at": job.cancelled_at.isoformat() if job.cancelled_at else datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        }
    
    def complete_assignment(
        self,
        assignment_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Mark assignment as completed after successful delivery.
        
        Triggers driver payout.
        """
        logger.info(f"Completing assignment {assignment_id}")
        
        from app.models.driver import DriverJob, DriverJobStatus, Driver
        from app.services.wallet_service import wallet_service
        from app.models.transaction import Transaction, TransactionType
        
        # Validate assignment exists
        job = self.db.query(DriverJob).filter(DriverJob.id == assignment_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update status to COMPLETED
        job.status = DriverJobStatus.PAID
        job.completed_at = datetime.now(timezone.utc)
        job.paid_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # Trigger driver payout via settlement service
        driver = self.db.query(Driver).filter(Driver.id == job.driver_id).first()
        if driver:
            try:
                wallet_service.deposit(self.db, driver.user_id, job.driver_payout, "USD", reference=f"JOB-{job.id}")
                
                # Log transaction
                self.db.add(Transaction(
                    order_id=job.order_id,
                    user_id=driver.user_id,
                    type=TransactionType.ESCROW_RELEASE,
                    amount=job.driver_payout,
                    currency="USD",
                    status="completed",
                ))
                
                # Update driver stats
                driver.total_deliveries += 1
                driver.successful_deliveries += 1
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to process driver payout: {e}")
        
        # Notify driver
        try:
            from app.services.notification_service import notification_service
            if driver and driver.user:
                notification_service._send_sms(
                    driver.user.phone_number,
                    f"ZimAgritrust: 💰 ${job.driver_payout:.2f} added to your wallet for Job #{job.id}."
                )
        except Exception as e:
            logger.warning(f"Failed to notify driver: {e}")
        
        return {
            "id": str(assignment_id),
            "status": AssignmentStatus.COMPLETED.value,
            "completed_at": job.completed_at.isoformat() if job.completed_at else datetime.now(timezone.utc).isoformat(),
        }
    
    def check_response_timeouts(self) -> int:
        """
        Check for assignments that have exceeded response timeout.
        
        Reassign to next available driver or escalate to admin.
        This is typically run as a scheduled job.
        """
        logger.info("Checking for assignment response timeouts")
        
        from app.models.driver import DriverJob, DriverJobStatus
        from app.models.transaction import Order
        from app.models.logistics import OrderDelivery
        
        timeout_count = 0
        timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=self.RESPONSE_TIMEOUT_MINUTES)
        
        # Query assignments where status = ASSIGNED and assigned_at < timeout threshold
        timed_out_jobs = self.db.query(DriverJob).filter(
            DriverJob.status == DriverJobStatus.PENDING,
            DriverJob.assigned_at < timeout_threshold
        ).all()
        
        for job in timed_out_jobs:
            timeout_count += 1
            logger.warning(f"Job {job.id} timed out, reassigning")
            
            # Update status to REJECTED
            job.status = DriverJobStatus.REJECTED
            job.driver_rejection_reason = "TIMEOUT"
            job.reassignment_attempts = (job.reassignment_attempts or 0) + 1
            self.db.commit()
            
            # Attempt reassignment
            order = self.db.query(Order).filter(Order.id == job.order_id).first()
            if order and job.reassignment_attempts < self.MAX_REASSIGNMENT_ATTEMPTS:
                try:
                    delivery = self.db.query(OrderDelivery).filter(OrderDelivery.order_id == order.id).first()
                    if delivery:
                        pickup_district = delivery.pickup_address or ""
                        criteria = DriverCriteria(
                            required_capacity_kg=order.quantity or 100,
                            pickup_district=pickup_district[:50] if pickup_district else None,
                        )
                        transport_quote = {
                            "total_amount": job.total_transport_fee,
                            "distance_km": job.distance_km,
                        }
                        new_job = self.auto_assign_driver(order.id, criteria, transport_quote)
                        if new_job:
                            logger.info(f"Reassigned timed-out job {job.id} to driver {new_job['driver_id']}")
                except Exception as e:
                    logger.warning(f"Reassignment failed for timed-out job {job.id}: {e}")
            
            # If max attempts, escalate to admin
            if job.reassignment_attempts >= self.MAX_REASSIGNMENT_ATTEMPTS:
                logger.warning(f"Max reassignment attempts reached for timed-out job {job.id}, escalating to admin")
                # TODO: Implement admin escalation notification
        
        return timeout_count
    
    def get_driver_assignments(
        self,
        driver_id: uuid.UUID,
        status: Optional[AssignmentStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all assignments for a driver.
        """
        from app.models.driver import DriverJob, DriverJobStatus
        from app.models.transaction import Order
        
        # Query driver_assignments table
        query = self.db.query(DriverJob).filter(DriverJob.driver_id == driver_id)
        
        # Filter by status if provided
        if status:
            query = query.filter(DriverJob.status == DriverJobStatus(status.value))
        
        jobs = query.order_by(DriverJob.assigned_at.desc()).all()
        
        # Return assignments
        assignments = []
        for job in jobs:
            order = self.db.query(Order).filter(Order.id == job.order_id).first()
            assignments.append({
                "id": str(job.id),
                "order_id": str(job.order_id),
                "order_number": order.order_number if order else None,
                "distance_km": job.distance_km,
                "total_transport_fee": job.total_transport_fee,
                "driver_payout": job.driver_payout,
                "status": job.status.value,
                "assigned_at": job.assigned_at.isoformat() if job.assigned_at else None,
                "accepted_at": job.accepted_at.isoformat() if job.accepted_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "paid_at": job.paid_at.isoformat() if job.paid_at else None,
            })
        
        return assignments
    
    def get_transport_assignments(
        self,
        transport_request_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all assignments for a transport request.
        """
        from app.models.driver import DriverJob, DriverJobStatus, Driver
        from app.models.transaction import Order
        
        # Query driver_assignments table
        jobs = self.db.query(DriverJob).filter(
            DriverJob.order_id == transport_request_id
        ).order_by(DriverJob.assigned_at.asc()).all()
        
        # Return assignments (including reassignments)
        assignments = []
        for job in jobs:
            driver = self.db.query(Driver).filter(Driver.id == job.driver_id).first()
            order = self.db.query(Order).filter(Order.id == job.order_id).first()
            assignments.append({
                "id": str(job.id),
                "driver_id": str(job.driver_id),
                "driver_name": driver.user.full_name if driver and driver.user else None,
                "vehicle_type": driver.vehicle_type if driver else None,
                "vehicle_registration": driver.vehicle_reg if driver else None,
                "distance_km": job.distance_km,
                "total_transport_fee": job.total_transport_fee,
                "driver_payout": job.driver_payout,
                "status": job.status.value,
                "assigned_at": job.assigned_at.isoformat() if job.assigned_at else None,
                "accepted_at": job.accepted_at.isoformat() if job.accepted_at else None,
                "rejected_at": job.rejected_at.isoformat() if job.rejected_at else None,
                "rejection_reason": job.driver_rejection_reason,
                "reassignment_attempts": job.reassignment_attempts,
            })
        
        return assignments
    
    def get_driver_earnings(
        self,
        driver_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculate driver earnings for a period.
        """
        from app.models.driver import DriverJob, DriverJobStatus
        
        # Query driver_assignments table
        query = self.db.query(DriverJob).filter(
            DriverJob.driver_id == driver_id,
            DriverJob.status == DriverJobStatus.PAID
        )
        
        # Filter by date range if provided
        if start_date:
            query = query.filter(DriverJob.paid_at >= start_date)
        if end_date:
            query = query.filter(DriverJob.paid_at <= end_date)
        
        jobs = query.all()
        
        # Sum driver_earnings
        total_earnings = sum(job.driver_payout for job in jobs)
        
        # Count completed deliveries
        completed_deliveries = len(jobs)
        
        # Calculate average per delivery
        average_per_delivery = total_earnings / completed_deliveries if completed_deliveries > 0 else 0.0
        
        return {
            "driver_id": str(driver_id),
            "total_earnings": round(total_earnings, 2),
            "completed_deliveries": completed_deliveries,
            "average_per_delivery": round(average_per_delivery, 2),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    
    def update_driver_location(
        self,
        driver_id: uuid.UUID,
        latitude: float,
        longitude: float,
        accuracy_meters: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Update driver's current location.
        
        Used for real-time tracking and proximity calculations.
        """
        from app.models.driver import Driver
        
        # Update driver's current_location in drivers table
        driver = self.db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        driver.current_latitude = latitude
        driver.current_longitude = longitude
        driver.last_location_update_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # Store in delivery_tracking if on active delivery
        try:
            from app.models.driver import DriverJob, DriverJobStatus
            from app.models.logistics import DeliveryTracking
            
            active_job = self.db.query(DriverJob).filter(
                DriverJob.driver_id == driver_id,
                DriverJob.status.in_([DriverJobStatus.ACCEPTED, DriverJobStatus.IN_TRANSIT])
            ).first()
            
            if active_job:
                tracking = DeliveryTracking(
                    delivery_id=active_job.id,
                    driver_id=driver_id,
                    latitude=latitude,
                    longitude=longitude,
                    accuracy_meters=accuracy_meters,
                    recorded_at=datetime.now(timezone.utc),
                )
                self.db.add(tracking)
                self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to store location in delivery_tracking: {e}")
        
        return {
            "driver_id": str(driver_id),
            "latitude": latitude,
            "longitude": longitude,
            "updated_at": driver.last_location_update_at.isoformat() if driver.last_location_update_at else datetime.now(timezone.utc).isoformat(),
        }


# ── Helper Functions ─────────────────────────────────────────────────────────

def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate distance between two points using Haversine formula.
    """
    from math import radians, cos, sin, asin, sqrt
    
    lat1, lon1 = radians(lat1), radians(lon1)
    lat2, lon2 = radians(lat2), radians(lon2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    
    r = 6371  # Earth's radius in kilometers
    
    return c * r


def calculate_driver_score(
    driver: Dict[str, Any],
    distance_km: Optional[float] = None,
) -> float:
    """
    Calculate a composite score for driver selection.
    
    Factors:
    - Rating (weight: 0.5)
    - Proximity (weight: 0.3)
    - Success rate (weight: 0.2)
    """
    rating = driver.get("avg_rating", 4.0)
    success_rate = driver.get("success_rate", 0.95)
    
    # Normalize rating to 0-1 (assuming max 5.0)
    rating_score = rating / 5.0
    
    # Calculate proximity score (closer is better)
    if distance_km:
        # Score decreases with distance (0-50km range)
        proximity_score = max(0, 1 - (distance_km / 50))
    else:
        proximity_score = 0.5  # Neutral if no distance
    
    # Composite score
    score = (
        rating_score * 0.5 +
        proximity_score * 0.3 +
        success_rate * 0.2
    )
    
    return round(score, 3)
