import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.logistics import LogisticsTrip
from app.models.user import User, UserRole
from app.schemas.logistics import LogisticsTripCreate, LogisticsTripResponse, TripManifest
from app.services.logistics_service import LogisticsService

router = APIRouter()

@router.get("/trips", response_model=list[LogisticsTripResponse])
def list_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[LogisticsTrip]:
    return db.query(LogisticsTrip).all()

@router.post("/trips", response_model=LogisticsTripResponse)
def create_trip(
    payload: LogisticsTripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN))
) -> LogisticsTrip:
    trip = LogisticsTrip(
        transporter_id=current_user.id,
        **payload.model_dump()
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip

@router.get("/trips/{trip_id}/manifest", response_model=TripManifest)
def get_manifest(
    trip_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN))
):
    items = LogisticsService.get_trip_load_manifest(db, str(trip_id))
    return {"trip_id": trip_id, "items": items}
