"""
Core security service for ZimAgriTrust
Handles PIN, passwords, tokens, sessions, and MFA
"""
import secrets
import hashlib
import hmac
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, List
import uuid

from jose import jwt
from passlib.context import CryptContext
import qrcode
import io
from functools import lru_cache

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.config import settings
from app.models.user import User
from app.models.security_enhanced import (
    PINHistory, PINLockout, PINAttempt,
    TokenBlacklist, TokenType, MFAConfiguration, MFAStatus, MFAAttempt,
    MFAMethod, SecurityAuditLog, AuditLogAction, SecurityThreat, RateLimit, RateLimitKey,
    PasswordHistory, BreachedCredential
)
from app.models.session import UserSession


# ============================================================================
# PASSWORD & PIN HASHING
# ============================================================================

class PasswordHasher:
    """Secure password hashing with Argon2id (preferred) or bcrypt"""
    
    def __init__(self):
        # Try Argon2id, fallback to bcrypt
        try:
            self.context = CryptContext(
                schemes=["argon2", "bcrypt"],
                deprecated="auto",
                argon2__memory_cost=65536,  # 64MB
                argon2__time_cost=3,
                argon2__parallelism=4,
                bcrypt__rounds=12,
            )
            self.uses_argon2 = True
        except Exception:
            self.context = CryptContext(
                schemes=["bcrypt"],
                deprecated="auto",
                bcrypt__rounds=12,
            )
            self.uses_argon2 = False
    
    def hash_password(self, password: str) -> str:
        """Hash password with Argon2id or bcrypt"""
        return self.context.hash(password)
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password"""
        return self.context.verify(password, password_hash)
    
    def hash_needs_update(self, password_hash: str) -> bool:
        """Check if hash should be re-hashed with updated algorithm"""
        return self.context.needs_update(password_hash)


class PINHasher:
    """Secure PIN hashing with bcrypt + pepper"""
    
    def __init__(self, pepper: str = None):
        self.context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12,
        )
        self.pepper = pepper or settings.PIN_PEPPER  # From environment
    
    def hash_pin(self, pin: str) -> str:
        """Hash PIN with pepper"""
        peppered_pin = f"{pin}{self.pepper}"
        return self.context.hash(peppered_pin)
    
    def verify_pin(self, pin: str, pin_hash: str) -> bool:
        """Verify PIN"""
        peppered_pin = f"{pin}{self.pepper}"
        return self.context.verify(peppered_pin, pin_hash)


# ============================================================================
# PIN VALIDATION & SECURITY
# ============================================================================

class PINValidator:
    """Validate PIN requirements"""
    
    MIN_LENGTH = 4
    MAX_LENGTH = 6
    
    # Common patterns to reject
    SEQUENTIAL_PATTERNS = [
        '1234', '2345', '3456', '4567', '5678', '6789',  # Ascending
        '9876', '8765', '7654', '6543', '5432', '4321',  # Descending
    ]
    
    REPEATED_PATTERNS = ['1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888', '9999', '0000']
    
    @classmethod
    def is_valid(cls, pin: str, phone_number: str = None, birthdate: str = None) -> Tuple[bool, Optional[str]]:
        """
        Validate PIN meets all requirements
        Returns: (is_valid, error_message)
        """
        # Check length
        if not pin.isdigit():
            return False, "PIN must contain only digits"
        
        if len(pin) < cls.MIN_LENGTH or len(pin) > cls.MAX_LENGTH:
            return False, f"PIN must be {cls.MIN_LENGTH}-{cls.MAX_LENGTH} digits"
        
        # Check sequential patterns
        if any(pattern in pin for pattern in cls.SEQUENTIAL_PATTERNS):
            return False, "PIN cannot contain sequential digits (1234, 5678, etc)"
        
        # Check repeated digits
        if any(pattern in pin for pattern in cls.REPEATED_PATTERNS):
            return False, "PIN cannot contain repeated digits (1111, 2222, etc)"
        
        # Check against phone number
        if phone_number:
            # Extract last 4 digits of phone
            phone_digits = ''.join(filter(str.isdigit, phone_number))[-4:]
            if phone_digits in pin:
                return False, "PIN cannot contain phone number digits"
        
        # Check against birth year
        if birthdate:
            try:
                year = birthdate.split('-')[0]  # YYYY-MM-DD format
                if year in pin:
                    return False, "PIN cannot contain birth year"
            except:
                pass
        
        # Check minimum entropy (at least 3 different digits)
        if len(set(pin)) < 3:
            return False, "PIN must contain at least 3 different digits"
        
        return True, None


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Manage user sessions with device tracking and concurrency limits"""
    
    # Session expiry times by role (in minutes)
    SESSION_TIMEOUT = {
        'SUPER_ADMIN': 15,
        'SYSTEM_ADMIN': 30,
        'FINANCE_ADMIN': 30,
        'REGIONAL_ADMIN': 30,
        'SUPPORT_ADMIN': 60,
        'BRANCH_ADMIN': 60,
        'AGENT': 480,  # 8 hours
        'STAFF': 60,
        'FARMER': 60,
        'BUYER': 60,
        'DRIVER': 60,
    }
    
    # Max concurrent sessions by role
    MAX_SESSIONS = {
        'SUPER_ADMIN': 1,
        'SYSTEM_ADMIN': 2,
        'FINANCE_ADMIN': 2,
        'REGIONAL_ADMIN': 3,
        'SUPPORT_ADMIN': 5,
        'BRANCH_ADMIN': 5,
        'AGENT': 1,
        'STAFF': 3,
        'FARMER': None,  # Unlimited
        'BUYER': None,
        'DRIVER': 1,
    }
    
    @staticmethod
    def create_session(
        db: Session,
        user: User,
        access_token_hash: str,
        refresh_token_hash: str,
        ip_address: str,
        device_fingerprint: str,
        user_agent: str = None,
        platform: str = None,
    ) -> UserSession:
        """Create new user session with device tracking"""
        
        role = user.role.value if hasattr(user.role, 'value') else str(user.role).upper()
        timeout_minutes = SessionManager.SESSION_TIMEOUT.get(role, 60)
        
        session = UserSession(
            user_id=user.id,
            access_token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            user_agent=user_agent,
            platform=platform,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes),
        )
        
        db.add(session)
        db.commit()
        return session
    
    @staticmethod
    def enforce_concurrency_limit(db: Session, user: User) -> bool:
        """
        Enforce max concurrent sessions per role
        Returns True if limit enforced, False otherwise
        """
        role = user.role.value if hasattr(user.role, 'value') else str(user.role).upper()
        max_sessions = SessionManager.MAX_SESSIONS.get(role)
        
        if max_sessions is None:  # Unlimited
            return False
        
        # Count active sessions
        active_sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user.id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        ).count()
        
        if active_sessions >= max_sessions:
            # Terminate oldest session
            oldest_session = db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user.id,
                    UserSession.is_active == True,
                )
            ).order_by(UserSession.created_at).first()
            
            if oldest_session:
                oldest_session.is_active = False
                oldest_session.revoked_at = datetime.now(timezone.utc)
                oldest_session.revoke_reason = 'max_sessions_exceeded'
                db.commit()
            
            return True
        
        return False
    
    @staticmethod
    def terminate_session(db: Session, session_id: uuid.UUID, reason: str = "logout"):
        """Terminate a session"""
        session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if session:
            session.is_active = False
            session.revoked_at = datetime.now(timezone.utc)
            session.revoke_reason = reason
            db.commit()
    
    @staticmethod
    def get_active_sessions(db: Session, user_id: uuid.UUID) -> List[UserSession]:
        """Get all active sessions for a user"""
        return db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        ).all()
    
    @staticmethod
    def terminate_all_sessions(db: Session, user_id: uuid.UUID, reason: str = "manual"):
        """Terminate all active sessions for a user"""
        sessions = SessionManager.get_active_sessions(db, user_id)
        for session in sessions:
            SessionManager.terminate_session(db, session.id, reason)


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

class TokenManager:
    """Manage JWT tokens with rotation and blacklisting"""
    
    TOKEN_EXPIRY = {
        TokenType.ACCESS: {
            'SUPER_ADMIN': 15,
            'SYSTEM_ADMIN': 30,
            'FINANCE_ADMIN': 30,
            'REGIONAL_ADMIN': 30,
            'SUPPORT_ADMIN': 60,
            'BRANCH_ADMIN': 60,
            'AGENT': 480,  # 8 hours
            'STAFF': 60,
            'FARMER': 60,
            'BUYER': 60,
            'DRIVER': 60,
        },
        TokenType.REFRESH: {
            'SUPER_ADMIN': 10080,  # 7 days
            'SYSTEM_ADMIN': 10080,
            'FINANCE_ADMIN': 10080,
            'REGIONAL_ADMIN': 10080,
            'SUPPORT_ADMIN': 20160,  # 14 days
            'BRANCH_ADMIN': 20160,
            'AGENT': 43200,  # 30 days
            'STAFF': 20160,
            'FARMER': 43200,
            'BUYER': 43200,
            'DRIVER': 43200,
        },
        TokenType.RESET: 60,  # 1 hour for all
        TokenType.INVITATION: 4320,  # 72 hours for all
    }
    
    @staticmethod
    def create_access_token(user: User, session_id: uuid.UUID = None) -> Tuple[str, datetime]:
        """Create JWT access token"""
        role = user.role.value if hasattr(user.role, 'value') else str(user.role).upper()
        expires_in = TokenManager.TOKEN_EXPIRY[TokenType.ACCESS].get(role, 60)
        
        payload = {
            'sub': str(user.id),
            'email': user.email,
            'role': role,
            'type': TokenType.ACCESS.value,
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        }
        
        if session_id:
            payload['sid'] = str(session_id)
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return token, payload['exp']
    
    @staticmethod
    def create_refresh_token(user: User, session_id: uuid.UUID = None) -> Tuple[str, datetime]:
        """Create JWT refresh token"""
        role = user.role.value if hasattr(user.role, 'value') else str(user.role).upper()
        expires_in = TokenManager.TOKEN_EXPIRY[TokenType.REFRESH].get(role, 10080)
        
        payload = {
            'sub': str(user.id),
            'role': role,
            'type': TokenType.REFRESH.value,
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        }
        
        if session_id:
            payload['sid'] = str(session_id)
        
        token = jwt.encode(
            payload,
            settings.REFRESH_SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return token, payload['exp']
    
    @staticmethod
    def create_password_reset_token(user: User) -> Tuple[str, datetime]:
        """Create password reset token"""
        expires_in = TokenManager.TOKEN_EXPIRY[TokenType.RESET]
        
        payload = {
            'sub': str(user.id),
            'type': TokenType.RESET.value,
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_in),
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return token, payload['exp']
    
    @staticmethod
    def verify_token(token: str, token_type: TokenType = TokenType.ACCESS) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            secret_key = settings.REFRESH_SECRET_KEY if token_type == TokenType.REFRESH else settings.SECRET_KEY
            
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[settings.ALGORITHM]
            )
            
            # Verify token type
            if payload.get('type') != token_type.value:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def blacklist_token(db: Session, token: str, token_type: TokenType, user_id: uuid.UUID):
        """Blacklist a token (for logout, password change, etc)"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Decode to get expiry
        payload = jwt.decode(
            token,
            settings.SECRET_KEY if token_type != TokenType.REFRESH else settings.REFRESH_SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        
        blacklist_entry = TokenBlacklist(
            token_hash=token_hash,
            token_type=token_type,
            user_id=user_id,
            expires_at=datetime.fromtimestamp(payload['exp']),
        )
        
        db.add(blacklist_entry)
        db.commit()
    
    @staticmethod
    def is_token_blacklisted(db: Session, token: str) -> bool:
        """Check if token is blacklisted"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        entry = db.query(TokenBlacklist).filter(
            TokenBlacklist.token_hash == token_hash
        ).first()
        
        return entry is not None


# ============================================================================
# PIN MANAGEMENT
# ============================================================================

class PINManager:
    """Manage unified PIN system (USSD + App)"""
    
    @staticmethod
    def create_pin(db: Session, user: User, pin: str, change_reason: str = "initial_setup"):
        """Create or change PIN"""
        
        # Validate PIN
        is_valid, error = PINValidator.is_valid(pin, user.phone_number)
        if not is_valid:
            raise ValueError(error)
        
        # Hash PIN
        hasher = PINHasher()
        pin_hash = hasher.hash_pin(pin)
        
        # Store in history
        history = PINHistory(
            user_id=user.id,
            pin_hash=pin_hash,
            change_reason=change_reason,
            created_at=datetime.now(timezone.utc),
        )
        
        # Check for reuse (last 3 PINs)
        last_pins = db.query(PINHistory).filter(
            PINHistory.user_id == user.id
        ).order_by(PINHistory.created_at.desc()).limit(3).all()
        
        for old_pin_record in last_pins:
            if hasher.verify_pin(pin, old_pin_record.pin_hash):
                raise ValueError("Cannot reuse last 3 PINs")
        
        # Update user
        user.ussd_pin_hash = pin_hash
        
        # Reset lockout
        lockout = db.query(PINLockout).filter(PINLockout.user_id == user.id).first()
        if lockout:
            lockout.failed_attempts = 0
            lockout.locked_until = None
            lockout.lockout_count = 0
        
        db.add(history)
        db.commit()
        
        return history
    
    @staticmethod
    def verify_pin(db: Session, user: User, pin: str, channel: str = "app", ip_address: str = None) -> Tuple[bool, Optional[str]]:
        """
        Verify PIN (unified USSD + App)
        Returns: (is_valid, error_message)
        """
        
        # Check if account is locked
        lockout = db.query(PINLockout).filter(PINLockout.user_id == user.id).first()
        
        if lockout and lockout.locked_until and lockout.locked_until > datetime.now(timezone.utc):
            return False, f"Account locked until {lockout.locked_until}. Contact support."
        
        # Check if user has PIN set
        if not user.ussd_pin_hash:
            return False, "PIN not set. Contact support."
        
        # Verify PIN
        hasher = PINHasher()
        is_valid = hasher.verify_pin(pin, user.ussd_pin_hash)
        
        # Record attempt
        attempt = PINAttempt(
            user_id=user.id,
            channel=channel,
            success=is_valid,
            ip_address=ip_address,
        )
        db.add(attempt)
        
        if is_valid:
            # Reset failed attempts
            if lockout:
                lockout.failed_attempts = 0
                lockout.locked_until = None
            db.commit()
            return True, None
        else:
            # Increment failed attempts
            if not lockout:
                lockout = PINLockout(user_id=user.id, failed_attempts=0)
                db.add(lockout)
            
            lockout.failed_attempts += 1
            lockout.last_attempt_at = datetime.now(timezone.utc)
            
            # Lock after 3 failed attempts
            if lockout.failed_attempts >= 3:
                lockout.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                lockout.lockout_count += 1
                db.commit()
                
                # Log security threat
                threat = SecurityThreat(
                    threat_type="pin_brute_force",
                    severity="high" if lockout.lockout_count >= 3 else "medium",
                    user_id=user.id,
                    ip_address=ip_address,
                    details={
                        "channel": channel,
                        "attempts": lockout.failed_attempts,
                        "lockout_count": lockout.lockout_count,
                    }
                )
                db.add(threat)
                db.commit()
                
                return False, "Account locked due to too many failed attempts. Try again in 15 minutes or contact support."
            
            db.commit()
            return False, f"Invalid PIN. {3 - lockout.failed_attempts} attempts remaining."


# ============================================================================
# MFA MANAGEMENT
# ============================================================================

class MFAManager:
    """Manage multi-factor authentication (TOTP, Hardware, SMS)"""
    
    @staticmethod
    def generate_totp_secret() -> str:
        """Generate TOTP secret (base32 encoded)"""
        return secrets.token_hex(20)
    
    @staticmethod
    def generate_qr_code(user_email: str, secret: str, issuer: str = "ZimAgriTrust") -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = f"otpauth://totp/{user_email}?secret={secret}&issuer={issuer}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        import base64
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            code = '-'.join(secrets.token_hex(2).upper() for _ in range(3))
            codes.append(code)
        return codes
    
    @staticmethod
    def hash_backup_code(code: str) -> str:
        """Hash backup code"""
        context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
        return context.hash(code)
    
    @staticmethod
    def enable_mfa(db: Session, user: User, method: MFAMethod = MFAMethod.TOTP) -> Dict:
        """Enable MFA for user"""
        
        config = db.query(MFAConfiguration).filter(MFAConfiguration.user_id == user.id).first()
        
        if not config:
            config = MFAConfiguration(user_id=user.id)
            db.add(config)
        
        if method == MFAMethod.TOTP:
            secret = MFAManager.generate_totp_secret()
            qr_code = MFAManager.generate_qr_code(user.email or user.phone_number, secret)
            backup_codes = MFAManager.generate_backup_codes()
            
            config.totp_secret = secret
            config.totp_backup_codes = [MFAManager.hash_backup_code(code) for code in backup_codes]
            config.status = MFAStatus.SETUP_IN_PROGRESS
            
            db.commit()
            
            return {
                "secret": secret,
                "qr_code": qr_code,
                "backup_codes": backup_codes,
            }
        
        return {}
    
    @staticmethod
    def verify_mfa(db: Session, user: User, code: str, method: MFAMethod = MFAMethod.TOTP) -> bool:
        """Verify MFA code"""
        
        config = db.query(MFAConfiguration).filter(
            and_(
                MFAConfiguration.user_id == user.id,
                MFAConfiguration.status == MFAStatus.ACTIVE,
            )
        ).first()
        
        if not config:
            return False
        
        if method == MFAMethod.TOTP:
            # TOTP verification using pyotp
            try:
                import pyotp
                totp = pyotp.TOTP(config.secret)
                return totp.verify(code, valid_window=1)
            except ImportError:
                logger.warning("pyotp not installed, TOTP verification unavailable")
                return False
            except Exception as e:
                logger.error(f"TOTP verification failed: {e}")
                return False
        
        return False


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Log security events to audit trail"""
    
    @staticmethod
    def log(
        db: Session,
        action: AuditLogAction,
        user_id: uuid.UUID = None,
        actor_id: uuid.UUID = None,
        resource_type: str = None,
        resource_id: uuid.UUID = None,
        ip_address: str = None,
        details: Dict = None,
        status: str = "success",
    ):
        """Log audit event"""
        
        log_entry = AuditLog(
            action=action,
            user_id=user_id,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details or {},
            status=status,
        )
        
        db.add(log_entry)
        db.commit()


# ============================================================================
# DEVICE FINGERPRINTING
# ============================================================================

class DeviceFingerprint:
    """Generate consistent device fingerprint"""
    
    @staticmethod
    def generate(
        user_agent: str,
        platform: str = None,
        device_id: str = None,
    ) -> str:
        """Generate device fingerprint"""
        
        fingerprint_data = f"{user_agent}|{platform or 'unknown'}|{device_id or 'unknown'}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Rate limit security-sensitive operations"""
    
    # Default limits (requests per hour)
    DEFAULT_LIMITS = {
        RateLimitKey.LOGIN_ATTEMPTS: 5,
        RateLimitKey.PASSWORD_RESET: 3,
        RateLimitKey.PIN_ATTEMPTS: 5,
        RateLimitKey.OTP_REQUESTS: 3,
        RateLimitKey.MFA_ATTEMPTS: 10,
    }
    
    @staticmethod
    def check_limit(
        db: Session,
        identifier: str,
        key: RateLimitKey,
        limit: int = None,
        window_minutes: int = 60,
    ) -> Tuple[bool, int]:
        """
        Check if identifier is within rate limit
        Returns: (is_allowed, remaining)
        """
        
        if limit is None:
            limit = RateLimiter.DEFAULT_LIMITS.get(key, 100)
        
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        
        # Count requests in window
        count = db.query(RateLimit).filter(
            and_(
                RateLimit.identifier == identifier,
                RateLimit.key == key.value,
                RateLimit.window_start >= window_start,
            )
        ).count()
        
        if count >= limit:
            return False, 0
        
        return True, limit - count
    
    @staticmethod
    def record_attempt(
        db: Session,
        identifier: str,
        key: RateLimitKey,
        window_minutes: int = 60,
    ):
        """Record rate limit attempt"""
        
        rate_limit = RateLimit(
            identifier=identifier,
            key=key.value,
            window_start=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=window_minutes),
        )
        
        db.add(rate_limit)
        db.commit()
