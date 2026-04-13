from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister


def register_user(db: Session, payload: UserRegister) -> User:
    user = User(
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
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


def get_or_create_master_user(db: Session) -> User:
    canonical_phone = normalize_phone_identifier(settings.MASTER_TEST_PHONE) or settings.MASTER_TEST_PHONE.strip()
    lookup_candidates = build_phone_lookup_candidates(canonical_phone)
    user = db.query(User).filter(User.phone_number.in_(lookup_candidates)).first()

    if not user:
        user = User(
            full_name=settings.MASTER_TEST_NAME,
            phone_number=canonical_phone,
            password_hash=get_password_hash(settings.MASTER_TEST_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
            is_suspended=False,
            trust_score=100,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    should_commit = False
    if user.full_name != settings.MASTER_TEST_NAME:
        user.full_name = settings.MASTER_TEST_NAME
        should_commit = True
    if user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
        should_commit = True
    if not user.is_active:
        user.is_active = True
        should_commit = True
    if user.is_suspended:
        user.is_suspended = False
        should_commit = True
    if user.phone_number != canonical_phone:
        conflict = (
            db.query(User)
            .filter(User.phone_number == canonical_phone, User.id != user.id)
            .first()
        )
        if not conflict:
            user.phone_number = canonical_phone
            should_commit = True
    if not verify_password(settings.MASTER_TEST_PASSWORD, user.password_hash):
        user.password_hash = get_password_hash(settings.MASTER_TEST_PASSWORD)
        should_commit = True

    if should_commit:
        db.commit()
        db.refresh(user)
    return user


def authenticate_with_master_credential(db: Session, phone_number: str, password: str) -> User | None:
    if not settings.MASTER_TEST_LOGIN_ENABLED:
        return None
    if password != settings.MASTER_TEST_PASSWORD:
        return None

    raw_identifier = phone_number.strip().lower()
    if settings.MASTER_TEST_ALIAS and raw_identifier == settings.MASTER_TEST_ALIAS.strip().lower():
        return get_or_create_master_user(db)

    incoming_candidates = build_phone_lookup_candidates(phone_number)
    master_candidates = build_phone_lookup_candidates(settings.MASTER_TEST_PHONE)
    if incoming_candidates & master_candidates:
        return get_or_create_master_user(db)
    return None


def authenticate_user(db: Session, phone_number: str, password: str) -> User | None:
    candidates = build_phone_lookup_candidates(phone_number)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
