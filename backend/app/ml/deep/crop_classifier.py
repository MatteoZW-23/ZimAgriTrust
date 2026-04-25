from PIL import Image
import numpy as np

class CropClassifier:
    """Stub — real classification handled by app/ml/vision/crop_classifier.py (YOLOv8)."""
    def __init__(self, model_path="data/ml-weights/crop_classifier_convnext.pth"):
        self.architecture = "YOLOv8-cls"

    def classify(self, image_path: str):
        return {"crop": "Unknown", "confidence": 0.0, "variety_status": "Unverified"}

crop_classifier = CropClassifier()
