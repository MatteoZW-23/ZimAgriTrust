"""
PIN Validation Service for ZimAgriTrust
Enforces PIN security rules for Farmers, Buyers, Drivers, and Agents.

Rules:
- Length: 4-6 digits (numbers only)
- No sequential digits (1234, 2345, etc.)
- No repeated digits (1111, 2222, etc.)
- Cannot contain user's phone number digits
- Cannot contain birth year
- Cannot reuse last 3 PINs
"""
import re
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.models.security_enhanced import PINHistory


# Sequential digit patterns to reject
SEQUENTIAL_PATTERNS = [
    "0123", "1234", "2345", "3456", "4567", "5678", "6789",
    "9876", "8765", "7654", "6543", "5432", "4321", "3210",
]

# Repeated digit patterns to reject
REPEATED_PATTERNS = [
    "0000", "1111", "2222", "3333", "4444",
    "5555", "6666", "7777", "8888", "9999",
    "00000", "11111", "22222", "33333", "44444",
    "55555", "66666", "77777", "88888", "99999",
    "000000", "111111", "222222", "333333", "444444",
    "555555", "666666", "777777", "888888", "999999",
]


class PINValidator:
    """Validates PIN against security rules"""

    @staticmethod
    def validate(
        pin: str,
        phone_number: Optional[str] = None,
        birth_year: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Validate PIN against all security rules.

        Returns:
            (is_valid, error_message)
        """
        # Rule 1: Must be digits only
        if not pin.isdigit():
            return False, "PIN must contain only digits"

        # Rule 2: Length check (4-6 digits)
        if len(pin) < settings.PIN_MIN_LENGTH:
            return False, f"PIN must be at least {settings.PIN_MIN_LENGTH} digits"
        if len(pin) > settings.PIN_MAX_LENGTH:
            return False, f"PIN must be at most {settings.PIN_MAX_LENGTH} digits"

        # Rule 3: No sequential digits
        for pattern in SEQUENTIAL_PATTERNS:
            if pattern in pin:
                return False, "PIN cannot contain sequential digits (e.g., 1234)"

        # Rule 4: No repeated digits
        for pattern in REPEATED_PATTERNS:
            if pin == pattern or (len(pin) >= 4 and all(c == pin[0] for c in pin)):
                return False, "PIN cannot be all repeated digits (e.g., 1111)"

        # Rule 5: Cannot contain phone number digits
        if phone_number:
            # Extract last 4-6 digits of phone number
            phone_digits = re.sub(r'\D', '', phone_number)
            if len(phone_digits) >= 4:
                # Check if PIN matches any 4+ digit substring of phone
                for i in range(len(phone_digits) - 3):
                    segment = phone_digits[i:i + len(pin)]
                    if segment == pin:
                        return False, "PIN cannot contain digits from your phone number"
                # Also check last N digits
                if phone_digits[-len(pin):] == pin:
                    return False, "PIN cannot contain digits from your phone number"

        # Rule 6: Cannot contain birth year
        if birth_year and len(birth_year) == 4 and birth_year in pin:
            return False, "PIN cannot contain your birth year"

        # Rule 7: No keyboard patterns
        keyboard_patterns = ["1470", "2580", "3690", "0852", "0741"]
        if pin in keyboard_patterns:
            return False, "PIN cannot be a common keyboard pattern"

        return True, ""

    @staticmethod
    def check_pin_history(
        db: Session,
        user_id,
        new_pin: str,
        max_history: int = None,
    ) -> Tuple[bool, str]:
        """
        Check if PIN was recently used (prevents reuse of last N PINs).

        Returns:
            (is_allowed, error_message)
        """
        if max_history is None:
            max_history = settings.PIN_HISTORY_COUNT

        # Get recent PIN hashes
        recent_pins = (
            db.query(PINHistory)
            .filter(PINHistory.user_id == user_id)
            .order_by(PINHistory.created_at.desc())
            .limit(max_history)
            .all()
        )

        for pin_record in recent_pins:
            if verify_password(new_pin, pin_record.pin_hash):
                return False, f"Cannot reuse your last {max_history} PINs"

        return True, ""

    @staticmethod
    def record_pin_change(
        db: Session,
        user_id,
        pin_hash: str,
        reason: str = "user_initiated",
        changed_by=None,
    ) -> None:
        """Record a PIN change in history for reuse prevention"""
        history = PINHistory(
            user_id=user_id,
            pin_hash=pin_hash,
            change_reason=reason,
            changed_by=changed_by,
        )
        db.add(history)
        db.commit()

    @staticmethod
    def validate_and_check_history(
        db: Session,
        user_id,
        new_pin: str,
        phone_number: Optional[str] = None,
        birth_year: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Full validation: rules + history check.

        Returns:
            (is_valid, error_message)
        """
        # Validate rules
        is_valid, error = PINValidator.validate(
            new_pin, phone_number=phone_number, birth_year=birth_year
        )
        if not is_valid:
            return False, error

        # Check history
        is_allowed, error = PINValidator.check_pin_history(db, user_id, new_pin)
        if not is_allowed:
            return False, error

        return True, ""
