from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.ml.risk_scorer import RiskScorer
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
    Real-time Price Intelligence Endpoint.
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

@router.get("/risk/{user_id}")
async def evaluate_risk(user_id: str, db: Session = Depends(get_db)):
    """
    Transaction Risk Scoring Endpoint — evaluates a user's risk profile from live DB data.
    """
    try:
        scorer = RiskScorer(db=db)
        assessment = scorer.calculate_risk_score(user_id)
        return assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
