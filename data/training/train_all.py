#!/={sys.executable}
"""
Master Training Script - Train all models in sequence
Run with: python train_all.py
"""

import subprocess
import sys
import os
from datetime import datetime

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def run_script(script_path):
    """Run a Python script and return success status"""
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=False
    )
    return result.returncode == 0

def main():
    print_header("AGRITRUST MODEL TRAINING PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    scripts_dir = "scripts"
    results = {}
    
    # Order matters - dependencies first
    models = [
        ("Risk Scorer",       f"{scripts_dir}/train_risk_scorer.py"),
        ("Fraud Detector",    f"{scripts_dir}/train_fraud_detector.py"),
        ("Price Forecaster",  f"{scripts_dir}/train_price_forecaster.py"),
        ("Demand Forecaster", f"{scripts_dir}/train_demand_forecaster.py"),
        ("Crop Vision",       f"{scripts_dir}/train_crop_vision.py"),
    ]
    
    for name, script in models:
        script_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
        if os.path.exists(script_full_path):
            print_header(f"Training {name}")
            success = run_script(script_full_path)
            results[name] = "✅ PASS" if success else "❌ FAIL"
        else:
            print(f"⚠️ Script not found: {script_full_path}")
            results[name] = "⚠️ SKIPPED"
    
    # Summary
    print_header("TRAINING SUMMARY")
    for name, status in results.items():
        print(f"  {status} - {name}")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✅ All models saved to: ../ml_weights/")

if __name__ == "__main__":
    main()
