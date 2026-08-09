"""Shared pytest fixtures for Phase 1 API tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.base import Base
from app.core.config import get_settings
from app.core.db import get_db
from app.identity.service import create_bootstrap_super_admin
from app.main import app as fastapi_app
from app.taxation.service import seed_india_default_rules

# Import models for metadata.
import app.businesses.models  # noqa: F401
import app.cart.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.fulfillment.models  # noqa: F401
import app.identity.models  # noqa: F401
import app.inventory.models  # noqa: F401
import app.ledger.models  # noqa: F401
import app.locations.models  # noqa: F401
import app.orders.models  # noqa: F401
import app.payments.models  # noqa: F401
import app.settlements.models  # noqa: F401
import app.taxation.models  # noqa: F401
import app.tenants.models  # noqa: F401

TEST_DATABASE_URL = get_settings().database_url


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def prepare_database() -> AsyncGenerator[None, None]:
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        await create_bootstrap_super_admin(
            session, email="admin@example.com", password="ChangeMe123!"
        )
        await seed_india_default_rules(session)
    await engine.dispose()
    yield


@pytest_asyncio.fixture(loop_scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()
    await engine.dispose()
