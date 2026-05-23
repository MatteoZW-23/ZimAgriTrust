"""
Mock Innbucks Payment Provider
Simulates Innbucks mobile money behavior for Zimbabwe
"""

import asyncio
import random
import hmac
import hashlib
import json
from typing import Dict, Optional, Any
from datetime import datetime
from .base_provider import (
    BasePaymentProvider, 
    PaymentStatus, 
    PaymentRequest, 
    PaymentResponse,
    PaymentError
)


class MockInnbucksProvider(BasePaymentProvider):
    """Mock Innbucks provider simulating real mobile money behavior"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider_name = "Innbucks"
        self.api_key = self.config.get("api_key", "mock_innbucks_key")
        self.secret_key = self.config.get("secret_key", "mock_innbucks_secret")
        self.merchant_code = self.config.get("merchant_code", "INN001")
        self._webhook_queue: list = []
        
        self.success_rate = self.config.get("success_rate", 0.94)
        self.delay_range = self.config.get("delay_range", (1, 4))
        self.timeout_rate = self.config.get("timeout_rate", 0.02)
        self.failure_rate = self.config.get("failure_rate", 0.04)
    
    async def initialize_payment(self, request: PaymentRequest) -> PaymentResponse:
        transaction_id = self._generate_transaction_id()
        provider_ref = self._generate_provider_reference()
        
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)
        
        rand = random.random()
        
        if rand < self.failure_rate:
            response = PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                amount=request.amount,
                currency=request.currency,
                reference=request.reference,
                provider_reference=provider_ref,
                message="Payment failed: Transaction declined",
                created_at=datetime.utcnow(),
                failure_reason="TRANSACTION_DECLINED",
                metadata={"provider": self.provider_name, "phone": request.phone_number}
            )
        elif rand < self.failure_rate + self.timeout_rate:
            response = PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.TIMEOUT,
                amount=request.amount,
                currency=request.currency,
                reference=request.reference,
                provider_reference=provider_ref,
                message="Payment timed out",
                created_at=datetime.utcnow(),
                failure_reason="TIMEOUT",
                metadata={"provider": self.provider_name, "phone": request.phone_number}
            )
        else:
            response = PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.SUCCESS,
                amount=request.amount,
                currency=request.currency,
                reference=request.reference,
                provider_reference=provider_ref,
                message="Payment successful",
                created_at=datetime.utcnow(),
                processed_at=datetime.utcnow(),
                metadata={"provider": self.provider_name, "phone": request.phone_number}
            )
            
            if request.callback_url:
                await self._queue_webhook(response)
        
        self._store_transaction(response)
        return response
    
    async def verify_payment(self, transaction_id: str) -> PaymentResponse:
        transaction = self._get_transaction(transaction_id)
        if not transaction:
            raise PaymentError("Transaction not found", "TRANSACTION_NOT_FOUND", {"transaction_id": transaction_id})
        
        if transaction.status == PaymentStatus.PENDING:
            await asyncio.sleep(0.5)
            transaction.status = PaymentStatus.PROCESSING
            self._store_transaction(transaction)
        
        return transaction
    
    async def process_withdrawal(
        self, amount: float, currency: str, account_number: str, reference: str
    ) -> PaymentResponse:
        transaction_id = self._generate_transaction_id()
        provider_ref = self._generate_provider_reference()
        
        await asyncio.sleep(random.uniform(2, 4))
        
        rand = random.random()
        
        if rand < self.failure_rate:
            response = PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                amount=amount,
                currency=currency,
                reference=reference,
                provider_reference=provider_ref,
                message="Withdrawal failed",
                created_at=datetime.utcnow(),
                failure_reason="WITHDRAWAL_FAILED",
                metadata={"provider": self.provider_name, "account": account_number}
            )
        else:
            response = PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.SUCCESS,
                amount=amount,
                currency=currency,
                reference=reference,
                provider_reference=provider_ref,
                message="Withdrawal successful",
                created_at=datetime.utcnow(),
                processed_at=datetime.utcnow(),
                metadata={"provider": self.provider_name, "account": account_number}
            )
        
        self._store_transaction(response)
        return response
    
    async def refund_payment(
        self, transaction_id: str, amount: Optional[float] = None, reason: Optional[str] = None
    ) -> PaymentResponse:
        original_transaction = self._get_transaction(transaction_id)
        if not original_transaction:
            raise PaymentError("Original transaction not found", "TRANSACTION_NOT_FOUND", {"transaction_id": transaction_id})
        
        refund_amount = amount or original_transaction.amount
        refund_transaction_id = self._generate_transaction_id()
        provider_ref = self._generate_provider_reference()
        
        await asyncio.sleep(random.uniform(1, 3))
        
        response = PaymentResponse(
            transaction_id=refund_transaction_id,
            status=PaymentStatus.REFUNDED,
            amount=refund_amount,
            currency=original_transaction.currency,
            reference=f"REFUND_{original_transaction.reference}",
            provider_reference=provider_ref,
            message=f"Refund processed: {reason or 'No reason'}",
            created_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
            metadata={"provider": self.provider_name, "original_transaction_id": transaction_id, "refund_reason": reason}
        )
        
        self._store_transaction(response)
        return response
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> PaymentResponse:
        signature = payload.get("signature")
        if not self.verify_webhook_signature(payload, signature):
            raise PaymentError("Invalid webhook signature", "INVALID_SIGNATURE", {"payload": payload})
        
        transaction_id = payload.get("transaction_id")
        transaction = self._get_transaction(transaction_id)
        
        if not transaction:
            raise PaymentError("Webhook for unknown transaction", "TRANSACTION_NOT_FOUND", {"transaction_id": transaction_id})
        
        status_str = payload.get("status")
        if status_str:
            try:
                transaction.status = PaymentStatus(status_str)
                transaction.processed_at = datetime.utcnow()
                self._store_transaction(transaction)
            except ValueError:
                raise PaymentError(f"Invalid status: {status_str}", "INVALID_STATUS", {"status": status_str})
        
        return transaction
    
    async def get_transaction_status(self, transaction_id: str) -> PaymentStatus:
        transaction = self._get_transaction(transaction_id)
        if not transaction:
            raise PaymentError("Transaction not found", "TRANSACTION_NOT_FOUND", {"transaction_id": transaction_id})
        return transaction.status
    
    def generate_webhook_signature(self, payload: Dict[str, Any]) -> str:
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(self.secret_key.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
        return signature
    
    def verify_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        expected_signature = self.generate_webhook_signature(payload)
        return hmac.compare_digest(expected_signature, signature)
    
    async def _queue_webhook(self, transaction: PaymentResponse) -> None:
        webhook_payload = {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status.value,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "reference": transaction.reference,
            "provider_reference": transaction.provider_reference,
            "timestamp": transaction.created_at.isoformat(),
            "signature": self.generate_webhook_signature({
                "transaction_id": transaction.transaction_id,
                "status": transaction.status.value,
                "amount": transaction.amount,
                "currency": transaction.currency
            }),
            "metadata": transaction.metadata
        }
        self._webhook_queue.append(webhook_payload)
    
    async def get_pending_webhooks(self) -> list:
        return self._webhook_queue.copy()
    
    async def clear_webhook_queue(self) -> None:
        self._webhook_queue.clear()
