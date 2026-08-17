"""Initialize SQLite database for Playwright API E2E runs."""

from __future__ import annotations

import asyncio
import os

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.config import get_settings
from app.core.db import Base
from app.identity import service as identity_service


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, _compiler, **_kw) -> str:
    return "JSON"


async def main() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Register all ORM models on Base.metadata (same as pytest conftest).
    import app.main  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        await identity_service.create_bootstrap_super_admin(
            db,
            email=settings.bootstrap_super_admin_email,
            password=settings.bootstrap_super_admin_password,
        )
        from app.taxation.service import ensure_default_tax_rules

        await ensure_default_tax_rules(db)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
