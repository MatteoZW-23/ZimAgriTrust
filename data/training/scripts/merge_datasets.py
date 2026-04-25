#!/usr/bin/env python3
"""
AgriTrust Dataset Merger
Combines two image datasets into one unified train/val split:
  1. Local dataset  — data/training/data/local_crops/   (30 classes, flat layout)
  2. Kaggle dataset — data/training/data/kaggle_crops/  (run download_kaggle_dataset.py first)

Output:
  data/training/data/merged_crops/
    images/train/<class>/
    images/val/<class>/
  data/training/data/merged_crops/class_map.json
  data/training/data/merged_crops/dataset.yaml

Usage:
    python data/training/scripts/merge_datasets.py
    python data/training/scripts/merge_datasets.py --local-only   # skip Kaggle
"""

import argparse
import json
import logging
import random
import shutil
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT    = Path(__file__).resolve().parents[3]
LOCAL_SRC    = REPO_ROOT / "data/training/data/local_crops"
KAGGLE_SRC   = REPO_ROOT / "data/training/data/kaggle_crops/images/train"
MERGED_ROOT  = REPO_ROOT / "data/training/data/merged_crops"
TRAIN_DIR    = MERGED_ROOT / "images" / "train"
VAL_DIR      = MERGED_ROOT / "images" / "val"
CLASS_MAP    = MERGED_ROOT / "class_map.json"
YAML_PATH    = MERGED_ROOT / "dataset.yaml"

VAL_SPLIT    = 0.20
RANDOM_SEED  = 42
IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ── Name normalisation ─────────────────────────────────────────────────────────
# Maps folder names from both datasets to a single canonical class name.
NAME_MAP = {
    # local dataset variations
    "coffee-plant":          "coffee",
    "fox_nut(makhana)":      "fox_nut",
    "mustard-oil":           "mustard",
    "olive-tree":            "olive",
    "pearl_millet(bajra)":   "pearl_millet",
    "tobacco-plant":         "tobacco",
    "vigna-radiati(mung)":   "mung_bean",
    "soyabean":              "soya_beans",
    # kaggle dataset variations
    "soybeans":              "soya_beans",
    "soya beans":            "soya_beans",
    "groundnut":             "groundnuts",
    "chili":                 "chilli",
    "chilli pepper":         "chilli",
}


def normalise(name: str) -> str:
    key = name.lower().strip().replace(" ", "_")
    return NAME_MAP.get(key, key)


def collect_images(folder: Path) -> list[Path]:
    return [f for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTS]


def merge_sources(local_only: bool) -> dict[str, list[Path]]:
    """Returns {canonical_class: [image_paths]} from all sources."""
    class_images: dict[str, list[Path]] = {}

    # ── Source 1: Local dataset ────────────────────────────────────────────────
    if LOCAL_SRC.exists():
        for cls_dir in sorted(LOCAL_SRC.iterdir()):
            if not cls_dir.is_dir():
                continue
            canon = normalise(cls_dir.name)
            imgs  = collect_images(cls_dir)
            if imgs:
                class_images.setdefault(canon, []).extend(imgs)
                logger.info("LOCAL  | %-25s → %d images", canon, len(imgs))
    else:
        logger.warning("Local dataset not found at %s", LOCAL_SRC)

    # ── Source 2: Kaggle dataset ───────────────────────────────────────────────
    if not local_only:
        if KAGGLE_SRC.exists():
            for cls_dir in sorted(KAGGLE_SRC.iterdir()):
                if not cls_dir.is_dir():
                    continue
                canon = normalise(cls_dir.name)
                imgs  = collect_images(cls_dir)
                if imgs:
                    class_images.setdefault(canon, []).extend(imgs)
                    logger.info("KAGGLE | %-25s → %d images", canon, len(imgs))
        else:
            logger.warning(
                "Kaggle dataset not found at %s — run download_kaggle_dataset.py first", KAGGLE_SRC
            )

    return class_images


def split_and_copy(class_images: dict[str, list[Path]]) -> dict:
    """Deduplicate by filename, split 80/20, copy into merged folder."""
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    VAL_DIR.mkdir(parents=True, exist_ok=True)

    random.seed(RANDOM_SEED)
    stats = {}

    for canon, imgs in sorted(class_images.items()):
        # Deduplicate by filename (keeps last occurrence if same name from both sources)
        seen: dict[str, Path] = {}
        for p in imgs:
            seen[p.name] = p
        unique = list(seen.values())
        random.shuffle(unique)

        split_idx   = max(1, int(len(unique) * (1 - VAL_SPLIT)))
        train_imgs  = unique[:split_idx]
        val_imgs    = unique[split_idx:]

        for split, split_imgs in [("train", train_imgs), ("val", val_imgs)]:
            dest = (TRAIN_DIR if split == "train" else VAL_DIR) / canon
            dest.mkdir(parents=True, exist_ok=True)
            for img in split_imgs:
                shutil.copy2(img, dest / img.name)

        stats[canon] = {"train": len(train_imgs), "val": len(val_imgs), "total": len(unique)}
        logger.info("MERGED | %-25s → %d train / %d val", canon, len(train_imgs), len(val_imgs))

    return stats


def write_outputs(stats: dict) -> None:
    class_names = sorted(stats.keys())

    # class_map.json
    mapping = {str(i): name for i, name in enumerate(class_names)}
    with open(CLASS_MAP, "w") as f:
        json.dump(mapping, f, indent=2)
    logger.info("Wrote class_map.json  (%d classes)", len(class_names))

    # dataset.yaml
    config = {
        "path":  str(MERGED_ROOT.resolve()),
        "train": "images/train",
        "val":   "images/val",
        "nc":    len(class_names),
        "names": class_names,
        "task":  "classify",
    }
    with open(YAML_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info("Wrote dataset.yaml")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-only", action="store_true", help="Use only the local dataset")
    args = parser.parse_args()

    logger.info("=== AgriTrust Dataset Merger ===")
    logger.info("Local  : %s", LOCAL_SRC)
    logger.info("Kaggle : %s", KAGGLE_SRC)
    logger.info("Output : %s", MERGED_ROOT)

    class_images = merge_sources(local_only=args.local_only)

    if not class_images:
        raise RuntimeError("No images found in any source. Check dataset paths.")

    logger.info("\nSplitting and copying %d classes...", len(class_images))
    stats = split_and_copy(class_images)
    write_outputs(stats)

    total_train = sum(v["train"] for v in stats.values())
    total_val   = sum(v["val"]   for v in stats.values())
    total_imgs  = sum(v["total"] for v in stats.values())

    logger.info("\n=== Merge Complete ===")
    logger.info("Classes : %d", len(stats))
    logger.info("Total   : %d images", total_imgs)
    logger.info("Train   : %d", total_train)
    logger.info("Val     : %d", total_val)
    logger.info("Next    : python data/training/scripts/train_crop_vision.py --data merged_crops")


if __name__ == "__main__":
    main()
