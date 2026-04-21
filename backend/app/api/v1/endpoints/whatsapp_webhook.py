from fastapi import APIRouter, Request, HTTPException
from app.services.whatsapp_service import whatsapp_service
import json

router = APIRouter()

@router.post("/webhook")
async def whatsapp_incoming(request: Request):
    """
    Direct interface with Meta/WhatsApp Business API.
    Routes messages to AI handlers for listings, training, and disputes.
    """
    payload = await request.json()
    # Process message via service
    result = whatsapp_service.handle_incoming(payload)
    return {"status": "Handled", "response": result}

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Standard WhatsApp Webhook verification (GET challenge).
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode == "subscribe" and token == "AGRITRUST_SOVEREIGN_TOKEN":
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification Failed")
