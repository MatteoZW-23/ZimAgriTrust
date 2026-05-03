#!/usr/bin/env python3
"""
Kaggle Agriculture Crops Dataset Downloader & Preprocessor
Dataset: osamajalilhassan/agriculture-crops-dataset

Usage:
    python download_kaggle_dataset.py

Requirements:
    pip install kagglehub
    Set KAGGLE_USERNAME and KAGGLE_KEY environment variables,
    or place kaggle.json in ~/.kaggle/kaggle.json

What this does:
    1. Downloads the dataset via kagglehub
    2. Inspects the folder structure to discover class names
    3. Splits images into train/val sets (80/20)
    4. Writes dataset.yaml for YOLO training
    5. Outputs a class_map.json for use by the classifier
"""

import json
import logging
import os
import random
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
DEST_ROOT   = Path("data/training/data/kaggle_crops")
TRAIN_DIR   = DEST_ROOT / "images" / "train"
VAL_DIR     = DEST_ROOT / "images" / "val"
YAML_PATH   = DEST_ROOT / "dataset.yaml"
CLASS_MAP   = DEST_ROOT / "class_map.json"

VAL_SPLIT   = 0.20   # 20% validation
RANDOM_SEED = 42

IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def download_dataset() -> Path:
    """Download via kagglehub and return the local path."""
    try:
        import kagglehub
    except ImportError:
        raise RuntimeError(
            "kagglehub is not installed. Run: pip install kagglehub"
        )

    logger.info("Downloading osamajalilhassan/agriculture-crops-dataset ...")
    path = kagglehub.dataset_download("osamajalilhassan/agriculture-crops-dataset")
    logger.info(f"Dataset downloaded to: {path}")
    return Path(path)


def discover_classes(dataset_path: Path) -> dict[str, Path]:
    """
    Walk the downloaded folder and find class directories.
    Supports both flat  (dataset_path/<class>/)
    and nested          (dataset_path/<split>/<class>/) layouts.
    Returns {class_name: source_dir}.
    """
    class_dirs: dict[str, Path] = {}

    # Try flat layout first
    candidates = [p for p in dataset_path.iterdir() if p.is_dir()]
    has_images = any(
        f.suffix.lower() in IMAGE_EXTS
        for c in candidates
        for f in c.iterdir()
        if f.is_file()
    )

    if has_images:
        for d in candidates:
            class_dirs[d.name.lower().replace(" ", "_")] = d
        logger.info(f"Flat layout detected — {len(class_dirs)} classes")
        return class_dirs

    # Nested layout: look one level deeper
    for split_dir in candidates:
        for class_dir in split_dir.iterdir():
            if class_dir.is_dir():
                key = class_dir.name.lower().replace(" ", "_")
                if key not in class_dirs:
                    class_dirs[key] = class_dir
    logger.info(f"Nested layout detected — {len(class_dirs)} classes")
    return class_dirs


def collect_images(class_dir: Path) -> list[Path]:
    return [
        f for f in class_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    ]


def split_and_copy(class_dirs: dict[str, Path]) -> dict:
    """Copy images into train/val folders and return stats."""
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    VAL_DIR.mkdir(parents=True, exist_ok=True)

    random.seed(RANDOM_SEED)
    stats = {}

    for class_name, src_dir in class_dirs.items():
        images = collect_images(src_dir)
        if not images:
            logger.warning(f"No images found for class '{class_name}' — skipping")
            continue

        random.shuffle(images)
        split_idx = max(1, int(len(images) * (1 - VAL_SPLIT)))
        train_imgs = images[:split_idx]
        val_imgs   = images[split_idx:]

        for split, imgs in [("train", train_imgs), ("val", val_imgs)]:
            dest = (TRAIN_DIR if split == "train" else VAL_DIR) / class_name
            dest.mkdir(parents=True, exist_ok=True)
            for img in imgs:
                shutil.copy2(img, dest / img.name)

        stats[class_name] = {"train": len(train_imgs), "val": len(val_imgs)}
        logger.info(f"  {class_name}: {len(train_imgs)} train / {len(val_imgs)} val")

    return stats


def write_yaml(class_names: list[str]) -> None:
    """Write dataset.yaml for YOLO classification training."""
    import yaml  # PyYAML

    config = {
        "path": str(DEST_ROOT.resolve()),
        "train": "images/train",
        "val":   "images/val",
        "nc":    len(class_names),
        "names": class_names,
        "task":  "classify",
    }
    with open(YAML_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info(f"dataset.yaml written → {YAML_PATH}")


def write_class_map(class_names: list[str]) -> None:
    """Write class_map.json so the classifier can load it at runtime."""
    mapping = {str(i): name for i, name in enumerate(class_names)}
    with open(CLASS_MAP, "w") as f:
        json.dump(mapping, f, indent=2)
    logger.info(f"class_map.json written → {CLASS_MAP}")


def main():
    logger.info("=== ZimAgritrust Kaggle Dataset Preprocessor ===")

    dataset_path = download_dataset()

    logger.info("Discovering class directories ...")
    class_dirs = discover_classes(dataset_path)

    if not class_dirs:
        raise RuntimeError(
            f"No class directories found in {dataset_path}. "
            "Check the dataset structure manually."
        )

    logger.info(f"Found {len(class_dirs)} classes: {sorted(class_dirs.keys())}")

    logger.info("Splitting and copying images ...")
    stats = split_and_copy(class_dirs)

    class_names = sorted(stats.keys())
    write_yaml(class_names)
    write_class_map(class_names)

    # Summary
    total_train = sum(v["train"] for v in stats.values())
    total_val   = sum(v["val"]   for v in stats.values())
    logger.info("=== Preprocessing Complete ===")
    logger.info(f"Classes : {len(class_names)}")
    logger.info(f"Train   : {total_train} images")
    logger.info(f"Val     : {total_val} images")
    logger.info(f"Output  : {DEST_ROOT.resolve()}")
    logger.info(f"YAML    : {YAML_PATH}")
    logger.info(f"Classes : {CLASS_MAP}")
    logger.info("Next step: python data/training/scripts/train_crop_vision.py")


if __name__ == "__main__":
    main()
