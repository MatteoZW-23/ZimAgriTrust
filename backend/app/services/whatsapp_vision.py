"""
WhatsApp Vision Adapter - Handles vision features for WhatsApp bot
"""

import logging
from typing import Dict, Any, Optional
from app.services.ml_service import classify_crop, detect_disease
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
        # Use new ONNX-based classifier
        result = await classify_crop(image_data)
        
        if result.get("success") and result.get("crop_type", "").lower() == claimed_crop.lower():
            # Verified match
            return {
                "verified": True,
                "message": f"✅ *Crop Verified!*\n\n"
                          f"Detected: **{result.get('crop_name', 'Unknown')}**\n"
                          f"Confidence: {int(result.get('confidence', 0)*100)}%\n\n"
                          f"Now, please share your farm location.",
                "confidence": result.get("confidence", 0)
            }
        else:
            return {
                "verified": False,
                "message": f"⚠️ Could not verify crop as {claimed_crop}\n\n"
                          f"Detected: **{result.get('crop_name', 'Unknown')}**\n"
                          f"Please try again with a clearer photo.",
                "requires_retry": True
            }
    
    async def analyze_crop_photo(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze crop photo for advisory purposes
        """
        # Use new ONNX-based classifier
        result = await classify_crop(image_data)
        
        if not result.get("success"):
            return {
                "message": f"⚠️ {result.get('message', 'Could not analyze image')}\n\n"
                          f"Please try again with a clearer photo."
            }
        
        crop_name = result.get("crop_name", "Unknown")
        confidence = result.get("confidence", 0)
        
        message = (f"🔬 *ZimAgritrust AI Analysis*\n\n"
                   f"🌿 **Crop:** {crop_name}\n"
                   f"📊 **Confidence:** {int(confidence*100)}%\n\n")
        
        message += f"Type 'sell' to list this {crop_name} on the marketplace."
        
        return {"message": message}


whatsapp_vision = WhatsAppVisionAdapter()
