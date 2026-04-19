from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import requests
import os
import logging

from app.db.session import SessionLocal
from app.models.user import User
from app.services.whatsapp_service import whatsapp_service
from app.services.auth_service import build_phone_lookup_candidates

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Bridge URL for sending messages back
WHATSAPP_BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://whatsapp-bridge:3006/send")

@router.post("/webhook")
async def whatsapp_webhook(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Handles incoming messages from the WhatsApp bridge.
    """
    sender_phone = data.get("from") # Format: 263777777777@c.us
    
    # Ignore WhatsApp Status broadcasts, Newsletters, and Groups
    if sender_phone == "status@broadcast" or (sender_phone and (sender_phone.endswith("@newsletter") or sender_phone.endswith("@g.us"))):
        return {"status": "ignored", "reason": "broadcast_newsletter_or_group"}

    body = data.get("body", "").strip()

    has_media = data.get("hasMedia", False)
    media = data.get("media")
    
    # Extract clean phone number
    clean_phone = sender_phone.split("@")[0]
    
    # Identify User
    candidates = build_phone_lookup_candidates(clean_phone)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    
    if not user:
        return {"reply": "Welcome to AgriTrust! I see you're not registered yet. Please register via our USSD (*232#) or visit our website to get started."}

    # Process via Service
    reply_text = await whatsapp_service.process_message(db, user, body, has_media, media)
    
    return {"reply": reply_text}

@router.post("/test-alert")
async def test_alert(phone: str, message: str):
    """
    Manually triggers a proactive alert for testing purposes.
    """
    send_notification(phone, message)
    return {"status": "Alert sent"}

@router.get("/status")
async def get_whatsapp_status():
    """
    Checks the connectivity status of the WhatsApp bridge.
    """
    return await whatsapp_service.get_status()

def send_notification(to_phone: str, message: str):
    """
    Utility function to send a message to a user via WhatsApp Bridge.
    to_phone: clean phone number (e.g. 263777777777)
    """
    try:
        formatted_to = f"{to_phone}@c.us"
        payload = {"to": formatted_to, "message": message}
        requests.post(WHATSAPP_BRIDGE_URL, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"Failed to send WhatsApp notification: {str(e)}")
