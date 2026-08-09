"""Geo helpers for V1 assignment (haversine + simple service area)."""

from __future__ import annotations

import math
from typing import Any


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometers."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def in_service_area(
    *,
    partner_lat: float,
    partner_lng: float,
    pickup_lat: float,
    pickup_lng: float,
    service_area: dict[str, Any] | None,
) -> bool:
    """V1: optional radius_km around partner, or center+radius, else allow."""
    if not service_area:
        return True
    radius = service_area.get("radius_km")
    if radius is None:
        return True
    center_lat = service_area.get("center_lat", partner_lat)
    center_lng = service_area.get("center_lng", partner_lng)
    try:
        return haversine_km(float(center_lat), float(center_lng), pickup_lat, pickup_lng) <= float(
            radius
        )
    except (TypeError, ValueError):
        return True
