from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PayoutMethodType(str, enum.Enum):
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    INNBUCKS = "innbucks"
    OMARI = "omari"
    BANK_ACCOUNT = "bank_account"
    BANK_TRANSFER = "bank_transfer"


class PayoutMethodProvider(str, enum.Enum):
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    INNBUCKS = "innbucks"
    OMARI = "omari"
    BANK = "bank"
    BANK_TRANSFER = "bank_transfer"


class PayoutMethodStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    DISABLED = "DISABLED"


class UserPayoutMethod(Base):
    __tablename__ = "user_payout_methods"
    __table_args__ = (
        UniqueConstraint("user_id", "method_type", "provider", "account_number", name="uq_user_payout_method_identity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    method_type: Mapped[PayoutMethodType] = mapped_column(Enum(PayoutMethodType), nullable=False)
    provider: Mapped[PayoutMethodProvider] = mapped_column(Enum(PayoutMethodProvider), nullable=False)
    account_name: Mapped[str] = mapped_column(String(150), nullable=False)
    account_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    branch_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[PayoutMethodStatus] = mapped_column(Enum(PayoutMethodStatus), default=PayoutMethodStatus.PENDING, nullable=False, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verification_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
