"""
Enhanced security models for ZimAgriTrust with:
- Unified PIN system (USSD + App)
- Multi-layer authentication
- Session management
- Token management
- Audit logging
- Rate limiting & threat detection
"""
import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


# ============================================================================
# ROLE HIERARCHY (Level-based inheritance)
# ============================================================================

class RoleLevel(int, enum.Enum):
    """Role hierarchy levels - higher number = more privileged"""
    FARMER = 10
    BUYER = 10
    DRIVER = 20
    STAFF = 30
    AGENT = 40
    SUPPLIER = 60
    BRANCH_ADMIN = 70
    SUPPORT_ADMIN = 75
    REGIONAL_ADMIN = 80
    FINANCE_ADMIN = 85
    SYSTEM_ADMIN = 90
    ADMIN = 100
    SUPER_ADMIN = 100


# ============================================================================
# PIN SECURITY & MANAGEMENT
# ============================================================================

class PINStatus(str, enum.Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    EXPIRED = "expired"


class PINHistory(Base):
    """Track PIN changes for audit and reuse prevention"""
    __tablename__ = "pin_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # bcrypt + pepper
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    change_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'user_initiated', 'forced_change', 'compromised'
    changed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class PINLockout(Base):
    """Track PIN attempt lockouts (unified USSD + App)"""
    __tablename__ = "pin_lockout"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lockout_count: Mapped[int] = mapped_column(Integer, default=0)  # Number of lockouts (reset after 3)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=False)


class PINAttempt(Base):
    """Audit trail of PIN attempts across USSD and App"""
    __tablename__ = "pin_attempt"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # 'ussd', 'app'
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


# ============================================================================
# TOKEN MANAGEMENT (JWT + Refresh tokens)
# ============================================================================

class TokenType(str, enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "password_reset"
    INVITATION = "invitation"
    MFA = "mfa"


class TokenBlacklist(Base):
    """Revoked tokens (for logout, password changes, etc)"""
    __tablename__ = "token_blacklist"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    token_type: Mapped[TokenType] = mapped_column(Enum(TokenType), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


# ============================================================================
# MFA (Multi-Factor Authentication)
# ============================================================================

class MFAMethod(str, enum.Enum):
    TOTP = "totp"  # Time-based One-Time Password (Authenticator App)
    HARDWARE = "hardware"  # YubiKey / WebAuthn
    SMS = "sms"  # Recovery only


class MFAStatus(str, enum.Enum):
    SETUP_IN_PROGRESS = "setup_in_progress"
    ACTIVE = "active"
    DISABLED = "disabled"


class MFAConfiguration(Base):
    """MFA settings per user"""
    __tablename__ = "mfa_configurations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # TOTP Method
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Encrypted
    totp_backup_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)  # List of hashed backup codes
    
    # Hardware MFA
    yubikey_public_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    webauthn_credential_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # SMS Recovery
    recovery_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    
    # Status
    status: Mapped[MFAStatus] = mapped_column(Enum(MFAStatus), default=MFAStatus.DISABLED, nullable=False)
    enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=False)


class MFAAttempt(Base):
    """Audit trail of MFA verification attempts"""
    __tablename__ = "mfa_attempt"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    method: Mapped[MFAMethod] = mapped_column(Enum(MFAMethod), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


# ============================================================================
# RATE LIMITING & THREAT DETECTION
# ============================================================================

class RateLimitKey(str, enum.Enum):
    LOGIN_ATTEMPTS = "login_attempts"
    PASSWORD_RESET = "password_reset"
    PIN_ATTEMPTS = "pin_attempts"
    MFA_ATTEMPTS = "mfa_attempts"
    OTP_REQUESTS = "otp_requests"
    API_GENERAL = "api_general"
    WITHDRAWALS = "withdrawals"
    DEPOSITS = "deposits"


class RateLimit(Base):
    """Track rate limit hits (stored in Redis for performance)"""
    __tablename__ = "rate_limits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # User ID or IP
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class SecurityThreat(Base):
    """Log security threats for analysis"""
    __tablename__ = "security_threats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    threat_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'brute_force', 'suspicious_login', 'abnormal_activity'
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ============================================================================
# AUDIT LOGGING (Immutable audit trail)
# ============================================================================

class AuditLogAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PIN_CHANGE = "pin_change"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLE = "mfa_enable"
    MFA_DISABLE = "mfa_disable"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    ROLE_CHANGED = "role_changed"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ADMIN_ACTION = "admin_action"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"


class SecurityAuditLog(Base):
    """Immutable audit trail of all security events"""
    __tablename__ = "security_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action: Mapped[AuditLogAction] = mapped_column(Enum(AuditLogAction), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Admin who performed action
    
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # 'user', 'transaction', 'role'
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Event details
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success")  # 'success', 'failure', 'warning'
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timestamp (immutable)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_audit_logs_user_action', 'user_id', 'action'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id'),
    )


# ============================================================================
# NOTIFICATION PREFERENCES & TRACKING
# ============================================================================

class NotificationChannel(str, enum.Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class NotificationCategory(str, enum.Enum):
    AUTH_SECURITY = "auth_security"
    TRANSACTION_PAYMENT = "transaction_payment"
    LISTING_INPUT = "listing_input"
    DELIVERY_LOGISTICS = "delivery_logistics"
    DISPUTE_SUPPORT = "dispute_support"
    VERIFICATION_KYC = "verification_kyc"
    AGENT_DRIVER = "agent_driver"
    ADMIN_SYSTEM = "admin_system"


class NotificationPreference(Base):
    """User notification preferences per channel & category"""
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Per-channel settings
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Per-category settings (JSON for flexibility)
    category_preferences: Mapped[dict] = mapped_column(JSON, default={})
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=False)


class NotificationLog(Base):
    """Audit trail of all notifications sent"""
    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    category: Mapped[NotificationCategory] = mapped_column(Enum(NotificationCategory), nullable=False)
    
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)  # Phone, WhatsApp ID, or email
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Delivery tracking
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'sent', 'failed', 'delivered'
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Response tracking
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_notification_logs_user_status', 'user_id', 'status'),
    )


# ============================================================================
# PASSWORD & CREDENTIAL SECURITY
# ============================================================================

class PasswordHistory(Base):
    """Prevent password reuse (last 5 passwords)"""
    __tablename__ = "password_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BreachedCredential(Base):
    """Track potentially compromised credentials (checked against HaveIBeenPwned)"""
    __tablename__ = "breached_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    breach_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'password', 'email', 'phone'
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    remediated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    breach_source: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g., 'HaveIBeenPwned'
    remediation_action: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 'password_reset', 'email_verified'
