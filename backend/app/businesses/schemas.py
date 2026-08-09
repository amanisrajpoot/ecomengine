"""Business configuration schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BusinessConfig(BaseModel):
    preparation_time_minutes: int | None = None
    accepts_scheduled_orders: bool = False
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    extra: dict[str, Any] = Field(default_factory=dict)


def default_capabilities(business_type: str) -> dict[str, bool]:
    presets: dict[str, dict[str, bool]] = {
        "FOOD": {
            "catalog": True,
            "inventory": False,
            "addons": True,
            "delivery": True,
            "scheduledOrders": True,
        },
        "GROCERY": {
            "catalog": True,
            "inventory": True,
            "addons": False,
            "delivery": True,
            "scheduledOrders": True,
        },
        "RETAIL": {
            "catalog": True,
            "inventory": True,
            "addons": False,
            "delivery": True,
            "scheduledOrders": False,
        },
        "COURIER": {
            "catalog": False,
            "inventory": False,
            "addons": False,
            "delivery": True,
            "scheduledOrders": True,
        },
    }
    return presets.get(business_type, presets["FOOD"])
