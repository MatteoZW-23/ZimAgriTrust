"""
Webhook for receiving images from all channels
Single endpoint for all vision processing
"""

from fastapi import APIRouter, Request, BackgroundTasks
from datetime import datetime
from app.ml.vision.core.vision_engine import vision_engine
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/webhooks/vision", tags=["Webhooks"])


@router.post("/process")
async def process_vision_request(request: Request, background_tasks: BackgroundTasks):
    """
    Universal vision processing endpoint
    Accepts images from WhatsApp, Mobile App, Web, USSD (via proxy)
    """
    data = await request.json()
    
    image_data = data.get("image_data")  # base64 encoded
    channel = data.get("channel")  # whatsapp, mobile, web, ussd
    context = data.get("context", {})
    
    # Process in background to not block
    background_tasks.add_task(
        process_vision_background,
        image_data=image_data,
        channel=channel,
        context=context
    )
    
    return {"status": "processing", "message": "Image queued for analysis"}


async def process_vision_background(image_data: str, channel: str, context: dict):
    """Background processing of vision request"""
    import base64
    
    # Decode base64 image
    try:
        image_bytes = base64.b64decode(image_data)
        
        # Run analysis
        result = await vision_engine.full_analysis(image_bytes, context)
        
        # Store result in database (Simplified for now)
        # In a real app, you'd create a VisionLog model
        logger = logging.getLogger(__name__)
        logger.info(f"Vision analysis complete for channel {channel}. Result: {result.get('success')}")
        
        # Send notification based on channel
        if channel == "whatsapp":
            await NotificationService.send_whatsapp_vision_result(
                context.get("user_phone"),
                result
            )
        # elif channel == "mobile":
        #    await notification_service.send_push_notification(...)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Vision background processing error: {e}")
