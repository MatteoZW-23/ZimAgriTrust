"""
Train YOLOv8-cls disease detection model on the Crop Disease dataset.

Run AFTER prepare_disease_dataset.py:

    # Step 1 — prepare dataset (one-time)
    python data/training/disease/prepare_disease_dataset.py

    # Step 2 — train
    python data/training/disease/train_disease_model.py

    # Optional flags
    python data/training/disease/train_disease_model.py \
        --epochs 60 --batch 32 --imgsz 224 --device cpu

Outputs:
    ml_weights/disease_classifier.pt   ← best weights (auto-copied)
    ml_weights/disease_class_map.json  ← class index → disease name
    ml_weights/runs/disease_*/         ← full training run artefacts
"""

import argparse
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

_DATASET_DIR    = Path("data/training/disease/dataset")
_WEIGHTS_DIR    = Path("ml_weights")
_FINAL_WEIGHTS  = _WEIGHTS_DIR / "disease_classifier.pt"
_FINAL_CLASS_MAP = _WEIGHTS_DIR / "disease_class_map.json"


def train(epochs: int, batch: int, imgsz: int, device: str, patience: int):
    try:
        from ultralytics import YOLO
    except ImportError:
        raise RuntimeError("ultralytics not installed. Run: pip install ultralytics")

    dataset = _DATASET_DIR.resolve()
    if not (dataset / "images" / "train").exists():
        raise RuntimeError(
            f"Dataset not found at {dataset}.\n"
            "Run: python data/training/disease/prepare_disease_dataset.py"
        )

    # Copy class_map to ml_weights so the service can load it at runtime
    src_map = dataset / "class_map.json"
    if src_map.exists():
        shutil.copy2(src_map, _FINAL_CLASS_MAP)
        with open(_FINAL_CLASS_MAP) as f:
            class_map = json.load(f)
        logger.info("Classes (%d): %s", len(class_map), list(class_map.values()))
    else:
        raise FileNotFoundError(f"class_map.json not found at {src_map}")

    _WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    run_name = f"disease_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info("Starting training run: %s", run_name)
    logger.info("  epochs=%d  batch=%d  imgsz=%d  device=%s", epochs, batch, imgsz, device)

    model = YOLO("yolov8n-cls.pt")   # nano classification head — fast, accurate

    results = model.train(
        data=str(dataset),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=str(_WEIGHTS_DIR / "runs"),
        name=run_name,
        exist_ok=True,
        patience=patience,
        save=True,
        plots=True,
        workers=4,
        # Augmentation — helps with limited rice/wheat samples
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        flipud=0.3,
        fliplr=0.5,
        degrees=15.0,
        translate=0.1,
        scale=0.5,
    )

    # Copy best weights to canonical path
    best_pt = _WEIGHTS_DIR / "runs" / run_name / "weights" / "best.pt"
    if best_pt.exists():
        shutil.copy2(best_pt, _FINAL_WEIGHTS)
        logger.info("Best weights saved → %s", _FINAL_WEIGHTS)
    else:
        logger.warning("best.pt not found at %s — check training run", best_pt)

    # Print final metrics
    try:
        top1 = results.results_dict.get("metrics/accuracy_top1", "N/A")
        top5 = results.results_dict.get("metrics/accuracy_top5", "N/A")
        logger.info("Final  top-1: %s  top-5: %s", top1, top5)
    except Exception:
        pass

    logger.info("\nTraining complete. Model ready at: %s", _FINAL_WEIGHTS)
    return results


def validate():
    """Quick validation pass on the val split."""
    try:
        from ultralytics import YOLO
    except ImportError:
        raise RuntimeError("ultralytics not installed.")

    if not _FINAL_WEIGHTS.exists():
        raise FileNotFoundError(f"No trained model at {_FINAL_WEIGHTS}. Train first.")

    model = YOLO(str(_FINAL_WEIGHTS))
    metrics = model.val(data=str(_DATASET_DIR.resolve()))
    logger.info("Validation  top-1: %.4f  top-5: %.4f", metrics.top1, metrics.top5)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train crop disease classifier")
    parser.add_argument("--epochs",   type=int,   default=50)
    parser.add_argument("--batch",    type=int,   default=32)
    parser.add_argument("--imgsz",    type=int,   default=224)
    parser.add_argument("--device",   type=str,   default="cpu",
                        help="cpu | 0 | 0,1  (GPU index for CUDA)")
    parser.add_argument("--patience", type=int,   default=15,
                        help="Early-stopping patience (epochs without improvement)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Skip training, just run validation on existing model")
    args = parser.parse_args()

    if args.validate_only:
        validate()
    else:
        train(
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            patience=args.patience,
        )
