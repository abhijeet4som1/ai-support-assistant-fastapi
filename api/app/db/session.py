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
    return create_async_engine(
        to_async_url(database_url), pool_size=pool_size, max_overflow=5, pool_pre_ping=True
    )


def create_session_factory(engine: AsyncEngine) -> SessionFactory:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


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
