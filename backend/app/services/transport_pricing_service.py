"""
ZimAgritrust Transport Pricing Engine
Implements dynamic transport pricing with multiple factors.
Core Business Rule: WHOEVER REQUESTS TRANSPORT = WHO PAYS FOR TRANSPORT
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ── Vehicle Pricing Configuration ───────────────────────────────────────────────

@dataclass
class VehiclePricing:
    """Base pricing per vehicle type"""
    vehicle_type: str
    base_fee: float
    per_km_rate: float
    min_fee: float
    max_fee: Optional[float] = None


VEHICLE_PRICING = {
    "motorcycle": VehiclePricing("motorcycle", 2.00, 0.30, 5.00, 50.00),
    "car": VehiclePricing("car", 4.00, 0.40, 8.00, 100.00),
    "van": VehiclePricing("van", 5.00, 0.45, 10.00, 200.00),
    "truck": VehiclePricing("truck", 6.00, 0.50, 15.00, 500.00),
}


# ── Pricing Factors ─────────────────────────────────────────────────────────────

@dataclass
class PricingFactors:
    """All factors that influence transport pricing"""
    distance_km: float
    vehicle_type: str
    cargo_weight_kg: float
    cargo_volume_m3: Optional[float] = None
    urgency_level: str = "STANDARD"
    fuel_multiplier: float = 1.0
    road_accessibility: str = "GOOD"
    weather_risk: str = "LOW"
    rural_accessibility_score: float = 1.0
    driver_availability: str = "HIGH"
    peak_demand_multiplier: float = 1.0
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None


# ── Urgency Multipliers ─────────────────────────────────────────────────────────

URGENCY_MULTIPLIERS = {
    "STANDARD": 1.0,
    "URGENT": 1.3,
    "EXPEDITED": 1.5,
}


# ── Weather Risk Multipliers ────────────────────────────────────────────────────

WEATHER_RISK_MULTIPLIERS = {
    "LOW": 1.0,
    "MODERATE": 1.1,
    "HIGH": 1.25,
    "SEVERE": 1.5,
}


# ── Road Accessibility Multipliers ───────────────────────────────────────────────

ROAD_ACCESSIBILITY_MULTIPLIERS = {
    "EXCELLENT": 0.9,
    "GOOD": 1.0,
    "FAIR": 1.15,
    "POOR": 1.3,
}


# ── Rural Accessibility Surcharges ───────────────────────────────────────────────

RURAL_SURCHARGE_RATES = {
    "URBAN": 0.0,
    "SUBURBAN": 0.05,
    "RURAL": 0.15,
    "REMOTE": 0.25,
}


# ── Driver Availability Multipliers ─────────────────────────────────────────────

DRIVER_AVAILABILITY_MULTIPLIERS = {
    "HIGH": 1.0,
    "MEDIUM": 1.1,
    "LOW": 1.25,
    "CRITICAL": 1.5,
}


# ── Peak Demand Multipliers ─────────────────────────────────────────────────────

PEAK_DEMAND_MULTIPLIERS = {
    "OFF_PEAK": 1.0,
    "MODERATE": 1.1,
    "HIGH": 1.25,
    "EXTREME": 1.5,
}


# ── Pricing Engine ───────────────────────────────────────────────────────────────

class TransportPricingEngine:
    """Dynamic transport pricing engine"""

    def __init__(self):
        self.pricing_algorithm = "DYNAMIC_V2"
        self.pricing_version = "2.0.0"

    def calculate_quote(
        self,
        factors: PricingFactors,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Calculate transport quote based on all pricing factors.

        Returns complete breakdown with:
        - base_fee
        - distance_fee
        - weight_fee
        - volume_fee
        - urgency_fee
        - rural_surcharge
        - peak_surcharge
        - weather_surcharge
        - subtotal
        - tax_amount
        - total_amount
        """
        # Validate vehicle type
        if factors.vehicle_type not in VEHICLE_PRICING:
            raise ValueError(f"Invalid vehicle type: {factors.vehicle_type}")

        vehicle_pricing = VEHICLE_PRICING[factors.vehicle_type]

        # Calculate base components
        base_fee = vehicle_pricing.base_fee
        distance_fee = self._calculate_distance_fee(
            factors.distance_km,
            vehicle_pricing.per_km_rate
        )
        weight_fee = self._calculate_weight_fee(factors.cargo_weight_kg)
        volume_fee = self._calculate_volume_fee(
            factors.cargo_volume_m3,
            factors.cargo_weight_kg
        )

        # Calculate subtotal before multipliers
        subtotal_before_multipliers = base_fee + distance_fee + weight_fee + volume_fee

        # Calculate multipliers
        urgency_multiplier = URGENCY_MULTIPLIERS.get(
            factors.urgency_level,
            URGENCY_MULTIPLIERS["STANDARD"]
        )
        weather_multiplier = WEATHER_RISK_MULTIPLIERS.get(
            factors.weather_risk,
            WEATHER_RISK_MULTIPLIERS["LOW"]
        )
        road_multiplier = ROAD_ACCESSIBILITY_MULTIPLIERS.get(
            factors.road_accessibility,
            ROAD_ACCESSIBILITY_MULTIPLIERS["GOOD"]
        )
        driver_multiplier = DRIVER_AVAILABILITY_MULTIPLIERS.get(
            factors.driver_availability,
            DRIVER_AVAILABILITY_MULTIPLIERS["HIGH"]
        )

        # Apply combined multiplier
        combined_multiplier = (
            urgency_multiplier *
            weather_multiplier *
            road_multiplier *
            driver_multiplier *
            factors.peak_demand_multiplier *
            factors.fuel_multiplier
        )

        # Calculate adjusted subtotal
        subtotal = subtotal_before_multipliers * combined_multiplier

        # Calculate surcharges
        rural_surcharge = self._calculate_rural_surcharge(
            subtotal,
            factors.rural_accessibility_score
        )

        # Calculate individual fee components for transparency
        urgency_fee = subtotal_before_multipliers * (urgency_multiplier - 1.0)
        weather_surcharge = subtotal_before_multipliers * (weather_multiplier - 1.0)
        peak_surcharge = subtotal_before_multipliers * (factors.peak_demand_multiplier - 1.0)

        # Add surcharges
        subtotal += rural_surcharge

        # Calculate tax (15% VAT for Zimbabwe)
        tax_rate = 0.15
        tax_amount = round(subtotal * tax_rate, 2)

        # Calculate total
        total_amount = round(subtotal + tax_amount, 2)

        # Apply min/max fee constraints
        if total_amount < vehicle_pricing.min_fee:
            total_amount = vehicle_pricing.min_fee
            tax_amount = round(total_amount / (1 + tax_rate) * tax_rate, 2)
            subtotal = total_amount - tax_amount
        elif vehicle_pricing.max_fee and total_amount > vehicle_pricing.max_fee:
            total_amount = vehicle_pricing.max_fee
            tax_amount = round(total_amount / (1 + tax_rate) * tax_rate, 2)
            subtotal = total_amount - tax_amount

        # Build pricing factors for audit
        pricing_factors = {
            "distance_km": factors.distance_km,
            "vehicle_type": factors.vehicle_type,
            "cargo_weight_kg": factors.cargo_weight_kg,
            "cargo_volume_m3": factors.cargo_volume_m3,
            "urgency_level": factors.urgency_level,
            "fuel_multiplier": factors.fuel_multiplier,
            "road_accessibility": factors.road_accessibility,
            "weather_risk": factors.weather_risk,
            "rural_accessibility_score": factors.rural_accessibility_score,
            "driver_availability": factors.driver_availability,
            "peak_demand_multiplier": factors.peak_demand_multiplier,
            "urgency_multiplier": urgency_multiplier,
            "weather_multiplier": weather_multiplier,
            "road_multiplier": road_multiplier,
            "driver_multiplier": driver_multiplier,
            "combined_multiplier": combined_multiplier,
            "tax_rate": tax_rate,
        }

        return {
            "base_fee": round(base_fee, 2),
            "distance_km": round(factors.distance_km, 2),
            "per_km_rate": vehicle_pricing.per_km_rate,
            "distance_fee": round(distance_fee, 2),
            "weight_fee": round(weight_fee, 2),
            "volume_fee": round(volume_fee, 2),
            "urgency_multiplier": urgency_multiplier,
            "urgency_fee": round(urgency_fee, 2),
            "rural_surcharge": round(rural_surcharge, 2),
            "peak_surcharge": round(peak_surcharge, 2),
            "weather_surcharge": round(weather_surcharge, 2),
            "subtotal": round(subtotal, 2),
            "tax_amount": round(tax_amount, 2),
            "total_amount": total_amount,
            "currency": "USD",
            "vehicle_type": factors.vehicle_type,
            "vehicle_base_fee": vehicle_pricing.base_fee,
            "vehicle_per_km_rate": vehicle_pricing.per_km_rate,
            "pricing_algorithm": self.pricing_algorithm,
            "pricing_version": self.pricing_version,
            "pricing_factors": pricing_factors,
        }

    def _calculate_distance_fee(self, distance_km: float, per_km_rate: float) -> float:
        """Calculate distance-based fee"""
        return round(distance_km * per_km_rate, 2)

    def _calculate_weight_fee(self, weight_kg: float) -> float:
        """Calculate weight-based surcharge"""
        # No surcharge for weights under 100kg
        if weight_kg <= 100:
            return 0.0

        # $0.05 per kg over 100kg
        excess_weight = weight_kg - 100
        return round(excess_weight * 0.05, 2)

    def _calculate_volume_fee(self, volume_m3: Optional[float], weight_kg: float) -> float:
        """Calculate volume-based surcharge"""
        if not volume_m3:
            return 0.0

        # $2.00 per cubic meter over 2m3
        if volume_m3 <= 2.0:
            return 0.0

        excess_volume = volume_m3 - 2.0
        return round(excess_volume * 2.00, 2)

    def _calculate_rural_surcharge(self, subtotal: float, rural_score: float) -> float:
        """Calculate rural accessibility surcharge"""
        # rural_score: 1.0 (urban) to 5.0 (remote)
        if rural_score <= 1.5:
            return round(subtotal * 0.0, 2)
        elif rural_score <= 2.5:
            return round(subtotal * 0.05, 2)
        elif rural_score <= 3.5:
            return round(subtotal * 0.15, 2)
        else:
            return round(subtotal * 0.25, 2)

    def estimate_distance(
        self,
        pickup_lat: float,
        pickup_lon: float,
        delivery_lat: float,
        delivery_lon: float,
    ) -> float:
        """
        Estimate distance using Haversine formula.
        In production, this would use Google Maps Distance Matrix API.
        """
        from math import radians, cos, sin, asin, sqrt

        # Convert to radians
        lat1, lon1 = radians(pickup_lat), radians(pickup_lon)
        lat2, lon2 = radians(delivery_lat), radians(delivery_lon)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))

        # Earth's radius in kilometers
        r = 6371

        return round(c * r, 2)

    def determine_rural_accessibility(
        self,
        latitude: float,
        longitude: float,
        db: Optional[Session] = None,
    ) -> float:
        """
        Determine rural accessibility score (1.0-5.0).
        Uses district-based mapping for Zimbabwe regions.
        """
        # Simplified logic based on Zimbabwe regions
        # Harare/Bulawayo = 1.0 (urban)
        # Major towns = 2.5 (suburban)
        # Rural areas = 3.5 (rural)
        # Remote areas = 5.0 (remote)

        urban_districts = ["harare", "bulawayo"]
        major_towns = ["chitungwiza", "gweru", "mutare", "masvingo", "kwekwe"]

        district_lower = district.lower() if district else ""

        if any(urban in district_lower for urban in urban_districts):
            return 1.0
        elif any(town in district_lower for town in major_towns):
            return 2.5
        elif district_lower:
            return 3.5
        else:
            return 2.0  # Default to suburban if unknown

    def get_peak_demand_multiplier(self, datetime: datetime) -> float:
        """
        Determine peak demand multiplier based on time.
        """
        hour = datetime.hour
        day = datetime.weekday()

        # Peak hours: 7-9 AM and 5-7 PM on weekdays
        if day < 5 and (7 <= hour <= 9 or 17 <= hour <= 19):
            return PEAK_DEMAND_MULTIPLIERS["HIGH"]

        # Moderate: weekends and weekday evenings
        if day >= 5 or (10 <= hour <= 16 or 20 <= hour <= 22):
            return PEAK_DEMAND_MULTIPLIERS["MODERATE"]

        # Off-peak: late night and early morning
        return PEAK_DEMAND_MULTIPLIERS["OFF_PEAK"]

    def calculate_multi_stop_pricing(
        self,
        factors: PricingFactors,
        stops: list[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Calculate pricing for multi-stop deliveries.
        """
        if not stops:
            return self.calculate_quote(factors, db)

        # Calculate total distance with stops
        total_distance = factors.distance_km

        # Add distance for each additional stop
        for i, stop in enumerate(stops):
            if i == 0:
                # Distance from pickup to first stop
                if stop.get("latitude") and stop.get("longitude"):
                    dist = self.estimate_distance(
                        factors.pickup_latitude or 0,
                        factors.pickup_longitude or 0,
                        stop["latitude"],
                        stop["longitude"],
                    )
                    total_distance += dist
            else:
                # Distance from previous stop to current stop
                prev_stop = stops[i - 1]
                if (stop.get("latitude") and stop.get("longitude") and
                    prev_stop.get("latitude") and prev_stop.get("longitude")):
                    dist = self.estimate_distance(
                        prev_stop["latitude"],
                        prev_stop["longitude"],
                        stop["latitude"],
                        stop["longitude"],
                    )
                    total_distance += dist

        # Multi-stop surcharge: $2.00 per additional stop
        multi_stop_surcharge = len(stops) * 2.00

        # Update factors with total distance
        updated_factors = PricingFactors(
            distance_km=total_distance,
            vehicle_type=factors.vehicle_type,
            cargo_weight_kg=factors.cargo_weight_kg,
            cargo_volume_m3=factors.cargo_volume_m3,
            urgency_level=factors.urgency_level,
            fuel_multiplier=factors.fuel_multiplier,
            road_accessibility=factors.road_accessibility,
            weather_risk=factors.weather_risk,
            rural_accessibility_score=factors.rural_accessibility_score,
            driver_availability=factors.driver_availability,
            peak_demand_multiplier=factors.peak_demand_multiplier,
        )

        quote = self.calculate_quote(updated_factors, db)

        # Add multi-stop surcharge
        quote["subtotal"] += multi_stop_surcharge
        quote["total_amount"] = round(quote["subtotal"] + quote["tax_amount"], 2)
        quote["multi_stop_surcharge"] = multi_stop_surcharge
        quote["number_of_stops"] = len(stops)
        quote["total_distance_km"] = round(total_distance, 2)

        return quote


# ── Singleton Instance ─────────────────────────────────────────────────────────

transport_pricing_engine = TransportPricingEngine()


# ── Helper Functions ───────────────────────────────────────────────────────────

def get_vehicle_types() -> list[Dict[str, Any]]:
    """Get available vehicle types with pricing"""
    return [
        {
            "type": vt.vehicle_type,
            "base_fee": vt.base_fee,
            "per_km_rate": vt.per_km_rate,
            "min_fee": vt.min_fee,
            "max_fee": vt.max_fee,
            "description": f"{vt.vehicle_type.capitalize()} - Base: ${vt.base_fee}, ${vt.per_km_rate}/km"
        }
        for vt in VEHICLE_PRICING.values()
    ]


def estimate_delivery_time(
    distance_km: float,
    vehicle_type: str,
    urgency_level: str = "STANDARD",
) -> Dict[str, Any]:
    """
    Estimate delivery time based on distance and vehicle type.
    """
    # Average speeds (km/h)
    vehicle_speeds = {
        "motorcycle": 40,
        "car": 35,
        "van": 30,
        "truck": 25,
    }

    base_speed = vehicle_speeds.get(vehicle_type, 30)

    # Urgency affects speed (urgent = faster)
    urgency_speed_multiplier = URGENCY_MULTIPLIERS.get(urgency_level, 1.0)
    adjusted_speed = base_speed * urgency_speed_multiplier

    # Calculate base time in hours
    time_hours = distance_km / adjusted_speed

    # Add pickup/dropoff time (30 minutes each)
    handling_time_hours = 1.0

    total_time_hours = time_hours + handling_time_hours

    # Convert to minutes
    total_minutes = int(total_time_hours * 60)

    # Add buffer time
    buffer_minutes = int(total_minutes * 0.2)
    estimated_minutes = total_minutes + buffer_minutes

    return {
        "estimated_minutes": estimated_minutes,
        "estimated_hours": round(estimated_minutes / 60, 1),
        "pickup_time_minutes": 30,
        "dropoff_time_minutes": 30,
        "travel_time_minutes": int(time_hours * 60),
        "buffer_minutes": buffer_minutes,
    }
