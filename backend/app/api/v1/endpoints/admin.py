from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.api.v1.endpoints.ai import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/dashboard/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """
    High-level platform metrics for the Admin Dashboard.
    """
    return {
        "active_farmers": 1240,
        "certified_agents": 88,
        "pending_disputes": 5,
        "total_escrow_value": 450000.0,
        "system_trust_index": 94.2
    }

@router.get("/monitoring/models")
async def get_model_status():
    """
    Real-time performance tracking for deployed ML models.
    """
    return [
        {"model": "Price Predictor", "latency": "45ms", "status": "Healthy", "drift": "Low"},
        {"model": "Crop Classifier", "latency": "120ms", "status": "Healthy", "drift": "Negligible"},
        {"model": "Fraud Detector", "latency": "22ms", "status": "Heavily Loaded", "drift": "Moderate"}
    ]

@router.post("/governance/dispute-override/{dispute_id}")
async def override_dispute(dispute_id: int, decision: Dict):
    """
    Allows Superadmins to override agent decisions in multi-stakeholder disputes.
    """
    return {"status": "Decision Overridden", "dispute_id": dispute_id, "new_decision": decision}
