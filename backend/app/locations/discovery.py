"""Hyperlocal store discovery — nearby active locations with inventory+delivery."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import Business
from app.delivery.geo import haversine_km
from app.locations.models import BusinessLocation
from app.locations.schemas import NearbyStoreRead
from app.verticals.hyperlocal import HYPERLOCAL_TYPES


def _covers_customer(
    *,
    store_lat: float,
    store_lng: float,
    customer_lat: float,
    customer_lng: float,
    service_area: dict | None,
    query_radius_km: float,
) -> tuple[bool, float]:
    distance = haversine_km(customer_lat, customer_lng, store_lat, store_lng)
    # Prefer explicit store service radius when present.
    if service_area and service_area.get("radius_km") is not None:
        try:
            radius = float(service_area["radius_km"])
        except (TypeError, ValueError):
            radius = query_radius_km
        return distance <= radius, distance
    return distance <= query_radius_km, distance


async def discover_nearby_stores(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    lat: float,
    lng: float,
    radius_km: float = 5.0,
    business_type: str | None = None,
    limit: int = 50,
) -> list[NearbyStoreRead]:
    types = {business_type} if business_type else set(HYPERLOCAL_TYPES)
    stmt = (
        select(BusinessLocation, Business)
        .join(Business, Business.id == BusinessLocation.business_id)
        .where(
            BusinessLocation.tenant_id == tenant_id,
            BusinessLocation.is_active.is_(True),
            Business.status == "ACTIVE",
            Business.type.in_(types),
        )
    )
    rows = list(await db.execute(stmt))
    results: list[NearbyStoreRead] = []
    for location, business in rows:
        caps = business.capabilities or {}
        if not caps.get("delivery", True):
            continue
        # Hyperlocal discovery prefers inventory-capable stores.
        if not caps.get("inventory", False):
            continue
        ok, distance = _covers_customer(
            store_lat=float(location.lat),
            store_lng=float(location.lng),
            customer_lat=lat,
            customer_lng=lng,
            service_area=location.service_area if isinstance(location.service_area, dict) else None,
            query_radius_km=radius_km,
        )
        if not ok:
            continue
        results.append(
            NearbyStoreRead(
                business_id=business.id,
                business_name=business.name,
                business_type=business.type,
                location_id=location.id,
                location_name=location.name,
                address=location.address or {},
                lat=float(location.lat),
                lng=float(location.lng),
                distance_km=round(distance, 3),
                service_area=location.service_area,
                capabilities=caps,
            )
        )
    results.sort(key=lambda s: s.distance_km)
    return results[: max(1, min(limit, 100))]
