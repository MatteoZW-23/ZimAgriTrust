from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

import logging
import re
import bcrypt
import secrets
import hmac
import hashlib
import json

logger = logging.getLogger(__name__)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, AttributeError):
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)  # Increased rounds for better security
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT with strict algorithm enforcement.
    Explicitly rejects alg=none and requires all security claims.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],  # Only HS256 allowed - explicit whitelist
        options={
            "require": ["exp", "iat", "sub", "type"],
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "verify_nbf": True,
        }
    )


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_hex(length)


def generate_otp(length: int = 6) -> str:
    """Generate a one-time password (OTP)"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def validate_token_integrity(token: str, expected_user_id: str) -> bool:
    """Validate that token belongs to expected user"""
    try:
        payload = decode_token(token)
        return payload.get("sub") == expected_user_id
    except:
        return False


def check_password_strength(password: str) -> dict:
    """Check password strength against security requirements"""
    result = {
        "valid": True,
        "strength": "weak",
        "score": 0,
        "issues": []
    }
    
    # Length check
    if len(password) < 8:
        result["valid"] = False
        result["issues"].append("Password must be at least 8 characters")
    else:
        result["score"] += 20
    
    # Uppercase check
    if not re.search(r'[A-Z]', password):
        result["valid"] = False
        result["issues"].append("Password must contain uppercase letter")
    else:
        result["score"] += 20
    
    # Lowercase check
    if not re.search(r'[a-z]', password):
        result["valid"] = False
        result["issues"].append("Password must contain lowercase letter")
    else:
        result["score"] += 20
    
    # Digit check
    if not re.search(r'\d', password):
        result["valid"] = False
        result["issues"].append("Password must contain digit")
    else:
        result["score"] += 20
    
    # Special character check
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["valid"] = False
        result["issues"].append("Password must contain special character")
    else:
        result["score"] += 20
    
    # Determine strength
    if result["score"] >= 80:
        result["strength"] = "strong"
    elif result["score"] >= 60:
        result["strength"] = "medium"
    else:
        result["strength"] = "weak"
    
    return result


def is_common_password(password: str) -> bool:
    """Check if password is in common passwords list"""
    common_passwords = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'monkey', 'letmein', 'dragon', '111111', 'baseball',
        'iloveyou', 'master', 'sunshine', 'ashley', 'bailey',
        'passw0rd', 'admin', 'welcome', 'login', 'football'
    ]
    return password.lower() in [p.lower() for p in common_passwords]


def check_password_history(password: str, history: list[str] | None, max_history: int = 5) -> bool:
    """
    Check if password has been used before in the user's history.
    Returns True if password is NEW (not in history), False if reused.
    """
    if not history:
        return True
    recent = history[-max_history:]
    for old_hash in recent:
        if verify_password(password, old_hash):
            return False
    return True


def sign_request(payload: dict, secret: str = None) -> str:
    """
    Generate HMAC-SHA256 signature for webhook/request integrity.
    """
    key = secret or settings.HMAC_SECRET or settings.SECRET_KEY
    body = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hmac.new(key.encode(), body.encode(), hashlib.sha256).hexdigest()


def verify_request_signature(payload: dict, signature: str, secret: str = None) -> bool:
    """Verify HMAC-SHA256 signature for incoming webhooks."""
    expected = sign_request(payload, secret)
    return secrets.compare_digest(expected, signature)


def generate_email_verification_token() -> str:
    """Generate a secure email verification token."""
    return secrets.token_urlsafe(32)


def hash_sensitive_value(value: str) -> str:
    """One-way hash for logging sensitive data (e.g., last-4-digits of ID)."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]
