"""
USSD Input Validators
=====================
Validates and sanitizes all USSD input for Zimbabwe telco safety.
Prevents injection, validates phone numbers, PINs, amounts, etc.
"""
from __future__ import annotations

import re
import logging
from typing import Optional

logger = logging.getLogger("ussd.validators")

# Zimbabwe phone number patterns
ZW_PHONE_PATTERNS = {
    "econet": re.compile(r"^(\+?263|0)7[78]\d{7}$"),
    "netone": re.compile(r"^(\+?263|0)71\d{7}$"),
    "telecel": re.compile(r"^(\+?263|0)73\d{7}$"),
}

# Unified Zimbabwe phone pattern (any network)
ZW_PHONE_ANY = re.compile(r"^(\+?263|0)7[1378]\d{7}$")

# PIN pattern
PIN_PATTERN = re.compile(r"^\d{4,6}$")

# Amount pattern (USD)
AMOUNT_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")

# Text sanitization — allow only safe characters
SAFE_TEXT_PATTERN = re.compile(r"^[a-zA-Z0-9\s\.\,\-\_\/\(\)\+\#\*\@]+$")

# Maximum input length
MAX_INPUT_LENGTH = 160

# Blacklisted inputs (prevent USSD injection)
BLACKLISTED_INPUTS = {"*", "#", "**", "##", "*#", "#*"}


class USSDValidator:
    """Validates all USSD inputs for security and correctness."""

    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate session ID format."""
        if not session_id:
            return False
        if len(session_id) > 64:
            return False
        # Session IDs are alphanumeric with optional hyphens
        return bool(re.match(r"^[a-zA-Z0-9\-_]+$", session_id))

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate Zimbabwe phone number."""
        if not phone:
            return False
        cleaned = phone.replace(" ", "").replace("-", "")
        return bool(ZW_PHONE_ANY.match(cleaned))

    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """Normalize phone to +263 format."""
        if not phone:
            return ""
        cleaned = phone.replace(" ", "").replace("-", "")
        if cleaned.startswith("0"):
            return f"+263{cleaned[1:]}"
        if cleaned.startswith("263"):
            return f"+{cleaned}"
        if cleaned.startswith("+263"):
            return cleaned
        return cleaned

    @staticmethod
    def detect_provider(phone: str) -> str:
        """Detect network provider from phone number."""
        normalized = USSDValidator.normalize_phone_number(phone)
        if not normalized:
            return "unknown"
        # Remove +263 prefix
        suffix = normalized.replace("+263", "")
        if suffix.startswith("77") or suffix.startswith("78"):
            return "econet"
        if suffix.startswith("71"):
            return "netone"
        if suffix.startswith("73"):
            return "telecel"
        return "unknown"

    @staticmethod
    def validate_pin(pin: str) -> tuple[bool, str]:
        """Validate PIN format. Returns (valid, error_message)."""
        if not pin:
            return False, "PIN is required"
        if not pin.isdigit():
            return False, "PIN must be digits only"
        if len(pin) < 4:
            return False, "PIN must be at least 4 digits"
        if len(pin) > 6:
            return False, "PIN must be at most 6 digits"
        # Check for weak PINs
        if pin in {"0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888", "9999"}:
            return False, "PIN is too simple"
        if pin in {"1234", "4321", "0123", "9876", "1111", "123456"}:
            return False, "PIN is too common"
        return True, ""

    @staticmethod
    def validate_amount(amount_str: str) -> tuple[bool, float, str]:
        """Validate monetary amount. Returns (valid, amount, error_message)."""
        if not amount_str:
            return False, 0.0, "Amount is required"
        if not AMOUNT_PATTERN.match(amount_str):
            return False, 0.0, "Invalid amount format"
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, 0.0, "Amount must be positive"
            if amount > 100000:
                return False, 0.0, "Amount exceeds maximum"
            return True, amount, ""
        except ValueError:
            return False, 0.0, "Invalid amount"

    @staticmethod
    def validate_menu_selection(selection: str, max_option: int) -> tuple[bool, int, str]:
        """Validate menu option selection."""
        if not selection:
            return False, 0, "Selection required"
        if not selection.isdigit():
            return False, 0, "Enter a number"
        num = int(selection)
        if num < 0 or num > max_option:
            return False, 0, f"Enter 1-{max_option}"
        return True, num, ""

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input — remove dangerous characters."""
        if not text:
            return ""
        # Truncate to max length
        text = text[:MAX_INPUT_LENGTH]
        # Remove control characters
        text = "".join(c for c in text if ord(c) >= 32)
        # Strip whitespace
        text = text.strip()
        return text

    @staticmethod
    def validate_text_input(text: str, min_len: int = 1, max_len: int = 50) -> tuple[bool, str]:
        """Validate free-text input."""
        if not text or len(text.strip()) < min_len:
            return False, f"Must be at least {min_len} characters"
        if len(text) > max_len:
            return False, f"Must be at most {max_len} characters"
        if not SAFE_TEXT_PATTERN.match(text):
            return False, "Contains invalid characters"
        return True, ""

    @staticmethod
    def is_blacklisted(text: str) -> bool:
        """Check if input is a blacklisted/dangerous pattern."""
        return text.strip() in BLACKLISTED_INPUTS

    @staticmethod
    def validate_service_code(code: str) -> bool:
        """Validate USSD service code format."""
        if not code:
            return False
        return bool(re.match(r"^\*\d{2,5}#$", code))

    @staticmethod
    def validate_quantity(qty_str: str) -> tuple[bool, float, str]:
        """Validate quantity input (kg)."""
        if not qty_str:
            return False, 0.0, "Quantity required"
        try:
            qty = float(qty_str)
            if qty <= 0:
                return False, 0.0, "Must be positive"
            if qty > 1000000:
                return False, 0.0, "Exceeds maximum"
            return True, qty, ""
        except ValueError:
            return False, 0.0, "Enter a valid number"


# Module-level instance
validator = USSDValidator()
