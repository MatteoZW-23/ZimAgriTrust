"""
Super-Admin specific security primitives.

Distinct from regular auth:
- Separate signing key (config.SUPER_ADMIN_SECRET_KEY) — compromise of normal
  SECRET_KEY does NOT grant super-admin access.
- Stricter expiry (30 min default).
- Hardware MFA verification (TOTP / YubiKey OTP).
- Token type marker `"type": "super_admin_access"`.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings


SUPER_ADMIN_TOKEN_TYPE = "super_admin_access"
SUPER_ADMIN_PRE_MFA_TOKEN_TYPE = "super_admin_pre_mfa"


# ---------------------------------------------------------------------------
# JWT helpers (separate signing key)
# ---------------------------------------------------------------------------

def create_super_admin_token(super_admin_id: int, *, mfa_verified: bool = True) -> str:
    """Issue super-admin JWT with strict 30-min expiry, signed with dedicated key."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.SUPER_ADMIN_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(super_admin_id),
        "type": SUPER_ADMIN_TOKEN_TYPE,
        "mfa": bool(mfa_verified),
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.effective_super_admin_secret, algorithm=settings.ALGORITHM)


def create_super_admin_pre_mfa_token(super_admin_id: int) -> str:
    """Short-lived (5 min) token issued after password but before MFA verification."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=5)
    payload = {
        "sub": str(super_admin_id),
        "type": SUPER_ADMIN_PRE_MFA_TOKEN_TYPE,
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.effective_super_admin_secret, algorithm=settings.ALGORITHM)


def decode_super_admin_token(token: str) -> dict:
    """Decode and validate signature. Raises JWTError on tamper / expiry."""
    return jwt.decode(token, settings.effective_super_admin_secret, algorithms=[settings.ALGORITHM])


def is_valid_super_admin_token(token: str, *, require_mfa: bool = True) -> Optional[dict]:
    """Returns payload dict if valid + correct type, else None."""
    try:
        payload = decode_super_admin_token(token)
    except JWTError:
        return None
    if payload.get("type") != SUPER_ADMIN_TOKEN_TYPE:
        return None
    if require_mfa and not payload.get("mfa"):
        return None
    return payload


# ---------------------------------------------------------------------------
# TOTP (RFC 6238) — minimal stdlib implementation, no extra deps required
# ---------------------------------------------------------------------------

def _hotp(secret_b32: str, counter: int, digits: int = 6) -> str:
    key = base64.b32decode(secret_b32.upper() + "=" * ((8 - len(secret_b32) % 8) % 8))
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(code).zfill(digits)


def generate_totp_secret() -> str:
    """Generate a base32 TOTP secret (160-bit) suitable for Authenticator apps."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def verify_totp(secret_b32: str, code: str, *, window: int = 1, period: int = 30) -> bool:
    """Verify TOTP code with ±`window` periods of clock skew tolerance."""
    if not secret_b32 or not code or not code.isdigit():
        return False
    now = int(time.time() // period)
    for delta in range(-window, window + 1):
        expected = _hotp(secret_b32, now + delta, digits=len(code))
        if hmac.compare_digest(expected, code):
            return True
    return False


def totp_provisioning_uri(secret_b32: str, *, account_name: str, issuer: str = "ZimAgriTrust") -> str:
    """otpauth URI for QR-code provisioning into Authenticator apps."""
    from urllib.parse import quote
    return (
        f"otpauth://totp/{quote(issuer)}:{quote(account_name)}"
        f"?secret={secret_b32}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"
    )


# ---------------------------------------------------------------------------
# YubiKey OTP — basic shape verification (full validation requires Yubico API)
# ---------------------------------------------------------------------------

def yubikey_public_id(otp: str) -> Optional[str]:
    """
    YubiKey OTPs are 44 modhex chars; first 12 are the public identity.
    For full validation in production, call the Yubico verification API.
    For MVP we accept any well-formed OTP whose public ID matches the stored one.
    """
    if not otp or len(otp) < 32 or len(otp) > 48:
        return None
    if not all(c in "cbdefghijklnrtuv" for c in otp.lower()):
        return None
    return otp[:12].lower()


def verify_yubikey_otp(otp: str, expected_public_id: str) -> bool:
    pid = yubikey_public_id(otp)
    if not pid or not expected_public_id:
        return False
    return hmac.compare_digest(pid, expected_public_id.lower())


# ---------------------------------------------------------------------------
# IP whitelist enforcement
# ---------------------------------------------------------------------------

def super_admin_ip_allowed(client_ip: str, account_whitelist: Optional[list[str]] = None) -> bool:
    """
    Allow if (a) global SUPER_ADMIN_IP_WHITELIST is empty AND no per-account
    whitelist set (dev mode), OR (b) IP appears in either list.
    Loopback always allowed when global whitelist empty.
    """
    global_wl = settings.super_admin_ip_whitelist_list
    account_wl = account_whitelist or []

    if not global_wl and not account_wl:
        return True  # disabled — typical dev environment

    candidates = set(global_wl) | set(account_wl)
    if client_ip in candidates:
        return True
    if client_ip in {"127.0.0.1", "::1"} and ("localhost" in candidates or "127.0.0.1" in candidates):
        return True
    return False
