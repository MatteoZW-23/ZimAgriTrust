from collections.abc import Generator

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
    
    token = request.cookies.get("access_token")
    if not token:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            
    if not token:
        raise credentials_exception

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

        # Check session table validity (session revocation, expiry)
        from app.models.session import UserSession
        session_valid = (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.access_token_jti == jti,
                UserSession.is_active == True,
            )
            .first()
        )
        if not session_valid:
            raise credentials_exception

    except JWTError as exc:
        raise credentials_exception from exc

    # user_id is now a UUID string, so no int() conversion
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
        if user.role not in roles:
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
    
    if lockdown and lockdown.value == "true" and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PLATFORM_LOCKDOWN: The system is currently in emergency read-only mode."
        )
    return True
