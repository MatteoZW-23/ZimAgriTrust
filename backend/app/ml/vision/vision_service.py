"""
Vision Service - Main entry point for all AI vision features
Handles crop classification, disease detection, and quality grading
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

from app.ml.vision.crop_classifier import crop_classifier, grade_estimator
from app.ml.vision.disease_detector import disease_detector

logger = logging.getLogger(__name__)


class VisionService:
    """
    Main vision service for crop analysis
    Integrates classification, disease detection, and grading
    """
    
    def __init__(self):
        self.classifier = crop_classifier
        self.grader = grade_estimator
        self.disease = disease_detector
        
        # Confidence thresholds
        self.CONFIDENCE_HIGH = 0.85
        self.CONFIDENCE_MEDIUM = 0.70
        self.CONFIDENCE_LOW = 0.55
    
    async def analyze_crop(self, image_data: bytes, expected_crop: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete crop analysis
        If expected_crop is provided, verifies match
        """
        # Step 1: Classify the crop
        classification = await self.classifier.classify(image_data)
        
        if not classification.get("success"):
            return {
                "success": False,
                "error": classification.get("error", "Unable to analyze image"),
                "verified": False,
                "message": "Could not identify the crop. Please send a clearer photo."
            }
        
        detected_crop = classification.get("crop_type")
        confidence = classification.get("confidence", 0)
        
        # Step 2: Verify against expected crop if provided
        verified = False
        match_message = None
        
        if expected_crop:
            # Normalize crop names for comparison
            expected_normalized = expected_crop.lower().strip()
            detected_normalized = detected_crop.lower().strip()
            
            if expected_normalized == detected_normalized:
                verified = True
                match_message = f"✅ Verified: This is {classification.get('crop_name', detected_crop.title())}"
            else:
                verified = False
                match_message = (
                    f"⚠️ MISMATCH: You are trying to list **{expected_crop.title()}** "
                    f"but the image shows **{classification.get('crop_name', detected_crop.title())}**.\n\n"
                    f"Please send the correct photo of your {expected_crop.title()} to proceed."
                )
        
        # Step 3: Estimate grade
        # Note: In production, you'd need to load the image properly
        # For now, use classification confidence as proxy
        grade_result = {
            "grade": classification.get("grade", "Standard"),
            "quality_score": confidence,
            "description": self._get_grade_description(classification.get("grade", "Standard"))
        }
        
        # Step 4: Build response
        result = {
            "success": True,
            "verified": verified if expected_crop else None,
            "match_message": match_message,
            "crop": {
                "type": detected_crop,
                "name": classification.get("crop_name", detected_crop.title()),
                "confidence": confidence,
                "confidence_level": self._get_confidence_level(confidence)
            },
            "grade": grade_result,
            "health": {
                "status": classification.get("health_status", "Unknown"),
                "issues": classification.get("health_issues", [])
            },
            "recommendations": classification.get("recommendations", []),
            "features": classification.get("detected_features", {})
        }
        
        return result
    
    async def verify_crop_match(self, image_data: bytes, claimed_crop: str) -> Dict[str, Any]:
        """
        Specifically verify if the image matches the claimed crop
        This is the main function for listing verification
        """
        analysis = await self.analyze_crop(image_data, expected_crop=claimed_crop)
        
        return {
            "is_match": analysis.get("verified", False),
            "detected_crop": analysis.get("crop", {}).get("name", "Unknown"),
            "detected_crop_type": analysis.get("crop", {}).get("type", "unknown"),
            "confidence": analysis.get("crop", {}).get("confidence", 0),
            "message": analysis.get("match_message", "Unable to verify"),
            "grade": analysis.get("grade", {}).get("grade", "Standard"),
            "quality_score": analysis.get("grade", {}).get("quality_score", 0)
        }
    
    async def analyze_for_agent(self, image_data: bytes) -> Dict[str, Any]:
        """
        Enhanced analysis for agent verification
        Provides more detailed information for agent review
        """
        analysis = await self.analyze_crop(image_data)
        
        if not analysis.get("success"):
            return analysis
        
        return {
            "success": True,
            "crop_type": analysis["crop"]["type"],
            "crop_name": analysis["crop"]["name"],
            "confidence": analysis["crop"]["confidence"],
            "estimated_grade": analysis["grade"]["grade"],
            "quality_score": analysis["grade"]["quality_score"],
            "health_status": analysis["health"]["status"],
            "issues_detected": analysis["health"]["issues"],
            "requires_agent_review": analysis["crop"]["confidence"] < self.CONFIDENCE_MEDIUM,
            "recommendations": analysis["recommendations"]
        }
    
    async def detect_disease(self, image_data: bytes) -> dict:
        """
        Detect crop diseases using the trained YOLOv8-cls disease model.
        Falls back to colour heuristics if model is not yet trained.
        """
        result = self.disease.detect(image_data)
        return result

    async def full_analysis(self, image_data: bytes, expected_crop: str = None) -> dict:
        """
        Combined crop classification + disease detection in one call.
        """
        crop_result    = await self.analyze_crop(image_data, expected_crop)
        disease_result = self.disease.detect(image_data)

        return {
            **crop_result,
            "disease": {
                "detected":         disease_result.get("disease_detected", False),
                "name":             disease_result.get("disease_name"),
                "severity":         disease_result.get("severity"),
                "severity_color":   disease_result.get("severity_color"),
                "confidence":       disease_result.get("confidence"),
                "treatment":        disease_result.get("treatment"),
                "prevention":       disease_result.get("prevention"),
                "top_predictions":  disease_result.get("top_predictions", []),
                "requires_review":  disease_result.get("requires_agent_review", False),
                "model":            disease_result.get("model"),
            },
        }
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to human-readable level"""
        if confidence >= self.CONFIDENCE_HIGH:
            return "High"
        elif confidence >= self.CONFIDENCE_MEDIUM:
            return "Medium"
        else:
            return "Low"
    
    def _get_grade_description(self, grade: str) -> str:
        """Get description for each grade"""
        descriptions = {
            "Grade A": "Premium quality - excellent appearance, no defects",
            "Grade B": "Good quality - minor imperfections",
            "Grade C": "Standard quality - some defects visible",
            "Standard": "Basic quality - review recommended"
        }
        return descriptions.get(grade, "Quality assessment completed")


# Singleton instance
vision_service = VisionService()
