"""
WhatsApp Vision Adapter - Handles vision features for WhatsApp bot
"""

import logging
from typing import Dict, Any, Optional
from app.ml.vision.core.vision_engine import vision_engine
from app.services.media_service import media_service

logger = logging.getLogger(__name__)


class WhatsAppVisionAdapter:
    """
    Adapter for WhatsApp-specific vision features
    """
    
    async def process_listing_photo(self, image_data: bytes, claimed_crop: str) -> Dict[str, Any]:
        """
        Process listing photo from farmer
        Returns WhatsApp-friendly response
        """
        # Use core engine for verification
        result = await vision_engine.verify_crop_match(image_data, claimed_crop)
        
        if result["verified"]:
            # Get grade for response
            grade_result = await vision_engine.estimate_grade(image_data, 
                {"crop_type": result["detected_crop"], "confidence": result["confidence"]})
            
            return {
                "verified": True,
                "message": f"✅ *Crop Verified!*\n\n"
                          f"Detected: **{result['detected_crop_name']}**\n"
                          f"Grade: **{grade_result['grade']}**\n"
                          f"Confidence: {int(result['confidence']*100)}%\n\n"
                          f"Now, please share your farm location.",
                "grade": grade_result["grade"],
                "confidence": result["confidence"]
            }
        else:
            return {
                "verified": False,
                "message": result["message"],
                "requires_retry": True
            }
    
    async def analyze_crop_photo(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze crop photo for advisory purposes
        """
        analysis = await vision_engine.full_analysis(image_data)
        
        if not analysis["success"]:
            return {
                "message": f"⚠️ {analysis.get('error', 'Could not analyze image')}\n\n"
                          f"Please try again with a clearer photo."
            }
        
        crop = analysis["crop"]
        grade = analysis["grade"]
        
        message = (f"🔬 *AgriTrust AI Analysis*\n\n"
                   f"🌿 **Crop:** {crop['crop_name']}\n"
                   f"📊 **Confidence:** {int(crop['confidence']*100)}%\n"
                   f"⭐ **Grade:** {grade['grade']}\n"
                   f"💬 **Note:** {grade['description']}\n\n")
        
        if analysis["recommendations"]:
            message += f"💡 **Tip:** {analysis['recommendations'][0]}\n\n"
        
        message += f"Type 'sell' to list this {crop['crop_name']} on the marketplace."
        
        return {"message": message}


whatsapp_vision = WhatsAppVisionAdapter()
