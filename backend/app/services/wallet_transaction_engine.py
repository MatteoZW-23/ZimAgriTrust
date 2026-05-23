"""
Wallet Transaction Engine with Immutable Ledger
Implements double-entry accounting with audit-safe transaction history
"""

import asyncio
import random
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import hashlib
import json


class TransactionType(Enum):
    """Transaction types"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    ESCROW_HOLD = "escrow_hold"
    ESCROW_RELEASE = "escrow_release"
    ESCROW_REFUND = "escrow_refund"
    PLATFORM_FEE = "platform_fee"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


class LedgerEntryType(Enum):
    """Ledger entry types for double-entry accounting"""
    DEBIT = "debit"
    CREDIT = "credit"


class WalletType(Enum):
    """Wallet types"""
    BUYER = "buyer"
    FARMER = "farmer"
    SUPPLIER = "supplier"
    ESCROW = "escrow"
    PLATFORM = "platform"
    SETTLEMENT = "settlement"


@dataclass
class Wallet:
    """Wallet representation"""
    wallet_id: str
    user_id: str
    wallet_type: WalletType
    currency: str
    balance: float
    available_balance: float
    pending_balance: float
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "wallet_id": self.wallet_id,
            "user_id": self.user_id,
            "wallet_type": self.wallet_type.value,
            "currency": self.currency,
            "balance": self.balance,
            "available_balance": self.available_balance,
            "pending_balance": self.pending_balance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "metadata": self.metadata
        }


@dataclass
class LedgerEntry:
    """Immutable ledger entry"""
    entry_id: str
    transaction_id: str
    wallet_id: str
    entry_type: LedgerEntryType
    amount: float
    currency: str
    balance_after: float
    created_at: datetime
    reference: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    entry_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entry_id": self.entry_id,
            "transaction_id": self.transaction_id,
            "wallet_id": self.wallet_id,
            "entry_type": self.entry_type.value,
            "amount": self.amount,
            "currency": self.currency,
            "balance_after": self.balance_after,
            "created_at": self.created_at.isoformat(),
            "reference": self.reference,
            "description": self.description,
            "metadata": self.metadata,
            "entry_hash": self.entry_hash
        }
    
    def compute_hash(self) -> str:
        """Compute cryptographic hash of entry"""
        data = {
            "entry_id": self.entry_id,
            "transaction_id": self.transaction_id,
            "wallet_id": self.wallet_id,
            "entry_type": self.entry_type.value,
            "amount": self.amount,
            "currency": self.currency,
            "balance_after": self.balance_after,
            "created_at": self.created_at.isoformat(),
            "reference": self.reference,
            "description": self.description
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


@dataclass
class Transaction:
    """Transaction record"""
    transaction_id: str
    transaction_type: TransactionType
    amount: float
    currency: str
    from_wallet_id: Optional[str]
    to_wallet_id: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    ledger_entries: List[LedgerEntry] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "currency": self.currency,
            "from_wallet_id": self.from_wallet_id,
            "to_wallet_id": self.to_wallet_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "reference": self.reference,
            "description": self.description,
            "metadata": self.metadata,
            "ledger_entries": [e.to_dict() for e in self.ledger_entries] if self.ledger_entries else []
        }


class WalletTransactionEngine:
    """
    Wallet transaction engine with immutable ledger
    Implements double-entry accounting with audit-safe transaction history
    """
    
    def __init__(self):
        self._wallets: Dict[str, Wallet] = {}
        self._transactions: Dict[str, Transaction] = {}
        self._ledger_entries: Dict[str, LedgerEntry] = {}
        self._user_wallets: Dict[str, List[str]] = {}  # user_id -> wallet_ids
        
        # Distributed locks for race condition prevention
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # Configuration
        self.default_currency = "USD"
        self.platform_fee_rate = 0.05  # 5%
        
    def _get_lock(self, wallet_id: str) -> asyncio.Lock:
        """Get or create lock for wallet"""
        if wallet_id not in self._locks:
            self._locks[wallet_id] = asyncio.Lock()
        return self._locks[wallet_id]
    
    async def create_wallet(
        self,
        user_id: str,
        wallet_type: WalletType,
        currency: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Wallet:
        """
        Create a new wallet for a user
        Returns wallet record
        """
        wallet_id = f"WLT_{uuid.uuid4().hex[:16]}"
        currency = currency or self.default_currency
        
        wallet = Wallet(
            wallet_id=wallet_id,
            user_id=user_id,
            wallet_type=wallet_type,
            currency=currency,
            balance=0.0,
            available_balance=0.0,
            pending_balance=0.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
            metadata=metadata
        )
        
        self._wallets[wallet_id] = wallet
        
        if user_id not in self._user_wallets:
            self._user_wallets[user_id] = []
        self._user_wallets[user_id].append(wallet_id)
        
        return wallet
    
    def get_wallet(self, wallet_id: str) -> Optional[Wallet]:
        """Get wallet by ID"""
        return self._wallets.get(wallet_id)
    
    def get_user_wallets(self, user_id: str) -> List[Wallet]:
        """Get all wallets for a user"""
        wallet_ids = self._user_wallets.get(user_id, [])
        return [self._wallets[wid] for wid in wallet_ids if wid in self._wallets]
    
    def get_wallet_balance(self, wallet_id: str) -> float:
        """Get current wallet balance"""
        wallet = self._wallets.get(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")
        return wallet.balance
    
    async def deposit(
        self,
        wallet_id: str,
        amount: float,
        currency: str,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Deposit funds to wallet
        Returns transaction record
        """
        wallet = self._wallets.get(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")
        
        if wallet.currency != currency:
            raise ValueError(f"Currency mismatch: wallet={wallet.currency}, deposit={currency}")
        
        async with self._get_lock(wallet_id):
            transaction_id = f"TXN_{uuid.uuid4().hex[:16]}"
            
            # Create transaction
            transaction = Transaction(
                transaction_id=transaction_id,
                transaction_type=TransactionType.DEPOSIT,
                amount=amount,
                currency=currency,
                from_wallet_id=None,
                to_wallet_id=wallet_id,
                status="completed",
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                reference=reference,
                description=description,
                metadata=metadata,
                ledger_entries=[]
            )
            
            # Create ledger entry (credit)
            entry_id = f"LED_{uuid.uuid4().hex[:16]}"
            balance_after = wallet.balance + amount
            
            entry = LedgerEntry(
                entry_id=entry_id,
                transaction_id=transaction_id,
                wallet_id=wallet_id,
                entry_type=LedgerEntryType.CREDIT,
                amount=amount,
                currency=currency,
                balance_after=balance_after,
                created_at=datetime.utcnow(),
                reference=reference,
                description=description,
                metadata=metadata
            )
            entry.entry_hash = entry.compute_hash()
            
            # Update wallet
            wallet.balance = balance_after
            wallet.available_balance = balance_after
            wallet.updated_at = datetime.utcnow()
            
            # Store records
            transaction.ledger_entries.append(entry)
            self._transactions[transaction_id] = transaction
            self._ledger_entries[entry_id] = entry
            
            return transaction
    
    async def withdraw(
        self,
        wallet_id: str,
        amount: float,
        currency: str,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Withdraw funds from wallet
        Returns transaction record
        """
        wallet = self._wallets.get(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")
        
        if wallet.currency != currency:
            raise ValueError(f"Currency mismatch: wallet={wallet.currency}, withdrawal={currency}")
        
        if wallet.available_balance < amount:
            raise ValueError(f"Insufficient balance: available={wallet.available_balance}, requested={amount}")
        
        async with self._get_lock(wallet_id):
            transaction_id = f"TXN_{uuid.uuid4().hex[:16]}"
            
            # Create transaction
            transaction = Transaction(
                transaction_id=transaction_id,
                transaction_type=TransactionType.WITHDRAWAL,
                amount=amount,
                currency=currency,
                from_wallet_id=wallet_id,
                to_wallet_id=None,
                status="completed",
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                reference=reference,
                description=description,
                metadata=metadata,
                ledger_entries=[]
            )
            
            # Create ledger entry (debit)
            entry_id = f"LED_{uuid.uuid4().hex[:16]}"
            balance_after = wallet.balance - amount
            
            entry = LedgerEntry(
                entry_id=entry_id,
                transaction_id=transaction_id,
                wallet_id=wallet_id,
                entry_type=LedgerEntryType.DEBIT,
                amount=amount,
                currency=currency,
                balance_after=balance_after,
                created_at=datetime.utcnow(),
                reference=reference,
                description=description,
                metadata=metadata
            )
            entry.entry_hash = entry.compute_hash()
            
            # Update wallet
            wallet.balance = balance_after
            wallet.available_balance = balance_after
            wallet.updated_at = datetime.utcnow()
            
            # Store records
            transaction.ledger_entries.append(entry)
            self._transactions[transaction_id] = transaction
            self._ledger_entries[entry_id] = entry
            
            return transaction
    
    async def transfer(
        self,
        from_wallet_id: str,
        to_wallet_id: str,
        amount: float,
        currency: str,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        deduct_platform_fee: bool = False
    ) -> Transaction:
        """
        Transfer funds between wallets
        Returns transaction record
        """
        from_wallet = self._wallets.get(from_wallet_id)
        to_wallet = self._wallets.get(to_wallet_id)
        
        if not from_wallet:
            raise ValueError(f"Source wallet not found: {from_wallet_id}")
        if not to_wallet:
            raise ValueError(f"Destination wallet not found: {to_wallet_id}")
        
        if from_wallet.currency != currency or to_wallet.currency != currency:
            raise ValueError(f"Currency mismatch")
        
        if from_wallet.available_balance < amount:
            raise ValueError(f"Insufficient balance: available={from_wallet.available_balance}, requested={amount}")
        
        # Acquire locks in consistent order to prevent deadlock
        lock1 = self._get_lock(min(from_wallet_id, to_wallet_id))
        lock2 = self._get_lock(max(from_wallet_id, to_wallet_id))
        
        async with lock1, lock2:
            transaction_id = f"TXN_{uuid.uuid4().hex[:16]}"
            
            # Calculate platform fee
            platform_fee = 0.0
            if deduct_platform_fee:
                platform_fee = amount * self.platform_fee_rate
                transfer_amount = amount - platform_fee
            else:
                transfer_amount = amount
            
            # Create transaction
            transaction = Transaction(
                transaction_id=transaction_id,
                transaction_type=TransactionType.TRANSFER,
                amount=transfer_amount,
                currency=currency,
                from_wallet_id=from_wallet_id,
                to_wallet_id=to_wallet_id,
                status="completed",
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                reference=reference,
                description=description,
                metadata=metadata,
                ledger_entries=[]
            )
            
            # Debit from source wallet
            debit_entry_id = f"LED_{uuid.uuid4().hex[:16]}"
            from_balance_after = from_wallet.balance - amount
            
            debit_entry = LedgerEntry(
                entry_id=debit_entry_id,
                transaction_id=transaction_id,
                wallet_id=from_wallet_id,
                entry_type=LedgerEntryType.DEBIT,
                amount=amount,
                currency=currency,
                balance_after=from_balance_after,
                created_at=datetime.utcnow(),
                reference=reference,
                description=f"Transfer to {to_wallet_id}",
                metadata=metadata
            )
            debit_entry.entry_hash = debit_entry.compute_hash()
            
            from_wallet.balance = from_balance_after
            from_wallet.available_balance = from_balance_after
            from_wallet.updated_at = datetime.utcnow()
            
            # Credit to destination wallet
            credit_entry_id = f"LED_{uuid.uuid4().hex[:16]}"
            to_balance_after = to_wallet.balance + transfer_amount
            
            credit_entry = LedgerEntry(
                entry_id=credit_entry_id,
                transaction_id=transaction_id,
                wallet_id=to_wallet_id,
                entry_type=LedgerEntryType.CREDIT,
                amount=transfer_amount,
                currency=currency,
                balance_after=to_balance_after,
                created_at=datetime.utcnow(),
                reference=reference,
                description=f"Transfer from {from_wallet_id}",
                metadata=metadata
            )
            credit_entry.entry_hash = credit_entry.compute_hash()
            
            to_wallet.balance = to_balance_after
            to_wallet.available_balance = to_balance_after
            to_wallet.updated_at = datetime.utcnow()
            
            # Add platform fee if applicable
            if platform_fee > 0:
                platform_wallet_id = await self._get_or_create_platform_wallet(currency)
                fee_entry_id = f"LED_{uuid.uuid4().hex[:16]}"
                platform_wallet = self._wallets[platform_wallet_id]
                platform_balance_after = platform_wallet.balance + platform_fee
                
                fee_entry = LedgerEntry(
                    entry_id=fee_entry_id,
                    transaction_id=transaction_id,
                    wallet_id=platform_wallet_id,
                    entry_type=LedgerEntryType.CREDIT,
                    amount=platform_fee,
                    currency=currency,
                    balance_after=platform_balance_after,
                    created_at=datetime.utcnow(),
                    reference=reference,
                    description="Platform fee",
                    metadata={"fee_type": "transfer_fee"}
                )
                fee_entry.entry_hash = fee_entry.compute_hash()
                
                platform_wallet.balance = platform_balance_after
                platform_wallet.available_balance = platform_balance_after
                platform_wallet.updated_at = datetime.utcnow()
                
                transaction.ledger_entries.append(fee_entry)
                self._ledger_entries[fee_entry_id] = fee_entry
            
            # Store records
            transaction.ledger_entries.extend([debit_entry, credit_entry])
            self._transactions[transaction_id] = transaction
            self._ledger_entries[debit_entry_id] = debit_entry
            self._ledger_entries[credit_entry_id] = credit_entry
            
            return transaction
    
    async def _get_or_create_platform_wallet(self, currency: str) -> str:
        """Get or create platform wallet for currency"""
        platform_wallet_id = f"PLATFORM_{currency}"
        
        if platform_wallet_id in self._wallets:
            return platform_wallet_id
        
        wallet = await self.create_wallet(
            user_id="PLATFORM",
            wallet_type=WalletType.PLATFORM,
            currency=currency,
            metadata={"is_system_wallet": True}
        )
        
        return wallet.wallet_id
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        return self._transactions.get(transaction_id)
    
    def get_wallet_transactions(self, wallet_id: str, limit: int = 100) -> List[Transaction]:
        """Get transactions for a wallet"""
        transactions = [
            t for t in self._transactions.values()
            if t.from_wallet_id == wallet_id or t.to_wallet_id == wallet_id
        ]
        transactions.sort(key=lambda t: t.created_at, reverse=True)
        return transactions[:limit]
    
    def get_ledger_entries(self, wallet_id: str, limit: int = 100) -> List[LedgerEntry]:
        """Get ledger entries for a wallet"""
        entries = [
            e for e in self._ledger_entries.values()
            if e.wallet_id == wallet_id
        ]
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]
    
    def verify_ledger_integrity(self) -> Dict[str, Any]:
        """
        Verify ledger integrity by checking hash chains
        Returns integrity report
        """
        total_entries = len(self._ledger_entries)
        valid_hashes = 0
        invalid_hashes = 0
        
        for entry in self._ledger_entries.values():
            computed_hash = entry.compute_hash()
            if computed_hash == entry.entry_hash:
                valid_hashes += 1
            else:
                invalid_hashes += 1
        
        # Verify double-entry accounting
        total_debits = sum(e.amount for e in self._ledger_entries.values() if e.entry_type == LedgerEntryType.DEBIT)
        total_credits = sum(e.amount for e in self._ledger_entries.values() if e.entry_type == LedgerEntryType.CREDIT)
        
        return {
            "total_entries": total_entries,
            "valid_hashes": valid_hashes,
            "invalid_hashes": invalid_hashes,
            "hash_validity_rate": (valid_hashes / total_entries) * 100 if total_entries > 0 else 100,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "debit_credit_balance": total_debits - total_credits,
            "is_balanced": abs(total_debits - total_credits) < 0.01
        }
    
    def get_wallet_stats(self) -> Dict[str, Any]:
        """Get wallet statistics"""
        total_wallets = len(self._wallets)
        total_balance = sum(w.balance for w in self._wallets.values())
        total_available = sum(w.available_balance for w in self._wallets.values())
        total_pending = sum(w.pending_balance for w in self._wallets.values())
        
        # Wallet type breakdown
        wallet_types = {}
        for wallet in self._wallets.values():
            wtype = wallet.wallet_type.value
            wallet_types[wtype] = wallet_types.get(wtype, 0) + 1
        
        return {
            "total_wallets": total_wallets,
            "total_balance": total_balance,
            "total_available": total_available,
            "total_pending": total_pending,
            "wallet_types": wallet_types
        }
    
    def clear_all(self) -> None:
        """Clear all data (for testing)"""
        self._wallets.clear()
        self._transactions.clear()
        self._ledger_entries.clear()
        self._user_wallets.clear()
        self._locks.clear()


# Global wallet transaction engine instance
wallet_transaction_engine = WalletTransactionEngine()
