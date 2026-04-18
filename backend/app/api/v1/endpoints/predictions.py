from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.ml.risk_scorer import risk_engine
from app.services.price_service import get_price_prediction
from typing import Dict, Any

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/price")
async def predict_price(crop: str, db: Session = Depends(get_db)):
    """
    Sovereign AI: Real-time Price Intelligence Endpoint.
    """
    try:
        prediction = get_price_prediction(db, crop)
        return {
            "status": "success",
            "crop": crop,
            "data": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk")
async def evaluate_risk(features: Dict[str, Any]):
    """
    Sovereign AI: Transaction Risk Scoring Endpoint.
    """
    try:
        assessment = risk_engine.predict_risk(features)
        return assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
