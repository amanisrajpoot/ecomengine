"""Bootstrap a platform SUPER_ADMIN user.

Usage:
  cd backend && PYTHONPATH=. python -m app.scripts.bootstrap_super_admin
"""

from __future__ import annotations

import asyncio
import os

from app.core.db import SessionLocal
from app.core import models as _orm  # noqa: F401 — register all tables
from app.identity.service import create_bootstrap_super_admin


async def main() -> None:
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "ChangeMe123!")
    async with SessionLocal() as session:
        user = await create_bootstrap_super_admin(session, email=email, password=password)
        print(f"Super admin ready: {user.email} ({user.id})")


if __name__ == "__main__":
    asyncio.run(main())
