"""
Central model loader for all production inference models.
Loads ONNX models and sklearn .pkl models from the shared volume.
NO training logic here — this is pure inference loading.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np

from app.ml.onnx_inference import ONNXModelLoader

logger = logging.getLogger(__name__)

# Shared volume path injected via MODELS_PATH env var (default /app/models)
_MODELS_PATH = Path(os.getenv("MODELS_PATH", "/app/models"))

def _resolve_model(filename: str) -> Path:
    """Return model path from shared volume (MODELS_PATH). Returns path regardless of existence — callers handle missing."""
    return _MODELS_PATH / filename


class ModelLoader:
    """
    Singleton-style central loader.
    Call load_all() once at startup; then use get_prediction() for inference.
    """

    def __init__(self):
        self._crop_classifier: Optional[ONNXModelLoader] = None
        self._disease_detector: Optional[ONNXModelLoader] = None
        self._price_predictor: Optional[Any] = None
        self._price_scaler: Optional[Any] = None
        self._fraud_detector: Optional[Any] = None
        self._fraud_scaler: Optional[Any] = None
        self._manifest: Dict = {}

    # ──────────────────────────────────────────────
    # Loaders
    # ──────────────────────────────────────────────

    def load_crop_classifier(self) -> bool:
        path = _resolve_model("crop_classifier_v1.onnx")
        self._crop_classifier = ONNXModelLoader(str(path))
        ok = self._crop_classifier.load()
        logger.info("ModelLoader | crop_classifier loaded=%s path=%s", ok, path)
        return ok

    def load_disease_detector(self) -> bool:
        path = _resolve_model("disease_detector_v1.onnx")
        self._disease_detector = ONNXModelLoader(str(path))
        ok = self._disease_detector.load()
        logger.info("ModelLoader | disease_detector loaded=%s path=%s", ok, path)
        return ok

    def load_price_predictor(self) -> bool:
        model_path = _resolve_model("price_predictor_v1.pkl")
        scaler_path = _resolve_model("price_scaler_v1.pkl")
        try:
            self._price_predictor = joblib.load(model_path)
            if scaler_path.exists():
                self._price_scaler = joblib.load(scaler_path)
            logger.info("ModelLoader | price_predictor loaded from %s", model_path)
            return True
        except Exception as exc:
            logger.warning("ModelLoader | price_predictor not yet available: %s", exc)
            return False

    def load_fraud_detector(self) -> bool:
        model_path = _resolve_model("fraud_detector_v1.pkl")
        scaler_path = _resolve_model("fraud_scaler_v1.pkl")
        try:
            self._fraud_detector = joblib.load(model_path)
            if scaler_path.exists():
                self._fraud_scaler = joblib.load(scaler_path)
            logger.info("ModelLoader | fraud_detector loaded from %s", model_path)
            return True
        except Exception as exc:
            logger.warning("ModelLoader | fraud_detector not yet available: %s", exc)
            return False

    def load_manifest(self):
        path = _resolve_model("manifest.json")
        try:
            with open(path) as f:
                self._manifest = json.load(f)
        except Exception:
            self._manifest = {}

    def load_all(self):
        """Load every model at startup. Failures are non-fatal."""
        self.load_manifest()
        self.load_crop_classifier()
        self.load_disease_detector()
        self.load_price_predictor()
        self.load_fraud_detector()
        logger.info("ModelLoader | all models loaded. manifest=%s", self._manifest)

    # ──────────────────────────────────────────────
    # Inference routing
    # ──────────────────────────────────────────────

    CROP_CLASSES = [
        "maize", "mango", "tomato", "soya_beans", "groundnuts",
        "tobacco", "cotton", "cabbage", "potato", "onion",
        "sugar_beans", "sunflower",
    ]

    DISEASE_CLASSES = [
        "healthy", "rust", "blight", "powdery_mildew",
        "mosaic_virus", "leaf_spot", "rot",
    ]

    def get_prediction(self, task: str, **kwargs) -> Dict:
        """Route to the correct model based on task name."""
        if task == "classify_crop":
            return self._infer_crop(kwargs["image_bytes"])
        if task == "detect_disease":
            return self._infer_disease(kwargs["image_bytes"])
        if task == "predict_price":
            return self._infer_price(kwargs["features"])
        if task == "detect_fraud":
            return self._infer_fraud(kwargs["features"])
        return {"success": False, "error": f"Unknown task: {task}"}

    def _infer_crop(self, image_bytes: bytes) -> Dict:
        if self._crop_classifier is None or self._crop_classifier.session is None:
            return {"success": False, "error": "crop_classifier model not loaded", "crop_type": "unknown", "confidence": 0.0}
        result = self._crop_classifier.predict(image_bytes)
        if not result["success"]:
            return result
        idx = result["top_class_index"] % len(self.CROP_CLASSES)
        return {
            "success": True,
            "crop_type": self.CROP_CLASSES[idx],
            "confidence": result["confidence"],
            "top_class_index": idx,
        }

    def _infer_disease(self, image_bytes: bytes) -> Dict:
        if self._disease_detector is None or self._disease_detector.session is None:
            return {"success": False, "error": "disease_detector model not loaded", "disease": "unknown", "confidence": 0.0}
        result = self._disease_detector.predict(image_bytes)
        if not result["success"]:
            return result
        idx = result["top_class_index"] % len(self.DISEASE_CLASSES)
        return {
            "success": True,
            "disease": self.DISEASE_CLASSES[idx],
            "confidence": result["confidence"],
        }

    def _infer_price(self, features: np.ndarray) -> Dict:
        if self._price_predictor is None:
            return {"success": False, "error": "price_predictor model not loaded"}
        try:
            X = np.array(features).reshape(1, -1)
            if self._price_scaler is not None:
                X = self._price_scaler.transform(X)
            pred = float(self._price_predictor.predict(X)[0])
            return {"success": True, "predicted_price_usd": round(pred, 4)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _infer_fraud(self, features: np.ndarray) -> Dict:
        if self._fraud_detector is None:
            return {"success": False, "error": "fraud_detector model not loaded"}
        try:
            X = np.array(features).reshape(1, -1)
            if self._fraud_scaler is not None:
                X = self._fraud_scaler.transform(X)
            prediction = self._fraud_detector.predict(X)[0]
            score = float(self._fraud_detector.score_samples(X)[0])
            is_fraud = prediction == -1
            return {
                "success": True,
                "is_fraudulent": bool(is_fraud),
                "anomaly_score": round(score, 4),
                "risk_level": "high" if is_fraud else ("medium" if score < -0.1 else "low"),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    @property
    def manifest(self) -> Dict:
        return self._manifest


# Module-level singleton
model_loader = ModelLoader()
