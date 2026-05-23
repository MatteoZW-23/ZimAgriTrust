"""
ZimAgritrust Delivery Tracking Service
Manages real-time location tracking, ETA calculation, and delivery verification.
Integrates with GPS, geofencing, and route monitoring.
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

from app.models.logistics import DeliveryStatus as ModelDeliveryStatus

logger = logging.getLogger(__name__)


# ── Tracking Status Enum ─────────────────────────────────────────────────────

class TrackingStatus(str, Enum):
    MOVING = "MOVING"
    STOPPED = "STOPPED"
    IDLE = "IDLE"


# Use DeliveryStatus from models to avoid duplication
DeliveryStatus = ModelDeliveryStatus


# ── Location Data ───────────────────────────────────────────────────────────

@dataclass
class LocationUpdate:
    """Location update data"""
    delivery_id: uuid.UUID
    driver_id: uuid.UUID
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    altitude: Optional[float] = None
    speed_kmh: Optional[float] = None
    heading_degrees: Optional[float] = None
    status: TrackingStatus = TrackingStatus.MOVING
    device_id: Optional[str] = None
    battery_level: Optional[int] = None


@dataclass
class Geofence:
    """Geofence definition"""
    latitude: float
    longitude: float
    radius_meters: float
    name: str


# ── Delivery Tracking Service ───────────────────────────────────────────────

class DeliveryTrackingService:
    """Manages real-time delivery tracking"""
    
    LOCATION_UPDATE_INTERVAL_SECONDS = 30
    GEOFENCE_THRESHOLD_METERS = 100
    ETA_UPDATE_THRESHOLD_MINUTES = 5
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_delivery(
        self,
        order_id: uuid.UUID,
        driver_assignment_id: Optional[uuid.UUID],
        pickup_address: str,
        pickup_latitude: Optional[float],
        pickup_longitude: Optional[float],
        delivery_address: str,
        delivery_latitude: Optional[float],
        delivery_longitude: Optional[float],
    ) -> Dict[str, Any]:
        """
        Create a delivery record.
        """
        logger.info(f"Creating delivery for order {order_id}")
        
        from app.models.logistics import OrderDelivery
        
        # Insert into deliveries table
        delivery = OrderDelivery(
            order_id=order_id,
            driver_id=driver_assignment_id,
            pickup_address=pickup_address,
            pickup_latitude=pickup_latitude,
            pickup_longitude=pickup_longitude,
            delivery_address=delivery_address,
            delivery_latitude=delivery_latitude,
            delivery_longitude=delivery_longitude,
            status=DeliveryStatus.PENDING.value,
            created_at=datetime.utcnow(),
        )
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)
        
        # Calculate initial ETA
        if pickup_latitude and pickup_longitude and delivery_latitude and delivery_longitude:
            distance_km = calculate_distance(pickup_latitude, pickup_longitude, delivery_latitude, delivery_longitude) / 1000
            eta_minutes = estimate_eta(distance_km, 40)  # Assume 40 km/h average speed
            delivery.estimated_arrival_time = datetime.utcnow() + timedelta(minutes=eta_minutes)
            delivery.estimated_distance_km = distance_km
            self.db.commit()
        
        return {
            "id": str(delivery.id),
            "order_id": str(order_id),
            "driver_assignment_id": str(driver_assignment_id) if driver_assignment_id else None,
            "status": delivery.status,
            "pickup_address": pickup_address,
            "delivery_address": delivery_address,
            "estimated_distance_km": delivery.estimated_distance_km,
            "estimated_arrival_time": delivery.estimated_arrival_time.isoformat() if delivery.estimated_arrival_time else None,
            "created_at": delivery.created_at.isoformat() if delivery.created_at else datetime.utcnow().isoformat(),
        }
    
    def update_location(
        self,
        location: LocationUpdate,
    ) -> Dict[str, Any]:
        """
        Update driver location for real-time tracking.
        """
        logger.info(
            f"Updating location for delivery {location.delivery_id}: "
            f"lat={location.latitude}, lon={location.longitude}"
        )
        
        from app.models.logistics import OrderDelivery, DeliveryTracking
        
        # Insert into delivery_tracking table
        tracking = DeliveryTracking(
            delivery_id=location.delivery_id,
            driver_id=location.driver_id,
            latitude=location.latitude,
            longitude=location.longitude,
            accuracy_meters=location.accuracy_meters,
            altitude=location.altitude,
            speed_kmh=location.speed_kmh,
            heading_degrees=location.heading_degrees,
            status=location.status.value,
            device_id=location.device_id,
            battery_level=location.battery_level,
            recorded_at=datetime.utcnow(),
        )
        self.db.add(tracking)
        self.db.commit()
        self.db.refresh(tracking)
        
        # Update delivery current_location
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == location.delivery_id).first()
        if delivery:
            delivery.current_latitude = location.latitude
            delivery.current_longitude = location.longitude
            delivery.last_location_update_at = datetime.utcnow()
            self.db.commit()
        
        # Check geofences (pickup, delivery)
        geofence_status = self.check_geofences(location.delivery_id, location.latitude, location.longitude)
        
        # Update delivery status based on geofence
        if delivery and geofence_status["pickup_geofence"] and delivery.status == DeliveryStatus.ASSIGNED.value:
            self.update_delivery_status(location.delivery_id, DeliveryStatus.AT_PICKUP)
        elif delivery and geofence_status["delivery_geofence"] and delivery.status == DeliveryStatus.IN_TRANSIT.value:
            self.update_delivery_status(location.delivery_id, DeliveryStatus.AT_DELIVERY)
        
        # Recalculate ETA if needed
        if delivery and delivery.estimated_arrival_time:
            time_since_eta = datetime.utcnow() - delivery.estimated_arrival_time.replace(tzinfo=None)
            if abs(time_since_eta.total_seconds()) > self.ETA_UPDATE_THRESHOLD_MINUTES * 60:
                self.calculate_eta(location.delivery_id)
        
        # Check for route deviations
        deviation = self.check_route_deviation(location.delivery_id)
        if deviation["alert_required"]:
            logger.warning(f"Route deviation detected for delivery {location.delivery_id}: {deviation['deviation_meters']}m")
        
        return {
            "id": str(tracking.id),
            "delivery_id": str(location.delivery_id),
            "latitude": location.latitude,
            "longitude": location.longitude,
            "status": location.status.value,
            "recorded_at": tracking.recorded_at.isoformat() if tracking.recorded_at else datetime.utcnow().isoformat(),
        }
    
    def check_geofences(
        self,
        delivery_id: uuid.UUID,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """
        Check if location is within pickup or delivery geofence.
        """
        from app.models.logistics import OrderDelivery
        
        # Get delivery details
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery:
            return {
                "delivery_id": str(delivery_id),
                "pickup_geofence": False,
                "delivery_geofence": False,
                "distance_to_pickup_m": 0,
                "distance_to_delivery_m": 0,
            }
        
        # Calculate distance to pickup location
        distance_to_pickup_m = 0
        pickup_geofence = False
        if delivery.pickup_latitude and delivery.pickup_longitude:
            distance_to_pickup_m = calculate_distance(
                latitude, longitude,
                delivery.pickup_latitude, delivery.pickup_longitude
            )
            pickup_geofence = distance_to_pickup_m <= self.GEOFENCE_THRESHOLD_METERS
        
        # Calculate distance to delivery location
        distance_to_delivery_m = 0
        delivery_geofence = False
        if delivery.delivery_latitude and delivery.delivery_longitude:
            distance_to_delivery_m = calculate_distance(
                latitude, longitude,
                delivery.delivery_latitude, delivery.delivery_longitude
            )
            delivery_geofence = distance_to_delivery_m <= self.GEOFENCE_THRESHOLD_METERS
        
        return {
            "delivery_id": str(delivery_id),
            "pickup_geofence": pickup_geofence,
            "delivery_geofence": delivery_geofence,
            "distance_to_pickup_m": round(distance_to_pickup_m, 2),
            "distance_to_delivery_m": round(distance_to_delivery_m, 2),
        }
    
    def update_delivery_status(
        self,
        delivery_id: uuid.UUID,
        new_status: DeliveryStatus,
        updated_by: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update delivery status.
        """
        logger.info(f"Updating delivery {delivery_id} status to {new_status.value}")
        
        from app.models.logistics import OrderDelivery
        from app.models.driver import DriverJob, DriverJobStatus
        
        # Validate delivery exists
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")
        
        # Validate status transition is valid
        valid_transitions = {
            DeliveryStatus.PENDING: [DeliveryStatus.ASSIGNED, DeliveryStatus.CANCELLED],
            DeliveryStatus.ASSIGNED: [DeliveryStatus.DRIVER_EN_ROUTE, DeliveryStatus.AT_PICKUP, DeliveryStatus.CANCELLED],
            DeliveryStatus.DRIVER_EN_ROUTE: [DeliveryStatus.AT_PICKUP, DeliveryStatus.CANCELLED],
            DeliveryStatus.AT_PICKUP: [DeliveryStatus.PICKED_UP, DeliveryStatus.CANCELLED],
            DeliveryStatus.PICKED_UP: [DeliveryStatus.IN_TRANSIT, DeliveryStatus.CANCELLED],
            DeliveryStatus.IN_TRANSIT: [DeliveryStatus.AT_DELIVERY, DeliveryStatus.CANCELLED],
            DeliveryStatus.AT_DELIVERY: [DeliveryStatus.DELIVERED],
            DeliveryStatus.DELIVERED: [],
            DeliveryStatus.CANCELLED: [],
            DeliveryStatus.FAILED: [],
        }
        
        current_status = DeliveryStatus(delivery.status)
        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(status_code=400, detail=f"Invalid status transition from {current_status.value} to {new_status.value}")
        
        # Update delivery status
        delivery.status = new_status.value
        
        # Set appropriate timestamp
        if new_status == DeliveryStatus.PICKED_UP:
            delivery.pickup_confirmed_at = datetime.utcnow()
        elif new_status == DeliveryStatus.DELIVERED:
            delivery.delivery_confirmed_at = datetime.utcnow()
        
        # Update linked DriverJob status
        job = self.db.query(DriverJob).filter(DriverJob.order_id == delivery.order_id).first()
        if job:
            if new_status == DeliveryStatus.PICKED_UP:
                job.status = DriverJobStatus.IN_TRANSIT
            elif new_status == DeliveryStatus.DELIVERED:
                job.status = DriverJobStatus.DELIVERED
            self.db.commit()
        
        self.db.commit()
        
        # Send notifications based on status change
        try:
            from app.services.notification_service import notification_service
            if new_status == DeliveryStatus.PICKED_UP:
                if delivery.order and delivery.order.buyer:
                    notification_service._send_sms(
                        delivery.order.buyer.phone_number,
                        f"ZimAgritrust: Your order pickup has been confirmed. Driver is en route."
                    )
            elif new_status == DeliveryStatus.DELIVERED:
                if delivery.order and delivery.order.buyer:
                    notification_service._send_sms(
                        delivery.order.buyer.phone_number,
                        f"ZimAgritrust: Your order has been delivered successfully!"
                    )
        except Exception as e:
            logger.warning(f"Failed to send status notification: {e}")
        
        # Trigger settlement if status = DELIVERED
        if new_status == DeliveryStatus.DELIVERED:
            try:
                from app.services.driver_assignment_service import DriverAssignmentService
                assignment_service = DriverAssignmentService(self.db)
                if job:
                    assignment_service.complete_assignment(job.id)
            except Exception as e:
                logger.error(f"Failed to trigger settlement: {e}")
        
        return {
            "id": str(delivery_id),
            "status": new_status.value,
            "updated_at": datetime.utcnow().isoformat(),
        }
    
    def confirm_pickup(
        self,
        delivery_id: uuid.UUID,
        driver_id: uuid.UUID,
        pickup_code: Optional[str] = None,
        photo_url: Optional[str] = None,
        signature_url: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Confirm pickup by driver.
        
        Requires pickup code verification if provided.
        """
        logger.info(f"Confirming pickup for delivery {delivery_id}")
        
        from app.models.logistics import OrderDelivery
        
        # Validate delivery exists
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")
        
        # Validate pickup code if provided
        if pickup_code and not self.verify_pickup_code(delivery_id, pickup_code):
            raise HTTPException(status_code=400, detail="Invalid pickup code")
        
        # Verify location is at pickup geofence
        if delivery.current_latitude and delivery.current_longitude:
            geofence_status = self.check_geofences(delivery_id, delivery.current_latitude, delivery.current_longitude)
            if not geofence_status["pickup_geofence"]:
                logger.warning(f"Pickup confirmed outside geofence for delivery {delivery_id}")
        
        # Update delivery status to PICKED_UP
        delivery.status = DeliveryStatus.PICKED_UP.value
        delivery.pickup_confirmed_at = datetime.utcnow()
        delivery.pickup_confirmed_by = driver_id
        delivery.pickup_photo_url = photo_url
        delivery.pickup_signature_url = signature_url
        delivery.pickup_notes = notes
        
        # Generate delivery code
        delivery.delivery_code = self.generate_delivery_code()
        
        self.db.commit()
        
        # Notify buyer/farmer
        try:
            from app.services.notification_service import notification_service
            if delivery.order:
                if delivery.order.buyer:
                    notification_service._send_sms(
                        delivery.order.buyer.phone_number,
                        f"ZimAgritrust: Your order pickup has been confirmed. Delivery code: {delivery.delivery_code}. Driver is en route."
                    )
                if delivery.order.seller:
                    notification_service._send_sms(
                        delivery.order.seller.phone_number,
                        f"ZimAgritrust: Your goods have been picked up. Driver is en route to buyer."
                    )
        except Exception as e:
            logger.warning(f"Failed to send pickup notification: {e}")
        
        return {
            "id": str(delivery_id),
            "status": DeliveryStatus.PICKED_UP.value,
            "pickup_confirmed_at": delivery.pickup_confirmed_at.isoformat() if delivery.pickup_confirmed_at else datetime.utcnow().isoformat(),
            "delivery_code": delivery.delivery_code,
        }
    
    def confirm_delivery(
        self,
        delivery_id: uuid.UUID,
        driver_id: uuid.UUID,
        delivery_code: Optional[str] = None,
        photo_url: Optional[str] = None,
        signature_url: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Confirm delivery by driver.
        
        Requires delivery code verification if provided.
        """
        logger.info(f"Confirming delivery for delivery {delivery_id}")
        
        from app.models.logistics import OrderDelivery
        from app.models.driver import DriverJob, DriverJobStatus
        
        # Validate delivery exists
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")
        
        # Validate delivery code if provided
        if delivery_code and not self.verify_delivery_code(delivery_id, delivery_code):
            raise HTTPException(status_code=400, detail="Invalid delivery code")
        
        # Verify location is at delivery geofence
        if delivery.current_latitude and delivery.current_longitude:
            geofence_status = self.check_geofences(delivery_id, delivery.current_latitude, delivery.current_longitude)
            if not geofence_status["delivery_geofence"]:
                logger.warning(f"Delivery confirmed outside geofence for delivery {delivery_id}")
        
        # Update delivery status to DELIVERED
        delivery.status = DeliveryStatus.DELIVERED.value
        delivery.delivery_confirmed_at = datetime.utcnow()
        delivery.delivery_confirmed_by = driver_id
        delivery.delivery_photo_url = photo_url
        delivery.delivery_signature_url = signature_url
        delivery.delivery_notes = notes
        
        self.db.commit()
        
        # Trigger payment settlement
        job = self.db.query(DriverJob).filter(DriverJob.order_id == delivery.order_id).first()
        if job:
            try:
                from app.services.driver_assignment_service import DriverAssignmentService
                assignment_service = DriverAssignmentService(self.db)
                assignment_service.complete_assignment(job.id)
            except Exception as e:
                logger.error(f"Failed to trigger settlement: {e}")
        
        # Notify buyer/farmer
        try:
            from app.services.notification_service import notification_service
            if delivery.order:
                if delivery.order.buyer:
                    notification_service._send_sms(
                        delivery.order.buyer.phone_number,
                        f"ZimAgritrust: Your order has been delivered successfully! Please rate your experience."
                    )
                if delivery.order.seller:
                    notification_service._send_sms(
                        delivery.order.seller.phone_number,
                        f"ZimAgritrust: Your goods have been delivered to the buyer."
                    )
        except Exception as e:
            logger.warning(f"Failed to send delivery notification: {e}")
        
        return {
            "id": str(delivery_id),
            "status": DeliveryStatus.DELIVERED.value,
            "delivery_confirmed_at": delivery.delivery_confirmed_at.isoformat() if delivery.delivery_confirmed_at else datetime.utcnow().isoformat(),
        }
    
    def calculate_eta(
        self,
        delivery_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Calculate estimated time of arrival.
        
        Based on current location, destination, and average speed.
        """
        from app.models.logistics import OrderDelivery
        
        # Get delivery details
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery:
            return {
                "delivery_id": str(delivery_id),
                "estimated_arrival_time": None,
                "remaining_distance_km": 0,
                "estimated_minutes_remaining": 0,
            }
        
        # Get current driver location
        current_lat = delivery.current_latitude
        current_lon = delivery.current_longitude
        dest_lat = delivery.delivery_latitude
        dest_lon = delivery.delivery_longitude
        
        if not current_lat or not current_lon or not dest_lat or not dest_lon:
            return {
                "delivery_id": str(delivery_id),
                "estimated_arrival_time": None,
                "remaining_distance_km": 0,
                "estimated_minutes_remaining": 0,
            }
        
        # Calculate remaining distance
        remaining_distance_km = calculate_distance(current_lat, current_lon, dest_lat, dest_lon) / 1000
        
        # Estimate average speed based on road conditions (assume 40 km/h average)
        average_speed_kmh = 40
        
        # Calculate ETA
        eta_minutes = estimate_eta(remaining_distance_km, average_speed_kmh)
        estimated_arrival_time = datetime.utcnow() + timedelta(minutes=eta_minutes)
        
        # Update delivery estimated_arrival_time
        delivery.estimated_arrival_time = estimated_arrival_time
        delivery.estimated_distance_km = remaining_distance_km
        self.db.commit()
        
        return {
            "delivery_id": str(delivery_id),
            "estimated_arrival_time": estimated_arrival_time.isoformat(),
            "remaining_distance_km": round(remaining_distance_km, 2),
            "estimated_minutes_remaining": eta_minutes,
        }
    
    def get_tracking_history(
        self,
        delivery_id: uuid.UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get tracking history for a delivery.
        """
        from app.models.logistics import DeliveryTracking
        
        # Query delivery_tracking table
        query = self.db.query(DeliveryTracking).filter(DeliveryTracking.delivery_id == delivery_id)
        
        # Filter by time range if provided
        if start_time:
            query = query.filter(DeliveryTracking.recorded_at >= start_time)
        if end_time:
            query = query.filter(DeliveryTracking.recorded_at <= end_time)
        
        # Order by recorded_at DESC
        tracking_points = query.order_by(DeliveryTracking.recorded_at.desc()).all()
        
        # Return tracking points
        return [
            {
                "id": str(tp.id),
                "latitude": tp.latitude,
                "longitude": tp.longitude,
                "accuracy_meters": tp.accuracy_meters,
                "speed_kmh": tp.speed_kmh,
                "status": tp.status,
                "recorded_at": tp.recorded_at.isoformat() if tp.recorded_at else None,
            }
            for tp in tracking_points
        ]
    
    def get_current_location(
        self,
        delivery_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current driver location for a delivery.
        """
        from app.models.logistics import OrderDelivery, DeliveryTracking
        
        # Query delivery table for current_location
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery:
            return None
        
        # Query delivery_tracking for latest location
        latest_tracking = self.db.query(DeliveryTracking).filter(
            DeliveryTracking.delivery_id == delivery_id
        ).order_by(DeliveryTracking.recorded_at.desc()).first()
        
        # Return current location with timestamp
        return {
            "delivery_id": str(delivery_id),
            "latitude": delivery.current_latitude,
            "longitude": delivery.current_longitude,
            "accuracy_meters": latest_tracking.accuracy_meters if latest_tracking else None,
            "speed_kmh": latest_tracking.speed_kmh if latest_tracking else None,
            "status": latest_tracking.status if latest_tracking else None,
            "last_location_update_at": delivery.last_location_update_at.isoformat() if delivery.last_location_update_at else None,
        }
    
    def check_route_deviation(
        self,
        delivery_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Check if driver has deviated from expected route.
        """
        from app.models.logistics import OrderDelivery
        
        # Get current location
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery or not delivery.current_latitude or not delivery.current_longitude:
            return {
                "delivery_id": str(delivery_id),
                "on_route": True,
                "deviation_meters": 0,
                "alert_required": False,
            }
        
        # Get expected route polyline (simplified - just check if moving toward destination)
        if delivery.pickup_latitude and delivery.pickup_longitude and delivery.delivery_latitude and delivery.delivery_longitude:
            # Calculate distance from pickup to current
            dist_from_pickup = calculate_distance(
                delivery.pickup_latitude, delivery.pickup_longitude,
                delivery.current_latitude, delivery.current_longitude
            )
            
            # Calculate total route distance
            total_distance = calculate_distance(
                delivery.pickup_latitude, delivery.pickup_longitude,
                delivery.delivery_latitude, delivery.delivery_longitude
            )
            
            # Calculate distance from current to destination
            dist_to_dest = calculate_distance(
                delivery.current_latitude, delivery.current_longitude,
                delivery.delivery_latitude, delivery.delivery_longitude
            )
            
            # Simple deviation check: if current + to_dest is significantly more than total distance
            deviation_meters = (dist_from_pickup + dist_to_dest) - total_distance
            deviation_threshold = 500  # 500 meters tolerance
            
            alert_required = deviation_meters > deviation_threshold
            
            return {
                "delivery_id": str(delivery_id),
                "on_route": not alert_required,
                "deviation_meters": round(deviation_meters, 2),
                "alert_required": alert_required,
            }
        
        return {
            "delivery_id": str(delivery_id),
            "on_route": True,
            "deviation_meters": 0,
            "alert_required": False,
        }
    
    def generate_pickup_code(self) -> str:
        """Generate a 6-digit pickup code"""
        import random
        return f"{random.randint(100000, 999999)}"
    
    def generate_delivery_code(self) -> str:
        """Generate a 6-digit delivery code"""
        import random
        return f"{random.randint(100000, 999999)}"
    
    def verify_pickup_code(
        self,
        delivery_id: uuid.UUID,
        code: str,
    ) -> bool:
        """
        Verify pickup code.
        """
        from app.models.logistics import OrderDelivery
        
        # Get delivery pickup_code
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery or not delivery.pickup_code:
            return False
        
        # Compare with provided code
        return delivery.pickup_code == code
    
    def verify_delivery_code(
        self,
        delivery_id: uuid.UUID,
        code: str,
    ) -> bool:
        """
        Verify delivery code.
        """
        from app.models.logistics import OrderDelivery
        
        # Get delivery delivery_code
        delivery = self.db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
        if not delivery or not delivery.delivery_code:
            return False
        
        # Compare with provided code
        return delivery.delivery_code == code
    
    def get_active_deliveries(
        self,
        driver_id: Optional[uuid.UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all active deliveries (in transit).
        """
        from app.models.logistics import OrderDelivery
        
        # Query deliveries table
        active_statuses = [DeliveryStatus.DRIVER_EN_ROUTE.value, DeliveryStatus.AT_PICKUP.value, 
                         DeliveryStatus.PICKED_UP.value, DeliveryStatus.IN_TRANSIT.value, 
                         DeliveryStatus.AT_DELIVERY.value]
        
        query = self.db.query(OrderDelivery).filter(OrderDelivery.status.in_(active_statuses))
        
        # Filter by driver_id if provided
        if driver_id:
            query = query.filter(OrderDelivery.driver_id == driver_id)
        
        deliveries = query.all()
        
        # Return active deliveries
        return [
            {
                "id": str(d.id),
                "order_id": str(d.order_id),
                "driver_id": str(d.driver_id) if d.driver_id else None,
                "status": d.status,
                "pickup_address": d.pickup_address,
                "delivery_address": d.delivery_address,
                "current_latitude": d.current_latitude,
                "current_longitude": d.current_longitude,
                "estimated_arrival_time": d.estimated_arrival_time.isoformat() if d.estimated_arrival_time else None,
            }
            for d in deliveries
        ]
    
    def cleanup_old_tracking_data(
        self,
        days_to_keep: int = 30,
    ) -> int:
        """
        Clean up old tracking data to manage storage.
        
        This is typically run as a scheduled job.
        """
        logger.info(f"Cleaning up tracking data older than {days_to_keep} days")
        
        from app.models.logistics import DeliveryTracking
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete from delivery_tracking where recorded_at < cutoff_date
        deleted = self.db.query(DeliveryTracking).filter(
            DeliveryTracking.recorded_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Deleted {deleted} old tracking records")
        
        return deleted


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
    
    return c * r * 1000  # Return in meters


def is_within_geofence(
    latitude: float,
    longitude: float,
    geofence: Geofence,
) -> bool:
    """
    Check if a point is within a geofence.
    """
    distance = calculate_distance(
        latitude, longitude,
        geofence.latitude, geofence.longitude
    )
    
    return distance <= geofence.radius_meters


def estimate_eta(
    distance_km: float,
    average_speed_kmh: float,
) -> int:
    """
    Estimate ETA in minutes.
    """
    if average_speed_kmh <= 0:
        return 0
    
    time_hours = distance_km / average_speed_kmh
    time_minutes = int(time_hours * 60)
    
    # Add buffer time (20%)
    buffer = int(time_minutes * 0.2)
    
    return time_minutes + buffer


def determine_tracking_status(
    speed_kmh: Optional[float],
    previous_location: Optional[Dict[str, Any]],
) -> TrackingStatus:
    """
    Determine tracking status based on speed and movement.
    """
    if speed_kmh is None:
        return TrackingStatus.IDLE
    
    if speed_kmh > 5:
        return TrackingStatus.MOVING
    elif speed_kmh > 0:
        return TrackingStatus.STOPPED
    else:
        return TrackingStatus.IDLE
