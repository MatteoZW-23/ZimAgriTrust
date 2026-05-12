#!/usr/bin/env python3
"""
Export validation script.
Run inside the Jupyter container after training notebooks to verify all models
are correct and copy them to the shared volume for backend consumption.

Usage:
    python export_to_production.py [--exports-dir /workspace/exports/models]
                                   [--prod-dir /app/models]
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_MODELS = {
    "crop_classifier_v1.onnx":  "onnx",
    "disease_detector_v1.onnx": "onnx",
    "quality_grader_v1.onnx":   "onnx",
    "price_predictor_v1.pkl":   "pkl",
    "price_scaler_v1.pkl":      "pkl",
    "risk_scorer_v1.pkl":       "pkl",
    "risk_scaler_v1.pkl":       "pkl",
    "fraud_detector_v1.pkl":    "pkl",
    "fraud_scaler_v1.pkl":      "pkl",
    "demand_forecaster_v1.pkl": "pkl",
    "demand_scaler_v1.pkl":     "pkl",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_onnx(path: Path) -> bool:
    try:
        import numpy as np
        import onnxruntime as ort
        sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        dummy = np.random.randn(1, 3, 224, 224).astype(np.float32)
        out = sess.run(None, {sess.get_inputs()[0].name: dummy})
        print(f"  ✓ ONNX {path.name} — output shape {out[0].shape}")
        return True
    except Exception as e:
        print(f"  ✗ ONNX {path.name} validation failed: {e}")
        return False


def validate_pkl(path: Path) -> bool:
    try:
        import joblib
        obj = joblib.load(path)
        print(f"  ✓ pkl  {path.name} — type: {type(obj).__name__}")
        return True
    except Exception as e:
        print(f"  ✗ pkl  {path.name} validation failed: {e}")
        return False


def run(exports_dir: Path, prod_dir: Path) -> int:
    print(f"\n{'='*60}")
    print("ZimAgriTrust — Model Export Validation Pipeline")
    print(f"Source : {exports_dir}")
    print(f"Target : {prod_dir}")
    print(f"{'='*60}\n")

    # 1. Check all required files exist
    missing = [f for f in REQUIRED_MODELS if not (exports_dir / f).exists()]
    if missing:
        print(f"[FAIL] {len(missing)} required model(s) missing:")
        for f in missing:
            print(f"       ✗ {f}")
        print("\nRun notebooks 04-07 to train and export the models first.")
        return 1

    print("[PASS] All required model files present\n")

    # 2. Validate each model loads correctly
    print("Validating model files...")
    errors = []
    for fname, ftype in REQUIRED_MODELS.items():
        path = exports_dir / fname
        ok = validate_onnx(path) if ftype == "onnx" else validate_pkl(path)
        if not ok:
            errors.append(fname)

    if errors:
        print(f"\n[FAIL] {len(errors)} model(s) failed validation: {errors}")
        return 1

    print("\n[PASS] All models validated successfully\n")

    # 3. Generate manifest with checksums
    print("Generating manifest.json...")
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sovereign_status": "PRODUCTION_READY",
        "models": {},
    }
    for fname in REQUIRED_MODELS:
        path = exports_dir / fname
        manifest["models"][fname] = {
            "sha256":   sha256(path),
            "size_kb":  path.stat().st_size // 1024,
            "status":   "ready",
        }

    manifest_path = exports_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"  ✓ manifest.json written to {manifest_path}")

    # 4. Copy to production shared volume
    print(f"\nCopying models to production directory: {prod_dir}")
    prod_dir.mkdir(parents=True, exist_ok=True)
    for fname in list(REQUIRED_MODELS.keys()) + ["manifest.json"]:
        src = exports_dir / fname
        dst = prod_dir / fname
        shutil.copy2(src, dst)
        print(f"  → {fname} ({src.stat().st_size // 1024} KB)")

    # 5. Verify destination checksums match source
    print("\nVerifying destination checksums...")
    for fname in REQUIRED_MODELS:
        src_hash = manifest["models"][fname]["sha256"]
        dst_hash = sha256(prod_dir / fname)
        if src_hash != dst_hash:
            print(f"  ✗ Checksum mismatch for {fname}")
            return 1
        print(f"  ✓ {fname}")

    print("\n" + "="*60)
    print("✅  EXPORT COMPLETE — all models ready for production")
    print(f"    Backend container loads from: {prod_dir}")
    print("="*60 + "\n")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate and copy ML models to production volume")
    parser.add_argument("--exports-dir", default="/workspace/exports/models", type=Path)
    parser.add_argument("--prod-dir",    default="/app/models",               type=Path)
    args = parser.parse_args()

    sys.exit(run(args.exports_dir, args.prod_dir))
