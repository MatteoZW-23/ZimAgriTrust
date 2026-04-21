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


# Master credential logic removed for production security.
# Bootstrap administrator is now created via scripts/init_db.py.


def authenticate_user(db: Session, phone_number: str, password: str) -> User | None:
    candidates = build_phone_lookup_candidates(phone_number)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
