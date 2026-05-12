"""
ONNX Runtime inference wrapper — production only, no training dependencies.
Loads pre-exported .onnx models from the shared volume mounted at /app/models.
"""

import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
    _ONNX_AVAILABLE = True
except ImportError:
    _ONNX_AVAILABLE = False
    logger.warning("onnxruntime not installed — ONNX inference disabled")

try:
    from PIL import Image
    import io
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


class ONNXModelLoader:
    """
    Lightweight ONNX inference session wrapper.
    Handles image preprocessing and single-image prediction.
    """

    def __init__(self, model_path: str, input_size: int = 224):
        self.model_path = Path(model_path)
        self.input_size = input_size
        self.session: Optional["ort.InferenceSession"] = None
        self.input_name: Optional[str] = None
        self.output_name: Optional[str] = None

    def load(self) -> bool:
        if not _ONNX_AVAILABLE:
            logger.error("onnxruntime not available — cannot load %s", self.model_path)
            return False
        if not self.model_path.exists():
            logger.warning("ONNX model not found at %s", self.model_path)
            return False
        try:
            providers = ["CPUExecutionProvider"]
            self.session = ort.InferenceSession(str(self.model_path), providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            logger.info("ONNXModelLoader | loaded %s", self.model_path.name)
            return True
        except Exception as exc:
            logger.error("ONNXModelLoader.load error: %s", exc)
            return False

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Resize + normalize image bytes to (1, 3, H, W) float32 tensor."""
        if _PIL_AVAILABLE:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img = img.resize((self.input_size, self.input_size), Image.BILINEAR)
            arr = np.array(img, dtype=np.float32) / 255.0
        elif _CV2_AVAILABLE:
            buf = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (self.input_size, self.input_size))
            arr = img.astype(np.float32) / 255.0
        else:
            raise RuntimeError("Neither Pillow nor OpenCV is available for image preprocessing")

        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = (arr - mean) / std
        # HWC → CHW → NCHW
        arr = arr.transpose(2, 0, 1)[np.newaxis, ...]
        return arr

    def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        """Run inference on raw image bytes. Returns top class index and confidence."""
        if self.session is None:
            return {"success": False, "error": "Model not loaded"}
        try:
            tensor = self.preprocess(image_bytes)
            outputs = self.session.run([self.output_name], {self.input_name: tensor})
            logits = outputs[0][0]
            # Softmax
            exp = np.exp(logits - logits.max())
            probs = exp / exp.sum()
            top_idx = int(np.argmax(probs))
            confidence = float(probs[top_idx])
            return {
                "success": True,
                "top_class_index": top_idx,
                "confidence": round(confidence, 4),
                "probabilities": probs.tolist(),
            }
        except Exception as exc:
            logger.error("ONNXModelLoader.predict error: %s", exc)
            return {"success": False, "error": str(exc)}


class BatchInference:
    """
    Optional batched inference over multiple images using a single ONNX session.
    """

    def __init__(self, loader: ONNXModelLoader):
        self.loader = loader

    def predict_batch(self, images: List[bytes]) -> List[Dict[str, Any]]:
        if self.loader.session is None:
            return [{"success": False, "error": "Model not loaded"}] * len(images)
        try:
            tensors = np.concatenate(
                [self.loader.preprocess(img) for img in images], axis=0
            )
            outputs = self.loader.session.run(
                [self.loader.output_name], {self.loader.input_name: tensors}
            )
            logits_batch = outputs[0]
            results = []
            for logits in logits_batch:
                exp = np.exp(logits - logits.max())
                probs = exp / exp.sum()
                top_idx = int(np.argmax(probs))
                results.append({
                    "success": True,
                    "top_class_index": top_idx,
                    "confidence": round(float(probs[top_idx]), 4),
                })
            return results
        except Exception as exc:
            logger.error("BatchInference.predict_batch error: %s", exc)
            return [{"success": False, "error": str(exc)}] * len(images)
