from collections.abc import Generator
from types import SimpleNamespace

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

from app.services.cache_service import cache_service


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "bearer" and credentials:
            token = credentials.strip()
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    # ── Try super-admin JWT first (separate signing key) ──────────────────────
    try:
        from app.core.super_admin_security import is_valid_super_admin_token
        from app.models.security import SuperAdmin

        sa_payload = is_valid_super_admin_token(token, require_mfa=True)
        if sa_payload is not None:
            sa = db.query(SuperAdmin).filter(
                SuperAdmin.id == int(sa_payload["sub"])
            ).first()
            if sa and sa.is_active:
                from app.models.user import SubscriptionTier, UserStatus
                virtual = SimpleNamespace(
                    id=str(sa.id),
                    full_name=sa.username,
                    phone_number=sa.phone_number or "",
                    email=sa.email,
                    role=UserRole.SUPER_ADMIN,
                    is_active=True,
                    is_suspended=False,
                    is_phone_verified=True,
                    trust_score=100,
                    must_change_password=False,
                    status=UserStatus.ACTIVE,
                    password_hash="",
                    mfa_enabled=True,
                    subscription_tier=SubscriptionTier.ENTERPRISE,
                    subscription_expires_at=None,
                    balance_usd=0.0,
                    balance_zig=0.0,
                    pending_usd=0.0,
                    pending_zig=0.0,
                )
                return virtual
    except (ValueError, TypeError, KeyError):
        raise credentials_exception

    # ── Regular user JWT ──────────────────────────────────────────────────────
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        jti: str | None = payload.get("jti")

        if user_id is None or token_type != "access":
            raise credentials_exception

        # Check Redis blacklist (immediate revocation)
        is_blacklisted = await cache_service.get(f"blacklist_{jti}")
        if is_blacklisted:
            raise credentials_exception

        from app.services.session_service import is_session_valid, update_session_activity

        if not is_session_valid(db, user_id, jti):
            raise credentials_exception
        from app.models.session import UserSession

        session = db.query(UserSession).filter(UserSession.access_token_jti == jti).first()
        if session:
            update_session_activity(db, session.id)

    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended pending review",
        )
    return user


def require_roles(*roles: UserRole):
    def dependency(user: User = Depends(get_current_user)) -> User:
        allowed_roles = set(roles)
        if UserRole.ADMIN in allowed_roles:
            allowed_roles.update({UserRole.SUPER_ADMIN, UserRole.REGIONAL_MANAGER})
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
        return user

    return dependency


def get_current_agent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Agent:
    """Dependency to get the agent profile for the current user"""
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user does not have an associated agent profile"
        )
    
    if agent.status == AgentStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACADEMY_DISMISSAL: Access denied. Your certification candidacy has been terminated."
        )
        
    return agent


def check_lockdown(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    """
    Enforces 'Read-Only' mode during an Emergency Lockdown.
    Admins are exempted from the lockdown to allow for resolution.
    """
    from app.models.system_config import SystemConfig
    lockdown = db.query(SystemConfig).filter(SystemConfig.key == "SYSTEM_LOCKDOWN").first()
    
    if lockdown and lockdown.value == "true" and current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PLATFORM_LOCKDOWN: The system is currently in emergency read-only mode."
        )
    return True
