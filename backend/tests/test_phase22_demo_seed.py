"""Phase 22: unified demo seed for local PWA testing."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select

from app.core.db import SessionLocal
from app.identity.models import User
from app.partners.models import DeliveryPartnerProfile
from app.scripts import seed_demo
from app.tenants.models import Tenant


@pytest.mark.asyncio
async def test_seed_demo_is_idempotent() -> None:
    await seed_demo.main()
    await seed_demo.main()

    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "commerce-demo"))
        assert tenant is not None
        customer = await db.scalar(
            select(User).where(
                User.email == "customer@demo.com", User.tenant_id == tenant.id
            )
        )
        rider = await db.scalar(
            select(User).where(User.email == "rider@demo.com", User.tenant_id == tenant.id)
        )
        assert customer is not None
        assert rider is not None
        partner = await db.scalar(
            select(DeliveryPartnerProfile).where(
                DeliveryPartnerProfile.tenant_id == tenant.id,
                DeliveryPartnerProfile.user_id == rider.id,
            )
        )
        assert partner is not None

    assert seed_demo._demo_env_path().exists()
    content = seed_demo._demo_env_path().read_text(encoding="utf-8")
    assert str(tenant.id) in content
    assert "customer@demo.com" in content
