"""Seed platform-default India GST tax rules.

Usage:
  cd backend && PYTHONPATH=. python -m app.scripts.seed_tax_rules
"""

from __future__ import annotations

import asyncio

from app.core.db import SessionLocal
from app.taxation.service import seed_india_default_rules


async def main() -> None:
    async with SessionLocal() as session:
        rules = await seed_india_default_rules(session)
        print(f"Seeded/ensured {len(rules)} tax rules")


if __name__ == "__main__":
    asyncio.run(main())
