from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.logistics import LogisticsTrip, AggregationBooking, TripStatus
from app.models.listing import Listing
from datetime import datetime

class LogisticsService:
    """
    Logistics Optimization Engine for rural smallholders.
    Solves the 'Last-Mile' bottleneck through virtual aggregation.
    """

    @staticmethod
    def match_listing_to_trips(db: Session, listing: Listing, destination: str):
        """
        Finds all available transporters passing through the farmer's district.
        """
        trips = db.query(LogisticsTrip).filter(
            LogisticsTrip.origin_district == listing.location_district,
            LogisticsTrip.destination_city == destination,
            LogisticsTrip.status == TripStatus.PLANNED,
            LogisticsTrip.available_capacity_kg >= listing.quantity
        ).all()
        
        return trips

    @staticmethod
    def pool_harvest_to_trip(db: Session, trip_id: str, listing_id: str, quantity: float):
        """
        Reserve space on a truck for a specific rural harvest.
        """
        trip = db.query(LogisticsTrip).filter(LogisticsTrip.id == trip_id).first()
        if not trip or trip.available_capacity_kg < quantity:
            return None
            
        booking = AggregationBooking(
            trip_id=trip_id,
            listing_id=listing_id,
            booked_quantity_kg=quantity
        )
        
        # Deduct capacity
        trip.available_capacity_kg -= quantity
        
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        # Apply 'Pooling Discount' if trip capacity is > 80% full
        discount = 1.0
        if trip.available_capacity_kg / (trip.available_capacity_kg + quantity) < 0.2:
            discount = 0.85 # 15% Bulk Aggregation Discount
            
        return {
            "booking_id": booking.id,
            "shipping_cost": (quantity * trip.price_per_kg) * discount,
            "pooling_discount_applied": discount < 1.0
        }

    @staticmethod
    def get_trip_load_manifest(db: Session, trip_id: str):
        """
        Generates a digital manifest for the truck driver.
        Lists all rural pickup points and quantities for this trip.
        """
        bookings = db.query(AggregationBooking).filter(
            AggregationBooking.trip_id == trip_id
        ).all()
        
        manifest = []
        for b in bookings:
            manifest.append({
                "farmer": b.listing.seller.full_name,
                "district": b.listing.location_district,
                "pickup_point": b.listing.pickup_address,
                "quantity": f"{b.booked_quantity_kg} {b.listing.quantity_unit}",
                "confirmed": b.pickup_confirmed
            })
            
        return manifest
