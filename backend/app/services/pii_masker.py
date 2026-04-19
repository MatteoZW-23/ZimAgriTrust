import re
from typing import Tuple

class PIIMasker:
    # Regex for Zimbabwean phone numbers and general email patterns
    PHONE_PATTERN = r'(\+263|00263|0)(71|73|77|78)\d{7}'
    EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

    @staticmethod
    def mask_content(content: str) -> Tuple[str, bool]:
        """
        Scans content for PII (phone/email) and masks it.
        Returns (masked_content, was_masked).
        """
        masked = content
        was_masked = False

        # Mask Phone Numbers
        if re.search(PIIMasker.PHONE_PATTERN, content):
            masked = re.sub(PIIMasker.PHONE_PATTERN, "[PHONE_REDACTED]", masked)
            was_masked = True

        # Mask Emails
        if re.search(PIIMasker.EMAIL_PATTERN, content):
            masked = re.sub(PIIMasker.EMAIL_PATTERN, "[EMAIL_REDACTED]", masked)
            was_masked = True

        return masked, was_masked

    @staticmethod
    def get_security_warning() -> str:
        return "🛡️ SYSTEM SECURITY: Direct contact exchange is restricted until Escrow is locked for your protection."

pii_masker = PIIMasker()
