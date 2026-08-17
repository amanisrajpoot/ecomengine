"""Catalog API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parent_id: uuid.UUID | None = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: uuid.UUID | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    business_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category_id: uuid.UUID | None = None
    description: str | None = None
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category_id: uuid.UUID | None = None
    description: str | None = None
    images: list[str] | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    business_id: uuid.UUID
    category_id: uuid.UUID | None
    name: str
    description: str | None
    images: list[Any]
    tags: list[Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str | None = Field(default=None, max_length=64)
    base_price_paise: int = Field(ge=0)
    is_available: bool = True
    meta: dict[str, Any] = Field(default_factory=dict)


class VariantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sku: str | None = Field(default=None, max_length=64)
    base_price_paise: int | None = Field(default=None, ge=0)
    is_available: bool | None = None
    meta: dict[str, Any] | None = None


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    name: str
    sku: str | None
    base_price_paise: int
    is_available: bool
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AddonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price_paise: int = Field(ge=0)
    max_qty: int = Field(default=1, ge=1)
    is_active: bool = True


class AddonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    price_paise: int | None = Field(default=None, ge=0)
    max_qty: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class AddonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    business_id: uuid.UUID
    name: str
    price_paise: int
    max_qty: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductAddonLinkCreate(BaseModel):
    addon_id: uuid.UUID
    group_name: str | None = None
    is_required: bool = False


class ProductAddonLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    addon_id: uuid.UUID
    group_name: str | None
    is_required: bool


class BundleItem(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class BundleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price_paise: int | None = Field(default=None, ge=0)
    items: list[BundleItem] = Field(default_factory=list)
    is_active: bool = True


class BundleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    price_paise: int | None = Field(default=None, ge=0)
    items: list[BundleItem] | None = None
    is_active: bool | None = None


class BundleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    business_id: uuid.UUID
    name: str
    price_paise: int | None
    items: list[Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
