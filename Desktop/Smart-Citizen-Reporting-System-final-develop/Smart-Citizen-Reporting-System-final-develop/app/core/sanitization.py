"""
Input sanitization utilities.

Uses bleach to strip all HTML tags from user-supplied text fields.
This prevents XSS attacks when content is rendered in the frontend.
"""

import bleach


def strip_html(value: str) -> str:
    """
    Remove all HTML tags from a string and strip leading/trailing whitespace.

    Example:
        strip_html("<script>alert('xss')</script>Hello") -> "Hello"
        strip_html("<b>Bold text</b>") -> "Bold text"
    """
    return bleach.clean(value, tags=[], attributes={}, strip=True).strip()


def sanitize_text(value: str | None) -> str | None:
    """Sanitize optional text field — returns None if input is None."""
    if value is None:
        return None
    return strip_html(value)