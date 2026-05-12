"""
ML Inference API — 4 endpoints powered by ONNX Runtime and scikit-learn.
No training; models are pre-exported from Jupyter and loaded from shared volume.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.services.ml_service import classify_crop, detect_disease, predict_price, detect_fraud

router = APIRouter(prefix="/ml", tags=["ml-inference"])

_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


# ──────────────────────────────────────────────
# Request/Response schemas
# ──────────────────────────────────────────────

class PricePredictRequest(BaseModel):
    crop_type: str
    quantity_kg: float = 100.0
    days_ahead: int = 7


class FraudDetectRequest(BaseModel):
    amount: float
    quantity: float
    price_per_kg: Optional[float] = None
    hour: int = 12
    farmer_history: int = 0
    buyer_history: int = 0
    is_off_hour: int = 0


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.post("/classify-crop", summary="Classify crop type from photo")
async def api_classify_crop(
    image: UploadFile = File(..., description="Crop image (JPEG/PNG, max 10MB)"),
):
    """
    Upload a crop photo → returns detected crop type and confidence score.
    Model: crop_classifier_v1.onnx (exported from Jupyter YOLOv8 training).
    """
    image_bytes = await image.read()
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 10MB limit")
    result = await classify_crop(image_bytes)
    return result


@router.post("/detect-disease", summary="Detect plant disease from leaf/crop photo")
async def api_detect_disease(
    image: UploadFile = File(..., description="Leaf or crop image (JPEG/PNG, max 10MB)"),
):
    """
    Upload a leaf/crop photo → returns detected disease, severity, and treatment.
    Model: disease_detector_v1.onnx (exported from Jupyter ResNet training).
    """
    image_bytes = await image.read()
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 10MB limit")
    result = await detect_disease(image_bytes)
    return result


@router.post("/predict-price", summary="Predict crop price forecast")
async def api_predict_price(payload: PricePredictRequest):
    """
    POST {crop_type, quantity_kg, days_ahead} → predicted USD/kg price.
    Model: price_predictor_v1.pkl (exported from Jupyter Random Forest/XGBoost training).
    """
    if payload.quantity_kg <= 0:
        raise HTTPException(status_code=422, detail="quantity_kg must be positive")
    if not (1 <= payload.days_ahead <= 365):
        raise HTTPException(status_code=422, detail="days_ahead must be between 1 and 365")
    result = await predict_price(
        crop_type=payload.crop_type,
        quantity_kg=payload.quantity_kg,
        days_ahead=payload.days_ahead,
    )
    return result


@router.post("/detect-fraud", summary="Score a listing or transaction for fraud")
async def api_detect_fraud(payload: FraudDetectRequest):
    """
    POST transaction/listing features → fraud score and risk level.
    Model: fraud_detector_v1.pkl (exported from Jupyter IsolationForest training).
    """
    if payload.amount <= 0:
        raise HTTPException(status_code=422, detail="amount must be positive")
    result = await detect_fraud(payload.dict())
    return result


@router.get("/status", summary="Check which ML models are loaded")
async def ml_status():
    """Returns the current load status of all ML models and the model manifest."""
    from app.ml.model_loader import model_loader
    return {
        "crop_classifier":   model_loader._crop_classifier is not None and model_loader._crop_classifier.session is not None,
        "disease_detector":  model_loader._disease_detector is not None and model_loader._disease_detector.session is not None,
        "price_predictor":   model_loader._price_predictor is not None,
        "fraud_detector":    model_loader._fraud_detector is not None,
        "manifest":          model_loader.manifest,
    }
