"""
Unified WhatsApp API Endpoints
Includes: Core messaging, webhooks, enhanced features, bulk operations
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
import requests
import os
import logging

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.services.whatsapp_service import whatsapp_service
from app.services.auth_service import build_phone_lookup_candidates
from app.api.deps import get_current_user, require_roles

router = APIRouter()
logger = logging.getLogger(__name__)

WHATSAPP_BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://whatsapp-bridge:3006/send")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════

class BroadcastRequest(BaseModel):
    message: str
    role_filter: Optional[UserRole] = None
    province_filter: Optional[str] = None
    verified_only: bool = False

class PriceAlertRequest(BaseModel):
    commodity: str
    old_price: float
    new_price: float
    province: Optional[str] = None

class WeatherAlertRequest(BaseModel):
    province: str
    alert_type: str
    message_body: str

class HarvestReminderRequest(BaseModel):
    crop_type: str
    province: Optional[str] = None

class DeliveryReminderRequest(BaseModel):
    order_id: str
    recipient_phone: str
    days_remaining: int

class PaymentReminderRequest(BaseModel):
    user_phone: str
    amount: float
    due_date: datetime
    loan_id: str

class MobilePaymentRequest(BaseModel):
    amount: float
    reference: str
    provider: str = "ecocash"

class LocationShareRequest(BaseModel):
    latitude: float
    longitude: float

class MarketDemandRequest(BaseModel):
    crop_type: str
    province: str
    days_ahead: int = 7


# ═══════════════════════════════════════════════════════════════════════════
# CORE WEBHOOK ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/webhook")
async def whatsapp_webhook(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Handles incoming messages from the WhatsApp bridge"""
    sender_phone = data.get("from")
    
    # Ignore broadcasts, newsletters, and groups
    if sender_phone == "status@broadcast" or (sender_phone and (sender_phone.endswith("@newsletter") or sender_phone.endswith("@g.us"))):
        return {"status": "ignored", "reason": "broadcast_newsletter_or_group"}

    body = data.get("body", "").strip()
    has_media = data.get("hasMedia", False)
    media = data.get("media")
    
    clean_phone = sender_phone.split("@")[0]
    candidates = build_phone_lookup_candidates(clean_phone)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    
    if not user:
        return {"reply": "Welcome to ZimAgritrust! I see you're not registered yet. Please register via our USSD (*232#) or visit our website to get started."}

    reply_text = await whatsapp_service.process_message(db, user, body, has_media, media)
    return {"reply": reply_text}


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Standard WhatsApp Webhook verification (GET challenge)"""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode == "subscribe" and token == "ZimAgritrust_SOVEREIGN_TOKEN":
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification Failed")


@router.get("/status")
async def get_whatsapp_status():
    """Checks the connectivity status of the WhatsApp bridge"""
    return await whatsapp_service.get_status()


@router.post("/test-alert")
async def test_alert(phone: str, message: str):
    """Manually triggers a proactive alert for testing purposes"""
    send_notification(phone, message)
    return {"status": "Alert sent"}


def send_notification(to_phone: str, message: str):
    """Utility function to send a message to a user via WhatsApp Bridge"""
    try:
        formatted_to = f"{to_phone}@c.us"
        payload = {"to": formatted_to, "message": message}
        requests.post(WHATSAPP_BRIDGE_URL, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Failed to send WhatsApp notification: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# BULK MESSAGING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/broadcast")
async def broadcast_message(request: BroadcastRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Broadcast message to multiple users (Admin only)"""
    result = await whatsapp_service.broadcast_message(
        db, request.message, request.role_filter, request.province_filter, request.verified_only
    )
    return result


@router.post("/alerts/price")
async def send_price_alert(request: PriceAlertRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Send price change alerts to farmers (Admin only)"""
    result = await whatsapp_service.send_price_alert(db, request.commodity, request.old_price, request.new_price, request.province)
    return result


@router.post("/alerts/weather")
async def send_weather_alert(request: WeatherAlertRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Send weather alerts to farmers in specific province (Admin only)"""
    result = await whatsapp_service.send_weather_alert(db, request.province, request.alert_type, request.message_body)
    return result


@router.post("/alerts/harvest")
async def send_harvest_reminder(request: HarvestReminderRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Send harvest season reminders to farmers (Admin only)"""
    result = await whatsapp_service.send_harvest_reminder(db, request.crop_type, request.province)
    return result


# ═══════════════════════════════════════════════════════════════════════════
# SMART NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/reminders/delivery")
async def send_delivery_reminder(request: DeliveryReminderRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Send delivery reminder for an order"""
    await whatsapp_service.send_delivery_reminder(db, request.order_id, request.recipient_phone, request.days_remaining)
    return {"success": True, "message": "Reminder sent"}


@router.post("/reminders/payment")
async def send_payment_reminder(request: PaymentReminderRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Send loan repayment reminder (Admin only)"""
    await whatsapp_service.send_payment_reminder(db, request.user_phone, request.amount, request.due_date, request.loan_id)
    return {"success": True, "message": "Payment reminder sent"}


@router.post("/reminders/verification/{user_id}")
async def send_verification_reminder(user_id: str, verification_type: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Send verification reminder to user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await whatsapp_service.send_verification_reminder(db, user.phone_number, user.full_name, verification_type)
    return {"success": True, "message": "Verification reminder sent"}


# ═══════════════════════════════════════════════════════════════════════════
# MOBILE MONEY INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/payment/initiate")
async def initiate_mobile_payment(request: MobilePaymentRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Initiate mobile money payment (EcoCash, OneMoney)"""
    result = await whatsapp_service.initiate_mobile_payment(db, current_user, request.amount, request.reference, request.provider)
    return result


@router.post("/payment/receipt")
async def send_payment_receipt(transaction_id: str, amount: float, recipient: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Send payment receipt to user"""
    await whatsapp_service.send_payment_receipt(db, current_user.phone_number, transaction_id, amount, recipient, datetime.utcnow())
    return {"success": True, "message": "Receipt sent"}


# ═══════════════════════════════════════════════════════════════════════════
# LOCATION & INTERACTIVE FEATURES
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/location/share")
async def share_location(request: LocationShareRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Process shared GPS location"""
    response = await whatsapp_service.process_location_share(db, current_user, request.latitude, request.longitude)
    return {"success": True, "message": response}


@router.post("/interactive/listing/{listing_id}")
async def send_interactive_listing(listing_id: str, recipient_phone: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Send listing with interactive quick action buttons"""
    from app.models.listing import Listing
    
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    await whatsapp_service.send_interactive_listing(db, recipient_phone, listing)
    return {"success": True, "message": "Interactive listing sent"}


# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS & MARKET INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/analytics/engagement/{user_id}")
async def get_user_engagement(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Get user engagement statistics (Admin only)"""
    stats = await whatsapp_service.get_user_engagement_stats(db, user_id)
    return stats


@router.post("/analytics/track")
async def track_engagement(message_type: str, action_taken: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Track message engagement"""
    await whatsapp_service.track_message_engagement(db, current_user.id, message_type, action_taken)
    return {"success": True}


@router.post("/market/demand")
async def predict_market_demand(request: MarketDemandRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Predict market demand for specific crop"""
    prediction = await whatsapp_service.predict_market_demand(db, request.crop_type, request.province, request.days_ahead)
    return prediction


# ═══════════════════════════════════════════════════════════════════════════
# GROUP MANAGEMENT & LANGUAGE
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/groups/create")
async def create_farmer_group(group_name: str, province: str, crop_type: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Create WhatsApp group for farmers (Admin only)"""
    result = await whatsapp_service.create_farmer_group(db, group_name, province, crop_type)
    return result


@router.post("/groups/{group_id}/message")
async def send_group_message(group_id: str, message: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Send message to WhatsApp group (Admin only)"""
    await whatsapp_service.send_group_message(db, group_id, message)
    return {"success": True, "message": "Group message sent"}


@router.post("/translate")
async def translate_message(message: str, target_language: str = "sn", current_user: User = Depends(get_current_user)):
    """Translate message to local language (en, sn, nd)"""
    translated = await whatsapp_service.translate_message(message, target_language)
    return {"original": message, "translated": translated, "language": target_language}


@router.post("/detect-language")
async def detect_language(message: str, current_user: User = Depends(get_current_user)):
    """Detect message language"""
    language = await whatsapp_service.detect_language(message)
    return {"message": message, "detected_language": language}

