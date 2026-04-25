"""
Crop Disease Detector
Uses a YOLOv8-cls model trained on the Crop Disease dataset.

Model loading priority:
  1. ml_weights/disease_classifier.pt  (trained weights)
  2. OpenCV colour-histogram fallback   (no model required)

Class map loaded from: ml_weights/disease_class_map.json
"""

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

logger = logging.getLogger(__name__)

_WEIGHTS   = Path("ml_weights/disease_classifier.pt")
_CLASS_MAP = Path("ml_weights/disease_class_map.json")

# ── Human-readable metadata for each disease class ────────────────────────────
_DISEASE_META: Dict[str, Dict] = {
    "Corn___Common_Rust": {
        "display": "Corn Common Rust",
        "crop": "Corn / Maize",
        "severity": "Moderate",
        "description": "Orange-brown pustules on leaves caused by Puccinia sorghi.",
        "treatment": "Apply fungicide (mancozeb or azoxystrobin). Remove heavily infected leaves.",
        "prevention": "Plant resistant hybrids. Avoid overhead irrigation.",
    },
    "Corn___Gray_Leaf_Spot": {
        "display": "Corn Gray Leaf Spot",
        "crop": "Corn / Maize",
        "severity": "High",
        "description": "Rectangular gray-tan lesions caused by Cercospora zeae-maydis.",
        "treatment": "Apply strobilurin fungicide at early tasseling. Improve air circulation.",
        "prevention": "Rotate crops. Use resistant varieties. Reduce crop residue.",
    },
    "Corn___Healthy": {
        "display": "Healthy Corn",
        "crop": "Corn / Maize",
        "severity": "None",
        "description": "No disease detected. Crop appears healthy.",
        "treatment": "No treatment required.",
        "prevention": "Maintain current agronomic practices.",
    },
    "Corn___Leaf_Blight": {
        "display": "Corn Northern Leaf Blight",
        "crop": "Corn / Maize",
        "severity": "High",
        "description": "Long cigar-shaped gray-green lesions caused by Exserohilum turcicum.",
        "treatment": "Apply fungicide at first sign. Remove infected debris after harvest.",
        "prevention": "Plant resistant hybrids. Rotate with non-host crops.",
    },
    "Potato___Early_Blight": {
        "display": "Potato Early Blight",
        "crop": "Potato",
        "severity": "Moderate",
        "description": "Dark brown concentric ring lesions caused by Alternaria solani.",
        "treatment": "Apply chlorothalonil or mancozeb. Remove infected foliage.",
        "prevention": "Avoid overhead watering. Ensure adequate plant nutrition.",
    },
    "Potato___Healthy": {
        "display": "Healthy Potato",
        "crop": "Potato",
        "severity": "None",
        "description": "No disease detected. Crop appears healthy.",
        "treatment": "No treatment required.",
        "prevention": "Maintain current agronomic practices.",
    },
    "Potato___Late_Blight": {
        "display": "Potato Late Blight",
        "crop": "Potato",
        "severity": "Critical",
        "description": "Water-soaked lesions caused by Phytophthora infestans. Spreads rapidly.",
        "treatment": "Apply metalaxyl or cymoxanil immediately. Destroy infected plants.",
        "prevention": "Use certified disease-free seed. Apply preventive fungicide in wet seasons.",
    },
    "Rice___Brown_Spot": {
        "display": "Rice Brown Spot",
        "crop": "Rice",
        "severity": "Moderate",
        "description": "Oval brown lesions with yellow halo caused by Cochliobolus miyabeanus.",
        "treatment": "Apply iprodione or propiconazole. Ensure balanced fertilization.",
        "prevention": "Use resistant varieties. Avoid water stress and nutrient deficiency.",
    },
    "Rice___Healthy": {
        "display": "Healthy Rice",
        "crop": "Rice",
        "severity": "None",
        "description": "No disease detected. Crop appears healthy.",
        "treatment": "No treatment required.",
        "prevention": "Maintain current agronomic practices.",
    },
    "Rice___Hispa": {
        "display": "Rice Hispa",
        "crop": "Rice",
        "severity": "Moderate",
        "description": "White streaks on leaves caused by Dicladispa armigera (leaf miner beetle).",
        "treatment": "Apply chlorpyrifos or malathion. Remove and destroy affected tillers.",
        "prevention": "Avoid dense planting. Use light traps to monitor adult beetles.",
    },
    "Rice___Leaf_Blast": {
        "display": "Rice Leaf Blast",
        "crop": "Rice",
        "severity": "High",
        "description": "Diamond-shaped lesions with gray centers caused by Magnaporthe oryzae.",
        "treatment": "Apply tricyclazole or isoprothiolane at first sign.",
        "prevention": "Avoid excess nitrogen. Use blast-resistant varieties.",
    },
    "Wheat___Brown_Rust": {
        "display": "Wheat Brown Rust",
        "crop": "Wheat",
        "severity": "High",
        "description": "Orange-brown pustules on upper leaf surface caused by Puccinia triticina.",
        "treatment": "Apply propiconazole or tebuconazole fungicide.",
        "prevention": "Plant resistant varieties. Monitor fields from tillering stage.",
    },
    "Wheat___Healthy": {
        "display": "Healthy Wheat",
        "crop": "Wheat",
        "severity": "None",
        "description": "No disease detected. Crop appears healthy.",
        "treatment": "No treatment required.",
        "prevention": "Maintain current agronomic practices.",
    },
    "Wheat___Yellow_Rust": {
        "display": "Wheat Yellow Rust (Stripe Rust)",
        "crop": "Wheat",
        "severity": "High",
        "description": "Yellow-orange stripes of pustules caused by Puccinia striiformis.",
        "treatment": "Apply triazole fungicide (tebuconazole/propiconazole) immediately.",
        "prevention": "Use resistant varieties. Early sowing reduces exposure.",
    },
}

_SEVERITY_COLORS = {
    "None":     "#16a34a",
    "Moderate": "#f59e0b",
    "High":     "#ef4444",
    "Critical": "#7f1d1d",
}


def _load_class_map() -> Dict[str, str]:
    if _CLASS_MAP.exists():
        with open(_CLASS_MAP) as f:
            return json.load(f)
    return {}


class DiseaseDetector:
    """
    Crop disease classifier using a trained YOLOv8-cls model.
    Falls back to colour-histogram heuristics if no model is available.
    """

    def __init__(self):
        self.model = None
        self._class_map = _load_class_map()
        self._class_names: List[str] = [
            self._class_map[str(i)] for i in range(len(self._class_map))
        ]
        self._load_model()

    # ── Model loading ──────────────────────────────────────────────────────────

    def _load_model(self):
        if not YOLO_AVAILABLE:
            logger.info("DiseaseDetector | ultralytics not installed — using fallback.")
            return
        if _WEIGHTS.exists():
            try:
                self.model = YOLO(str(_WEIGHTS))
                logger.info("DiseaseDetector | Loaded trained weights: %s", _WEIGHTS)
            except Exception as e:
                logger.warning("DiseaseDetector | Failed to load weights (%s) — fallback active.", e)
        else:
            logger.info(
                "DiseaseDetector | No trained model at %s. "
                "Run: python data/training/disease/train_disease_model.py",
                _WEIGHTS,
            )

    def reload(self):
        """Hot-reload model weights (call after training completes)."""
        self._class_map = _load_class_map()
        self._class_names = [self._class_map[str(i)] for i in range(len(self._class_map))]
        self._load_model()

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect(self, image_data: bytes) -> Dict[str, Any]:
        """
        Detect disease from raw image bytes.
        Returns a structured result with disease name, severity, treatment advice.
        """
        try:
            image = self._preprocess(image_data)
            if self.model and self._class_names:
                return self._predict_yolo(image_data)
            return self._fallback(image)
        except Exception as e:
            logger.error("DiseaseDetector.detect error: %s", e)
            return self._error_response(str(e))

    def detect_batch(self, images: List[bytes]) -> List[Dict[str, Any]]:
        return [self.detect(img) for img in images]

    @property
    def is_trained(self) -> bool:
        return self.model is not None and bool(self._class_names)

    @property
    def supported_classes(self) -> List[str]:
        return list(self._class_names)

    # ── Inference ──────────────────────────────────────────────────────────────

    def _predict_yolo(self, image_data: bytes) -> Dict[str, Any]:
        results = self.model(self._preprocess(image_data), verbose=False)
        result  = results[0]

        probs      = result.probs
        top_idx    = int(probs.top1)
        confidence = float(probs.top1conf)

        class_name = self._class_names[top_idx] if top_idx < len(self._class_names) else "unknown"
        meta       = _DISEASE_META.get(class_name, {})
        is_healthy = "Healthy" in class_name

        # Top-3 predictions for UI display
        top3 = []
        for idx in probs.top5[:3]:
            idx = int(idx)
            name = self._class_names[idx] if idx < len(self._class_names) else "unknown"
            top3.append({
                "class": name,
                "display": _DISEASE_META.get(name, {}).get("display", name),
                "confidence": float(probs.data[idx]),
            })

        return {
            "success":          True,
            "disease_detected": not is_healthy,
            "class_name":       class_name,
            "disease_name":     meta.get("display", class_name.replace("___", " — ")),
            "crop":             meta.get("crop", class_name.split("___")[0]),
            "confidence":       round(confidence, 4),
            "severity":         meta.get("severity", "Unknown"),
            "severity_color":   _SEVERITY_COLORS.get(meta.get("severity", ""), "#94a3b8"),
            "description":      meta.get("description", ""),
            "treatment":        meta.get("treatment", "Consult an agricultural extension officer."),
            "prevention":       meta.get("prevention", ""),
            "top_predictions":  top3,
            "model":            "YOLOv8-cls (trained)",
            "requires_agent_review": confidence < 0.70,
        }

    def _fallback(self, image: np.ndarray) -> Dict[str, Any]:
        """Colour-histogram heuristic when no model is loaded."""
        hsv       = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        hue_mean  = float(np.mean(hsv[:, :, 0]))
        sat_mean  = float(np.mean(hsv[:, :, 1]))
        val_mean  = float(np.mean(hsv[:, :, 2]))

        # Very rough heuristic: brown/yellow tones suggest disease
        disease_detected = (hue_mean < 30 or hue_mean > 150) and sat_mean > 80

        return {
            "success":          True,
            "disease_detected": disease_detected,
            "class_name":       "unknown",
            "disease_name":     "Possible disease detected" if disease_detected else "Appears healthy",
            "crop":             "Unknown",
            "confidence":       0.45,
            "severity":         "Moderate" if disease_detected else "None",
            "severity_color":   _SEVERITY_COLORS.get("Moderate" if disease_detected else "None"),
            "description":      "Colour analysis only — train the model for accurate diagnosis.",
            "treatment":        "Consult an agricultural extension officer for confirmation.",
            "prevention":       "Train the disease model for precise recommendations.",
            "top_predictions":  [],
            "model":            "fallback (colour histogram)",
            "requires_agent_review": True,
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _preprocess(self, image_data: bytes) -> np.ndarray:
        img = Image.open(io.BytesIO(image_data)).convert("RGB").resize((224, 224))
        return np.array(img)

    def _error_response(self, error: str) -> Dict[str, Any]:
        return {
            "success":          False,
            "disease_detected": False,
            "error":            error,
            "disease_name":     "Analysis failed",
            "confidence":       0.0,
            "severity":         "Unknown",
            "treatment":        "Please retry with a clearer image.",
            "requires_agent_review": True,
        }


# Singleton
disease_detector = DiseaseDetector()
