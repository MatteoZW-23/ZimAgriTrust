from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.ussd import USSDRequest, USSDResponse
from app.services.ussd_service import USSDService

router = APIRouter()
ussd_service = USSDService()


@router.post("/session", response_model=USSDResponse)
async def handle_ussd(payload: USSDRequest, db: Session = Depends(get_db)) -> USSDResponse:
    return await ussd_service.handle_request(db, payload)
