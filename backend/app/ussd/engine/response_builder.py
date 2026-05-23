"""
USSD Response Builder
=====================
Constructs properly formatted USSD responses for Zimbabwe telco protocols.
Handles:
- CON (continue) vs END (terminate) prefixes
- Character limits (182 chars for most Zim providers)
- Menu pagination
- Multi-language rendering
"""
from __future__ import annotations

import textwrap
from typing import Optional

# Zimbabwe USSD character limits
MAX_CHARS_ECONET = 182
MAX_CHARS_NETONE = 160
MAX_CHARS_TELECEL = 160
DEFAULT_MAX_CHARS = 160


class ResponseBuilder:
    """Builds properly formatted USSD response strings."""

    def __init__(self, provider: str = "econet", language: str = "en"):
        self.provider = provider.lower()
        self.language = language
        self._max_chars = self._get_max_chars()

    def _get_max_chars(self) -> int:
        limits = {
            "econet": MAX_CHARS_ECONET,
            "netone": MAX_CHARS_NETONE,
            "telecel": MAX_CHARS_TELECEL,
        }
        return limits.get(self.provider, DEFAULT_MAX_CHARS)

    def continue_response(self, text: str) -> str:
        """Build a CON (continue) response — session stays open."""
        content = self._truncate(text)
        return f"CON {content}"

    def end_response(self, text: str) -> str:
        """Build an END response — session terminates."""
        content = self._truncate(text)
        return f"END {content}"

    def menu(self, title: str, options: list[tuple[str, str]], footer: str = "") -> str:
        """
        Build a numbered menu.
        options: list of (number, label) tuples
        """
        lines = [title]
        for num, label in options:
            lines.append(f"{num}. {label}")
        if footer:
            lines.append(footer)
        content = "\n".join(lines)
        return f"CON {self._truncate(content)}"

    def paginated_menu(
        self,
        title: str,
        items: list[str],
        page: int = 1,
        page_size: int = 5,
        has_back: bool = True,
    ) -> str:
        """Build a paginated menu for long lists."""
        total_pages = (len(items) + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]

        lines = [title]
        for i, item in enumerate(page_items, start=start + 1):
            lines.append(f"{i}. {item}")

        nav = []
        if page < total_pages:
            nav.append("99. Next")
        if page > 1:
            nav.append("98. Previous")
        if has_back:
            nav.append("0. Back")

        if nav:
            lines.append("\n".join(nav))

        content = "\n".join(lines)
        return f"CON {self._truncate(content)}"

    def confirmation(self, title: str, details: list[str], confirm_text: str = "1. Confirm  2. Cancel") -> str:
        """Build a confirmation screen."""
        lines = [title] + details + [confirm_text]
        content = "\n".join(lines)
        return f"CON {self._truncate(content)}"

    def success(self, title: str, details: list[str] = None) -> str:
        """Build a success end screen."""
        lines = [title]
        if details:
            lines.extend(details)
        content = "\n".join(lines)
        return f"END {self._truncate(content)}"

    def error(self, message: str, retry_hint: str = "Dial *123# to try again.") -> str:
        """Build an error end screen."""
        content = f"{message}\n{retry_hint}"
        return f"END {self._truncate(content)}"

    def input_prompt(self, prompt: str, hint: str = "") -> str:
        """Build an input prompt."""
        content = prompt
        if hint:
            content += f"\n({hint})"
        return f"CON {self._truncate(content)}"

    def _truncate(self, text: str) -> str:
        """Truncate text to fit provider character limits."""
        # Remove the CON/END prefix space for calculation
        if len(text) <= self._max_chars - 4:  # -4 for "CON " or "END "
            return text
        truncated = text[: self._max_chars - 7] + "..."
        return truncated


def build_response(
    text: str,
    end_session: bool = False,
    provider: str = "econet",
    language: str = "en",
) -> str:
    """Convenience function for building responses."""
    builder = ResponseBuilder(provider=provider, language=language)
    if end_session:
        return builder.end_response(text)
    return builder.continue_response(text)
