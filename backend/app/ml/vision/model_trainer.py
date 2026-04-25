"""
AgriTrust Crop Vision Model Trainer
Trains a YOLOv8 classification model using the Kaggle agriculture-crops-dataset.

Dataset must be preprocessed first:
    python data/training/scripts/download_kaggle_dataset.py

Then train:
    python data/training/scripts/train_crop_vision.py
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Canonical paths ────────────────────────────────────────────────────────────
_DATASET_ROOT  = Path("data/training/data/kaggle_crops")
_WEIGHTS_DIR   = Path("ml_weights")
_FINAL_WEIGHTS = _WEIGHTS_DIR / "crop_classifier.pt"
_CLASS_MAP     = _DATASET_ROOT / "class_map.json"


class CropModelTrainer:
    """
    Trains a YOLOv8-cls model on the Kaggle agriculture-crops-dataset.
    Class names are loaded dynamically from class_map.json — no hardcoding.
    """

    def __init__(self, dataset_root: str = str(_DATASET_ROOT)):
        self.dataset_root = Path(dataset_root)
        self.class_map_path = self.dataset_root / "class_map.json"
        _WEIGHTS_DIR.mkdir(exist_ok=True, parents=True)

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_class_names(self) -> list[str]:
        """Return class names from class_map.json (populated by download script)."""
        if not self.class_map_path.exists():
            raise FileNotFoundError(
                f"class_map.json not found at {self.class_map_path}.\n"
                "Run: python data/training/scripts/download_kaggle_dataset.py"
            )
        with open(self.class_map_path) as f:
            mapping = json.load(f)
        return [mapping[str(i)] for i in range(len(mapping))]

    def train(
        self,
        epochs: int = 50,
        imgsz: int = 224,
        batch: int = 32,
        device: str = "cpu",
    ):
        """
        Train the YOLOv8 classification model.
        Saves best weights to ml_weights/crop_classifier.pt.
        """
        self._validate_dataset()
        class_names = self.get_class_names()
        logger.info(f"Training on {len(class_names)} classes: {class_names}")

        model = YOLO("yolov8n-cls.pt")
        run_name = f"crop_classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        results = model.train(
            data=str(self.dataset_root.resolve()),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            project=str(_WEIGHTS_DIR / "runs"),
            name=run_name,
            exist_ok=True,
            patience=15,
            save=True,
            plots=True,
        )

        best_pt = _WEIGHTS_DIR / "runs" / run_name / "weights" / "best.pt"
        if best_pt.exists():
            shutil.copy2(best_pt, _FINAL_WEIGHTS)
            logger.info(f"Best weights saved → {_FINAL_WEIGHTS}")
        else:
            logger.warning(f"best.pt not found at {best_pt}")

        return results

    def validate(self, model_path: Path = _FINAL_WEIGHTS):
        """Run validation and return metrics."""
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        model = YOLO(str(model_path))
        metrics = model.val(data=str(self.dataset_root.resolve()))
        logger.info(f"Top-1: {metrics.top1:.4f}  Top-5: {metrics.top5:.4f}")
        return metrics

    def export_onnx(self, model_path: Path = _FINAL_WEIGHTS) -> str:
        """Export trained model to ONNX for deployment."""
        model = YOLO(str(model_path))
        path = model.export(format="onnx", imgsz=224)
        logger.info(f"ONNX exported → {path}")
        return path

    # ── Internal ───────────────────────────────────────────────────────────────

    def _validate_dataset(self):
        train_dir = self.dataset_root / "images" / "train"
        if not train_dir.exists() or not any(train_dir.rglob("*")):
            raise RuntimeError(
                f"Training data not found at {train_dir}.\n"
                "Run: python data/training/scripts/download_kaggle_dataset.py"
            )
