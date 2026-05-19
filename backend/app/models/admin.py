import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, JSON, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.security_enhanced import RoleLevel


class AdminRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    SYSTEM_ADMIN = "system_admin"
    FINANCE_ADMIN = "finance_admin"
    REGIONAL_ADMIN = "regional_admin"
    SUPPORT_ADMIN = "support_admin"
    BRANCH_ADMIN = "branch_admin"


class AdminUser(Base):
    """
    Dedicated Admin User model for ZimAgriTrust Admin Portal.
    Provides isolation from regular users and strict role hierarchy.
    """
    __tablename__ = "admin_users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    
    role: Mapped[AdminRole] = mapped_column(String(50), default=AdminRole.SUPPORT_ADMIN)
    role_level: Mapped[int] = mapped_column(Integer, default=70) # Linked to RoleLevel values
    
    region: Mapped[Optional[str]] = mapped_column(String(100)) # For REGIONAL_ADMIN
    branch_id: Mapped[Optional[int]] = mapped_column(Integer) # For BRANCH_ADMIN
    
    # MFA Settings
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255)) # Encrypted TOTP secret
    mfa_backup_codes: Mapped[Optional[List[str]]] = mapped_column(JSON) # Hashed backup codes
    
    # Hardware MFA (YubiKey / WebAuthn)
    hardware_mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    hardware_mfa_credential_id: Mapped[Optional[str]] = mapped_column(String(255))
    hardware_mfa_public_key: Mapped[Optional[str]] = mapped_column(String(1024))
    
    # Lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_password_change: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Audit & Onboarding
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    creator = relationship("AdminUser", remote_side=[id], back_populates="created_admins")
    created_admins = relationship("AdminUser", back_populates="creator", foreign_keys="AdminUser.created_by")
