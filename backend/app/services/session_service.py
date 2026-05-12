"""
Session & Device Management Service
Handles concurrent session limits, device fingerprinting,
new-device alerts, and session revocation.
"""

import uuid
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.session import UserSession
from app.models.user import User
from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def compute_device_fingerprint(request_headers: dict, ip: str) -> str:
    """Generate a stable device fingerprint from request headers + IP."""
    components = [
        ip,
        request_headers.get("user-agent", ""),
        request_headers.get("accept-language", ""),
        request_headers.get("sec-ch-ua", ""),
        request_headers.get("sec-ch-ua-platform", ""),
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def create_session(
    db: Session,
    user_id: uuid.UUID,
    access_token_jti: str,
    refresh_token_jti: Optional[str],
    request_headers: dict,
    ip_address: str,
    access_expiry_minutes: int = 15,
    refresh_expiry_days: int = 30,
) -> UserSession:
    """Create a new user session after successful login."""

    fingerprint = compute_device_fingerprint(request_headers, ip_address) if settings.SESSION_FINGERPRINTING_ENABLED else None

    # Enforce concurrent session limit
    if settings.MAX_CONCURRENT_SESSIONS > 0:
        active_sessions = (
            db.query(UserSession)
            .filter(UserSession.user_id == user_id, UserSession.is_active == True)
            .order_by(desc(UserSession.last_active_at))
            .all()
        )
        # Revoke oldest sessions beyond the limit
        if len(active_sessions) >= settings.MAX_CONCURRENT_SESSIONS:
            to_revoke = active_sessions[settings.MAX_CONCURRENT_SESSIONS - 1:]
            for old in to_revoke:
                old.is_active = False
                old.revoked_at = datetime.now(timezone.utc)
                old.revoke_reason = "concurrent_limit"
                # Blacklist tokens
                await cache_service.set(f"blacklist_{old.access_token_jti}", "true", expire=3600)
                if old.refresh_token_jti:
                    await cache_service.set(f"blacklist_{old.refresh_token_jti}", "true", expire=7 * 24 * 3600)
            logger.info(f"Revoked {len(to_revoke)} old sessions for user {user_id}")
            db.commit()

    session = UserSession(
        user_id=user_id,
        access_token_jti=access_token_jti,
        refresh_token_jti=refresh_token_jti,
        device_fingerprint=fingerprint,
        user_agent=request_headers.get("user-agent", "")[:500],
        ip_address=ip_address,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=access_expiry_minutes),
        is_active=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # New-device detection
    if settings.NEW_DEVICE_ALERT and fingerprint:
        existing = (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.device_fingerprint == fingerprint,
                UserSession.is_active == True,
            )
            .first()
        )
        if not existing or existing.id == session.id:
            # Check if this fingerprint existed before (even if revoked)
            prior = (
                db.query(UserSession)
                .filter(
                    UserSession.user_id == user_id,
                    UserSession.device_fingerprint == fingerprint,
                    UserSession.id != session.id,
                )
                .first()
            )
            if not prior:
                logger.warning(f"NEW_DEVICE_ALERT | user={user_id} | ip={ip_address} | ua={request_headers.get('user-agent', '')[:80]}")
                # Store flag for notification async task
                await cache_service.set(
                    f"new_device:{user_id}:{session.id}",
                    f"{ip_address}|{request_headers.get('user-agent', '')[:200]}",
                    expire=3600,
                )

    return session


async def revoke_session(db: Session, session_id: uuid.UUID, reason: str = "logout") -> bool:
    """Revoke a specific session and blacklist its tokens."""
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session or not session.is_active:
        return False

    session.is_active = False
    session.revoked_at = datetime.now(timezone.utc)
    session.revoke_reason = reason
    db.commit()

    await cache_service.set(f"blacklist_{session.access_token_jti}", "true", expire=3600)
    if session.refresh_token_jti:
        await cache_service.set(f"blacklist_{session.refresh_token_jti}", "true", expire=7 * 24 * 3600)

    logger.info(f"Session revoked: {session_id} | user={session.user_id} | reason={reason}")
    return True


async def revoke_all_user_sessions(db: Session, user_id: uuid.UUID, except_session_id: Optional[uuid.UUID] = None, reason: str = "security_action") -> int:
    """Revoke all active sessions for a user (e.g., password change, suspension)."""
    query = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True,
    )
    if except_session_id:
        query = query.filter(UserSession.id != except_session_id)

    sessions = query.all()
    revoked_count = 0
    for session in sessions:
        session.is_active = False
        session.revoked_at = datetime.now(timezone.utc)
        session.revoke_reason = reason
        await cache_service.set(f"blacklist_{session.access_token_jti}", "true", expire=3600)
        if session.refresh_token_jti:
            await cache_service.set(f"blacklist_{session.refresh_token_jti}", "true", expire=7 * 24 * 3600)
        revoked_count += 1

    db.commit()
    logger.info(f"Revoked {revoked_count} sessions for user {user_id} | reason={reason}")
    return revoked_count


def get_active_sessions(db: Session, user_id: uuid.UUID) -> List[UserSession]:
    """List all active sessions for a user (for 'logout all devices' UI)."""
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.is_active == True)
        .order_by(desc(UserSession.last_active_at))
        .all()
    )


def update_session_activity(db: Session, session_id: uuid.UUID) -> None:
    """Update last_active timestamp on session."""
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        session.last_active_at = datetime.now(timezone.utc)
        db.commit()


def is_session_valid(db: Session, user_id: uuid.UUID, jti: str) -> bool:
    """Check if a session with the given JTI is still active."""
    session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user_id,
            UserSession.access_token_jti == jti,
            UserSession.is_active == True,
        )
        .first()
    )
    if not session:
        return False
    now = datetime.now(timezone.utc)
    if now > _as_utc(session.expires_at):
        # Auto-revoke expired session
        session.is_active = False
        session.revoked_at = now
        session.revoke_reason = "expired"
        db.commit()
        return False
    return True
