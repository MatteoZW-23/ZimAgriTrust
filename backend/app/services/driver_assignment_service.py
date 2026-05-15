"""
ZimAgritrust Driver Assignment Service
Manages driver assignment, availability, and dispatching for transport requests.
Integrates with the existing driver system and transport pricing.
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
        
        # TODO: Query drivers table
        # TODO: Filter by:
        #   - status = ACTIVE
        #   - vehicle_capacity_kg >= required_capacity_kg
        #   - current_district = pickup_district (if specified)
        #   - vehicle_type = preferred type (if specified)
        # TODO: Calculate distance if coordinates provided
        # TODO: Filter by max_distance_km (if specified)
        # TODO: Sort by: rating DESC, distance ASC
        # TODO: Return list of available drivers
        
        return []
    
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
        
        # TODO: Validate driver exists and is active
        # TODO: Validate driver has sufficient capacity
        # TODO: Calculate driver earnings
        # TODO: Create assignment with assigned_by = ADMIN
        # TODO: Notify driver
        # TODO: Notify buyer/farmer
        
        transport_fee = transport_quote["total_amount"]
        platform_commission = transport_fee * 0.10
        driver_earnings = transport_fee - platform_commission
        
        assignment = DriverAssignment(
            transport_request_id=transport_request_id,
            driver_id=driver_id,
            vehicle_type="van",  # TODO: Get from driver
            vehicle_registration="",  # TODO: Get from driver
            transport_fee=transport_fee,
            platform_commission=platform_commission,
            driver_earnings=driver_earnings,
            assigned_by=AssignmentType.ADMIN,
            assigned_by_user_id=assigned_by_user_id,
        )
        
        return self.create_assignment(assignment)
    
    def create_assignment(
        self,
        assignment: DriverAssignment,
    ) -> Dict[str, Any]:
        """
        Create a driver assignment record.
        """
        logger.info(
            f"Creating driver assignment: driver={assignment.driver_id}, "
            "fee=${assignment.transport_fee:.2f}"
        )
        
        # TODO: Insert into driver_assignments table
        # TODO: Generate route using Google Maps API
        # TODO: Update transport_request status to ASSIGNED
        # TODO: Send notification to driver
        # TODO: Send notification to buyer/farmer
        # TODO: Schedule response timeout check
        
        assignment_id = uuid.uuid4()
        
        return {
            "id": str(assignment_id),
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
            "assigned_at": datetime.utcnow().isoformat(),
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
        
        # TODO: Validate assignment exists
        # TODO: Validate assignment belongs to driver
        # TODO: Validate assignment status is ASSIGNED
        # TODO: Check if within timeout window
        # TODO: Update status to ACCEPTED
        # TODO: Set driver_response_at
        # TODO: Notify buyer/farmer
        # TODO: Create delivery record
        
        return {
            "id": str(assignment_id),
            "status": AssignmentStatus.ACCEPTED.value,
            "accepted_at": datetime.utcnow().isoformat(),
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
        
        # TODO: Validate assignment exists
        # TODO: Validate assignment belongs to driver
        # TODO: Update status to REJECTED
        # TODO: Set driver_rejection_reason
        # TODO: Attempt reassignment
        # TODO: Track reassignment attempts
        # TODO: If max attempts reached, escalate to admin
        
        return {
            "id": str(assignment_id),
            "status": AssignmentStatus.REJECTED.value,
            "rejected_at": datetime.utcnow().isoformat(),
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
        
        # TODO: Validate assignment exists
        # TODO: Update status to CANCELLED
        # TODO: Notify driver
        # TODO: Notify buyer/farmer
        # TODO: Attempt reassignment if needed
        
        return {
            "id": str(assignment_id),
            "status": AssignmentStatus.CANCELLED.value,
            "cancelled_at": datetime.utcnow().isoformat(),
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
        
        # TODO: Validate assignment exists
        # TODO: Update status to COMPLETED
        # TODO: Set completed_at
        # TODO: Trigger driver payout via settlement service
        # TODO: Update driver stats (total_deliveries, successful_deliveries)
        # TODO: Notify driver
        
        return {
            "id": str(assignment_id),
            "status": AssignmentStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat(),
        }
    
    def check_response_timeouts(self) -> int:
        """
        Check for assignments that have exceeded response timeout.
        
        Reassign to next available driver or escalate to admin.
        This is typically run as a scheduled job.
        """
        logger.info("Checking for assignment response timeouts")
        
        timeout_count = 0
        
        # TODO: Query assignments where:
        #   - status = ASSIGNED
        #   - assigned_at < NOW - RESPONSE_TIMEOUT_MINUTES
        # TODO: For each timed-out assignment:
        #   - Update status to REJECTED
        #   - Set driver_rejection_reason = "TIMEOUT"
        #   - Attempt reassignment
        #   - Track reassignment attempts
        #   - If max attempts, escalate to admin
        
        return timeout_count
    
    def get_driver_assignments(
        self,
        driver_id: uuid.UUID,
        status: Optional[AssignmentStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all assignments for a driver.
        """
        # TODO: Query driver_assignments table
        # TODO: Filter by driver_id
        # TODO: Filter by status if provided
        # TODO: Return assignments
        
        return []
    
    def get_transport_assignments(
        self,
        transport_request_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all assignments for a transport request.
        """
        # TODO: Query driver_assignments table
        # TODO: Filter by transport_request_id
        # TODO: Return assignments (including reassignments)
        
        return []
    
    def get_driver_earnings(
        self,
        driver_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculate driver earnings for a period.
        """
        # TODO: Query driver_assignments table
        # TODO: Filter by driver_id
        # TODO: Filter by date range if provided
        # TODO: Filter by status = COMPLETED
        # TODO: Sum driver_earnings
        # TODO: Count completed deliveries
        # TODO: Calculate average per delivery
        
        return {
            "driver_id": str(driver_id),
            "total_earnings": 0.0,
            "completed_deliveries": 0,
            "average_per_delivery": 0.0,
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
        # TODO: Update driver's current_location in drivers table
        # TODO: Update last_location_update_at
        # TODO: Store in delivery_tracking if on active delivery
        
        return {
            "driver_id": str(driver_id),
            "latitude": latitude,
            "longitude": longitude,
            "updated_at": datetime.utcnow().isoformat(),
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
