"""
Central vision configuration for all channels
"""

from pydantic_settings import BaseSettings
from typing import Dict, Any


class VisionSettings(BaseSettings):
    """Vision system settings"""
    
    # Core settings
    AI_VISION_ENABLED: bool = True
    AI_CONFIDENCE_THRESHOLD: float = 0.65
    
    # Model paths
    CROP_CLASSIFIER_MODEL: str = "data/ml-weights/crop_classifier.pt"
    DISEASE_DETECTOR_MODEL: str = "data/ml-weights/disease_detector.pt"
    GRADE_ESTIMATOR_MODEL: str = "data/ml-weights/grade_estimator.pt"
    
    # Channel-specific settings
    WHATSAPP_MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    MOBILE_MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    WEB_MAX_IMAGE_SIZE: int = 20 * 1024 * 1024  # 20MB
    
    # Verification thresholds
    AUTO_APPROVE_THRESHOLD: float = 0.85
    AGENT_REVIEW_THRESHOLD: float = 0.55
    
    # Supported crops (dynamic)
    SUPPORTED_CROPS: Dict[str, Dict] = {
        "maize": {"en": "Maize", "shona": "Chibage", "ndebele": "Umumbu"},
        "mango": {"en": "Mango", "shona": "Mango", "ndebele": "Mango"},
        "tomato": {"en": "Tomato", "shona": "Madomasi", "ndebele": "Utamatisi"},
        "soya_beans": {"en": "Soya Beans", "shona": "Soya", "ndebele": "Soya"},
        "groundnuts": {"en": "Groundnuts", "shona": "Nzungu", "ndebele": "Amazambane"},
        "tobacco": {"en": "Tobacco", "shona": "Fodya", "ndebele": "Ugwayi"},
        "cotton": {"en": "Cotton", "shona": "Donje", "ndebele": "Ugandaganda"},
        "cabbage": {"en": "Cabbage", "shona": "Kebheji", "ndebele": "Iklabishi"},
    }
    
    class Config:
        env_prefix = "VISION_"
        env_file = ".env"


vision_settings = VisionSettings()
