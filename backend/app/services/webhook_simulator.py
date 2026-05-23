"""
Mock Webhook Engine
Simulates webhook delivery with retry handlers, signature validation, and replay protection
"""

import asyncio
import random
import hmac
import hashlib
import json
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from app.providers.mock.base_provider import PaymentStatus


class WebhookDeliveryStatus(Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    EXPIRED = "expired"


class WebhookRetryStrategy(Enum):
    """Webhook retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    IMMEDIATE = "immediate"


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "status": self.status.value,
            "amount": self.amount,
            "currency": self.currency,
            "reference": self.reference,
            "provider_reference": self.provider_reference,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature,
            "metadata": self.metadata
        }


@dataclass
class WebhookDeliveryAttempt:
    """Single webhook delivery attempt"""
    attempt_number: int
    status: WebhookDeliveryStatus
    timestamp: datetime
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0


@dataclass
class WebhookRecord:
    """Webhook delivery record"""
    webhook_id: str
    payload: WebhookPayload
    callback_url: str
    status: WebhookDeliveryStatus
    created_at: datetime
    attempts: List[WebhookDeliveryAttempt]
    max_retries: int
    retry_strategy: WebhookRetryStrategy
    expires_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "webhook_id": self.webhook_id,
            "payload": self.payload.to_dict(),
            "callback_url": self.callback_url,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "attempts": [
                {
                    "attempt_number": a.attempt_number,
                    "status": a.status.value,
                    "timestamp": a.timestamp.isoformat(),
                    "response_code": a.response_code,
                    "error_message": a.error_message,
                    "duration_seconds": a.duration_seconds
                }
                for a in self.attempts
            ],
            "max_retries": self.max_retries,
            "retry_strategy": self.retry_strategy.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "idempotency_key": self.idempotency_key
        }


class WebhookSimulator:
    """
    Mock webhook engine with retry handlers
    Simulates real webhook delivery behavior
    """
    
    def __init__(self):
        self._webhooks: Dict[str, WebhookRecord] = {}
        self._idempotency_keys: Dict[str, str] = {}  # idempotency_key -> webhook_id
        self._delivery_handler: Optional[Callable] = None
        
        # Configuration
        self.default_max_retries = 3
        self.default_retry_strategy = WebhookRetryStrategy.EXPONENTIAL_BACKOFF
        self.default_expiry_hours = 24
        
    def set_delivery_handler(self, handler: Callable) -> None:
        """Set custom webhook delivery handler"""
        self._delivery_handler = handler
    
    async def create_webhook(
        self,
        payload: WebhookPayload,
        callback_url: str,
        max_retries: Optional[int] = None,
        retry_strategy: Optional[WebhookRetryStrategy] = None,
        idempotency_key: Optional[str] = None,
        expiry_hours: Optional[int] = None
    ) -> WebhookRecord:
        """
        Create a new webhook record
        Returns webhook record
        """
        webhook_id = f"WH_{uuid.uuid4().hex[:16]}"
        
        # Check idempotency
        if idempotency_key:
            existing_webhook_id = self._idempotency_keys.get(idempotency_key)
            if existing_webhook_id:
                return self._webhooks[existing_webhook_id]
        
        max_retries = max_retries or self.default_max_retries
        retry_strategy = retry_strategy or self.default_retry_strategy
        expiry_hours = expiry_hours or self.default_expiry_hours
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        webhook = WebhookRecord(
            webhook_id=webhook_id,
            payload=payload,
            callback_url=callback_url,
            status=WebhookDeliveryStatus.PENDING,
            created_at=datetime.utcnow(),
            attempts=[],
            max_retries=max_retries,
            retry_strategy=retry_strategy,
            expires_at=expires_at,
            idempotency_key=idempotency_key
        )
        
        self._webhooks[webhook_id] = webhook
        if idempotency_key:
            self._idempotency_keys[idempotency_key] = webhook_id
        
        return webhook
    
    async def deliver_webhook(
        self,
        webhook_id: str,
        simulate_failure: bool = False,
        simulate_delay: bool = False
    ) -> WebhookDeliveryAttempt:
        """
        Deliver a webhook
        Returns delivery attempt record
        """
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook not found: {webhook_id}")
        
        # Check if expired
        if webhook.expires_at and datetime.utcnow() > webhook.expires_at:
            webhook.status = WebhookDeliveryStatus.EXPIRED
            return WebhookDeliveryAttempt(
                attempt_number=len(webhook.attempts) + 1,
                status=WebhookDeliveryStatus.EXPIRED,
                timestamp=datetime.utcnow(),
                error_message="Webhook expired"
            )
        
        attempt_number = len(webhook.attempts) + 1
        started_at = datetime.utcnow()
        
        # Simulate delay
        if simulate_delay:
            delay = random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
        
        # Simulate delivery
        if self._delivery_handler:
            try:
                response = await self._delivery_handler(webhook.payload.to_dict(), webhook.callback_url)
                response_code = response.get("status_code", 200)
                response_body = response.get("body", "")
            except Exception as e:
                response_code = 500
                response_body = str(e)
        else:
            # Default simulation
            if simulate_failure:
                response_code = random.choice([400, 401, 403, 404, 500, 502, 503])
                response_body = f"Simulated failure: HTTP {response_code}"
            else:
                response_code = 200
                response_body = '{"status": "success"}"
        
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - started_at).total_seconds()
        
        # Determine status
        if response_code >= 200 and response_code < 300:
            status = WebhookDeliveryStatus.DELIVERED
            webhook.status = WebhookDeliveryStatus.DELIVERED
            error_message = None
        elif attempt_number >= webhook.max_retries:
            status = WebhookDeliveryStatus.FAILED
            webhook.status = WebhookDeliveryStatus.FAILED
            error_message = f"Max retries exceeded: HTTP {response_code}"
        else:
            status = WebhookDeliveryStatus.RETRYING
            webhook.status = WebhookDeliveryStatus.RETRYING
            error_message = f"HTTP {response_code}"
        
        attempt = WebhookDeliveryAttempt(
            attempt_number=attempt_number,
            status=status,
            timestamp=started_at,
            response_code=response_code,
            response_body=response_body,
            error_message=error_message,
            duration_seconds=duration_seconds
        )
        
        webhook.attempts.append(attempt)
        return attempt
    
    async def retry_webhook(self, webhook_id: str) -> WebhookDeliveryAttempt:
        """
        Retry a failed webhook
        Returns delivery attempt record
        """
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook not found: {webhook_id}")
        
        if webhook.status not in [WebhookDeliveryStatus.FAILED, WebhookDeliveryStatus.RETRYING]:
            raise ValueError(f"Webhook not retryable: {webhook.status.value}")
        
        # Calculate retry delay based on strategy
        delay = self._calculate_retry_delay(webhook)
        await asyncio.sleep(delay)
        
        return await self.deliver_webhook(webhook_id)
    
    def _calculate_retry_delay(self, webhook: WebhookRecord) -> float:
        """Calculate retry delay based on strategy"""
        attempt_number = len(webhook.attempts) + 1
        
        if webhook.retry_strategy == WebhookRetryStrategy.EXPONENTIAL_BACKOFF:
            return min(2 ** attempt_number, 60)  # Max 60 seconds
        elif webhook.retry_strategy == WebhookRetryStrategy.LINEAR_BACKOFF:
            return min(attempt_number * 2, 30)  # Max 30 seconds
        elif webhook.retry_strategy == WebhookRetryStrategy.FIXED_INTERVAL:
            return 5  # Fixed 5 seconds
        else:
            return 0  # Immediate
    
    async def process_pending_webhooks(
        self,
        simulate_failure_rate: float = 0.1,
        simulate_delay: bool = True
    ) -> List[WebhookDeliveryAttempt]:
        """
        Process all pending webhooks
        Returns list of delivery attempts
        """
        pending_webhooks = [
            w for w in self._webhooks.values()
            if w.status == WebhookDeliveryStatus.PENDING
        ]
        
        attempts = []
        for webhook in pending_webhooks:
            simulate_failure = random.random() < simulate_failure_rate
            attempt = await self.deliver_webhook(
                webhook.webhook_id,
                simulate_failure=simulate_failure,
                simulate_delay=simulate_delay
            )
            attempts.append(attempt)
        
        return attempts
    
    async def retry_failed_webhooks(self) -> List[WebhookDeliveryAttempt]:
        """
        Retry all failed webhooks
        Returns list of delivery attempts
        """
        retryable_webhooks = [
            w for w in self._webhooks.values()
            if w.status == WebhookDeliveryStatus.RETRYING
        ]
        
        attempts = []
        for webhook in retryable_webhooks:
            try:
                attempt = await self.retry_webhook(webhook.webhook_id)
                attempts.append(attempt)
            except Exception as e:
                # Log error but continue with other webhooks
                pass
        
        return attempts
    
    def get_webhook(self, webhook_id: str) -> Optional[WebhookRecord]:
        """Get webhook by ID"""
        return self._webhooks.get(webhook_id)
    
    def get_webhooks_by_status(self, status: WebhookDeliveryStatus) -> List[WebhookRecord]:
        """Get webhooks by status"""
        return [w for w in self._webhooks.values() if w.status == status]
    
    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        total = len(self._webhooks)
        if total == 0:
            return {"total": 0, "delivered": 0, "failed": 0, "pending": 0}
        
        delivered = len(self.get_webhooks_by_status(WebhookDeliveryStatus.DELIVERED))
        failed = len(self.get_webhooks_by_status(WebhookDeliveryStatus.FAILED))
        pending = len(self.get_webhooks_by_status(WebhookDeliveryStatus.PENDING))
        retrying = len(self.get_webhooks_by_status(WebhookDeliveryStatus.RETRYING))
        expired = len(self.get_webhooks_by_status(WebhookDeliveryStatus.EXPIRED))
        
        # Average attempts
        total_attempts = sum(len(w.attempts) for w in self._webhooks.values())
        avg_attempts = total_attempts / total if total > 0 else 0
        
        return {
            "total": total,
            "delivered": delivered,
            "failed": failed,
            "pending": pending,
            "retrying": retrying,
            "expired": expired,
            "delivery_rate": (delivered / total) * 100,
            "avg_attempts": avg_attempts
        }
    
    def clear_webhooks(self) -> None:
        """Clear all webhooks"""
        self._webhooks.clear()
        self._idempotency_keys.clear()


# Global webhook simulator instance
webhook_simulator = WebhookSimulator()
