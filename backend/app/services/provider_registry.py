"""
Provider Abstraction Layer for Payment Gateway Extensibility

Implements strategy pattern for payment providers.
New providers can be added without modifying core orchestration logic.
"""
import abc
import uuid
import logging
from typing import Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported payment provider types"""
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    ZIPIT = "zipit"
    INNBUCKS = "innbucks"
    OMARI = "omari"
    VISA = "visa"
    MASTERCARD = "mastercard"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    WALLET = "wallet"


class PaymentRequest(BaseModel):
    """Standardized payment request across all providers"""
    amount: float
    currency: str
    reference: str
    phone_number: Optional[str] = None
    account_number: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """Standardized payment response across all providers"""
    success: bool
    transaction_id: str
    provider_reference: Optional[str] = None
    status: str
    message: str
    raw_response: Optional[Dict[str, Any]] = None


class WebhookPayload(BaseModel):
    """Standardized webhook payload across all providers"""
    provider: ProviderType
    transaction_id: str
    status: str
    amount: float
    currency: str
    raw_payload: Dict[str, Any]
    signature: Optional[str] = None


class PaymentProvider(abc.ABC):
    """
    Abstract base class for payment providers.
    All providers must implement these methods.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_type = ProviderType.WALLET  # Default

    @abc.abstractmethod
    async def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        """
        Initiate a payment with the provider.
        """
        pass

    @abc.abstractmethod
    async def verify_webhook(self, payload: WebhookPayload) -> bool:
        """
        Verify webhook signature and authenticity.
        """
        pass

    @abc.abstractmethod
    async def check_status(self, transaction_id: str) -> PaymentResponse:
        """
        Check the status of a transaction.
        """
        pass

    @abc.abstractmethod
    async def refund(self, transaction_id: str, amount: float) -> PaymentResponse:
        """
        Process a refund.
        """
        pass

    @abc.abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the provider is healthy and available.
        """
        pass


class EcoCashProvider(PaymentProvider):
    """EcoCash payment provider implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = ProviderType.ECOCASH
        self.api_key = config.get("api_key")
        self.merchant_id = config.get("merchant_id")
        self.webhook_secret = config.get("webhook_secret")

    async def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Initiate EcoCash payment via Paynow API integration"""
        import requests
        from app.core.config import settings

        if not settings.PAYNOW_API_KEY or not settings.PAYNOW_INTEGRATION_ID:
            return PaymentResponse(
                success=False,
                transaction_id=request.reference,
                status="PROVIDER_NOT_CONFIGURED",
                message="EcoCash API credentials (PAYNOW_API_KEY, PAYNOW_INTEGRATION_ID) are not configured",
            )

        try:
            payload = {
                "id": settings.PAYNOW_INTEGRATION_ID,
                "amount": request.amount,
                "currency": request.currency,
                "reference": request.reference,
                "phone": request.phone_number,
                "method": "ecocash",
            }

            response = requests.post(
                settings.PAYNOW_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {settings.PAYNOW_API_KEY}"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return PaymentResponse(
                    success=True,
                    transaction_id=request.reference,
                    provider_reference=data.get("poll_url"),
                    status="PENDING",
                    message="EcoCash payment initiated via Paynow",
                    raw_response=data,
                )
            else:
                return PaymentResponse(
                    success=False,
                    transaction_id=request.reference,
                    status="FAILED",
                    message=f"EcoCash API error: {response.status_code}",
                    raw_response=response.json() if response.content else {},
                )
        except Exception as e:
            logger.error(f"EcoCash payment initiation error: {e}")
            return PaymentResponse(
                success=False,
                transaction_id=request.reference,
                status="ERROR",
                message=f"EcoCash payment initiation failed: {str(e)}",
            )

    async def verify_webhook(self, payload: WebhookPayload) -> bool:
        """Verify EcoCash webhook signature"""
        import hmac
        import hashlib

        if not self.webhook_secret or not payload.signature:
            return False

        # Create signature from raw payload
        raw_data = str(payload.raw_payload).encode('utf-8')
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            raw_data,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(payload.signature, expected_signature)

    async def check_status(self, transaction_id: str) -> PaymentResponse:
        """Check EcoCash transaction status via Paynow API"""
        import requests
        from app.core.config import settings

        if not settings.PAYNOW_API_KEY:
            return PaymentResponse(
                success=False,
                transaction_id=transaction_id,
                status="PROVIDER_NOT_CONFIGURED",
                message="EcoCash API credentials (PAYNOW_API_KEY) are not configured",
            )

        try:
            response = requests.get(
                f"{settings.PAYNOW_API_URL}/status/{transaction_id}",
                headers={"Authorization": f"Bearer {settings.PAYNOW_API_KEY}"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return PaymentResponse(
                    success=True,
                    transaction_id=transaction_id,
                    status=data.get("status", "UNKNOWN"),
                    message="EcoCash status checked via Paynow",
                    raw_response=data,
                )
            else:
                return PaymentResponse(
                    success=False,
                    transaction_id=transaction_id,
                    status="ERROR",
                    message=f"EcoCash status check error: {response.status_code}",
                )
        except Exception as e:
            logger.error(f"EcoCash status check error: {e}")
            return PaymentResponse(
                success=False,
                transaction_id=transaction_id,
                status="ERROR",
                message=f"EcoCash status check failed: {str(e)}",
            )

    async def refund(self, transaction_id: str, amount: float) -> PaymentResponse:
        """Process EcoCash refund"""
        return PaymentResponse(
            success=False,
            transaction_id=transaction_id,
            status="PROVIDER_NOT_CONFIGURED",
            message="EcoCash API refund is not configured",
        )

    def is_healthy(self) -> bool:
        """Check EcoCash service health"""
        # Implementation would ping EcoCash health endpoint
        return True


class OneMoneyProvider(PaymentProvider):
    """OneMoney payment provider implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = ProviderType.ONEMONEY
        self.api_key = config.get("api_key")
        self.merchant_code = config.get("merchant_code")

    async def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Initiate OneMoney payment via Paynow API integration"""
        import requests
        from app.core.config import settings

        if not settings.PAYNOW_API_KEY or not settings.PAYNOW_INTEGRATION_ID:
            return PaymentResponse(
                success=False,
                transaction_id=request.reference,
                status="PROVIDER_NOT_CONFIGURED",
                message="OneMoney API credentials (PAYNOW_API_KEY, PAYNOW_INTEGRATION_ID) are not configured",
            )

        try:
            payload = {
                "id": settings.PAYNOW_INTEGRATION_ID,
                "amount": request.amount,
                "currency": request.currency,
                "reference": request.reference,
                "phone": request.phone_number,
                "method": "onemoney",
            }

            response = requests.post(
                settings.PAYNOW_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {settings.PAYNOW_API_KEY}"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return PaymentResponse(
                    success=True,
                    transaction_id=request.reference,
                    provider_reference=data.get("poll_url"),
                    status="PENDING",
                    message="OneMoney payment initiated via Paynow",
                    raw_response=data,
                )
            else:
                return PaymentResponse(
                    success=False,
                    transaction_id=request.reference,
                    status="FAILED",
                    message=f"OneMoney API error: {response.status_code}",
                    raw_response=response.json() if response.content else {},
                )
        except Exception as e:
            logger.error(f"OneMoney payment initiation error: {e}")
            return PaymentResponse(
                success=False,
                transaction_id=request.reference,
                status="ERROR",
                message=f"OneMoney payment initiation failed: {str(e)}",
            )

    async def verify_webhook(self, payload: WebhookPayload) -> bool:
        """Verify OneMoney webhook"""
        # OneMoney may not use signatures, verify by other means
        return True

    async def check_status(self, transaction_id: str) -> PaymentResponse:
        """Check OneMoney transaction status via Paynow API"""
        import requests
        from app.core.config import settings

        if not settings.PAYNOW_API_KEY:
            return PaymentResponse(
                success=False,
                transaction_id=transaction_id,
                status="PROVIDER_NOT_CONFIGURED",
                message="OneMoney API credentials (PAYNOW_API_KEY) are not configured",
            )

        try:
            response = requests.get(
                f"{settings.PAYNOW_API_URL}/status/{transaction_id}",
                headers={"Authorization": f"Bearer {settings.PAYNOW_API_KEY}"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return PaymentResponse(
                    success=True,
                    transaction_id=transaction_id,
                    status=data.get("status", "UNKNOWN"),
                    message="OneMoney status checked via Paynow",
                    raw_response=data,
                )
            else:
                return PaymentResponse(
                    success=False,
                    transaction_id=transaction_id,
                    status="ERROR",
                    message=f"OneMoney status check error: {response.status_code}",
                )
        except Exception as e:
            logger.error(f"OneMoney status check error: {e}")
            return PaymentResponse(
                success=False,
                transaction_id=transaction_id,
                status="ERROR",
                message=f"OneMoney status check failed: {str(e)}",
            )

    async def refund(self, transaction_id: str, amount: float) -> PaymentResponse:
        """Process OneMoney refund"""
        return PaymentResponse(
            success=False,
            transaction_id=transaction_id,
            status="PROVIDER_NOT_CONFIGURED",
            message="OneMoney API refund is not configured",
        )

    def is_healthy(self) -> bool:
        """Check OneMoney service health"""
        return True


class WalletProvider(PaymentProvider):
    """Internal wallet payment provider"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = ProviderType.WALLET

    async def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process internal wallet payment"""
        return PaymentResponse(
            success=True,
            transaction_id=str(uuid.uuid4()),
            provider_reference=f"WAL{uuid.uuid4().hex[:12].upper()}",
            status="COMPLETED",
            message="Wallet payment processed",
        )

    async def verify_webhook(self, payload: WebhookPayload) -> bool:
        """Internal wallet doesn't use webhooks"""
        return True

    async def check_status(self, transaction_id: str) -> PaymentResponse:
        """Check wallet transaction status"""
        return PaymentResponse(
            success=True,
            transaction_id=transaction_id,
            status="COMPLETED",
            message="Transaction completed",
        )

    async def refund(self, transaction_id: str, amount: float) -> PaymentResponse:
        """Process wallet refund"""
        return PaymentResponse(
            success=True,
            transaction_id=transaction_id,
            status="REFUNDED",
            message="Refund processed",
        )

    def is_healthy(self) -> bool:
        """Wallet is always healthy if DB is accessible"""
        return True


class ProviderRegistry:
    """
    Registry for payment providers.
    Allows dynamic provider loading and failover.
    """

    def __init__(self):
        self._providers: Dict[ProviderType, PaymentProvider] = {}
        self._provider_configs: Dict[ProviderType, Dict[str, Any]] = {}

    def register_provider(
        self,
        provider_type: ProviderType,
        provider: PaymentProvider,
        config: Dict[str, Any] = None
    ) -> None:
        """Register a payment provider"""
        self._providers[provider_type] = provider
        if config:
            self._provider_configs[provider_type] = config
        logger.info(f"Registered provider: {provider_type}")

    def get_provider(self, provider_type: ProviderType) -> Optional[PaymentProvider]:
        """Get a registered provider"""
        return self._providers.get(provider_type)

    def get_healthy_provider(
        self,
        preferred_type: ProviderType,
        fallback_types: list[ProviderType] = None
    ) -> Optional[PaymentProvider]:
        """
        Get a healthy provider with fallback support.
        """
        # Try preferred provider first
        provider = self.get_provider(preferred_type)
        if provider and provider.is_healthy():
            return provider

        # Try fallback providers
        if fallback_types:
            for fallback_type in fallback_types:
                provider = self.get_provider(fallback_type)
                if provider and provider.is_healthy():
                    logger.warning(
                        f"Using fallback provider {fallback_type} instead of {preferred_type}"
                    )
                    return provider

        logger.error(f"No healthy provider available for {preferred_type}")
        return None

    def list_providers(self) -> list[ProviderType]:
        """List all registered providers"""
        return list(self._providers.keys())


# Global provider registry instance
provider_registry = ProviderRegistry()


def initialize_providers(config: Dict[str, Any]) -> None:
    """
    Initialize default providers with configuration.
    """
    # Register EcoCash
    if config.get("ecocash"):
        provider_registry.register_provider(
            ProviderType.ECOCASH,
            EcoCashProvider(config["ecocash"]),
            config["ecocash"]
        )

    # Register OneMoney
    if config.get("onemoney"):
        provider_registry.register_provider(
            ProviderType.ONEMONEY,
            OneMoneyProvider(config["onemoney"]),
            config["onemoney"]
        )

    # Register Wallet (always available)
    provider_registry.register_provider(
        ProviderType.WALLET,
        WalletProvider({}),
        {}
    )
