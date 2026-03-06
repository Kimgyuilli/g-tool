"""JWT authentication and Fernet encryption utilities."""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.fernet import Fernet

from app.config import settings

# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def create_access_token(user_id: int) -> str:
    """Create a JWT access token for the given user_id."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_access_token(token: str) -> int | None:
    """Verify JWT and return user_id. Returns None on failure."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Fernet encryption (for DB-stored tokens)
# ---------------------------------------------------------------------------


def _get_fernet() -> Fernet:
    """Derive a Fernet-compatible 32-byte key from secret_key."""
    key = hashlib.sha256(settings.secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string and return the ciphertext."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string and return the plaintext."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()
