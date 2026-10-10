"""Async engine and session factory (asyncpg). One session per request, one per job run."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

SessionFactory = async_sessionmaker[AsyncSession]


def to_async_url(url: str) -> str:
    """`postgres://` / `postgresql://` → `postgresql+asyncpg://` (same DATABASE_URL as the TS api)."""
    for prefix in ("postgresql+asyncpg://", "postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix) :]
    return url


def to_sync_url(url: str) -> str:
    """Plain `postgresql://` form for drivers that take libpq URLs (Procrastinate, asyncpg)."""
    for prefix in ("postgresql+asyncpg://", "postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix) :]
    return url


def create_engine(database_url: str, *, pool_size: int = 10) -> AsyncEngine:
    # No pre-ping: it costs a round trip on every checkout; stale connections are recycled on a
    # timer instead and a failed statement surfaces as a 500 the way it did before.
    return create_async_engine(
        to_async_url(database_url), pool_size=pool_size, max_overflow=5, pool_recycle=1800
    )


def create_session_factory(engine: AsyncEngine) -> SessionFactory:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


def create_read_session_factory(engine: AsyncEngine) -> SessionFactory:
    """Sessions for read-only requests: AUTOCOMMIT, so a GET costs its queries and nothing else
    (no BEGIN, no COMMIT or ROLLBACK round trips). Never use it where a row lock must be held."""
    return async_sessionmaker(
        engine.execution_options(isolation_level="AUTOCOMMIT"),
        expire_on_commit=False,
        autoflush=False,
    )


STARTUP_LOCK_KEY = 7_204_315_001


@asynccontextmanager
async def startup_lock(engine: AsyncEngine) -> AsyncIterator[None]:
    """A session-level Postgres advisory lock held for the duration of start-up work."""
    from sqlalchemy import text

    async with engine.connect() as conn:
        await conn.execute(text("SELECT pg_advisory_lock(:key)"), {"key": STARTUP_LOCK_KEY})
        try:
            yield
        finally:
            await conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": STARTUP_LOCK_KEY})


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[None]:
    """A transaction block that nests (SAVEPOINT) when the session already has one open."""
    if session.in_transaction():
        async with session.begin_nested():
            yield
    else:
        async with session.begin():
            yield


def is_unique_violation(err: BaseException) -> bool:
    """Detects a PostgreSQL unique-constraint violation through SQLAlchemy's error wrapping."""
    current: BaseException | None = err
    for _ in range(4):
        if current is None:
            return False
        code = getattr(current, "sqlstate", None) or getattr(current, "pgcode", None)
        if code == "23505":
            return True
        orig = getattr(current, "orig", None)
        current = orig if isinstance(orig, BaseException) else current.__cause__
    return False
