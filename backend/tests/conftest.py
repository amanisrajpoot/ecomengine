"""Pytest fixtures for async API tests."""

from __future__ import annotations

import os

# Use in-memory SQLite when Postgres is not available (local pytest without Docker).
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.config import get_settings
from app.core.db import Base, get_db
from app.identity import service as identity_service
from app.main import app

get_settings.cache_clear()


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, _compiler, **_kw) -> str:
    return "JSON"


settings = get_settings()
test_engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def reset_db() -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as db:
        await identity_service.create_bootstrap_super_admin(
            db,
            email=settings.bootstrap_super_admin_email,
            password=settings.bootstrap_super_admin_password,
        )


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
