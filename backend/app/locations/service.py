"""Business location services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.service import get_business
from app.core.errors import AppError
from app.locations.models import BusinessLocation
from app.locations.schemas import LocationCreate, LocationUpdate


async def create_location(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: LocationCreate,
) -> BusinessLocation:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    location = BusinessLocation(
        tenant_id=tenant_id,
        business_id=business_id,
        name=payload.name,
        address=payload.address.model_dump(),
        lat=payload.lat,
        lng=payload.lng,
        hours=[h.model_dump() for h in payload.hours],
        timezone=payload.timezone,
        is_active=payload.is_active,
        service_area=payload.service_area,
    )
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location


async def get_location(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
) -> BusinessLocation:
    location = await db.scalar(
        select(BusinessLocation).where(
            BusinessLocation.id == location_id,
            BusinessLocation.business_id == business_id,
            BusinessLocation.tenant_id == tenant_id,
        )
    )
    if not location:
        raise AppError("LOCATION_NOT_FOUND", "Location not found", status_code=404)
    return location


async def list_locations(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    active_only: bool = True,
) -> list[BusinessLocation]:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    stmt = select(BusinessLocation).where(
        BusinessLocation.tenant_id == tenant_id,
        BusinessLocation.business_id == business_id,
    )
    if active_only:
        stmt = stmt.where(BusinessLocation.is_active.is_(True))
    stmt = stmt.order_by(BusinessLocation.created_at.asc())
    return list(await db.scalars(stmt))


async def update_location(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    payload: LocationUpdate,
) -> BusinessLocation:
    location = await get_location(
        db, tenant_id=tenant_id, business_id=business_id, location_id=location_id
    )
    data = payload.model_dump(exclude_unset=True, mode="json")
    if "address" in data and data["address"] is not None:
        location.address = data.pop("address")
    if "hours" in data and data["hours"] is not None:
        location.hours = data.pop("hours")
    for key, value in data.items():
        setattr(location, key, value)
    await db.commit()
    await db.refresh(location)
    return location
