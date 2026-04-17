import re

REDACTED_TOKEN = "[REDACTED_TOKEN]"
REDACTED_EMAIL = "[REDACTED_EMAIL]"
REDACTED_COOKIE = "[REDACTED_COOKIE]"
SAFE_FALLBACK_TEXT = "[REDACTED_UNAVAILABLE]"

_TOKEN_PATTERNS = [
    (
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s,;]+)"),
        rf"\1{REDACTED_TOKEN}",
    ),
    (re.compile(r"(?i)(bearer\s+)([^\s,;]+)"), rf"\1{REDACTED_TOKEN}"),
    (re.compile(r"(?i)(cookie\s*:\s*)([^\n]+)"), rf"\1{REDACTED_COOKIE}"),
    (re.compile(r"\bya29\.[A-Za-z0-9._\-]+\b"), REDACTED_TOKEN),
    (re.compile(r"\b1//[A-Za-z0-9._\-]+\b"), REDACTED_TOKEN),
]
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")


def sanitize_text(value: str | None, fallback: str = SAFE_FALLBACK_TEXT) -> str:
    """Best-effort redaction for Discord/GitHub output. Never raises."""
    if value is None:
        return fallback

    try:
        text = str(value)
        for pattern, replacement in _TOKEN_PATTERNS:
            text = pattern.sub(replacement, text)
        text = _EMAIL_PATTERN.sub(REDACTED_EMAIL, text)
        return text
    except Exception:
        return fallback


def sanitize_excerpt(value: str | None, limit: int = 1200, fallback: str = SAFE_FALLBACK_TEXT) -> str:
    text = sanitize_text(value, fallback=fallback)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
