"""
Logging utilities.

Masks sensitive data (emails, tokens) before writing to logs.
This ensures GDPR compliance and prevents sensitive data leakage
in log files or monitoring tools.
"""


def mask_email(email: str | None) -> str:
    """
    Mask an email address for safe logging.

    Examples:
        mask_email("john.doe@example.com") -> "j***e@example.com"
        mask_email("ab@example.com")       -> "a***b@example.com"
        mask_email(None)                   -> "[no email]"
    """
    if not email:
        return "[no email]"

    if "@" not in email:
        return "***"

    local, domain = email.split("@", 1)

    if len(local) <= 2:
        masked_local = f"{local[0]}***{local[-1]}"
    else:
        masked_local = f"{local[0]}***{local[-1]}"

    return f"{masked_local}@{domain}"


def mask_token(token: str | None) -> str:
    """
    Show only the first 8 characters of a token for debugging.

    Example:
        mask_token("eyJhbGciOiJIUzI1NiJ9...") -> "eyJhbGci..."
    """
    if not token:
        return "[no token]"
    return f"{token[:8]}..."