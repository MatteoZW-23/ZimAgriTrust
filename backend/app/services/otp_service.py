import random
import logging
from datetime import datetime
from typing import Optional, Dict

from app.services.cache_service import cache_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class OTPService:
    """
    OTP verification via WhatsApp with SMS fallback.
    Uses cache/Redis for OTP storage with 5-minute expiry.
    """
    
    OTP_LENGTH = 6
    OTP_EXPIRY_SECONDS = 300  # 5 minutes
    MAX_ATTEMPTS = 3
    RATE_LIMIT_MAX = 3  # max OTP requests per hour per number
    RATE_LIMIT_WINDOW = 3600  # 1 hour
    
    def __init__(self):
        self.otp_expiry = self.OTP_EXPIRY_SECONDS
        self.max_attempts = self.MAX_ATTEMPTS
    
    def _otp_key(self, phone_number: str) -> str:
        return f"otp:{phone_number}"
    
    def _attempts_key(self, phone_number: str) -> str:
        return f"otp_attempts:{phone_number}"
    
    def _rate_limit_key(self, phone_number: str) -> str:
        return f"otp_rate:{phone_number}"
    
    def _generate_code(self) -> str:
        """Generate 6-digit numeric OTP."""
        return str(random.randint(100000, 999999))
    
    async def _check_rate_limit(self, phone_number: str) -> bool:
        """Check if user has exceeded OTP request rate limit."""
        count = 0
        try:
            raw = await cache_service.get(self._rate_limit_key(phone_number))
            count = int(raw) if raw else 0
        except Exception:
            pass
        return count < self.RATE_LIMIT_MAX
    
    async def _increment_rate_limit(self, phone_number: str):
        """Increment OTP request rate limit counter."""
        key = self._rate_limit_key(phone_number)
        try:
            raw = await cache_service.get(key)
            count = int(raw) if raw else 0
            await cache_service.set(key, str(count + 1), expire=self.RATE_LIMIT_WINDOW)
        except Exception as e:
            logger.error(f"Rate limit increment error: {e}")
    
    async def generate_and_store(self, phone_number: str) -> str:
        """Generate OTP and store in cache."""
        otp = self._generate_code()
        
        # Store OTP
        await cache_service.set(
            self._otp_key(phone_number),
            otp,
            expire=self.otp_expiry
        )
        
        # Reset attempts
        await cache_service.set(
            self._attempts_key(phone_number),
            "0",
            expire=self.otp_expiry
        )
        
        logger.info(f"OTP generated for {phone_number}")
        return otp
    
    async def send_otp(self, phone_number: str, user_name: Optional[str] = None) -> Dict:
        """
        Send OTP via WhatsApp (primary) with SMS fallback.
        Returns: {success: bool, channel: str, message: str, otp: str}
        """
        # Rate limit check
        if not await self._check_rate_limit(phone_number):
            return {
                "success": False,
                "channel": None,
                "message": "Too many requests. Please wait 1 hour before requesting a new code.",
                "otp": None
            }
        
        # Generate OTP
        otp = await self.generate_and_store(phone_number)
        
        # Build WhatsApp message
        wa_message = (
            f"🔐 *ZimAgritrust Verification*\n\n"
            f"Welcome to ZimAgritrust! Please verify your phone number.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Your OTP code is: *{otp}*\n\n"
            f"Valid for: *5 minutes*\n"
            f"Attempts remaining: 3\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Never share this code with anyone*\n\n"
            f"Enter this code in the app or reply here with:\n"
            f"`verify {otp}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"❓ Didn't request this? Ignore this message."
        )
        
        # Try WhatsApp first
        try:
            from app.services.whatsapp_service import WhatsAppService
            await WhatsAppService.send_whatsapp_message(phone_number, wa_message)
            await self._increment_rate_limit(phone_number)
            logger.info(f"OTP sent via WhatsApp to {phone_number}")
            return {
                "success": True,
                "channel": "whatsapp",
                "message": "OTP sent via WhatsApp. Check your WhatsApp messages.",
                "otp": otp
            }
        except Exception as e:
            logger.error(f"WhatsApp OTP send failed: {e}")
        
        # Fallback to SMS
        try:
            sms_message = f"ZimAgritrust OTP: {otp}. Valid for 5 minutes. Never share this code."
            notification_service._send_sms(phone_number, sms_message)
            await self._increment_rate_limit(phone_number)
            logger.info(f"OTP sent via SMS to {phone_number}")
            return {
                "success": True,
                "channel": "sms",
                "message": "OTP sent via SMS. Check your text messages.",
                "otp": otp
            }
        except Exception as e:
            logger.error(f"SMS OTP send failed: {e}")
        
        return {
            "success": False,
            "channel": None,
            "message": "Failed to send OTP. Please try again later.",
            "otp": None
        }
    
    async def verify_otp(self, phone_number: str, user_otp: str) -> Dict:
        """
        Verify OTP entered by user.
        Returns: {success: bool, message: str, trust_score_change: int, remaining_attempts: int}
        """
        # Get stored OTP
        stored_otp = await cache_service.get(self._otp_key(phone_number))
        
        if not stored_otp:
            return {
                "success": False,
                "message": "OTP expired or not found. Please request a new code with `resend`.",
                "trust_score_change": 0,
                "remaining_attempts": 0
            }
        
        # Check attempts
        attempts_raw = await cache_service.get(self._attempts_key(phone_number))
        attempts = int(attempts_raw) if attempts_raw else 0
        
        if attempts >= self.max_attempts:
            await cache_service.delete(self._otp_key(phone_number))
            await cache_service.delete(self._attempts_key(phone_number))
            return {
                "success": False,
                "message": "Too many failed attempts. Please request a new OTP with `resend`.",
                "trust_score_change": 0,
                "remaining_attempts": 0
            }
        
        # Normalize user input
        user_otp = user_otp.strip()
        stored_otp = stored_otp.strip()
        
        # Verify OTP
        if user_otp == stored_otp:
            # OTP correct - clear cache
            await cache_service.delete(self._otp_key(phone_number))
            await cache_service.delete(self._attempts_key(phone_number))
            
            return {
                "success": True,
                "message": "Phone verified successfully! Trust Score +5",
                "trust_score_change": 5,
                "remaining_attempts": 0
            }
        
        # OTP incorrect
        attempts += 1
        remaining = self.max_attempts - attempts
        await cache_service.set(
            self._attempts_key(phone_number),
            str(attempts),
            expire=self.otp_expiry
        )
        
        if remaining <= 0:
            await cache_service.delete(self._otp_key(phone_number))
            await cache_service.delete(self._attempts_key(phone_number))
            return {
                "success": False,
                "message": "Too many failed attempts. Please request a new OTP with `resend`.",
                "trust_score_change": 0,
                "remaining_attempts": 0
            }
        
        return {
            "success": False,
            "message": f"Invalid OTP. {remaining} attempt(s) remaining.",
            "trust_score_change": 0,
            "remaining_attempts": remaining
        }
    
    async def resend_otp(self, phone_number: str, user_name: Optional[str] = None) -> Dict:
        """Clear old OTP and send a new one."""
        await cache_service.delete(self._otp_key(phone_number))
        await cache_service.delete(self._attempts_key(phone_number))
        return await self.send_otp(phone_number, user_name)
    
    async def is_otp_active(self, phone_number: str) -> bool:
        """Check if there's an active OTP for this phone number."""
        stored = await cache_service.get(self._otp_key(phone_number))
        return stored is not None


otp_service = OTPService()
