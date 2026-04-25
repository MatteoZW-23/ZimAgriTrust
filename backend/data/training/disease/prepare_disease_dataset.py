"""
Prepare the Crop Disease dataset for YOLOv8-cls training.

Usage:
    python data/training/disease/prepare_disease_dataset.py \
        --src "C:/Users/MJ/Desktop/CROP DESEASE/CropDisease/Crop___DIsease" \
        --dst data/training/disease/dataset

What it does:
  - Reads all class folders from --src
  - Skips the 'Invalid' folder
  - Splits images 80/20 train/val (stratified per class)
  - Writes YOLOv8-cls layout:
        dataset/
          train/<class>/<image>
          val/<class>/<image>
  - Writes class_map.json  {index: class_name}
  - Writes dataset_stats.json (counts per split/class)
"""

import argparse
import json
import random
import shutil
from pathlib import Path

SKIP_CLASSES = {"Invalid", "invalid"}
IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
TRAIN_RATIO  = 0.80
SEED         = 42


def prepare(src: Path, dst: Path):
    random.seed(SEED)

    src = src.resolve()
    dst = dst.resolve()

    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")

    # Collect class folders (sorted for reproducibility)
    class_dirs = sorted(
        [d for d in src.iterdir() if d.is_dir() and d.name not in SKIP_CLASSES]
    )
    if not class_dirs:
        raise RuntimeError(f"No class folders found in {src}")

    print(f"Found {len(class_dirs)} classes in {src}")

    class_map: dict[str, str] = {}   # {str(index): class_name}
    stats: dict = {"train": {}, "val": {}}

    for idx, cls_dir in enumerate(class_dirs):
        cls_name = cls_dir.name
        class_map[str(idx)] = cls_name

        images = [f for f in cls_dir.iterdir() if f.suffix.lower() in IMAGE_EXTS]
        random.shuffle(images)

        split_at   = int(len(images) * TRAIN_RATIO)
        train_imgs = images[:split_at]
        val_imgs   = images[split_at:]

        for split, imgs in [("train", train_imgs), ("val", val_imgs)]:
            out_dir = dst / "images" / split / cls_name
            out_dir.mkdir(parents=True, exist_ok=True)
            for img in imgs:
                shutil.copy2(img, out_dir / img.name)
            stats[split][cls_name] = len(imgs)

        print(f"  [{idx:02d}] {cls_name:<35} train={len(train_imgs):>4}  val={len(val_imgs):>4}")

    # Write class_map.json
    map_path = dst / "class_map.json"
    with open(map_path, "w") as f:
        json.dump(class_map, f, indent=2)
    print(f"\nclass_map.json → {map_path}")

    # Write stats
    stats_path = dst / "dataset_stats.json"
    total_train = sum(stats["train"].values())
    total_val   = sum(stats["val"].values())
    stats["totals"] = {"train": total_train, "val": total_val}
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"dataset_stats.json → {stats_path}")
    print(f"\nTotal  train: {total_train}  val: {total_val}  classes: {len(class_dirs)}")
    print(f"\nDataset ready at: {dst}")
    return dst, class_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Crop Disease dataset for YOLOv8-cls")
    parser.add_argument(
        "--src",
        default=r"C:/Users/MJ/Desktop/CROP DESEASE/CropDisease/Crop___DIsease",
        help="Path to the raw dataset folder containing class sub-folders",
    )
    parser.add_argument(
        "--dst",
        default="data/training/disease/dataset",
        help="Output directory for the prepared dataset",
    )
    args = parser.parse_args()
    prepare(Path(args.src), Path(args.dst))
