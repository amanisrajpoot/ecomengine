"""Catalog HTTP routes nested under businesses."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.schemas import (
    AddonCreate,
    AddonRead,
    AddonUpdate,
    BundleCreate,
    BundleRead,
    BundleUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ProductAddonLinkCreate,
    ProductAddonLinkRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    VariantCreate,
    VariantRead,
    VariantUpdate,
)
from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError

router = APIRouter(tags=["catalog"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


# Categories


@router.post("/businesses/{business_id}/categories", response_model=CategoryRead)
async def create_category(
    business_id: uuid.UUID,
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CategoryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.create_category(
        db, tenant_id=tid, business_id=business_id, payload=payload
    )
    return CategoryRead.model_validate(row)


@router.get("/businesses/{business_id}/categories", response_model=list[CategoryRead])
async def list_categories(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[CategoryRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_categories(db, tenant_id=tid, business_id=business_id)
    return [CategoryRead.model_validate(r) for r in rows]


@router.patch(
    "/businesses/{business_id}/categories/{category_id}", response_model=CategoryRead
)
async def update_category(
    business_id: uuid.UUID,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CategoryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.update_category(
        db,
        tenant_id=tid,
        business_id=business_id,
        category_id=category_id,
        payload=payload,
    )
    return CategoryRead.model_validate(row)


# Products


@router.post("/businesses/{business_id}/products", response_model=ProductRead)
async def create_product(
    business_id: uuid.UUID,
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> ProductRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.create_product(
        db, tenant_id=tid, business_id=business_id, payload=payload
    )
    return ProductRead.model_validate(row)


@router.get("/businesses/{business_id}/products", response_model=list[ProductRead])
async def list_products(
    business_id: uuid.UUID,
    category_id: uuid.UUID | None = Query(default=None),
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[ProductRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_products(
        db,
        tenant_id=tid,
        business_id=business_id,
        category_id=category_id,
        active_only=active_only,
    )
    return [ProductRead.model_validate(r) for r in rows]


@router.get(
    "/businesses/{business_id}/products/{product_id}", response_model=ProductRead
)
async def get_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> ProductRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.get_product(
        db, tenant_id=tid, business_id=business_id, product_id=product_id
    )
    return ProductRead.model_validate(row)


@router.patch(
    "/businesses/{business_id}/products/{product_id}", response_model=ProductRead
)
async def update_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> ProductRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.update_product(
        db,
        tenant_id=tid,
        business_id=business_id,
        product_id=product_id,
        payload=payload,
    )
    return ProductRead.model_validate(row)


# Variants


@router.post(
    "/businesses/{business_id}/products/{product_id}/variants",
    response_model=VariantRead,
)
async def create_variant(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: VariantCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> VariantRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.create_variant(
        db,
        tenant_id=tid,
        business_id=business_id,
        product_id=product_id,
        payload=payload,
    )
    return VariantRead.model_validate(row)


@router.get(
    "/businesses/{business_id}/products/{product_id}/variants",
    response_model=list[VariantRead],
)
async def list_variants(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[VariantRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_variants(
        db, tenant_id=tid, business_id=business_id, product_id=product_id
    )
    return [VariantRead.model_validate(r) for r in rows]


@router.patch(
    "/businesses/{business_id}/products/{product_id}/variants/{variant_id}",
    response_model=VariantRead,
)
async def update_variant(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: VariantUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> VariantRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.update_variant(
        db,
        tenant_id=tid,
        business_id=business_id,
        product_id=product_id,
        variant_id=variant_id,
        payload=payload,
    )
    return VariantRead.model_validate(row)


# Addons


@router.post("/businesses/{business_id}/addons", response_model=AddonRead)
async def create_addon(
    business_id: uuid.UUID,
    payload: AddonCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> AddonRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.create_addon(
        db, tenant_id=tid, business_id=business_id, payload=payload
    )
    return AddonRead.model_validate(row)


@router.get("/businesses/{business_id}/addons", response_model=list[AddonRead])
async def list_addons(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[AddonRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_addons(db, tenant_id=tid, business_id=business_id)
    return [AddonRead.model_validate(r) for r in rows]


@router.patch("/businesses/{business_id}/addons/{addon_id}", response_model=AddonRead)
async def update_addon(
    business_id: uuid.UUID,
    addon_id: uuid.UUID,
    payload: AddonUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> AddonRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.update_addon(
        db,
        tenant_id=tid,
        business_id=business_id,
        addon_id=addon_id,
        payload=payload,
    )
    return AddonRead.model_validate(row)


@router.post(
    "/businesses/{business_id}/products/{product_id}/addons",
    response_model=ProductAddonLinkRead,
)
async def link_addon(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductAddonLinkCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> ProductAddonLinkRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.link_product_addon(
        db,
        tenant_id=tid,
        business_id=business_id,
        product_id=product_id,
        payload=payload,
    )
    return ProductAddonLinkRead.model_validate(row)


@router.get(
    "/businesses/{business_id}/products/{product_id}/addons",
    response_model=list[ProductAddonLinkRead],
)
async def list_product_addons(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[ProductAddonLinkRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_product_addons(
        db, tenant_id=tid, business_id=business_id, product_id=product_id
    )
    return [ProductAddonLinkRead.model_validate(r) for r in rows]


# Bundles


@router.post("/businesses/{business_id}/bundles", response_model=BundleRead)
async def create_bundle(
    business_id: uuid.UUID,
    payload: BundleCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> BundleRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.create_bundle(
        db, tenant_id=tid, business_id=business_id, payload=payload
    )
    return BundleRead.model_validate(row)


@router.get("/businesses/{business_id}/bundles", response_model=list[BundleRead])
async def list_bundles(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[BundleRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_bundles(db, tenant_id=tid, business_id=business_id)
    return [BundleRead.model_validate(r) for r in rows]


@router.patch(
    "/businesses/{business_id}/bundles/{bundle_id}", response_model=BundleRead
)
async def update_bundle(
    business_id: uuid.UUID,
    bundle_id: uuid.UUID,
    payload: BundleUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("catalog.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> BundleRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.update_bundle(
        db,
        tenant_id=tid,
        business_id=business_id,
        bundle_id=bundle_id,
        payload=payload,
    )
    return BundleRead.model_validate(row)
