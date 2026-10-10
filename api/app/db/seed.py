"""Seeds users and the two sample companies at first start (filled in step 3)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import seed_users
from app.logging import Logger


async def run_seed(session: AsyncSession, deps: Any, log: Logger, seed_users_spec: str) -> None:
    users = await seed_users(session, seed_users_spec)
    if users:
        log.info("seeded users", users=users)
