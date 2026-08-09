"""Seed a demo COURIER business for local golden-path exploration.

Usage:
  cd backend && PYTHONPATH=. python -m app.scripts.seed_courier_demo

Creates (idempotent by slug):
  tenant courier-demo, COURIER business CityDash.
Does not place shipments — use the Phase 15 golden test or API docs for that.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.businesses.models import Business
from app.businesses.schemas import BusinessCapabilities
from app.core.db import SessionLocal
from app.tenants.models import Tenant
from app.verticals.courier import COURIER_CAPABILITIES


async def main() -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "courier-demo"))
        if not tenant:
            tenant = Tenant(
                name="Courier Demo",
                slug="courier-demo",
                status="ACTIVE",
                config={"default_currency": "INR", "default_timezone": "Asia/Kolkata"},
            )
            db.add(tenant)
            await db.flush()

        biz = await db.scalar(
            select(Business).where(
                Business.tenant_id == tenant.id, Business.name == "CityDash Courier"
            )
        )
        caps = COURIER_CAPABILITIES.model_dump()
        if not biz:
            biz = Business(
                tenant_id=tenant.id,
                name="CityDash Courier",
                type="COURIER",
                status="ACTIVE",
                capabilities=caps,
                settings={"currency": "INR"},
                contact={},
            )
            db.add(biz)
            await db.flush()

        await db.commit()
        print(f"Courier demo ready: tenant={tenant.id} business={biz.id}")
        print(
            "Capabilities:",
            BusinessCapabilities.model_validate(biz.capabilities).model_dump(),
        )
        print(
            "Quote: POST /api/v1/courier/quote "
            '{"pickup":{"lat":12.97,"lng":77.59},"drop":{"lat":12.93,"lng":77.62},'
            '"weight_kg":2,"vehicle_type":"BIKE"}'
        )


if __name__ == "__main__":
    asyncio.run(main())
