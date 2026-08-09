"""Seed a demo FOOD restaurant for local golden-path exploration.

Usage:
  cd backend && PYTHONPATH=. python -m app.scripts.seed_food_demo

Creates (idempotent by slug):
  tenant food-demo, FOOD business Spice Kitchen, location, menu item + addon.
Does not place orders — use the Phase 13 golden test or API docs for that.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.businesses.models import Business
from app.businesses.schemas import BusinessCapabilities
from app.catalog.models import Addon, Category, Product, ProductAddonLink, Variant
from app.core.db import SessionLocal
from app.locations.models import BusinessLocation
from app.tenants.models import Tenant
from app.verticals.food import FOOD_CAPABILITIES


async def main() -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "food-demo"))
        if not tenant:
            tenant = Tenant(
                name="Food Demo",
                slug="food-demo",
                status="ACTIVE",
                config={"default_currency": "INR", "default_timezone": "Asia/Kolkata"},
            )
            db.add(tenant)
            await db.flush()

        biz = await db.scalar(
            select(Business).where(
                Business.tenant_id == tenant.id, Business.name == "Spice Kitchen"
            )
        )
        caps = FOOD_CAPABILITIES.model_dump()
        if not biz:
            biz = Business(
                tenant_id=tenant.id,
                name="Spice Kitchen",
                type="FOOD",
                status="ACTIVE",
                capabilities=caps,
                settings={"preparation_time_minutes": 20, "currency": "INR"},
                contact={},
            )
            db.add(biz)
            await db.flush()

        loc = await db.scalar(
            select(BusinessLocation).where(
                BusinessLocation.business_id == biz.id, BusinessLocation.name == "Indiranagar"
            )
        )
        if not loc:
            loc = BusinessLocation(
                tenant_id=tenant.id,
                business_id=biz.id,
                name="Indiranagar",
                address={
                    "line1": "100 100 Feet Rd",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "pincode": "560038",
                },
                lat=12.9784,
                lng=77.6408,
                hours=[{"day": "mon", "open": "10:00", "close": "23:00"}],
                timezone="Asia/Kolkata",
                is_active=True,
            )
            db.add(loc)

        category = await db.scalar(
            select(Category).where(Category.business_id == biz.id, Category.name == "Mains")
        )
        if not category:
            category = Category(
                tenant_id=tenant.id, business_id=biz.id, name="Mains", sort_order=0
            )
            db.add(category)
            await db.flush()

        product = await db.scalar(
            select(Product).where(
                Product.business_id == biz.id, Product.name == "Butter Chicken"
            )
        )
        if not product:
            product = Product(
                tenant_id=tenant.id,
                business_id=biz.id,
                category_id=category.id,
                name="Butter Chicken",
                is_active=True,
            )
            db.add(product)
            await db.flush()
            db.add(
                Variant(
                    tenant_id=tenant.id,
                    product_id=product.id,
                    name="Regular",
                    base_price_paise=29900,
                    is_available=True,
                )
            )

        addon = await db.scalar(
            select(Addon).where(Addon.business_id == biz.id, Addon.name == "Extra Butter")
        )
        if not addon:
            addon = Addon(
                tenant_id=tenant.id,
                business_id=biz.id,
                name="Extra Butter",
                price_paise=3000,
                max_qty=2,
                is_active=True,
            )
            db.add(addon)
            await db.flush()

        if product and addon:
            existing_link = await db.scalar(
                select(ProductAddonLink).where(
                    ProductAddonLink.product_id == product.id,
                    ProductAddonLink.addon_id == addon.id,
                )
            )
            if not existing_link:
                db.add(
                    ProductAddonLink(
                        product_id=product.id,
                        addon_id=addon.id,
                        group_name="extras",
                        is_required=False,
                    )
                )

        await db.commit()
        print(
            f"Food demo ready: tenant={tenant.id} business={biz.id} "
            f"location={loc.id if loc else 'n/a'}"
        )
        print(
            "Capabilities:",
            BusinessCapabilities.model_validate(biz.capabilities).model_dump(),
        )


if __name__ == "__main__":
    asyncio.run(main())
