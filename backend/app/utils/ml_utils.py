import joblib
import os
from typing import Any

try:
    import torch as _torch
    _TORCH_AVAILABLE = True
except ImportError:
    _torch = None
    _TORCH_AVAILABLE = False

def load_sovereign_model(path: str, expected_version: str = None) -> Any:
    if not os.path.exists(path):
        return None
    if path.endswith(".pkl"):
        return joblib.load(path)
    elif (path.endswith(".pth") or path.endswith(".pt")) and _TORCH_AVAILABLE:
        return _torch.load(path, map_location=_torch.device('cpu'))
    return None

def log_model_inference(model_name: str, input_shape: tuple, duration_ms: float):
    print(f"Inference: {model_name} | Shape: {input_shape} | Latency: {duration_ms}ms")
