"""Delivery partner profile and vehicle services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.partners.models import DeliveryPartnerProfile, Vehicle
from app.partners.schemas import PartnerProfileCreate, PartnerProfileUpdate, VehicleCreate


async def _get_partner(
    db: AsyncSession, *, tenant_id: uuid.UUID, partner_id: uuid.UUID
) -> DeliveryPartnerProfile:
    partner = await db.scalar(
        select(DeliveryPartnerProfile).where(
            DeliveryPartnerProfile.id == partner_id,
            DeliveryPartnerProfile.tenant_id == tenant_id,
        )
    )
    if not partner:
        raise AppError("PARTNER_NOT_FOUND", "Delivery partner not found", status_code=404)
    return partner


async def create_partner_profile(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: PartnerProfileCreate,
) -> DeliveryPartnerProfile:
    existing = await db.scalar(
        select(DeliveryPartnerProfile).where(DeliveryPartnerProfile.user_id == user_id)
    )
    if existing:
        raise AppError("PARTNER_ALREADY_EXISTS", "Partner profile already exists", 400)

    profile = DeliveryPartnerProfile(
        tenant_id=tenant_id,
        user_id=user_id,
        documents=payload.documents,
        service_area=payload.service_area,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_partner_profile_for_user(
    db: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> DeliveryPartnerProfile:
    profile = await db.scalar(
        select(DeliveryPartnerProfile).where(
            DeliveryPartnerProfile.tenant_id == tenant_id,
            DeliveryPartnerProfile.user_id == user_id,
        )
    )
    if not profile:
        raise AppError("PARTNER_NOT_FOUND", "Partner profile not found", status_code=404)
    return profile


async def get_partner_profile(
    db: AsyncSession, *, tenant_id: uuid.UUID, partner_id: uuid.UUID
) -> DeliveryPartnerProfile:
    return await _get_partner(db, tenant_id=tenant_id, partner_id=partner_id)


async def update_partner_profile(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: PartnerProfileUpdate,
) -> DeliveryPartnerProfile:
    profile = await get_partner_profile_for_user(db, tenant_id=tenant_id, user_id=user_id)
    if payload.status is not None:
        profile.status = payload.status
    if payload.is_online is not None:
        profile.is_online = payload.is_online
    if payload.documents is not None:
        profile.documents = payload.documents
    if payload.current_lat is not None:
        profile.current_lat = payload.current_lat
    if payload.current_lng is not None:
        profile.current_lng = payload.current_lng
    if payload.service_area is not None:
        profile.service_area = payload.service_area
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_partner_location(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    lat: float,
    lng: float,
) -> DeliveryPartnerProfile:
    profile = await get_partner_profile_for_user(db, tenant_id=tenant_id, user_id=user_id)
    profile.current_lat = lat
    profile.current_lng = lng
    await db.commit()
    await db.refresh(profile)
    return profile


async def list_available_partners(
    db: AsyncSession, *, tenant_id: uuid.UUID, online_only: bool = True
) -> list[DeliveryPartnerProfile]:
    stmt = select(DeliveryPartnerProfile).where(
        DeliveryPartnerProfile.tenant_id == tenant_id,
        DeliveryPartnerProfile.status == "ACTIVE",
    )
    if online_only:
        stmt = stmt.where(DeliveryPartnerProfile.is_online.is_(True))
    return list(await db.scalars(stmt))


async def create_vehicle(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: VehicleCreate,
) -> Vehicle:
    profile = await get_partner_profile_for_user(db, tenant_id=tenant_id, user_id=user_id)
    vehicle = Vehicle(
        tenant_id=tenant_id,
        partner_id=profile.id,
        vehicle_type=payload.vehicle_type,
        registration=payload.registration,
        meta=payload.metadata,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def list_partner_vehicles(
    db: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> list[Vehicle]:
    profile = await get_partner_profile_for_user(db, tenant_id=tenant_id, user_id=user_id)
    stmt = select(Vehicle).where(
        Vehicle.tenant_id == tenant_id,
        Vehicle.partner_id == profile.id,
    )
    return list(await db.scalars(stmt))
