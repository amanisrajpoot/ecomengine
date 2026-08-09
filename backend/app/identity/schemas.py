"""Identity and auth schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.identity.rbac import Role


class OtpRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20, pattern=r"^\+[1-9]\d{7,14}$")


class OtpRequestResponse(BaseModel):
    message: str
    expires_in_seconds: int
    # Present only when settings.otp_echo_in_response is true (dev/test).
    debug_code: str | None = None


class OtpVerify(BaseModel):
    phone: str = Field(min_length=8, max_length=20, pattern=r"^\+[1-9]\d{7,14}$")
    code: str = Field(min_length=4, max_length=10)


class PasswordRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = None


class PasswordLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    tenant_id: uuid.UUID | None


class RoleBindingCreate(BaseModel):
    role: Role
    tenant_id: uuid.UUID | None = None
    business_id: uuid.UUID | None = None


class RoleBindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    tenant_id: uuid.UUID | None
    business_id: uuid.UUID | None
    created_at: datetime


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: str | None
    phone: str | None
    status: str
    display_name: str | None
    created_at: datetime
    updated_at: datetime
    roles: list[RoleBindingRead] = []
