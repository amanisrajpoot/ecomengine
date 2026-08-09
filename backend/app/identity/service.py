"""Authentication and identity services."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.identity.models import CustomerProfile, OtpChallenge, User, UserRoleBinding
from app.identity.rbac import Role
from app.identity.schemas import PasswordRegister


def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


async def request_otp(
    db: AsyncSession,
    *,
    phone: str,
    tenant_id: uuid.UUID | None,
) -> tuple[OtpChallenge, str]:
    settings = get_settings()
    code = "".join(secrets.choice("0123456789") for _ in range(settings.otp_length))
    challenge = OtpChallenge(
        tenant_id=tenant_id,
        phone=phone,
        code_hash=_hash_otp(code),
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.otp_ttl_seconds),
        consumed=False,
        attempts=0,
        metadata_json={},
    )
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)
    return challenge, code


async def verify_otp_and_login(
    db: AsyncSession,
    *,
    phone: str,
    code: str,
    tenant_id: uuid.UUID | None,
) -> tuple[User, str]:
    result = await db.scalars(
        select(OtpChallenge)
        .where(
            OtpChallenge.phone == phone,
            OtpChallenge.consumed.is_(False),
        )
        .order_by(OtpChallenge.created_at.desc())
        .limit(1)
    )
    challenge = result.first()
    if not challenge:
        raise AppError("OTP_NOT_FOUND", "No active OTP challenge", status_code=400)
    if challenge.expires_at < datetime.now(UTC):
        raise AppError("OTP_EXPIRED", "OTP has expired", status_code=400)
    if challenge.attempts >= 5:
        raise AppError("OTP_LOCKED", "Too many OTP attempts", status_code=429)

    challenge.attempts += 1
    if challenge.code_hash != _hash_otp(code):
        await db.commit()
        raise AppError("OTP_INVALID", "Invalid OTP code", status_code=400)

    challenge.consumed = True

    user = await db.scalar(
        select(User).where(User.phone == phone, User.tenant_id == tenant_id)
    )
    if user is None:
        user = User(phone=phone, tenant_id=tenant_id, status="ACTIVE")
        db.add(user)
        await db.flush()
        if tenant_id is not None:
            db.add(
                UserRoleBinding(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    business_id=None,
                    role=Role.CUSTOMER.value,
                )
            )
            db.add(
                CustomerProfile(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    display_name=None,
                )
            )

    await db.commit()
    await db.refresh(user)
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id)
    return user, token


async def register_with_password(
    db: AsyncSession,
    *,
    payload: PasswordRegister,
    tenant_id: uuid.UUID | None,
    role: Role = Role.CUSTOMER,
) -> tuple[User, str]:
    existing = await db.scalar(
        select(User).where(User.email == str(payload.email), User.tenant_id == tenant_id)
    )
    if existing:
        raise AppError("EMAIL_EXISTS", "Email already registered", status_code=409)

    user = User(
        email=str(payload.email).lower(),
        tenant_id=tenant_id,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        status="ACTIVE",
    )
    db.add(user)
    await db.flush()
    db.add(
        UserRoleBinding(
            user_id=user.id,
            tenant_id=tenant_id,
            business_id=None,
            role=role.value,
        )
    )
    if role == Role.CUSTOMER and tenant_id is not None:
        db.add(
            CustomerProfile(
                tenant_id=tenant_id,
                user_id=user.id,
                display_name=payload.display_name,
            )
        )
    await db.commit()
    await db.refresh(user)
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id)
    return user, token


async def login_with_password(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    tenant_id: uuid.UUID | None,
) -> tuple[User, str]:
    user = await db.scalar(
        select(User).where(User.email == email.lower(), User.tenant_id == tenant_id)
    )
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Invalid email or password", status_code=401)
    if user.status != "ACTIVE":
        raise AppError("USER_DISABLED", "User is disabled", status_code=403)
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id)
    return user, token


async def get_user_role_bindings(db: AsyncSession, user_id: uuid.UUID) -> list[UserRoleBinding]:
    result = await db.scalars(
        select(UserRoleBinding).where(UserRoleBinding.user_id == user_id)
    )
    return list(result)


async def assign_role(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    role: Role,
    tenant_id: uuid.UUID | None,
    business_id: uuid.UUID | None,
) -> UserRoleBinding:
    user = await db.get(User, user_id)
    if not user:
        raise AppError("USER_NOT_FOUND", "User not found", status_code=404)

    existing = await db.scalar(
        select(UserRoleBinding).where(
            UserRoleBinding.user_id == user_id,
            UserRoleBinding.role == role.value,
            UserRoleBinding.tenant_id == tenant_id,
            UserRoleBinding.business_id == business_id,
        )
    )
    if existing:
        return existing

    binding = UserRoleBinding(
        user_id=user_id,
        role=role.value,
        tenant_id=tenant_id,
        business_id=business_id,
    )
    db.add(binding)
    await db.commit()
    await db.refresh(binding)
    return binding


async def create_bootstrap_super_admin(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> User:
    existing = await db.scalar(
        select(User).where(User.email == email.lower(), User.tenant_id.is_(None))
    )
    if existing:
        return existing
    user = User(
        email=email.lower(),
        tenant_id=None,
        password_hash=hash_password(password),
        status="ACTIVE",
        display_name="Super Admin",
    )
    db.add(user)
    await db.flush()
    db.add(
        UserRoleBinding(
            user_id=user.id,
            tenant_id=None,
            business_id=None,
            role=Role.SUPER_ADMIN.value,
        )
    )
    await db.commit()
    await db.refresh(user)
    return user
