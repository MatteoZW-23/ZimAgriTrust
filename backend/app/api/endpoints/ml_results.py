"""
ML RESULTS API ENDPOINTS
Receives results from notebook scheduler and serves them to the app
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import json

from app.db.session import get_db
from app.models.ml_metadata import MLJobLog, MLPrediction, MLInsight
from app.services.prediction_cache import PredictionCache

router = APIRouter(prefix="/ml", tags=["machine_learning"])

# ============== RECEIVE RESULTS FROM SCHEDULER ==============

@router.post("/jobs/log")
async def receive_job_log(
    job_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive job execution log from scheduler
    Called by scheduler after each notebook run
    """
    
    # Save to database
    job_log = MLJobLog(
        job_name=job_data.get('job_name'),
        status=job_data.get('status'),
        duration_seconds=job_data.get('duration_seconds'),
        accuracy=job_data.get('accuracy'),
        metrics=job_data.get('metrics', {}),
        completed_at=datetime.fromisoformat(job_data.get('completed_at'))
    )
    
    db.add(job_log)
    db.commit()
    
    # If job was successful and produced predictions, update cache
    if job_data.get('status') == 'success':
        background_tasks.add_task(update_prediction_cache, job_data)
    
    return {"status": "received", "job_id": job_log.id}


@router.post("/predictions/price")
async def receive_price_predictions(
    predictions: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Receive price predictions from scheduler
    Stores in database and updates Redis cache
    """
    
    # Store each prediction
    for crop, price_data in predictions.get('predictions', {}).items():
        pred_record = MLPrediction(
            prediction_type='price',
            crop_type=crop,
            location=price_data.get('location'),
            predicted_value=price_data.get('price'),
            confidence=price_data.get('confidence', 0.85),
            valid_until=datetime.fromisoformat(predictions.get('valid_until')),
            metadata={'trend': price_data.get('trend')}
        )
        db.add(pred_record)
    
    db.commit()
    
    # Update Redis cache for fast app access
    cache = PredictionCache()
    cache.update_price_predictions(predictions.get('predictions', {}))
    
    return {"status": "received", "count": len(predictions.get('predictions', {}))}


@router.post("/ml/insights")
async def receive_insights(
    insights: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Receive insights from scheduler
    """
    
    for insight_text in insights.get('insights', []):
        insight = MLInsight(
            insight_type=insights.get('type', 'general'),
            content=insight_text,
            created_at=datetime.now()
        )
        db.add(insight)
    
    db.commit()
    
    return {"status": "received", "count": len(insights.get('insights', []))}


@router.post("/metrics")
async def receive_model_metrics(
    metrics: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Receive model performance metrics
    """
    
    # Update the latest job log with metrics
    latest_job = db.query(MLJobLog).filter(
        MLJobLog.job_name == metrics.get('job_name')
    ).order_by(MLJobLog.completed_at.desc()).first()
    
    if latest_job:
        latest_job.metrics = metrics.get('metrics', {})
        latest_job.accuracy = metrics.get('metrics', {}).get('accuracy')
        db.commit()
    
    return {"status": "received"}


@router.post("/jobs/alert")
async def receive_job_alert(
    alert: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Receive job failure alerts
    """
    
    # Log the alert
    job_log = MLJobLog(
        job_name=alert.get('job_name'),
        status='failed',
        metrics={'error': alert.get('error')},
        completed_at=datetime.fromisoformat(alert.get('timestamp'))
    )
    db.add(job_log)
    db.commit()
    
    # TODO: Send SMS/email notification to admin
    # notification_service.send_alert(alert)
    
    return {"status": "alert_received"}


# ============== SERVE RESULTS TO APP ==============

@router.get("/predictions/price/{crop}/{location}")
async def get_price_prediction(crop: str, location: str):
    """
    Get latest price prediction for app
    Called by mobile app and USSD
    """
    
    cache = PredictionCache()
    prediction = cache.get_price_prediction(crop, location)
    
    if prediction:
        return prediction
    
    # Fallback to database
    # Query latest prediction from DB
    return {"crop": crop, "location": location, "prediction": None, "available": False}


@router.get("/predictions/risk/{user_id}")
async def get_risk_score(user_id: int):
    """
    Get user risk score for app
    """
    
    cache = PredictionCache()
    risk_score = cache.get_risk_score(user_id)
    
    return {"user_id": user_id, "risk_score": risk_score, "updated_at": datetime.now()}


@router.get("/insights/latest")
async def get_latest_insights(limit: int = 5):
    """
    Get latest insights for agent dashboard
    """
    
    cache = PredictionCache()
    insights = cache.get_latest_insights(limit)
    
    return {"insights": insights, "count": len(insights)}


@router.get("/metrics/model")
async def get_model_metrics():
    """
    Get current model performance metrics
    """
    
    cache = PredictionCache()
    metrics = cache.get_model_metrics()
    
    return metrics


# ============== HELPER FUNCTIONS ==============

async def update_prediction_cache(job_data: Dict[str, Any]):
    """Background task to update cache after job completion"""
    cache = PredictionCache()
    
    if job_data.get('accuracy'):
        cache.update_model_accuracy(job_data['job_name'], job_data['accuracy'])
    
    if job_data.get('metrics'):
        cache.update_model_metrics(job_data['metrics'])
