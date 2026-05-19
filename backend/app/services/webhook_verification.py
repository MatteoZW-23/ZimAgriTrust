"""
Webhook Signature Verification Service

Validates webhook signatures from payment providers to prevent:
- Replay attacks
- Forged requests
- Man-in-the-middle attacks
"""
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import Request, HTTPException, status

from app.core.config import settings
from app.services.provider_registry import ProviderType, provider_registry

logger = logging.getLogger(__name__)


class WebhookVerificationError(Exception):
    """Raised when webhook verification fails"""
    pass


class WebhookVerifier:
    """
    Webhook signature verification service.
    Supports multiple provider signature schemes.
    """

    @staticmethod
    def verify_ecocash(
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify EcoCash webhook signature using HMAC-SHA256.
        """
        if not secret or not signature:
            return False

        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    @staticmethod
    def verify_onemoney(
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify OneMoney webhook signature using HMAC-SHA256.
        NOTE: Verify actual OneMoney signature scheme in production.
        """
        if not secret:
            logger.error("ONEMONEY_WEBHOOK_SECRET not configured")
            raise ValueError("ONEMONEY_WEBHOOK_SECRET not configured - webhook verification disabled")
        
        if not signature:
            return False
        
        try:
            # OneMoney uses HMAC-SHA256 similar to EcoCash
            # Verify this matches actual OneMoney API documentation
            expected = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)
        except Exception as e:
            logger.error(f"OneMoney signature verification error: {e}")
            return False

    @staticmethod
    def verify_zipit(
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify ZIPIT webhook signature.
        ZIPIT may use SHA256 hash.
        """
        if not secret or not signature:
            return False

        expected_hash = hashlib.sha256(
            payload + secret.encode('utf-8')
        ).hexdigest()

        return hmac.compare_digest(signature, expected_hash)

    @staticmethod
    def verify_stripe(
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify Stripe webhook signature.
        Stripe uses timestamp + signature scheme.
        """
        # Stripe signature format: t={timestamp},v1={signature}
        # This is a simplified version
        if not secret or not signature:
            return False

        try:
            timestamp = int(signature.split(',')[0].split('=')[1])
            sig_value = signature.split(',')[1].split('=')[1]

            # Check timestamp is within tolerance (5 minutes)
            current_time = int(datetime.utcnow().timestamp())
            if abs(current_time - timestamp) > 300:
                return False

            expected_sig = hmac.new(
                secret.encode('utf-8'),
                f"{timestamp}.{payload.decode('utf-8')}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(sig_value, expected_sig)
        except Exception:
            return False

    @staticmethod
    async def verify_webhook(
        provider: ProviderType,
        payload: bytes,
        signature: str,
        headers: Dict[str, str]
    ) -> bool:
        """
        Verify webhook signature based on provider type.
        """
        provider_instance = provider_registry.get_provider(provider)
        
        if not provider_instance:
            logger.error(f"Unknown provider: {provider}")
            return False

        # Get provider secret from config
        secret = WebhookVerifier._get_provider_secret(provider)
        
        if not secret:
            logger.warning(f"No secret configured for provider: {provider}")
            return False

        # Route to appropriate verification method
        verification_methods = {
            ProviderType.ECOCASH: WebhookVerifier.verify_ecocash,
            ProviderType.ONEMONEY: WebhookVerifier.verify_onemoney,
            ProviderType.ZIPIT: WebhookVerifier.verify_zipit,
            ProviderType.VISA: WebhookVerifier.verify_stripe,  # Visa may use Stripe-like scheme
            ProviderType.MASTERCARD: WebhookVerifier.verify_stripe,
        }

        verify_method = verification_methods.get(provider)
        
        if verify_method:
            return verify_method(payload, signature, secret)
        
        # Default to provider's own verification method
        webhook_payload = type('WebhookPayload', (), {
            'provider': provider,
            'raw_payload': payload,
            'signature': signature
        })()
        
        return await provider_instance.verify_webhook(webhook_payload)

    @staticmethod
    def _get_provider_secret(provider: ProviderType) -> Optional[str]:
        """Get webhook secret for provider from config"""
        secrets = {
            ProviderType.ECOCASH: settings.ECOCASH_WEBHOOK_SECRET if hasattr(settings, 'ECOCASH_WEBHOOK_SECRET') else None,
            ProviderType.ONEMONEY: settings.ONEMONEY_WEBHOOK_SECRET if hasattr(settings, 'ONEMONEY_WEBHOOK_SECRET') else None,
            ProviderType.ZIPIT: settings.ZIPIT_WEBHOOK_SECRET if hasattr(settings, 'ZIPIT_WEBHOOK_SECRET') else None,
        }
        return secrets.get(provider)

    @staticmethod
    async def check_replay_attack(
        self,
        request_id: str,
        timestamp: datetime,
        tolerance_seconds: int = 300
    ) -> bool:
        """
        Check if this is a replay attack by checking if we've seen this request_id recently.
        """
        from app.services.cache_service import cache_service
        
        cache_key = f"webhook_replay:{request_id}"
        
        # Check if we've seen this request_id
        seen = await cache_service.get(cache_key)
        
        if seen:
            logger.warning(f"Replay attack detected for request_id: {request_id}")
            return True
        
        # Store request_id with TTL
        await cache_service.set(cache_key, "seen", expire=tolerance_seconds)
        
        return False


async def verify_webhook_request(
    request: Request,
    provider: ProviderType
) -> bytes:
    """
    Verify webhook request and return raw payload.
    Raises HTTPException if verification fails.
    """
    # Get signature from headers
    signature = request.headers.get("X-Signature") or request.headers.get("X-Webhook-Signature")
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature header"
        )

    # Get raw payload
    payload = await request.body()
    
    # Verify signature
    is_valid = await WebhookVerifier.verify_webhook(
        provider,
        payload,
        signature,
        dict(request.headers)
    )
    
    if not is_valid:
        logger.error(f"Invalid webhook signature from {provider}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # Check for replay attack if request_id is present
    try:
        import json
        payload_dict = json.loads(payload.decode('utf-8'))
        request_id = payload_dict.get('request_id') or payload_dict.get('reference')
        
        if request_id:
            timestamp_str = payload_dict.get('timestamp')
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
            
            if WebhookVerifier.check_replay_attack(request_id, timestamp):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Duplicate webhook request"
                )
    except (json.JSONDecodeError, ValueError):
        pass  # Payload may not be JSON or may not have request_id

    return payload
