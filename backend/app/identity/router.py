"""Auth and identity HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import AuthContext, get_current_user, require_permission, resolve_tenant_id
from app.identity import service
from app.identity.schemas import (
    OtpRequest,
    OtpRequestResponse,
    OtpVerify,
    PasswordLogin,
    PasswordRegister,
    RoleBindingCreate,
    RoleBindingRead,
    TokenResponse,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


@router.post("/otp/request", response_model=OtpRequestResponse)
async def otp_request(
    payload: OtpRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OtpRequestResponse:
    settings = get_settings()
    _, code = await service.request_otp(db, phone=payload.phone, tenant_id=tenant_id)
    return OtpRequestResponse(
        message="OTP sent",
        expires_in_seconds=settings.otp_ttl_seconds,
        debug_code=code if settings.otp_echo_in_response else None,
    )


@router.post("/otp/verify", response_model=TokenResponse)
async def otp_verify(
    payload: OtpVerify,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> TokenResponse:
    user, token = await service.verify_otp_and_login(
        db, phone=payload.phone, code=payload.code, tenant_id=tenant_id
    )
    return TokenResponse(access_token=token, user_id=user.id, tenant_id=user.tenant_id)


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: PasswordRegister,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> TokenResponse:
    user, token = await service.register_with_password(
        db, payload=payload, tenant_id=tenant_id
    )
    return TokenResponse(access_token=token, user_id=user.id, tenant_id=user.tenant_id)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: PasswordLogin,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> TokenResponse:
    user, token = await service.login_with_password(
        db, email=str(payload.email), password=payload.password, tenant_id=tenant_id
    )
    return TokenResponse(access_token=token, user_id=user.id, tenant_id=user.tenant_id)


@router.get("/me", response_model=UserRead)
async def me(
    ctx: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    bindings = await service.get_user_role_bindings(db, ctx.user.id)
    data = UserRead.model_validate(ctx.user)
    data.roles = [RoleBindingRead.model_validate(b) for b in bindings]
    return data


@users_router.post("/{user_id}/roles", response_model=RoleBindingRead)
async def assign_role(
    user_id: uuid.UUID,
    payload: RoleBindingCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("users.roles.assign")),
) -> RoleBindingRead:
    _ = ctx
    binding = await service.assign_role(
        db,
        user_id=user_id,
        role=payload.role,
        tenant_id=payload.tenant_id,
        business_id=payload.business_id,
    )
    return RoleBindingRead.model_validate(binding)
