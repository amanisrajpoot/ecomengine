"""Delivery partner and vehicle services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.identity.models import User
from app.partners.models import DeliveryPartnerProfile, Vehicle
from app.partners.schemas import PartnerCreate, PartnerLocationUpdate, PartnerUpdate, VehicleCreate


async def create_partner(
    db: AsyncSession, *, tenant_id: uuid.UUID, payload: PartnerCreate
) -> DeliveryPartnerProfile:
    user = await db.get(User, payload.user_id)
    if not user:
        raise AppError("USER_NOT_FOUND", "User not found", 404)
    existing = await db.scalar(
        select(DeliveryPartnerProfile).where(
            DeliveryPartnerProfile.tenant_id == tenant_id,
            DeliveryPartnerProfile.user_id == payload.user_id,
        )
    )
    if existing:
        raise AppError("PARTNER_EXISTS", "Delivery partner profile already exists for user", 409)

    partner = DeliveryPartnerProfile(
        tenant_id=tenant_id,
        user_id=payload.user_id,
        display_name=payload.display_name,
        documents=payload.documents or {},
        service_area=payload.service_area,
        status=payload.status,
        is_online=False,
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return partner


async def list_partners(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    online_only: bool = False,
    status: str | None = None,
) -> list[DeliveryPartnerProfile]:
    stmt = select(DeliveryPartnerProfile).where(DeliveryPartnerProfile.tenant_id == tenant_id)
    if online_only:
        stmt = stmt.where(DeliveryPartnerProfile.is_online.is_(True))
    if status:
        stmt = stmt.where(DeliveryPartnerProfile.status == status)
    stmt = stmt.order_by(DeliveryPartnerProfile.created_at.desc())
    return list(await db.scalars(stmt))


async def get_partner(
    db: AsyncSession, *, tenant_id: uuid.UUID, partner_id: uuid.UUID
) -> DeliveryPartnerProfile:
    partner = await db.scalar(
        select(DeliveryPartnerProfile).where(
            DeliveryPartnerProfile.id == partner_id,
            DeliveryPartnerProfile.tenant_id == tenant_id,
        )
    )
    if not partner:
        raise AppError("PARTNER_NOT_FOUND", "Delivery partner not found", 404)
    return partner


async def get_partner_for_user(
    db: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> DeliveryPartnerProfile | None:
    return await db.scalar(
        select(DeliveryPartnerProfile).where(
            DeliveryPartnerProfile.tenant_id == tenant_id,
            DeliveryPartnerProfile.user_id == user_id,
        )
    )


async def require_partner_for_user(
    db: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> DeliveryPartnerProfile:
    partner = await get_partner_for_user(db, tenant_id=tenant_id, user_id=user_id)
    if not partner:
        raise AppError(
            "PARTNER_NOT_FOUND",
            "No delivery partner profile for this user",
            404,
        )
    return partner


async def update_partner(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    partner_id: uuid.UUID,
    payload: PartnerUpdate,
) -> DeliveryPartnerProfile:
    partner = await get_partner(db, tenant_id=tenant_id, partner_id=partner_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(partner, key, value)
    await db.commit()
    await db.refresh(partner)
    return partner


async def update_partner_location(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    partner_id: uuid.UUID,
    payload: PartnerLocationUpdate,
) -> DeliveryPartnerProfile:
    partner = await get_partner(db, tenant_id=tenant_id, partner_id=partner_id)
    partner.current_lat = payload.lat
    partner.current_lng = payload.lng
    if payload.is_online is not None:
        partner.is_online = payload.is_online
    await db.commit()
    await db.refresh(partner)
    return partner


async def create_vehicle(
    db: AsyncSession, *, tenant_id: uuid.UUID, payload: VehicleCreate
) -> Vehicle:
    await get_partner(db, tenant_id=tenant_id, partner_id=payload.partner_id)
    vehicle = Vehicle(
        tenant_id=tenant_id,
        partner_id=payload.partner_id,
        vehicle_type=payload.vehicle_type,
        registration=payload.registration,
        metadata_json=payload.metadata or {},
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def list_vehicles(
    db: AsyncSession, *, tenant_id: uuid.UUID, partner_id: uuid.UUID | None = None
) -> list[Vehicle]:
    stmt = select(Vehicle).where(Vehicle.tenant_id == tenant_id, Vehicle.is_active.is_(True))
    if partner_id:
        stmt = stmt.where(Vehicle.partner_id == partner_id)
    return list(await db.scalars(stmt.order_by(Vehicle.created_at.desc())))
