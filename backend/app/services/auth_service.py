import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister

logger = logging.getLogger(__name__)


def register_user(db: Session, payload: UserRegister) -> User:
    from app.models.user import UserStatus

    # Roles that self-register and are immediately active
    public_roles = {UserRole.FARMER, UserRole.BUYER}
    # Roles that self-register but need admin approval
    approval_roles = {UserRole.DRIVER, UserRole.TRANSPORTER, UserRole.SUPPLIER}
    # Roles that use Email + Password (not PIN)
    password_roles = {
        UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN,
        UserRole.FINANCE_ADMIN, UserRole.REGIONAL_ADMIN, UserRole.REGIONAL_MANAGER,
        UserRole.SUPPORT_ADMIN, UserRole.BRANCH_ADMIN,
        UserRole.AGENT, UserRole.SUPPLIER, UserRole.STAFF,
    }

    if payload.role in public_roles:
        initial_status = UserStatus.ACTIVE
    elif payload.role in approval_roles:
        initial_status = UserStatus.PENDING_VERIFICATION
    else:
        initial_status = UserStatus.PENDING_VERIFICATION

    if payload.role in password_roles:
        # Staff/Admin/Supplier: Set password_hash only (for password + MFA login)
        hashed_password = get_password_hash(payload.password)
        user = User(
            full_name=payload.full_name,
            phone_number=payload.phone_number,
            email=getattr(payload, "email", None),
            password_hash=hashed_password,
            role=payload.role,
            status=initial_status,
            is_active=True,
            trust_score=50,
        )
    else:
        # Farmers/Buyers/Drivers: Set ussd_pin_hash (for PIN-only login)
        hashed_pin = get_password_hash(payload.password)
        user = User(
            full_name=payload.full_name,
            phone_number=payload.phone_number,
            email=getattr(payload, "email", None),
            ussd_pin_hash=hashed_pin,
            password_hash=hashed_pin,
            role=payload.role,
            status=initial_status,
            is_active=True,
            trust_score=50,
        )
    db.add(user)
    db.commit()
    db.refresh(user)

    # NEW: Send Bootstrap Secret for Staff
    if payload.role in {UserRole.ADMIN, UserRole.AGENT, UserRole.REGIONAL_MANAGER}:
        try:
            from app.services.notification_service import NotificationService
            import asyncio
            
            # Since notification_service.send_bootstrap_secret is async, 
            # and we are in a sync function, we use a simple background task or just run it.
            # In a real app, this would be a Celery task.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(NotificationService().send_bootstrap_secret(user.phone_number, payload.password))
            loop.close()
            
            logger.info(f"Bootstrap secret dispatched to {user.phone_number}")
        except Exception as e:
            logger.error(f"Failed to send bootstrap secret: {e}")

    # F#246 / F#278 — welcome notification.
    # Email is best-effort (does not block registration on failure).
    if user.email:
        try:
            from app.services.email_service import email_service

            email_service.send_template(
                "email.welcome",
                to=user.email,
                context={
                    "name": user.full_name,
                    "role": user.role.value if hasattr(user.role, "value") else str(user.role),
                },
            )
        except Exception as exc:  # noqa: BLE001 — never let email kill registration
            logger.warning("welcome email failed user=%s err=%s", user.id, exc)

    return user


def normalize_phone_identifier(phone_number: str) -> str:
    candidate = phone_number.replace(" ", "").strip()
    if not candidate:
        return ""

    if candidate.startswith("+"):
        digits = "".join(ch for ch in candidate[1:] if ch.isdigit())
    else:
        digits = "".join(ch for ch in candidate if ch.isdigit())

    if not digits:
        return candidate.lower()

    if digits.startswith("263"):
        return f"+263{digits[3:]}"
    if digits.startswith("0"):
        return f"+263{digits[1:]}"
    if len(digits) == 9:
        return f"+263{digits}"
    return f"+{digits}" if candidate.startswith("+") else digits


def build_phone_lookup_candidates(phone_number: str) -> set[str]:
    normalized = normalize_phone_identifier(phone_number)
    candidates = {phone_number.strip(), normalized}

    if normalized.startswith("+263") and len(normalized) > 4:
        national_digits = normalized[4:]
        candidates.add(f"0{national_digits}")
        candidates.add(f"263{national_digits}")
        candidates.add(national_digits)
    elif normalized.startswith("+") and len(normalized) > 1:
        candidates.add(normalized[1:])

    return {value for value in candidates if value}


# Master credential logic removed for production security.
# Bootstrap administrator is now created via scripts/init_db.py.


def authenticate_user(db: Session, phone_number: str, password: str) -> User | None:
    """
    Authenticate user with password (for staff login with MFA).
    For PIN-based login (farmers/buyers), use authenticate_user_pin instead.
    """
    candidates = build_phone_lookup_candidates(phone_number)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        return None
    return user


def authenticate_user_pin(db: Session, phone_number: str, pin: str) -> User | None:
    """
    Authenticate user with PIN (for farmers/buyers - no MFA).
    """
    candidates = build_phone_lookup_candidates(phone_number)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    if not user or not user.ussd_pin_hash or not verify_password(pin, user.ussd_pin_hash):
        return None
    return user
