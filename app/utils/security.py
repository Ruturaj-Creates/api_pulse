"""
Password hashing and JWT helpers.

Never store plain-text passwords — only bcrypt hashes in the database.
JWT tokens prove the client logged in; the server verifies the signature.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import Settings


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (includes random salt)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    subject: str | int,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Build a signed JWT.

    `sub` (subject) = user id — we look up the user from this on each request.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any] | None:
    """Return token payload or None if invalid/expired."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
