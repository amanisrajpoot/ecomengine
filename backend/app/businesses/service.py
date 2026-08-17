"""Business onboarding service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import Business
from app.businesses.schemas import BusinessCreate, BusinessUpdate, default_capabilities
from app.core.errors import AppError
from app.identity.models import UserRoleBinding
from app.identity.rbac import Role


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
