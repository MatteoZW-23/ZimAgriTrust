"""
Settlement Simulator with Platform Fee Deduction
Simulates settlement processing, fee calculation, and batch settlements
"""

import asyncio
import random
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from app.services.wallet_transaction_engine import (
    WalletTransactionEngine,
    TransactionType,
    WalletType
)


class SettlementStatus(Enum):
    """Settlement status states"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_SETTLED = "partially_settled"
    CANCELLED = "cancelled"


class SettlementBatchStatus(Enum):
    """Settlement batch status states"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SettlementItem:
    """Individual settlement item"""
    item_id: str
    order_id: str
    seller_id: str
    amount: float
    currency: str
    platform_fee: float
    net_amount: float
    status: SettlementStatus
    created_at: datetime
    settled_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "item_id": self.item_id,
            "order_id": self.order_id,
            "seller_id": self.seller_id,
            "amount": self.amount,
            "currency": self.currency,
            "platform_fee": self.platform_fee,
            "net_amount": self.net_amount,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "settled_at": self.settled_at.isoformat() if self.settled_at else None,
            "transaction_id": self.transaction_id,
            "metadata": self.metadata
        }


@dataclass
class SettlementBatch:
    """Settlement batch for bulk processing"""
    batch_id: str
    batch_name: str
    status: SettlementBatchStatus
    total_amount: float
    total_platform_fee: float
    total_net_amount: float
    currency: str
    item_count: int
    created_at: datetime
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items: List[SettlementItem] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "batch_id": self.batch_id,
            "batch_name": self.batch_name,
            "status": self.status.value,
            "total_amount": self.total_amount,
            "total_platform_fee": self.total_platform_fee,
            "total_net_amount": self.total_net_amount,
            "currency": self.currency,
            "item_count": self.item_count,
            "created_at": self.created_at.isoformat(),
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "metadata": self.metadata
        }


class SettlementSimulator:
    """
    Settlement simulator with platform fee deduction
    Simulates settlement processing, fee calculation, and batch settlements
    """
    
    def __init__(self, wallet_engine: WalletTransactionEngine):
        self.wallet_engine = wallet_engine
        self._settlement_items: Dict[str, SettlementItem] = {}
        self._settlement_batches: Dict[str, SettlementBatch] = {}
        
        # Configuration
        self.default_platform_fee_rate = 0.05  # 5%
        self.min_settlement_amount = 10.0
        self.auto_settle_enabled = True
        self.settlement_delay_hours = 24
        
    async def create_settlement_item(
        self,
        order_id: str,
        seller_id: str,
        amount: float,
        currency: str,
        platform_fee_rate: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SettlementItem:
        """
        Create a settlement item with platform fee calculation
        Returns settlement item
        """
        item_id = f"STL_{uuid.uuid4().hex[:16]}"
        fee_rate = platform_fee_rate or self.default_platform_fee_rate
        platform_fee = amount * fee_rate
        net_amount = amount - platform_fee
        
        item = SettlementItem(
            item_id=item_id,
            order_id=order_id,
            seller_id=seller_id,
            amount=amount,
            currency=currency,
            platform_fee=platform_fee,
            net_amount=net_amount,
            status=SettlementStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata=metadata
        )
        
        self._settlement_items[item_id] = item
        return item
    
    async def settle_item(
        self,
        item_id: str,
        escrow_wallet_id: str,
        platform_wallet_id: str
    ) -> SettlementItem:
        """
        Settle an individual item
        Returns updated settlement item
        """
        item = self._settlement_items.get(item_id)
        if not item:
            raise ValueError(f"Settlement item not found: {item_id}")
        
        if item.status != SettlementStatus.PENDING:
            raise ValueError(f"Item already {item.status.value}: {item_id}")
        
        # Get or create seller wallet
        seller_wallets = self.wallet_engine.get_user_wallets(item.seller_id)
        seller_wallet = None
        for wallet in seller_wallets:
            if wallet.wallet_type == WalletType.FARMER and wallet.currency == item.currency:
                seller_wallet = wallet
                break
        
        if not seller_wallet:
            seller_wallet = await self.wallet_engine.create_wallet(
                user_id=item.seller_id,
                wallet_type=WalletType.FARMER,
                currency=item.currency
            )
        
        # Transfer platform fee to platform wallet
        if item.platform_fee > 0:
            fee_transaction = await self.wallet_engine.transfer(
                from_wallet_id=escrow_wallet_id,
                to_wallet_id=platform_wallet_id,
                amount=item.platform_fee,
                currency=item.currency,
                reference=f"Platform fee for order {item.order_id}",
                description="Platform fee settlement"
            )
        
        # Transfer net amount to seller wallet
        settlement_transaction = await self.wallet_engine.transfer(
            from_wallet_id=escrow_wallet_id,
            to_wallet_id=seller_wallet.wallet_id,
            amount=item.net_amount,
            currency=item.currency,
            reference=f"Settlement for order {item.order_id}",
            description="Order settlement"
        )
        
        # Update item
        item.status = SettlementStatus.COMPLETED
        item.settled_at = datetime.utcnow()
        item.transaction_id = settlement_transaction.transaction_id
        
        return item
    
    async def create_settlement_batch(
        self,
        batch_name: str,
        currency: str,
        item_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SettlementBatch:
        """
        Create a settlement batch
        Returns settlement batch
        """
        batch_id = f"BAT_{uuid.uuid4().hex[:16]}"
        
        # Get items for batch
        items = []
        if item_ids:
            for item_id in item_ids:
                item = self._settlement_items.get(item_id)
                if item and item.status == SettlementStatus.PENDING:
                    items.append(item)
        else:
            # Auto-select pending items
            items = [
                item for item in self._settlement_items.values()
                if item.status == SettlementStatus.PENDING
                and item.currency == currency
            ]
        
        # Calculate totals
        total_amount = sum(item.amount for item in items)
        total_platform_fee = sum(item.platform_fee for item in items)
        total_net_amount = sum(item.net_amount for item in items)
        
        batch = SettlementBatch(
            batch_id=batch_id,
            batch_name=batch_name,
            status=SettlementBatchStatus.DRAFT,
            total_amount=total_amount,
            total_platform_fee=total_platform_fee,
            total_net_amount=total_net_amount,
            currency=currency,
            item_count=len(items),
            created_at=datetime.utcnow(),
            items=items,
            metadata=metadata
        )
        
        self._settlement_batches[batch_id] = batch
        return batch
    
    async def submit_batch(
        self,
        batch_id: str
    ) -> SettlementBatch:
        """
        Submit a settlement batch for processing
        Returns updated batch
        """
        batch = self._settlement_batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")
        
        if batch.status != SettlementBatchStatus.DRAFT:
            raise ValueError(f"Batch already {batch.status.value}: {batch_id}")
        
        if batch.item_count == 0:
            raise ValueError(f"Batch has no items: {batch_id}")
        
        batch.status = SettlementBatchStatus.SUBMITTED
        batch.submitted_at = datetime.utcnow()
        
        return batch
    
    async def process_batch(
        self,
        batch_id: str,
        escrow_wallet_id: str,
        platform_wallet_id: str
    ) -> SettlementBatch:
        """
        Process a settlement batch
        Returns updated batch
        """
        batch = self._settlement_batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")
        
        if batch.status != SettlementBatchStatus.SUBMITTED:
            raise ValueError(f"Batch not submitted: {batch_id}")
        
        batch.status = SettlementBatchStatus.PROCESSING
        
        # Process each item
        completed_count = 0
        failed_count = 0
        
        for item in batch.items:
            try:
                await self.settle_item(item.item_id, escrow_wallet_id, platform_wallet_id)
                completed_count += 1
            except Exception:
                failed_count += 1
                item.status = SettlementStatus.FAILED
        
        # Update batch status
        if completed_count == batch.item_count:
            batch.status = SettlementBatchStatus.COMPLETED
        elif completed_count > 0:
            batch.status = SettlementBatchStatus.COMPLETED  # Partial success
        else:
            batch.status = SettlementBatchStatus.FAILED
        
        batch.completed_at = datetime.utcnow()
        
        return batch
    
    async def process_auto_settlements(
        self,
        escrow_wallet_id: str,
        platform_wallet_id: str
    ) -> List[SettlementBatch]:
        """
        Process automatic settlements for pending items
        Returns list of processed batches
        """
        if not self.auto_settle_enabled:
            return []
        
        # Group pending items by currency
        currency_groups: Dict[str, List[SettlementItem]] = {}
        for item in self._settlement_items.values():
            if item.status == SettlementStatus.PENDING:
                currency = item.currency
                if currency not in currency_groups:
                    currency_groups[currency] = []
                currency_groups[currency].append(item)
        
        processed_batches = []
        for currency, items in currency_groups.items():
            # Create and process batch
            batch = await self.create_settlement_batch(
                batch_name=f"Auto-settlement {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                currency=currency,
                item_ids=[item.item_id for item in items]
            )
            
            await self.submit_batch(batch.batch_id)
            processed_batch = await self.process_batch(batch.batch_id, escrow_wallet_id, platform_wallet_id)
            processed_batches.append(processed_batch)
        
        return processed_batches
    
    def get_settlement_item(self, item_id: str) -> Optional[SettlementItem]:
        """Get settlement item by ID"""
        return self._settlement_items.get(item_id)
    
    def get_settlement_batch(self, batch_id: str) -> Optional[SettlementBatch]:
        """Get settlement batch by ID"""
        return self._settlement_batches.get(batch_id)
    
    def get_pending_items(self, currency: Optional[str] = None) -> List[SettlementItem]:
        """Get pending settlement items"""
        items = [
            item for item in self._settlement_items.values()
            if item.status == SettlementStatus.PENDING
        ]
        if currency:
            items = [item for item in items if item.currency == currency]
        return items
    
    def get_settlement_stats(self) -> Dict[str, Any]:
        """Get settlement statistics"""
        total_items = len(self._settlement_items)
        if total_items == 0:
            return {"total_items": 0, "pending": 0, "completed": 0, "failed": 0}
        
        pending = len([i for i in self._settlement_items.values() if i.status == SettlementStatus.PENDING])
        completed = len([i for i in self._settlement_items.values() if i.status == SettlementStatus.COMPLETED])
        failed = len([i for i in self._settlement_items.values() if i.status == SettlementStatus.FAILED])
        
        total_amount = sum(i.amount for i in self._settlement_items.values())
        total_platform_fee = sum(i.platform_fee for i in self._settlement_items.values())
        total_net_amount = sum(i.net_amount for i in self._settlement_items.values())
        
        return {
            "total_items": total_items,
            "pending": pending,
            "completed": completed,
            "failed": failed,
            "completion_rate": (completed / total_items) * 100 if total_items > 0 else 0,
            "total_amount": total_amount,
            "total_platform_fee": total_platform_fee,
            "total_net_amount": total_net_amount
        }
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """Get batch statistics"""
        total_batches = len(self._settlement_batches)
        if total_batches == 0:
            return {"total_batches": 0, "draft": 0, "submitted": 0, "processing": 0, "completed": 0}
        
        draft = len([b for b in self._settlement_batches.values() if b.status == SettlementBatchStatus.DRAFT])
        submitted = len([b for b in self._settlement_batches.values() if b.status == SettlementBatchStatus.SUBMITTED])
        processing = len([b for b in self._settlement_batches.values() if b.status == SettlementBatchStatus.PROCESSING])
        completed = len([b for b in self._settlement_batches.values() if b.status == SettlementBatchStatus.COMPLETED])
        failed = len([b for b in self._settlement_batches.values() if b.status == SettlementBatchStatus.FAILED])
        
        return {
            "total_batches": total_batches,
            "draft": draft,
            "submitted": submitted,
            "processing": processing,
            "completed": completed,
            "failed": failed
        }
    
    def clear_settlements(self) -> None:
        """Clear all settlements (for testing)"""
        self._settlement_items.clear()
        self._settlement_batches.clear()
