"""
Base Payment Provider Interface
Defines the contract that all payment providers must implement
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import uuid


class PaymentStatus(Enum):
    """Payment states matching real provider behavior"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REVERSED = "reversed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    ESCROW_HELD = "escrow_held"
    SETTLED = "settled"
    REFUNDED = "refunded"


@dataclass
class PaymentRequest:
    """Payment request structure"""
    amount: float
    currency: str
    phone_number: str
    reference: str
    description: str
    metadata: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None


@dataclass
class PaymentResponse:
    """Payment response structure"""
    transaction_id: str
    status: PaymentStatus
    amount: float
    currency: str
    reference: str
    provider_reference: str
    message: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WebhookPayload:
    """Webhook payload structure"""
    transaction_id: str
    status: PaymentStatus
    amount: float
    currency: str
    reference: str
    provider_reference: str
    timestamp: datetime
    signature: str
    metadata: Optional[Dict[str, Any]] = None


class PaymentError(Exception):
    """Payment provider error"""
    def __init__(self, message: str, code: str, details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class BasePaymentProvider(ABC):
    """
    Abstract base class for all payment providers
    All mock providers must implement these methods
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.provider_name = self.__class__.__name__
        self._transaction_store: Dict[str, PaymentResponse] = {}
        
    @abstractmethod
    async def initialize_payment(self, request: PaymentRequest) -> PaymentResponse:
        """
        Initialize a payment transaction
        Returns payment response with transaction ID
        """
        pass
    
    @abstractmethod
    async def verify_payment(self, transaction_id: str) -> PaymentResponse:
        """
        Verify payment status with provider
        Returns current payment status
        """
        pass
    
    @abstractmethod
    async def process_withdrawal(
        self, 
        amount: float, 
        currency: str, 
        account_number: str, 
        reference: str
    ) -> PaymentResponse:
        """
        Process withdrawal to bank account or mobile wallet
        Returns withdrawal response
        """
        pass
    
    @abstractmethod
    async def refund_payment(
        self, 
        transaction_id: str, 
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> PaymentResponse:
        """
        Refund a payment (full or partial)
        Returns refund response
        """
        pass
    
    @abstractmethod
    async def handle_webhook(self, payload: Dict[str, Any]) -> PaymentResponse:
        """
        Process webhook callback from provider
        Returns updated payment status
        """
        pass
    
    @abstractmethod
    async def get_transaction_status(self, transaction_id: str) -> PaymentStatus:
        """
        Get current transaction status
        Returns payment status enum
        """
        pass
    
    @abstractmethod
    def generate_webhook_signature(self, payload: Dict[str, Any]) -> str:
        """
        Generate webhook signature for verification
        Returns signature string
        """
        pass
    
    @abstractmethod
    def verify_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify webhook signature authenticity
        Returns boolean validity
        """
        pass
    
    def _store_transaction(self, response: PaymentResponse) -> None:
        """Store transaction in memory for simulation"""
        self._transaction_store[response.transaction_id] = response
    
    def _get_transaction(self, transaction_id: str) -> Optional[PaymentResponse]:
        """Retrieve transaction from memory"""
        return self._transaction_store.get(transaction_id)
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"{self.provider_name}_{uuid.uuid4().hex[:16]}"
    
    def _generate_provider_reference(self) -> str:
        """Generate provider-specific reference"""
        return f"PROV_{uuid.uuid4().hex[:12]}"
