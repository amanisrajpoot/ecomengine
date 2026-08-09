"""Unified demo tenant for local UI testing across all PWAs.

Usage:
  cd backend && python -m app.scripts.seed_demo

Creates (idempotent):
  - Tenant slug `commerce-demo` with Food + Grocery + Courier businesses
  - Demo users: customer, merchant, rider (+ roles & rider partner profile)
  - Writes `demo.env` at repo root with tenant ID and credentials

Run after: bootstrap_super_admin, seed_tax_rules, alembic upgrade head
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import select

from app.businesses.models import Business
from app.catalog.models import Addon, Category, Product, ProductAddonLink, Variant
from app.core.db import SessionLocal
from app.core import models as _orm  # noqa: F401 — register all tables
from app.identity.models import User, UserRoleBinding
from app.identity.rbac import Role
from app.identity.schemas import PasswordRegister
from app.identity.service import assign_role, register_with_password
from app.inventory.models import InventoryItem, StockMovement
from app.inventory.schemas import StockReason
from app.locations.models import BusinessLocation
from app.partners.models import DeliveryPartnerProfile, Vehicle
from app.tenants.models import Tenant
from app.verticals.courier import COURIER_CAPABILITIES
from app.verticals.food import FOOD_CAPABILITIES
from app.verticals.hyperlocal import HYPERLOCAL_CAPABILITIES

DEMO_PASSWORD = "Demo123!"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_ENV_PATH = REPO_ROOT / "demo.env"

DEMO_USERS = {
    "customer": ("customer@demo.com", Role.CUSTOMER, None),
    "merchant": ("merchant@demo.com", Role.BUSINESS_OWNER, "food"),
    "rider": ("rider@demo.com", Role.DELIVERY_PARTNER, None),
}


async def _get_or_create_user(
    db,
    *,
    tenant_id,
    email: str,
    password: str,
    display_name: str,
) -> User:
    user = await db.scalar(
        select(User).where(User.email == email.lower(), User.tenant_id == tenant_id)
    )
    if user:
        return user
    user, _token = await register_with_password(
        db,
        payload=PasswordRegister(email=email, password=password, display_name=display_name),
        tenant_id=tenant_id,
        role=Role.CUSTOMER,
    )
    return user


async def _ensure_role(
    db,
    *,
    user_id,
    tenant_id,
    role: Role,
    business_id=None,
) -> None:
    existing = await db.scalar(
        select(UserRoleBinding).where(
            UserRoleBinding.user_id == user_id,
            UserRoleBinding.role == role.value,
            UserRoleBinding.tenant_id == tenant_id,
            UserRoleBinding.business_id == business_id,
        )
    )
    if existing:
        return
    await assign_role(
        db,
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
        business_id=business_id,
    )


async def main() -> None:
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "commerce-demo"))
        if not tenant:
            tenant = Tenant(
                name="Commerce Demo",
                slug="commerce-demo",
                status="ACTIVE",
                config={
                    "default_currency": "INR",
                    "default_timezone": "Asia/Kolkata",
                    "ondc": {"bpp_id": "bpp.commerce-demo.local"},
                },
            )
            db.add(tenant)
            await db.flush()

        # --- Food: Spice Kitchen ---
        food = await db.scalar(
            select(Business).where(
                Business.tenant_id == tenant.id, Business.name == "Spice Kitchen"
            )
        )
        if not food:
            food = Business(
                tenant_id=tenant.id,
                name="Spice Kitchen",
                type="FOOD",
                status="ACTIVE",
                capabilities=FOOD_CAPABILITIES.model_dump(),
                settings={"preparation_time_minutes": 20, "currency": "INR"},
                contact={},
            )
            db.add(food)
            await db.flush()

        food_loc = await db.scalar(
            select(BusinessLocation).where(
                BusinessLocation.business_id == food.id,
                BusinessLocation.name == "Indiranagar",
            )
        )
        if not food_loc:
            food_loc = BusinessLocation(
                tenant_id=tenant.id,
                business_id=food.id,
                name="Indiranagar",
                address={
                    "line1": "100 100 Feet Rd",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "pincode": "560038",
                },
                lat=12.9784,
                lng=77.6408,
                service_area={"type": "radius", "radius_km": 8},
                hours=[{"day": "mon", "open": "10:00", "close": "23:00"}],
                timezone="Asia/Kolkata",
                is_active=True,
            )
            db.add(food_loc)
            await db.flush()

        food_cat = await db.scalar(
            select(Category).where(Category.business_id == food.id, Category.name == "Mains")
        )
        if not food_cat:
            food_cat = Category(
                tenant_id=tenant.id, business_id=food.id, name="Mains", sort_order=0
            )
            db.add(food_cat)
            await db.flush()

        food_product = await db.scalar(
            select(Product).where(
                Product.business_id == food.id, Product.name == "Butter Chicken"
            )
        )
        if not food_product:
            food_product = Product(
                tenant_id=tenant.id,
                business_id=food.id,
                category_id=food_cat.id,
                name="Butter Chicken",
                is_active=True,
            )
            db.add(food_product)
            await db.flush()
            db.add(
                Variant(
                    tenant_id=tenant.id,
                    product_id=food_product.id,
                    name="Regular",
                    base_price_paise=29900,
                    is_available=True,
                )
            )
            addon = Addon(
                tenant_id=tenant.id,
                business_id=food.id,
                name="Extra Butter",
                price_paise=3000,
                max_qty=2,
                is_active=True,
            )
            db.add(addon)
            await db.flush()
            db.add(
                ProductAddonLink(
                    product_id=food_product.id,
                    addon_id=addon.id,
                    group_name="extras",
                    is_required=False,
                )
            )

        # --- Grocery: FreshMart ---
        grocery = await db.scalar(
            select(Business).where(
                Business.tenant_id == tenant.id, Business.name == "FreshMart Indiranagar"
            )
        )
        if not grocery:
            grocery = Business(
                tenant_id=tenant.id,
                name="FreshMart Indiranagar",
                type="GROCERY",
                status="ACTIVE",
                capabilities=HYPERLOCAL_CAPABILITIES.model_dump(),
                settings={"currency": "INR"},
                contact={},
            )
            db.add(grocery)
            await db.flush()

        grocery_loc = await db.scalar(
            select(BusinessLocation).where(
                BusinessLocation.business_id == grocery.id,
                BusinessLocation.name == "Indiranagar Store",
            )
        )
        if not grocery_loc:
            grocery_loc = BusinessLocation(
                tenant_id=tenant.id,
                business_id=grocery.id,
                name="Indiranagar Store",
                address={
                    "line1": "12 12th Main",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "pincode": "560038",
                },
                lat=12.9790,
                lng=77.6410,
                service_area={"type": "radius", "radius_km": 5},
                hours=[{"day": "mon", "open": "08:00", "close": "22:00"}],
                timezone="Asia/Kolkata",
                is_active=True,
            )
            db.add(grocery_loc)
            await db.flush()

        milk = await db.scalar(
            select(Product).where(
                Product.business_id == grocery.id, Product.name == "Milk 1L"
            )
        )
        if not milk:
            g_cat = Category(
                tenant_id=tenant.id, business_id=grocery.id, name="Dairy", sort_order=0
            )
            db.add(g_cat)
            await db.flush()
            milk = Product(
                tenant_id=tenant.id,
                business_id=grocery.id,
                category_id=g_cat.id,
                name="Milk 1L",
                is_active=True,
            )
            db.add(milk)
            await db.flush()
            variant = Variant(
                tenant_id=tenant.id,
                product_id=milk.id,
                name="Default",
                base_price_paise=6500,
                sku="MILK-1L",
                is_available=True,
            )
            db.add(variant)
            await db.flush()
            item = InventoryItem(
                tenant_id=tenant.id,
                business_id=grocery.id,
                location_id=grocery_loc.id,
                variant_id=variant.id,
                on_hand=0,
                reserved=0,
                low_stock_threshold=5,
            )
            db.add(item)
            await db.flush()
            item.on_hand = 50
            db.add(
                StockMovement(
                    tenant_id=tenant.id,
                    inventory_item_id=item.id,
                    reason=StockReason.RECEIVE.value,
                    delta_on_hand=50,
                    delta_reserved=0,
                    note="seed_demo",
                )
            )

        # --- Courier: CityDash ---
        courier = await db.scalar(
            select(Business).where(
                Business.tenant_id == tenant.id, Business.name == "CityDash Courier"
            )
        )
        if not courier:
            courier = Business(
                tenant_id=tenant.id,
                name="CityDash Courier",
                type="COURIER",
                status="ACTIVE",
                capabilities=COURIER_CAPABILITIES.model_dump(),
                settings={"currency": "INR"},
                contact={},
            )
            db.add(courier)
            await db.flush()

        await db.commit()

        # Users (separate session commits inside register_with_password)
        customer = await _get_or_create_user(
            db,
            tenant_id=tenant.id,
            email="customer@demo.com",
            password=DEMO_PASSWORD,
            display_name="Demo Customer",
        )
        await _ensure_role(
            db, user_id=customer.id, tenant_id=tenant.id, role=Role.CUSTOMER
        )

        merchant = await _get_or_create_user(
            db,
            tenant_id=tenant.id,
            email="merchant@demo.com",
            password=DEMO_PASSWORD,
            display_name="Demo Merchant",
        )
        await _ensure_role(
            db,
            user_id=merchant.id,
            tenant_id=tenant.id,
            role=Role.BUSINESS_OWNER,
            business_id=food.id,
        )
        await _ensure_role(
            db,
            user_id=merchant.id,
            tenant_id=tenant.id,
            role=Role.BUSINESS_MANAGER,
            business_id=food.id,
        )

        rider = await _get_or_create_user(
            db,
            tenant_id=tenant.id,
            email="rider@demo.com",
            password=DEMO_PASSWORD,
            display_name="Demo Rider",
        )
        await _ensure_role(
            db, user_id=rider.id, tenant_id=tenant.id, role=Role.DELIVERY_PARTNER
        )

        partner = await db.scalar(
            select(DeliveryPartnerProfile).where(
                DeliveryPartnerProfile.tenant_id == tenant.id,
                DeliveryPartnerProfile.user_id == rider.id,
            )
        )
        if not partner:
            partner = DeliveryPartnerProfile(
                tenant_id=tenant.id,
                user_id=rider.id,
                status="ACTIVE",
                is_online=False,
                display_name="Demo Rider",
                current_lat=12.9784,
                current_lng=77.6408,
                documents={},
            )
            db.add(partner)
            await db.flush()
            db.add(
                Vehicle(
                    tenant_id=tenant.id,
                    partner_id=partner.id,
                    vehicle_type="BIKE",
                    registration="KA01DE1234",
                    is_active=True,
                )
            )

        await db.commit()

        demo_env = f"""# Generated by seed_demo — source before starting PWAs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TENANT_ID={tenant.id}

# Platform super admin (no tenant ID on admin login)
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=ChangeMe123!

# Demo tenant users (password for all: {DEMO_PASSWORD})
DEMO_CUSTOMER_EMAIL=customer@demo.com
DEMO_MERCHANT_EMAIL=merchant@demo.com
DEMO_RIDER_EMAIL=rider@demo.com
DEMO_PASSWORD={DEMO_PASSWORD}

# Business IDs (merchant PWA auto-selects first)
DEMO_FOOD_BUSINESS_ID={food.id}
DEMO_GROCERY_BUSINESS_ID={grocery.id}
DEMO_COURIER_BUSINESS_ID={courier.id}
"""
        DEMO_ENV_PATH.write_text(demo_env, encoding="utf-8")

        print("=" * 60)
        print("Commerce Engine demo ready")
        print("=" * 60)
        print(f"Tenant ID:  {tenant.id}")
        print(f"Tenant slug: commerce-demo")
        print()
        print("Demo users (all passwords: Demo123!):")
        print("  customer@demo.com  — Customer PWA")
        print("  merchant@demo.com  — Merchant PWA (Spice Kitchen)")
        print("  rider@demo.com     — Rider PWA")
        print("  admin@example.com  — Admin web (super admin, no tenant)")
        print()
        print("App URLs (after pnpm dev:*):")
        print("  Customer  http://localhost:3000")
        print("  Merchant  http://localhost:3001")
        print("  Rider     http://localhost:3002")
        print("  Admin     http://localhost:3003")
        print("  API docs  http://localhost:8000/docs")
        print()
        print(f"Credentials written to: {DEMO_ENV_PATH}")
        print("  source demo.env   # then start PWAs")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
