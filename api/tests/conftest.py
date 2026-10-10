"""Test fixtures: one pgvector Postgres container per session, a template database migrated once,
and a fresh database (cloned from the template) per test app. The app is fully wired with seed
users, an in-memory job queue, the fake embedder and chat model and the recording tracer.
`run_jobs()` executes queued ingestion jobs synchronously."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer

from app.auth.users import seed_users
from app.config import Config, load_config
from app.db.migrate import run_migrations
from app.db.session import SessionFactory, create_engine, create_session_factory, to_sync_url
from app.ingestion.job import IngestionJob
from app.jobs.queue import INGEST_GUIDELINES, InMemoryQueue
from app.logging import configure_logging, get_logger
from app.main import build_deps, create_app
from app.observability.tracer import RecordingTracer, create_recording_tracer
from app.rag.embeddings import FakeEmbedder
from app.rag.llm import FakeChatModel

SEED_DIR = Path(__file__).resolve().parents[1] / "seed" / "guidelines"

TEST_ENV = {
    "NODE_ENV": "test",
    "DATABASE_URL": "postgres://unused",
    "JWT_SECRET": "test-secret-with-enough-length",
    "GEMINI_API_KEY": "test-key",
    "LOG_LEVEL": os.environ.get("TEST_LOG_LEVEL", "silent"),
    "SEED_USERS": "agent1:agent1pass,agent2:agent2pass",
    "MAX_UPLOAD_MB": "1",
    # The fake embedder (hashed bag of words) yields low cosine scores; lower the gate for tests.
    "RAG_MIN_SCORE": "0.05",
    "RAG_CORRECTIONS_MIN_SCORE": "0.05",
}

configure_logging(TEST_ENV["LOG_LEVEL"])


def test_config(**overrides: Any) -> Config:
    return load_config({**TEST_ENV, **{k: str(v) for k, v in overrides.items()}})


@dataclass
class DatabaseHarness:
    admin_url: str  # libpq URL of the maintenance database
    template: str

    def url_for(self, name: str) -> str:
        return self.admin_url.rsplit("/", 1)[0] + "/" + name

    async def create(self) -> str:
        name = "t_" + uuid.uuid4().hex[:12]
        conn = await asyncpg.connect(self.admin_url)
        try:
            await conn.execute(f'CREATE DATABASE "{name}" TEMPLATE "{self.template}"')
        finally:
            await conn.close()
        return self.url_for(name)

    async def drop(self, url: str) -> None:
        name = url.rsplit("/", 1)[1]
        conn = await asyncpg.connect(self.admin_url)
        try:
            await conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        finally:
            await conn.close()


@pytest.fixture(scope="session")
def postgres() -> Iterator[DatabaseHarness]:
    external = os.environ.get("TEST_DATABASE_URL")
    if external:
        yield DatabaseHarness(admin_url=to_sync_url(external), template="assistant_template")
        return
    with PostgresContainer("pgvector/pgvector:pg17", driver=None) as container:
        url = to_sync_url(container.get_connection_url())
        yield DatabaseHarness(admin_url=url, template="assistant_template")


@pytest.fixture(scope="session")
async def template_db(postgres: DatabaseHarness) -> DatabaseHarness:
    conn = await asyncpg.connect(postgres.admin_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", postgres.template
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{postgres.template}"')
    finally:
        await conn.close()
    if not exists:
        engine = create_engine(postgres.url_for(postgres.template), pool_size=2)
        await run_migrations(engine)
        await engine.dispose()
    return postgres


@dataclass
class AppHarness:
    app: Any
    client: AsyncClient
    sessions: SessionFactory
    queue: InMemoryQueue
    embedder: FakeEmbedder
    chat_model: FakeChatModel
    tracer: RecordingTracer
    deps: Any
    config: Config
    _close: Any

    async def run_jobs(self) -> None:
        await self.queue.drain()

    async def login(self, username: str = "agent1", password: str = "agent1pass") -> str:
        res = await self.client.post(
            "/api/auth/login", json={"username": username, "password": password}
        )
        if res.status_code != 200:
            raise RuntimeError(f"login failed: {res.status_code} {res.text}")
        return str(res.json()["tokens"]["accessToken"])

    async def auth(self, username: str = "agent1", password: str = "agent1pass") -> dict[str, str]:
        return {"authorization": f"Bearer {await self.login(username, password)}"}

    async def close(self) -> None:
        await self._close()


async def make_test_app(template_db: DatabaseHarness, **overrides: Any) -> AppHarness:
    config = test_config(**overrides)
    url = await template_db.create()
    engine = create_engine(url, pool_size=5)
    sessions = create_session_factory(engine)
    async with sessions() as session:
        await seed_users(session, config.SEED_USERS)
    queue = InMemoryQueue()
    embedder = FakeEmbedder()
    chat_model = FakeChatModel()
    tracer = create_recording_tracer()
    log = get_logger("test")
    deps = build_deps(
        config,
        sessions=sessions,
        queue=queue,
        embedder=embedder,
        chat_model=chat_model,
        tracer=tracer,
        log=log,
    )
    ingest = IngestionJob(deps, embed_batch_size=4)

    async def handler(payload: dict[str, Any], job_id: str) -> None:
        await ingest.run(payload)

    await queue.subscribe(INGEST_GUIDELINES, handler)
    app = create_app(deps)
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def close() -> None:
        await client.aclose()
        await engine.dispose()
        await template_db.drop(url)

    return AppHarness(
        app=app,
        client=client,
        sessions=sessions,
        queue=queue,
        embedder=embedder,
        chat_model=chat_model,
        tracer=tracer,
        deps=deps,
        config=config,
        _close=close,
    )


@pytest.fixture
async def t(template_db: DatabaseHarness) -> AsyncIterator[AppHarness]:
    """A fresh app per test function."""
    app = await make_test_app(template_db)
    try:
        yield app
    finally:
        await app.close()


@pytest.fixture(scope="module")
async def tm(template_db: DatabaseHarness) -> AsyncIterator[AppHarness]:
    """A fresh app per test module (ported `beforeAll` suites share state across tests)."""
    app = await make_test_app(template_db)
    try:
        yield app
    finally:
        await app.close()


def sample(name: str) -> bytes:
    return (SEED_DIR / name).read_bytes()
