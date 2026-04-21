"""
Mobile App Vision API - REST endpoints for mobile app
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ml.vision.core.vision_engine import vision_engine
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/vision", tags=["AI Vision"])


@router.post("/analyze-crop")
async def analyze_crop(
    image: UploadFile = File(...),
    claimed_crop: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze crop image from mobile app
    If claimed_crop provided, verifies match
    """
    # Read image data
    image_data = await image.read()
    
    if claimed_crop:
        # Verification mode
        result = await vision_engine.verify_crop_match(image_data, claimed_crop)
        return {
            "success": result["verified"],
            "detected_crop": result["detected_crop_name"],
            "confidence": result["confidence"],
            "message": result["message"]
        }
    else:
        # Full analysis mode
        result = await vision_engine.full_analysis(image_data)
        return result


@router.post("/verify-listing")
async def verify_listing_image(
    image: UploadFile = File(...),
    listing_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify image for an existing listing (agent use)
    """
    image_data = await image.read()
    
    # Get listing from database
    from app.models.listing import Listing
    
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return {"success": False, "error": "Listing not found"}
    
    # Verify image matches listing product
    result = await vision_engine.verify_crop_match(image_data, listing.product_type)
    
    if result["verified"]:
        # Update listing verification status
        listing.verification_status = "verified"
        listing.verified_by_ai = True  # Note: ensure this field exists or use ai_verified
        listing.ai_verified = True
        listing.ai_confidence = result["confidence"]
        db.commit()
    
    return result


@router.post("/detect-disease")
async def detect_disease(
    image: UploadFile = File(...),
    crop_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    Detect diseases in crop image
    """
    image_data = await image.read()
    
    # First verify crop
    verification = await vision_engine.verify_crop_match(image_data, crop_type)
    if not verification["verified"]:
        return {
            "success": False,
            "message": f"Image does not appear to be {crop_type}. Please upload correct image."
        }
    
    # Detect diseases
    diseases = await vision_engine.detect_diseases(image_data, crop_type)
    
    return {
        "success": True,
        "crop_type": crop_type,
        "diseases": diseases
    }
