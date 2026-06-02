import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EscrowStatus(str, enum.Enum):
    PENDING = "PENDING"
    FUNDED = "FUNDED"
    FROZEN = "FROZEN"
    PARTIAL_RELEASE = "PARTIAL_RELEASE"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class EscrowTransactionType(str, enum.Enum):
    FUND = "FUND"
    FREEZE = "FREEZE"
    RELEASE = "RELEASE"
    PARTIAL_RELEASE = "PARTIAL_RELEASE"
    REFUND = "REFUND"
    CANCEL = "CANCEL"


class EscrowAccount(Base):
    __tablename__ = "escrow_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=True, index=True)
    supplier_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("supplier_orders.id"), unique=True, nullable=True, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    seller_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("supplier_profiles.id"), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    status: Mapped[EscrowStatus] = mapped_column(Enum(EscrowStatus, native_enum=False), default=EscrowStatus.PENDING, index=True)
    funded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    frozen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="escrow_account")
    supplier_order = relationship("SupplierOrder")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])
    supplier = relationship("SupplierProfile")
    transactions = relationship("EscrowTransaction", back_populates="escrow_account", cascade="all, delete-orphan")


class EscrowTransaction(Base):
    __tablename__ = "escrow_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escrow_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("escrow_accounts.id"), nullable=False, index=True)
    transaction_type: Mapped[EscrowTransactionType] = mapped_column(Enum(EscrowTransactionType, native_enum=False), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    status: Mapped[EscrowStatus] = mapped_column(Enum(EscrowStatus, native_enum=False), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transaction_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    escrow_account = relationship("EscrowAccount", back_populates="transactions")
    created_by_user = relationship("User", foreign_keys=[created_by])
