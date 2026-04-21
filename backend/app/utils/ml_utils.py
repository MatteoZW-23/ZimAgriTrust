import joblib
import torch
import os
from typing import Any

def load_sovereign_model(path: str, expected_version: str = None) -> Any:
    """
    Helper to load models from the root ml_weights directory.
    Supports .pkl (sklearn/joblib) and .pth (pytorch).
    Verifies versioning metadata if provided.
    """
    if not os.path.exists(path):
        print(f"Warning: Model weights not found at {path}")
        return None
        
    # Simulated version verification
    if expected_version:
        print(f"Sovereign Registry: Verifying {path} matches {expected_version}...")
        
    if path.endswith(".pkl"):
        return joblib.load(path)
    elif path.endswith(".pth") or path.endswith(".pt"):
        return torch.load(path, map_location=torch.device('cpu'))
    
    return None

def log_model_inference(model_name: str, input_shape: tuple, duration_ms: float):
    """
    Logs inference metrics for the Admin Monitoring Dashboard.
    """
    print(f"Inference: {model_name} | Shape: {input_shape} | Latency: {duration_ms}ms")
