from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_db
from app.schemas.ussd import USSDRequest, USSDResponse
from app.services.ussd_service import USSDService

router = APIRouter()
ussd_service = USSDService()
logger = logging.getLogger(__name__)


@router.post("/session", response_model=USSDResponse)
async def handle_ussd(payload: USSDRequest, db: Session = Depends(get_db)) -> USSDResponse:
    try:
        return await ussd_service.handle_request(db, payload)
    except Exception as e:
        logger.error(f"USSD session error: {str(e)}")
        raise HTTPException(status_code=500, detail="USSD service error")
