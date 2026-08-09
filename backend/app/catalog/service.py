"""Catalog domain services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.service import get_business
from app.catalog.models import (
    Addon,
    Bundle,
    Category,
    Product,
    ProductAddonLink,
    Variant,
)
from app.catalog.schemas import (
    AddonCreate,
    AddonUpdate,
    BundleCreate,
    BundleUpdate,
    CategoryCreate,
    CategoryUpdate,
    ProductAddonLinkCreate,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)
from app.core.errors import AppError


async def _require_catalog_capability(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID
) -> None:
    business = await get_business(db, tenant_id=tenant_id, business_id=business_id)
    if not business.capabilities.get("catalog", False):
        raise AppError(
            "CATALOG_DISABLED",
            "Catalog capability is not enabled for this business",
            status_code=409,
        )


async def _get_product(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID, product_id: uuid.UUID
) -> Product:
    product = await db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.business_id == business_id,
            Product.tenant_id == tenant_id,
        )
    )
    if not product:
        raise AppError("PRODUCT_NOT_FOUND", "Product not found", status_code=404)
    return product


# --- Categories ---


async def create_category(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: CategoryCreate,
) -> Category:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    if payload.parent_id:
        parent = await db.scalar(
            select(Category).where(
                Category.id == payload.parent_id,
                Category.business_id == business_id,
                Category.tenant_id == tenant_id,
            )
        )
        if not parent:
            raise AppError("CATEGORY_NOT_FOUND", "Parent category not found", 404)
    category = Category(
        tenant_id=tenant_id,
        business_id=business_id,
        parent_id=payload.parent_id,
        name=payload.name,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def list_categories(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID
) -> list[Category]:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    stmt = (
        select(Category)
        .where(Category.tenant_id == tenant_id, Category.business_id == business_id)
        .order_by(Category.sort_order.asc(), Category.created_at.asc())
    )
    return list(await db.scalars(stmt))


async def update_category(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
) -> Category:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    category = await db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.business_id == business_id,
            Category.tenant_id == tenant_id,
        )
    )
    if not category:
        raise AppError("CATEGORY_NOT_FOUND", "Category not found", 404)
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


# --- Products ---


async def create_product(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: ProductCreate,
) -> Product:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    if payload.category_id:
        category = await db.scalar(
            select(Category).where(
                Category.id == payload.category_id,
                Category.business_id == business_id,
                Category.tenant_id == tenant_id,
            )
        )
        if not category:
            raise AppError("CATEGORY_NOT_FOUND", "Category not found", 404)
    product = Product(
        tenant_id=tenant_id,
        business_id=business_id,
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        images=payload.images,
        tags=payload.tags,
        is_active=payload.is_active,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def list_products(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    category_id: uuid.UUID | None = None,
    active_only: bool = False,
) -> list[Product]:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    stmt = select(Product).where(
        Product.tenant_id == tenant_id, Product.business_id == business_id
    )
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if active_only:
        stmt = stmt.where(Product.is_active.is_(True))
    stmt = stmt.order_by(Product.created_at.desc())
    return list(await db.scalars(stmt))


async def get_product(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID, product_id: uuid.UUID
) -> Product:
    return await _get_product(
        db, tenant_id=tenant_id, business_id=business_id, product_id=product_id
    )


async def update_product(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductUpdate,
) -> Product:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    product = await _get_product(
        db, tenant_id=tenant_id, business_id=business_id, product_id=product_id
    )
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


# --- Variants ---


async def create_variant(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: VariantCreate,
) -> Variant:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    await _get_product(db, tenant_id=tenant_id, business_id=business_id, product_id=product_id)
    variant = Variant(
        tenant_id=tenant_id,
        product_id=product_id,
        name=payload.name,
        sku=payload.sku,
        base_price_paise=payload.base_price_paise,
        is_available=payload.is_available,
        metadata_json=payload.metadata,
    )
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return variant


async def list_variants(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    product_id: uuid.UUID,
) -> list[Variant]:
    await _get_product(db, tenant_id=tenant_id, business_id=business_id, product_id=product_id)
    stmt = (
        select(Variant)
        .where(Variant.tenant_id == tenant_id, Variant.product_id == product_id)
        .order_by(Variant.created_at.asc())
    )
    return list(await db.scalars(stmt))


async def update_variant(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: VariantUpdate,
) -> Variant:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    await _get_product(db, tenant_id=tenant_id, business_id=business_id, product_id=product_id)
    variant = await db.scalar(
        select(Variant).where(
            Variant.id == variant_id,
            Variant.product_id == product_id,
            Variant.tenant_id == tenant_id,
        )
    )
    if not variant:
        raise AppError("VARIANT_NOT_FOUND", "Variant not found", 404)
    data = payload.model_dump(exclude_unset=True, mode="json")
    if "metadata" in data:
        variant.metadata_json = data.pop("metadata")
    for key, value in data.items():
        setattr(variant, key, value)
    await db.commit()
    await db.refresh(variant)
    return variant


# --- Addons ---


async def create_addon(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: AddonCreate,
) -> Addon:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    business = await get_business(db, tenant_id=tenant_id, business_id=business_id)
    if not business.capabilities.get("addons", False):
        raise AppError(
            "ADDONS_DISABLED",
            "Addons capability is not enabled for this business",
            status_code=409,
        )
    addon = Addon(
        tenant_id=tenant_id,
        business_id=business_id,
        name=payload.name,
        price_paise=payload.price_paise,
        max_qty=payload.max_qty,
        is_active=payload.is_active,
    )
    db.add(addon)
    await db.commit()
    await db.refresh(addon)
    return addon


async def list_addons(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID
) -> list[Addon]:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    stmt = (
        select(Addon)
        .where(Addon.tenant_id == tenant_id, Addon.business_id == business_id)
        .order_by(Addon.created_at.asc())
    )
    return list(await db.scalars(stmt))


async def update_addon(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    addon_id: uuid.UUID,
    payload: AddonUpdate,
) -> Addon:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    addon = await db.scalar(
        select(Addon).where(
            Addon.id == addon_id,
            Addon.business_id == business_id,
            Addon.tenant_id == tenant_id,
        )
    )
    if not addon:
        raise AppError("ADDON_NOT_FOUND", "Addon not found", 404)
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(addon, key, value)
    await db.commit()
    await db.refresh(addon)
    return addon


async def link_product_addon(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductAddonLinkCreate,
) -> ProductAddonLink:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    await _get_product(db, tenant_id=tenant_id, business_id=business_id, product_id=product_id)
    addon = await db.scalar(
        select(Addon).where(
            Addon.id == payload.addon_id,
            Addon.business_id == business_id,
            Addon.tenant_id == tenant_id,
        )
    )
    if not addon:
        raise AppError("ADDON_NOT_FOUND", "Addon not found", 404)
    existing = await db.scalar(
        select(ProductAddonLink).where(
            ProductAddonLink.product_id == product_id,
            ProductAddonLink.addon_id == payload.addon_id,
        )
    )
    if existing:
        return existing
    link = ProductAddonLink(
        product_id=product_id,
        addon_id=payload.addon_id,
        group_name=payload.group_name,
        is_required=payload.is_required,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def list_product_addons(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    product_id: uuid.UUID,
) -> list[ProductAddonLink]:
    await _get_product(db, tenant_id=tenant_id, business_id=business_id, product_id=product_id)
    return list(
        await db.scalars(select(ProductAddonLink).where(ProductAddonLink.product_id == product_id))
    )


# --- Bundles ---


async def create_bundle(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: BundleCreate,
) -> Bundle:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    bundle = Bundle(
        tenant_id=tenant_id,
        business_id=business_id,
        name=payload.name,
        price_paise=payload.price_paise,
        items=[item.model_dump(mode="json") for item in payload.items],
        is_active=payload.is_active,
    )
    db.add(bundle)
    await db.commit()
    await db.refresh(bundle)
    return bundle


async def list_bundles(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID
) -> list[Bundle]:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    stmt = (
        select(Bundle)
        .where(Bundle.tenant_id == tenant_id, Bundle.business_id == business_id)
        .order_by(Bundle.created_at.desc())
    )
    return list(await db.scalars(stmt))


async def update_bundle(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    bundle_id: uuid.UUID,
    payload: BundleUpdate,
) -> Bundle:
    await _require_catalog_capability(db, tenant_id=tenant_id, business_id=business_id)
    bundle = await db.scalar(
        select(Bundle).where(
            Bundle.id == bundle_id,
            Bundle.business_id == business_id,
            Bundle.tenant_id == tenant_id,
        )
    )
    if not bundle:
        raise AppError("BUNDLE_NOT_FOUND", "Bundle not found", 404)
    data = payload.model_dump(exclude_unset=True, mode="json")
    for key, value in data.items():
        setattr(bundle, key, value)
    await db.commit()
    await db.refresh(bundle)
    return bundle
