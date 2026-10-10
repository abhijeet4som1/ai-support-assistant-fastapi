"""A migrated pgvector Postgres for the evaluation harnesses: `TEST_DATABASE_URL` when set,
otherwise a throw-away testcontainer. Each `database()` call gives a fresh database."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from app.db.migrate import run_migrations
from app.db.session import SessionFactory, create_engine, create_session_factory, to_sync_url


class EvalPostgres:
    def __init__(self) -> None:
        self._container: Any = None
        external = os.environ.get("TEST_DATABASE_URL")
        if external:
            self.admin_url = to_sync_url(external)
        else:
            from testcontainers.postgres import PostgresContainer

            self._container = PostgresContainer("pgvector/pgvector:pg17", driver=None)
            self._container.start()
            self.admin_url = to_sync_url(self._container.get_connection_url())

    def stop(self) -> None:
        if self._container is not None:
            self._container.stop()

    @asynccontextmanager
    async def database(self) -> AsyncIterator[SessionFactory]:
        name = "eval_" + uuid.uuid4().hex[:10]
        conn = await asyncpg.connect(self.admin_url)
        try:
            await conn.execute(f'CREATE DATABASE "{name}"')
        finally:
            await conn.close()
        url = self.admin_url.rsplit("/", 1)[0] + "/" + name
        engine = create_engine(url, pool_size=4)
        await run_migrations(engine)
        try:
            yield create_session_factory(engine)
        finally:
            await engine.dispose()
            conn = await asyncpg.connect(self.admin_url)
            try:
                await conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            finally:
                await conn.close()
