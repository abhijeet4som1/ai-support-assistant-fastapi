"""Runs the Alembic migrations programmatically (api start-up, tests) or from the CLI:
`uv run python -m app.db.migrate`."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config as AlembicConfig
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import command

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def _alembic_config(url: str | None = None) -> AlembicConfig:
    cfg = AlembicConfig(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_INI.parent / "alembic"))
    if url:
        cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _upgrade_sync(connection: object) -> None:
    cfg = _alembic_config()
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


async def run_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(_upgrade_sync)


if __name__ == "__main__":
    import asyncio

    from app.config import load_config, load_dotenv_if_present
    from app.db.session import create_engine

    load_dotenv_if_present()
    cfg = load_config()
    engine = create_engine(cfg.DATABASE_URL)

    async def _main() -> None:
        await run_migrations(engine)
        await engine.dispose()
        print("migrations applied")

    asyncio.run(_main())
