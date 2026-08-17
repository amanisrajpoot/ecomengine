"""Password hashing and JWT access tokens."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def create_access_token(
    *,
    user_id: str,
    tenant_id: str | None,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(seconds=settings.jwt_ttl_seconds)
    )
    payload: dict[str, Any] = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
