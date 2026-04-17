from app.services.sanitizer import (
    REDACTED_COOKIE,
    REDACTED_EMAIL,
    REDACTED_TOKEN,
    SAFE_FALLBACK_TEXT,
    sanitize_excerpt,
    sanitize_text,
)


def test_sanitize_text_redacts_bearer_cookie_and_email():
    text = (
        "Authorization: Bearer abc123\n"
        "Cookie: session=secret\n"
        "contact me at dev@example.com\n"
        "token ya29.a0AfH6SMB and refresh 1//0gToken\n"
    )

    result = sanitize_text(text)

    assert "abc123" not in result
    assert "session=secret" not in result
    assert "dev@example.com" not in result
    assert REDACTED_TOKEN in result
    assert REDACTED_COOKIE in result
    assert REDACTED_EMAIL in result


def test_sanitize_text_returns_fallback_on_none():
    assert sanitize_text(None) == SAFE_FALLBACK_TEXT


def test_sanitize_excerpt_truncates():
    result = sanitize_excerpt("a" * 20, limit=10)
    assert result == "aaaaaaa..."
