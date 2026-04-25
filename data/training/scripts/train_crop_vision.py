#!/usr/bin/env python3
"""
AgriTrust Crop Vision Model Trainer
Trains a YOLOv8 classification model on the merged crop dataset.

Prerequisites:
    python data/training/scripts/merge_datasets.py   # merges local + Kaggle
    pip install ultralytics

Usage:
    python data/training/scripts/train_crop_vision.py
    python data/training/scripts/train_crop_vision.py --data kaggle_crops
    python data/training/scripts/train_crop_vision.py --epochs 100 --device cuda
    python data/training/scripts/train_crop_vision.py --validate-only
    python data/training/scripts/train_crop_vision.py --export
"""

import argparse
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

WEIGHTS_DIR   = Path("ml_weights")
FINAL_WEIGHTS = WEIGHTS_DIR / "crop_classifier.pt"
DATA_BASE     = Path("data/training/data")


def resolve_dataset(name: str) -> Path:
    p = DATA_BASE / name
    if p.exists():
        return p
    # fallbacks in priority order
    for fallback in ["merged_crops", "local_crops", "kaggle_crops"]:
        fb = DATA_BASE / fallback
        if fb.exists():
            logger.warning("'%s' not found — using '%s' instead", name, fallback)
            return fb
    raise FileNotFoundError(
        f"No dataset found under {DATA_BASE}.\n"
        "Run: python data/training/scripts/merge_datasets.py"
    )


def load_class_map(dataset_root: Path) -> dict:
    cm = dataset_root / "class_map.json"
    if not cm.exists():
        raise FileNotFoundError(f"class_map.json not found at {cm}")
    with open(cm) as f:
        return json.load(f)


def validate_dataset(dataset_root: Path) -> tuple[int, int]:
    train_dir = dataset_root / "images" / "train"
    val_dir   = dataset_root / "images" / "val"
    if not train_dir.exists() or not any(train_dir.rglob("*")):
        raise RuntimeError(
            f"Training data not found at {train_dir}.\n"
            "Run: python data/training/scripts/merge_datasets.py"
        )
    train_count = sum(1 for _ in train_dir.rglob("*") if _.is_file())
    val_count   = sum(1 for _ in val_dir.rglob("*")   if _.is_file())
    logger.info("Dataset OK — %d train / %d val images", train_count, val_count)
    return train_count, val_count


def train(epochs: int, imgsz: int, batch: int, device: str, dataset_root: Path):
    try:
        from ultralytics import YOLO
    except ImportError:
        raise RuntimeError("ultralytics not installed. Run: pip install ultralytics")

    validate_dataset(dataset_root)
    class_map = load_class_map(dataset_root)
    logger.info("Training on %d classes: %s", len(class_map), list(class_map.values()))

    WEIGHTS_DIR.mkdir(exist_ok=True)
    model    = YOLO("yolov8n-cls.pt")
    run_name = f"crop_cls_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    logger.info("epochs=%d  imgsz=%d  batch=%d  device=%s", epochs, imgsz, batch, device)
    results = model.train(
        data=str(dataset_root.resolve()),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=str(WEIGHTS_DIR / "runs"),
        name=run_name,
        exist_ok=True,
        patience=15,
        save=True,
        plots=True,
    )

    best_pt = WEIGHTS_DIR / "runs" / run_name / "weights" / "best.pt"
    if best_pt.exists():
        shutil.copy2(best_pt, FINAL_WEIGHTS)
        logger.info("Best weights saved → %s", FINAL_WEIGHTS)
    else:
        logger.warning("best.pt not found at %s", best_pt)

    return results


def run_validate(dataset_root: Path, model_path: Path = FINAL_WEIGHTS):
    try:
        from ultralytics import YOLO
    except ImportError:
        raise RuntimeError("ultralytics not installed.")
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    model   = YOLO(str(model_path))
    metrics = model.val(data=str(dataset_root.resolve()))
    logger.info("Top-1: %.4f  Top-5: %.4f", metrics.top1, metrics.top5)
    return metrics


def export_onnx(model_path: Path = FINAL_WEIGHTS):
    try:
        from ultralytics import YOLO
    except ImportError:
        raise RuntimeError("ultralytics not installed.")
    model = YOLO(str(model_path))
    path  = model.export(format="onnx", imgsz=224)
    logger.info("ONNX exported → %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AgriTrust crop vision model")
    parser.add_argument("--data",          type=str,   default="merged_crops", help="Dataset folder name under data/training/data/")
    parser.add_argument("--epochs",        type=int,   default=50)
    parser.add_argument("--imgsz",         type=int,   default=224)
    parser.add_argument("--batch",         type=int,   default=32)
    parser.add_argument("--device",        type=str,   default="cpu", help="cpu | cuda | mps")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--export",        action="store_true")
    args = parser.parse_args()

    dataset = resolve_dataset(args.data)

    if args.validate_only:
        run_validate(dataset)
    else:
        train(args.epochs, args.imgsz, args.batch, args.device, dataset)
        if args.export:
            export_onnx()
