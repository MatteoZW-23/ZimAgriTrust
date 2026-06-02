"""
Security models for ZimAgriTrust cash-handling subsystem.

These tables are SEPARATE from the regular admin/user/transaction tables.

Tables:
- super_admins        : highest-privilege accounts (separate from admin_users)
- admin_approvals     : dual / multi approval workflow for refunds & high-value txns
- audit_checksums     : tamper-proof checksum chain over financial records
- fraud_alerts        : real-time fraud signals raised by detection service
- withdrawal_limits   : per-tier daily/weekly/monthly caps (DB-overridable)
- admin_action_logs   : signed log of admin actions (HMAC)
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ---------------------------------------------------------------------------
# Super Admin
# ---------------------------------------------------------------------------

class SuperAdmin(Base):
    """
    Highest privilege account. NEVER created via normal flow — only DB seed
    or by another super admin (with second super-admin co-approval).
    Stored in a dedicated table for blast-radius isolation.
    """
    __tablename__ = "super_admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Hardware MFA — TOTP secret OR YubiKey public ID
    hardware_mfa_secret: Mapped[Optional[str]] = mapped_column(String(255))
    yubikey_public_id: Mapped[Optional[str]] = mapped_column(String(64))

    # Public key for digital signature verification (RSA / Ed25519 PEM)
    public_key: Mapped[Optional[str]] = mapped_column(Text)

    ip_whitelist: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_root: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("super_admins.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Admin Approval workflow
# ---------------------------------------------------------------------------

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL_APPROVED = "partial_approved"
    FULLY_APPROVED = "fully_approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalAction(str, enum.Enum):
    REFUND = "refund"
    LARGE_TRANSACTION = "large_transaction"
    ESCROW_RELEASE = "escrow_release"
    ESCROW_OVERRIDE = "escrow_override"
    LIMIT_OVERRIDE = "limit_override"


class AdminLevel(int, enum.Enum):
    SUPPORT = 1   # view only, no payment approval
    FINANCE = 2   # up to $500
    SENIOR = 3    # up to $2000
    SUPER = 4     # unlimited (super_admin table only)


class AdminApproval(Base):
    """
    Dual / multi admin approval workflow.

    Required when:
      - Refund > DUAL_APPROVAL_REFUND_THRESHOLD_USD (default $100)
      - Any single transaction > MULTI_APPROVAL_TXN_THRESHOLD_USD (default $2000)
      - Limit overrides
    """
    __tablename__ = "admin_approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Generic reference — may be order_id, transaction_id, or any UUID resource
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "order", "transaction", "withdrawal"
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    action: Mapped[ApprovalAction] = mapped_column(Enum(ApprovalAction), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    reason: Mapped[Optional[str]] = mapped_column(Text)

    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    approved_by_1: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    approved_at_1: Mapped[Optional[datetime]] = mapped_column(DateTime)
    signature_1: Mapped[Optional[str]] = mapped_column(String(128))  # HMAC-SHA256 of decision

    approved_by_2: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    approved_at_2: Mapped[Optional[datetime]] = mapped_column(DateTime)
    signature_2: Mapped[Optional[str]] = mapped_column(String(128))

    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True
    )
    rejected_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    fully_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Snapshot of approval rules at request time (audit replay)
    rules_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)


# ---------------------------------------------------------------------------
# Tamper-proof Audit Chain
# ---------------------------------------------------------------------------

class AuditChecksum(Base):
    """
    Append-only checksum chain. Each new row's checksum incorporates the
    previous row's checksum forming a hash chain.
    Any retroactive mutation to a record is detectable by re-hashing the chain.
    """
    __tablename__ = "audit_checksums"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(16), nullable=False)  # INSERT/UPDATE/DELETE

    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # sha256 of payload
    previous_checksum: Mapped[Optional[str]] = mapped_column(String(64))
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Optional context
    actor_id: Mapped[Optional[str]] = mapped_column(String(64))
    actor_role: Mapped[Optional[str]] = mapped_column(String(32))
    payload_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ---------------------------------------------------------------------------
# Fraud Alerts
# ---------------------------------------------------------------------------

class FraudSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudAlertType(str, enum.Enum):
    VELOCITY = "velocity"                       # multiple withdrawals in short time
    STRUCTURING = "structuring"                 # amount just below limit
    NEW_USER_LARGE_WITHDRAWAL = "new_user_large_withdrawal"
    DUPLICATE_BANK_DETAILS = "duplicate_bank_details"
    TRUST_SCORE_SPIKE = "trust_score_spike"
    LIMIT_BREACH_ATTEMPT = "limit_breach_attempt"
    SIGNATURE_MISMATCH = "signature_mismatch"
    UNAUTHORIZED_OVERRIDE = "unauthorized_override"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), index=True)
    alert_type: Mapped[FraudAlertType] = mapped_column(Enum(FraudAlertType), nullable=False, index=True)
    severity: Mapped[FraudSeverity] = mapped_column(Enum(FraudSeverity), nullable=False, index=True)

    details: Mapped[Optional[dict]] = mapped_column(JSON)
    related_resource_type: Mapped[Optional[str]] = mapped_column(String(50))
    related_resource_id: Mapped[Optional[str]] = mapped_column(String(64))

    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("super_admins.id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    notified_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ---------------------------------------------------------------------------
# Withdrawal Limits
# ---------------------------------------------------------------------------

class UserTier(str, enum.Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    TRUSTED = "trusted"


class WithdrawalLimit(Base):
    """
    Per-tier withdrawal caps. Seeded with defaults in migration but can be
    overridden at runtime by super-admin.
    """
    __tablename__ = "withdrawal_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_tier: Mapped[UserTier] = mapped_column(Enum(UserTier), unique=True, nullable=False)

    daily_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    weekly_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    monthly_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    per_transaction_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    min_trust_score: Mapped[Optional[int]] = mapped_column(Integer)  # only relevant for TRUSTED tier
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("super_admins.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_tier", name="uq_withdrawal_limit_tier"),)


# ---------------------------------------------------------------------------
# Admin Action Log (signed)
# ---------------------------------------------------------------------------

class AdminActionLog(Base):
    """
    Append-only signed log of admin/super-admin actions on financial resources.
    The HMAC signature binds: actor + action + resource + amount + timestamp.
    """
    __tablename__ = "admin_action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_kind: Mapped[str] = mapped_column(String(20), nullable=False)  # "admin" | "super_admin"
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_level: Mapped[Optional[int]] = mapped_column(Integer)  # AdminLevel value

    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50))
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    currency: Mapped[Optional[str]] = mapped_column(String(5))

    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    request_id: Mapped[Optional[str]] = mapped_column(String(64))

    payload: Mapped[Optional[dict]] = mapped_column(JSON)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
