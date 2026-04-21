import logging
import requests
import os

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def _send_sms(phone, message):
        """Internal method to send physical SMS via external gateway"""
        gateway_url = os.getenv("SMS_GATEWAY_URL", "https://api.sms-gateway.example.com/send")
        api_key = os.getenv("SMS_API_KEY")
        
        if not api_key:
            logger.warning(f"SMS simulation for {phone}: {message}")
            return False
            
        try:
            # Production SMS Gateway Integration
            response = requests.post(
                gateway_url,
                json={"to": phone, "message": message},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"SMS successfully sent to {phone}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send SMS to {phone}: {str(e)}")
            return False

    @staticmethod
    def notify_agent_assignment(agent_name, phone, task_type, location):
        """SMS notification for field agents"""
        message = (
            f"AgriTrust Assignment: Hello {agent_name}, you have a new {task_type} task "
            f"in {location}. Please check your dashboard for details."
        )
        return NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_farmer_on_verification(phone, crop, approved):
        """Notification for farmer list verification"""
        status = "APPROVED" if approved else "REJECTED"
        message = f"AgriTrust: Your {crop} listing was {status} by the quality team."
        return NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_transaction_update(phone, tx_id, status):
        """Notification for transaction/escrow state changes"""
        message = f"AgriTrust Transaction #{tx_id}: Status updated to {status}."
        return NotificationService._send_sms(phone, message)

    # --- AGENT ONBOARDING TEMPLATES ---

    @staticmethod
    def notify_onboarding_documentation(phone, name, portal_url):
        message = f"Welcome {name}! You've been screened for the AgriTrust Agent role. Sign your digital contract here: {portal_url}. Success, HQ."
        return NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_training_milestone(phone, progress):
        message = f"AgriTrust: Great work! You are now {progress}% through your training. Complete the next module to unlock shadowing: http://agritrust.app/academy"
        return NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_certification_ready(phone, name):
        message = f"Congratulations {name}! You are now a Certified AgriTrust Agent. Your credentials have been activated. Welcome to the field!"
        return NotificationService._send_sms(phone, message)

    @staticmethod
    async def send_verification_code(phone: str, code: str):
        """Sends a 2FA verification code via both SMS and WhatsApp for maximum reliability."""
        message = f"AgriTrust: Your verification code is {code}. This code expires in 10 minutes."
        
        # 1. Send SMS (Synchronous)
        sms_sent = NotificationService._send_sms(phone, message)
        
        # 2. Send WhatsApp (Asynchronous)
        try:
            from app.services.whatsapp_service import whatsapp_service
            import asyncio
            # We don't want to block the thread if this is called from a sync context,
            # but if it's called from an async endpoint (like auth.py), we should await it.
            # For now, we'll assume it's called from an async context as per user request for 2FA flow.
            await whatsapp_service.send_whatsapp_message(phone, f"🔐 *AgriTrust Security Code*\n\nYour 2-step verification code is: *{code}*\n\nThis code expires in 10 minutes. If you did not request this, please contact support.")
            wa_sent = True
        except Exception as e:
            logger.error(f"Failed to send 2FA via WhatsApp: {e}")
            wa_sent = False
            
        return sms_sent or wa_sent
