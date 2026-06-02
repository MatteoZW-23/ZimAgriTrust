from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.escrow import (
    EscrowAccount,
    EscrowStatus,
    EscrowTransaction,
    EscrowTransactionType,
)
from app.models.transaction import Order
from app.models.supplier import SupplierOrder


class EscrowAccountService:
    @staticmethod
    def _record(
        db: Session,
        account: EscrowAccount,
        transaction_type: EscrowTransactionType,
        amount: float,
        status: EscrowStatus,
        reference: Optional[str] = None,
        note: Optional[str] = None,
        metadata: Optional[dict] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> EscrowTransaction:
        event = EscrowTransaction(
            escrow_account_id=account.id,
            transaction_type=transaction_type,
            amount=round(float(amount or 0), 2),
            currency=account.currency,
            status=status,
            reference=reference,
            note=note,
            transaction_metadata=metadata,
            created_by=created_by,
        )
        db.add(event)
        return event

    @staticmethod
    def get_or_create_for_order(db: Session, order: Order, amount: Optional[float] = None) -> EscrowAccount:
        account = db.query(EscrowAccount).filter(EscrowAccount.order_id == order.id).first()
        if account:
            return account
        account = EscrowAccount(
            order_id=order.id,
            buyer_id=order.buyer_id,
            seller_id=order.seller_id,
            amount=round(float(amount if amount is not None else order.total_amount), 2),
            currency=order.currency,
            status=EscrowStatus.PENDING,
        )
        db.add(account)
        db.flush()
        return account

    @staticmethod
    def get_or_create_for_supplier_order(
        db: Session,
        order: SupplierOrder,
        amount: Optional[float] = None,
    ) -> EscrowAccount:
        account = db.query(EscrowAccount).filter(EscrowAccount.supplier_order_id == order.id).first()
        if account:
            return account
        supplier_user_id = order.supplier.user_id if order.supplier else None
        account = EscrowAccount(
            supplier_order_id=order.id,
            buyer_id=order.buyer_id,
            seller_id=supplier_user_id,
            supplier_id=order.supplier_id,
            amount=round(float(amount if amount is not None else order.total_amount), 2),
            currency=order.currency,
            status=EscrowStatus.PENDING,
        )
        db.add(account)
        db.flush()
        return account

    @staticmethod
    def mark_funded(db: Session, order: Order, amount: Optional[float] = None, reference: Optional[str] = None) -> EscrowAccount:
        account = EscrowAccountService.get_or_create_for_order(db, order, amount)
        if account.status in {EscrowStatus.RELEASED, EscrowStatus.REFUNDED, EscrowStatus.CANCELLED}:
            raise HTTPException(status_code=400, detail=f"Cannot fund escrow in {account.status.value} state")
        if account.status != EscrowStatus.FUNDED:
            account.status = EscrowStatus.FUNDED
            account.amount = round(float(amount if amount is not None else account.amount), 2)
            account.funded_at = datetime.now(timezone.utc)
            EscrowAccountService._record(
                db,
                account,
                EscrowTransactionType.FUND,
                account.amount,
                EscrowStatus.FUNDED,
                reference=reference or f"escrow_funded:{order.id}",
            )
        return account

    @staticmethod
    def mark_supplier_funded(
        db: Session,
        order: SupplierOrder,
        amount: Optional[float] = None,
        reference: Optional[str] = None,
    ) -> EscrowAccount:
        account = EscrowAccountService.get_or_create_for_supplier_order(db, order, amount)
        if account.status in {EscrowStatus.RELEASED, EscrowStatus.REFUNDED, EscrowStatus.CANCELLED}:
            raise HTTPException(status_code=400, detail=f"Cannot fund escrow in {account.status.value} state")
        if account.status != EscrowStatus.FUNDED:
            account.status = EscrowStatus.FUNDED
            account.amount = round(float(amount if amount is not None else account.amount), 2)
            account.funded_at = datetime.now(timezone.utc)
            EscrowAccountService._record(
                db,
                account,
                EscrowTransactionType.FUND,
                account.amount,
                EscrowStatus.FUNDED,
                reference=reference or f"supplier_escrow_funded:{order.id}",
            )
        return account

    @staticmethod
    def freeze_for_order(db: Session, order: Order, reason: str = "Dispute opened") -> EscrowAccount:
        account = EscrowAccountService.get_or_create_for_order(db, order)
        if account.status not in {EscrowStatus.PENDING, EscrowStatus.FUNDED, EscrowStatus.PARTIAL_RELEASE, EscrowStatus.FROZEN}:
            raise HTTPException(status_code=400, detail=f"Cannot freeze escrow in {account.status.value} state")
        if account.status != EscrowStatus.FROZEN:
            account.status = EscrowStatus.FROZEN
            account.frozen_at = datetime.now(timezone.utc)
            EscrowAccountService._record(
                db,
                account,
                EscrowTransactionType.FREEZE,
                account.amount,
                EscrowStatus.FROZEN,
                reference=f"escrow_frozen:{order.id}",
                note=reason,
            )
        return account

    @staticmethod
    def release_for_order(db: Session, order: Order, amount: float, fee: float = 0.0) -> EscrowAccount:
        account = EscrowAccountService.get_or_create_for_order(db, order)
        if account.status == EscrowStatus.RELEASED:
            return account
        if account.status not in {EscrowStatus.PENDING, EscrowStatus.FUNDED, EscrowStatus.FROZEN, EscrowStatus.PARTIAL_RELEASE}:
            raise HTTPException(status_code=400, detail=f"Cannot release escrow in {account.status.value} state")
        account.status = EscrowStatus.RELEASED
        account.released_at = datetime.now(timezone.utc)
        EscrowAccountService._record(
            db,
            account,
            EscrowTransactionType.RELEASE,
            amount,
            EscrowStatus.RELEASED,
            reference=f"escrow_released:{order.id}",
            metadata={"platform_fee": round(float(fee or 0), 2)},
        )
        return account

    @staticmethod
    def refund_for_order(db: Session, order: Order, amount: float) -> EscrowAccount:
        account = EscrowAccountService.get_or_create_for_order(db, order)
        if account.status == EscrowStatus.REFUNDED:
            return account
        if account.status not in {EscrowStatus.PENDING, EscrowStatus.FUNDED, EscrowStatus.FROZEN, EscrowStatus.PARTIAL_RELEASE}:
            raise HTTPException(status_code=400, detail=f"Cannot refund escrow in {account.status.value} state")
        account.status = EscrowStatus.REFUNDED
        account.refunded_at = datetime.now(timezone.utc)
        EscrowAccountService._record(
            db,
            account,
            EscrowTransactionType.REFUND,
            amount,
            EscrowStatus.REFUNDED,
            reference=f"escrow_refunded:{order.id}",
        )
        return account

    @staticmethod
    def partial_release_for_order(
        db: Session,
        order: Order,
        buyer_refund: float,
        seller_payout: float,
        fee: float,
    ) -> EscrowAccount:
        account = EscrowAccountService.get_or_create_for_order(db, order)
        if account.status == EscrowStatus.PARTIAL_RELEASE:
            return account
        if account.status not in {EscrowStatus.PENDING, EscrowStatus.FUNDED, EscrowStatus.FROZEN}:
            raise HTTPException(status_code=400, detail=f"Cannot split escrow in {account.status.value} state")
        account.status = EscrowStatus.PARTIAL_RELEASE
        account.released_at = datetime.now(timezone.utc)
        EscrowAccountService._record(
            db,
            account,
            EscrowTransactionType.PARTIAL_RELEASE,
            buyer_refund + seller_payout + fee,
            EscrowStatus.PARTIAL_RELEASE,
            reference=f"escrow_split:{order.id}",
            metadata={
                "buyer_refund": round(float(buyer_refund or 0), 2),
                "seller_payout": round(float(seller_payout or 0), 2),
                "platform_fee": round(float(fee or 0), 2),
            },
        )
        return account


escrow_account_service = EscrowAccountService()
