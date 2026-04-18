import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.logistics import TripStatus

class LogisticsTripCreate(BaseModel):
    origin_district: str
    destination_city: str
    available_capacity_kg: float
    price_per_kg: float
    departure_date: datetime

class LogisticsTripResponse(BaseModel):
    id: uuid.UUID
    transporter_id: uuid.UUID
    origin_district: str
    destination_city: str
    available_capacity_kg: float
    price_per_kg: float
    departure_date: datetime
    status: TripStatus
    created_at: datetime

    class Config:
        from_attributes = True

class ManifestItem(BaseModel):
    farmer: str
    district: str
    pickup_point: str
    quantity: str
    confirmed: bool

class TripManifest(BaseModel):
    trip_id: uuid.UUID
    items: List[ManifestItem]
