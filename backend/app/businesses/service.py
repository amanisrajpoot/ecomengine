"""Business onboarding service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import Business
from app.businesses.schemas import (
    BusinessCreate,
    BusinessUpdate,
    StaffAssign,
    StaffMemberRead,
    default_capabilities,
)
from app.core.errors import AppError
from app.identity.models import User, UserRoleBinding
from app.identity.rbac import Role
from app.identity.service import assign_role


async def create_business(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payload: BusinessCreate,
    owner_user_id: uuid.UUID | None = None,
) -> Business:
    caps = default_capabilities(payload.type)
    if payload.capabilities is not None:
        caps.update(payload.capabilities.model_dump())

    business = Business(
        tenant_id=tenant_id,
        type=payload.type.value,
        name=payload.name,
        description=payload.description,
        logo_url=payload.logo_url,
        contact=payload.contact.model_dump(exclude_none=True),
        settings=payload.settings.model_dump(),
        capabilities=caps,
        status=payload.status.value,
    )
    db.add(business)
    await db.flush()

    if owner_user_id is not None:
        existing = await db.scalar(
            select(UserRoleBinding).where(
                UserRoleBinding.user_id == owner_user_id,
                UserRoleBinding.role == Role.BUSINESS_OWNER.value,
                UserRoleBinding.tenant_id == tenant_id,
                UserRoleBinding.business_id == business.id,
            )
        )
        if not existing:
            db.add(
                UserRoleBinding(
                    user_id=owner_user_id,
                    role=Role.BUSINESS_OWNER.value,
                    tenant_id=tenant_id,
                    business_id=business.id,
                )
            )

    await db.commit()
    await db.refresh(business)
    return business


async def get_business(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID
) -> Business:
    business = await db.scalar(
        select(Business).where(Business.id == business_id, Business.tenant_id == tenant_id)
    )
    if not business:
        raise AppError("BUSINESS_NOT_FOUND", "Business not found", status_code=404)
    return business


async def list_businesses(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    status: str | None = None,
    business_type: str | None = None,
) -> list[Business]:
    stmt = select(Business).where(Business.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Business.status == status)
    if business_type:
        stmt = stmt.where(Business.type == business_type)
    stmt = stmt.order_by(Business.created_at.desc())
    return list(await db.scalars(stmt))


async def update_business(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: BusinessUpdate,
) -> Business:
    business = await get_business(db, tenant_id=tenant_id, business_id=business_id)
    data = payload.model_dump(exclude_unset=True, mode="json")
    if "contact" in data and data["contact"] is not None:
        business.contact = data.pop("contact")
    if "settings" in data and data["settings"] is not None:
        business.settings = data.pop("settings")
    if "capabilities" in data and data["capabilities"] is not None:
        caps = default_capabilities(business.type)
        caps.update(data.pop("capabilities"))
        business.capabilities = caps
    for key, value in data.items():
        setattr(business, key, value)
    await db.commit()
    await db.refresh(business)
    return business


_STAFF_LIST_ROLES = (
    Role.STAFF.value,
    Role.BUSINESS_MANAGER.value,
    Role.BUSINESS_OWNER.value,
)


async def list_business_staff(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
) -> list[StaffMemberRead]:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    stmt = (
        select(UserRoleBinding, User)
        .join(User, User.id == UserRoleBinding.user_id)
        .where(
            UserRoleBinding.tenant_id == tenant_id,
            UserRoleBinding.business_id == business_id,
            UserRoleBinding.role.in_(_STAFF_LIST_ROLES),
        )
        .order_by(UserRoleBinding.created_at.asc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        StaffMemberRead(
            binding_id=binding.id,
            user_id=user.id,
            role=binding.role,
            email=user.email,
            phone=user.phone,
            display_name=user.display_name,
            created_at=binding.created_at,
        )
        for binding, user in rows
    ]


async def _resolve_staff_user(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payload: StaffAssign,
) -> User:
    user: User | None = None
    if payload.user_id is not None:
        user = await db.get(User, payload.user_id)
    elif payload.email is not None:
        user = await db.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.email == str(payload.email).lower(),
            )
        )
    elif payload.phone is not None:
        user = await db.scalar(
            select(User).where(User.tenant_id == tenant_id, User.phone == payload.phone)
        )
    if not user:
        raise AppError("USER_NOT_FOUND", "User not found", status_code=404)
    if user.tenant_id != tenant_id:
        raise AppError("FORBIDDEN", "User is not in this tenant", status_code=403)
    return user


async def assign_business_staff(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: StaffAssign,
) -> StaffMemberRead:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    user = await _resolve_staff_user(db, tenant_id=tenant_id, payload=payload)
    binding = await assign_role(
        db,
        user_id=user.id,
        role=payload.role,
        tenant_id=tenant_id,
        business_id=business_id,
    )
    return StaffMemberRead(
        binding_id=binding.id,
        user_id=user.id,
        role=binding.role,
        email=user.email,
        phone=user.phone,
        display_name=user.display_name,
        created_at=binding.created_at,
    )
