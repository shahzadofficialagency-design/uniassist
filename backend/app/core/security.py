"""Password hashing (bcrypt) and JWT access/refresh tokens."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _create_token(user_id: int, role: str, token_type: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(user_id, role, "access", timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: int, role: str) -> str:
    return _create_token(user_id, role, "refresh", timedelta(days=settings.refresh_token_days))


def decode_token(token: str, expected_type: str = "access") -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_reset_token() -> str:
    return secrets.token_urlsafe(32)
