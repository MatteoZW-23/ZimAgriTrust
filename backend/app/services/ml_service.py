"""
ML Service — async thin wrappers over model_loader for use by API endpoints.
No training logic; pure inference delegation.
"""

import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np

from app.ml.model_loader import model_loader

logger = logging.getLogger(__name__)

CROP_DISPLAY_NAMES = {
    "maize":       "Maize (Chibage/Umumbu)",
    "mango":       "Mango",
    "tomato":      "Tomato (Madomasi)",
    "soya_beans":  "Soya Beans",
    "groundnuts":  "Groundnuts (Nzungu)",
    "tobacco":     "Tobacco (Fodya)",
    "cotton":      "Cotton (Donje)",
    "cabbage":     "Cabbage (Kebheji)",
    "potato":      "Potato (Mbatata)",
    "onion":       "Onion (Hanyanisi)",
    "sugar_beans": "Sugar Beans (Bhora)",
    "sunflower":   "Sunflower",
}


async def classify_crop(image_bytes: bytes) -> Dict[str, Any]:
    """
    Classify crop type from image bytes.
    Returns crop_type, display name, confidence, and a confidence_level label.
    """
    result = model_loader.get_prediction("classify_crop", image_bytes=image_bytes)
    if not result.get("success"):
        return {
            "success": False,
            "crop_type": "unknown",
            "crop_name": "Unknown",
            "confidence": 0.0,
            "confidence_level": "failed",
            "message": result.get("error", "Classifier unavailable"),
        }
    crop_type = result["crop_type"]
    confidence = result["confidence"]
    level = (
        "high"   if confidence >= 0.85 else
        "medium" if confidence >= 0.70 else
        "low"    if confidence >= 0.55 else
        "failed"
    )
    return {
        "success": True,
        "crop_type": crop_type,
        "crop_name": CROP_DISPLAY_NAMES.get(crop_type, crop_type.replace("_", " ").title()),
        "confidence": confidence,
        "confidence_level": level,
    }


async def detect_disease(image_bytes: bytes) -> Dict[str, Any]:
    """
    Detect plant disease from a leaf/crop image.
    Returns disease name and confidence.
    """
    result = model_loader.get_prediction("detect_disease", image_bytes=image_bytes)
    if not result.get("success"):
        return {
            "success": False,
            "disease": "unknown",
            "confidence": 0.0,
            "message": result.get("error", "Disease detector unavailable"),
            "severity": "unknown",
            "treatment": None,
        }
    disease = result["disease"]
    confidence = result["confidence"]
    severity = "none" if disease == "healthy" else ("high" if confidence > 0.80 else "medium")
    return {
        "success": True,
        "disease": disease,
        "disease_display": disease.replace("_", " ").title(),
        "confidence": confidence,
        "severity": severity,
        "treatment": _get_treatment(disease),
    }


async def predict_price(
    crop_type: str,
    quantity_kg: float,
    days_ahead: int = 7,
    extra_features: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Predict crop price (USD/kg) for a given crop and quantity.
    Feature vector: [quantity_kg, days_ahead, crop_index, ...extra_features]
    """
    crop_index = list(CROP_DISPLAY_NAMES.keys()).index(crop_type) if crop_type in CROP_DISPLAY_NAMES else 0
    base_features = [quantity_kg, days_ahead, crop_index, math.log1p(quantity_kg)]
    if extra_features:
        base_features.extend(extra_features)
    features = np.array(base_features, dtype=np.float32)

    result = model_loader.get_prediction("predict_price", features=features)
    if not result.get("success"):
        return {
            "success": False,
            "message": result.get("error", "Price predictor unavailable"),
            "predicted_price_usd": None,
        }
    return {
        "success": True,
        "crop_type": crop_type,
        "quantity_kg": quantity_kg,
        "days_ahead": days_ahead,
        "predicted_price_usd": result["predicted_price_usd"],
    }


async def detect_fraud(listing_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a listing for fraud using IsolationForest.
    Expected keys: amount, quantity, price_per_kg, hour, farmer_history,
                   buyer_history, is_off_hour (0/1)
    """
    amount         = float(listing_data.get("amount", 0))
    quantity       = float(listing_data.get("quantity", 1))
    price_per_kg   = float(listing_data.get("price_per_kg", amount / max(quantity, 1e-9)))
    hour           = float(listing_data.get("hour", 12))
    farmer_history = float(listing_data.get("farmer_history", 0))
    buyer_history  = float(listing_data.get("buyer_history", 0))
    is_off_hour    = float(listing_data.get("is_off_hour", 0))
    log_amount     = math.log1p(amount)
    log_quantity   = math.log1p(quantity)

    features = np.array(
        [amount, quantity, price_per_kg, hour, farmer_history, buyer_history,
         is_off_hour, log_amount, log_quantity],
        dtype=np.float32,
    )

    result = model_loader.get_prediction("detect_fraud", features=features)
    if not result.get("success"):
        return {
            "success": False,
            "message": result.get("error", "Fraud detector unavailable"),
            "is_fraudulent": False,
            "risk_level": "unknown",
        }
    return {
        "success": True,
        "is_fraudulent": result["is_fraudulent"],
        "anomaly_score": result["anomaly_score"],
        "risk_level": result["risk_level"],
        "requires_review": result["is_fraudulent"] or result["risk_level"] == "medium",
    }


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

_TREATMENTS: Dict[str, str] = {
    "rust":           "Apply fungicide; remove infected leaves; improve air circulation.",
    "blight":         "Remove affected parts; apply copper-based fungicide; avoid overhead watering.",
    "powdery_mildew": "Apply sulfur or potassium bicarbonate spray; reduce humidity.",
    "mosaic_virus":   "Remove infected plants; control aphid vectors; use resistant varieties.",
    "leaf_spot":      "Apply fungicide; avoid wetting foliage; rotate crops.",
    "rot":            "Improve drainage; reduce watering; remove infected material.",
    "healthy":        None,
}


def _get_treatment(disease: str) -> Optional[str]:
    return _TREATMENTS.get(disease, "Consult an agronomist for diagnosis and treatment.")
