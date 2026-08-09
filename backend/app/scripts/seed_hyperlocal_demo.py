"""Seed a demo GROCERY store for hyperlocal golden-path exploration.

Usage:
  cd backend && PYTHONPATH=. python -m app.scripts.seed_hyperlocal_demo

Creates (idempotent by slug):
  tenant hyperlocal-demo, GROCERY business FreshMart, location + stocked SKU.
Does not place orders — use the Phase 14 golden test or API docs for that.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.businesses.models import Business
from app.businesses.schemas import BusinessCapabilities
from app.catalog.models import Category, Product, Variant
from app.core.db import SessionLocal
from app.inventory.models import InventoryItem, StockMovement
from app.inventory.schemas import StockReason
from app.locations.models import BusinessLocation
from app.tenants.models import Tenant
from app.verticals.hyperlocal import HYPERLOCAL_CAPABILITIES


async def main() -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "hyperlocal-demo"))
        if not tenant:
            tenant = Tenant(
                name="Hyperlocal Demo",
                slug="hyperlocal-demo",
                status="ACTIVE",
                config={"default_currency": "INR", "default_timezone": "Asia/Kolkata"},
            )
            db.add(tenant)
            await db.flush()

        biz = await db.scalar(
            select(Business).where(
                Business.tenant_id == tenant.id, Business.name == "FreshMart Indiranagar"
            )
        )
        caps = HYPERLOCAL_CAPABILITIES.model_dump()
        if not biz:
            biz = Business(
                tenant_id=tenant.id,
                name="FreshMart Indiranagar",
                type="GROCERY",
                status="ACTIVE",
                capabilities=caps,
                settings={"currency": "INR"},
                contact={},
            )
            db.add(biz)
            await db.flush()

        loc = await db.scalar(
            select(BusinessLocation).where(
                BusinessLocation.business_id == biz.id,
                BusinessLocation.name == "Indiranagar Store",
            )
        )
        if not loc:
            loc = BusinessLocation(
                tenant_id=tenant.id,
                business_id=biz.id,
                name="Indiranagar Store",
                address={
                    "line1": "12 12th Main",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "pincode": "560038",
                },
                lat=12.9784,
                lng=77.6408,
                service_area={"type": "radius", "radius_km": 5},
                hours=[{"day": "mon", "open": "08:00", "close": "22:00"}],
                timezone="Asia/Kolkata",
                is_active=True,
            )
            db.add(loc)
            await db.flush()

        category = await db.scalar(
            select(Category).where(Category.business_id == biz.id, Category.name == "Dairy")
        )
        if not category:
            category = Category(
                tenant_id=tenant.id, business_id=biz.id, name="Dairy", sort_order=0
            )
            db.add(category)
            await db.flush()

        product = await db.scalar(
            select(Product).where(Product.business_id == biz.id, Product.name == "Milk 1L")
        )
        variant = None
        if not product:
            product = Product(
                tenant_id=tenant.id,
                business_id=biz.id,
                category_id=category.id,
                name="Milk 1L",
                is_active=True,
            )
            db.add(product)
            await db.flush()
            variant = Variant(
                tenant_id=tenant.id,
                product_id=product.id,
                name="Default",
                base_price_paise=6500,
                sku="MILK-1L",
                is_available=True,
            )
            db.add(variant)
            await db.flush()
        else:
            variant = await db.scalar(
                select(Variant).where(Variant.product_id == product.id)
            )

        if variant and loc:
            item = await db.scalar(
                select(InventoryItem).where(
                    InventoryItem.business_id == biz.id,
                    InventoryItem.location_id == loc.id,
                    InventoryItem.variant_id == variant.id,
                )
            )
            if not item:
                item = InventoryItem(
                    tenant_id=tenant.id,
                    business_id=biz.id,
                    location_id=loc.id,
                    variant_id=variant.id,
                    on_hand=0,
                    reserved=0,
                    low_stock_threshold=2,
                )
                db.add(item)
                await db.flush()
            if item.on_hand < 20:
                delta = 20 - item.on_hand
                item.on_hand += delta
                db.add(
                    StockMovement(
                        tenant_id=tenant.id,
                        inventory_item_id=item.id,
                        reason=StockReason.RECEIVE.value,
                        delta_on_hand=delta,
                        delta_reserved=0,
                        note="seed_hyperlocal_demo",
                    )
                )

        await db.commit()
        print(
            f"Hyperlocal demo ready: tenant={tenant.id} business={biz.id} "
            f"location={loc.id if loc else 'n/a'}"
        )
        print(
            "Capabilities:",
            BusinessCapabilities.model_validate(biz.capabilities).model_dump(),
        )
        print("Nearby: GET /api/v1/stores/nearby?lat=12.979&lng=77.641&radius_km=5")


if __name__ == "__main__":
    asyncio.run(main())
