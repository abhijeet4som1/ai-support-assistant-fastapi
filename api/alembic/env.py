"""Alembic environment (async, asyncpg). The URL comes from DATABASE_URL or from
`config.attributes["connection"]` when migrations run programmatically."""

from __future__ import annotations

import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from alembic import context
from app.db.models import Base
from app.db.session import to_async_url

config = context.config
target_metadata = Base.metadata


def _run(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


async def _run_async(url: str) -> None:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            await conn.run_sync(_run)
            await conn.commit()
    finally:
        await engine.dispose()


def run_migrations_online() -> None:
    connection: AsyncConnection | None = config.attributes.get("connection")
    if connection is not None:
        # Called from app.db.migrate with an open async connection.
        asyncio.get_event_loop()  # sanity: we are inside run_sync, connection is sync-wrapped
        _run(connection)
        return
    url = config.get_main_option("sqlalchemy.url") or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is required to run migrations")
    asyncio.run(_run_async(to_async_url(url)))


if context.is_offline_mode():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
