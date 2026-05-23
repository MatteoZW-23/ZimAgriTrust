"""USSD Notification Service."""
from __future__ import annotations
import logging

logger = logging.getLogger("ussd.notification")

class USSDNotificationService:
    @staticmethod
    async def send_sms(phone: str, message: str) -> bool:
        logger.info(f"SMS to {phone}: {message[:50]}...")
        return True
    
    @staticmethod
    async def send_whatsapp(phone: str, message: str) -> bool:
        logger.info(f"WhatsApp to {phone}: {message[:50]}...")
        return True
    
    @staticmethod
    async def notify_listing_created(user_id: str, product: str) -> None:
        pass
    
    @staticmethod
    async def notify_offer_received(user_id: str) -> None:
        pass

ussd_notification = USSDNotificationService()
