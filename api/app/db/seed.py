"""Seed users and the two sample companies at first start. Idempotent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import seed_users
from app.db.models import Company, User
from app.deps import AppDeps
from app.guidelines.service import GuidelinesService, UploadInput
from app.logging import Logger

SEED_GUIDELINES_DIR = Path(__file__).resolve().parents[2] / "seed" / "guidelines"


@dataclass
class SampleCompany:
    name: str
    description: str
    file: str


SAMPLE_COMPANIES = [
    SampleCompany("Bookshop", "Online bookstore", "bookshop_support_guidelines.txt"),
    SampleCompany("VPN SaaS", "VPN service provider", "vpn_support_guidelines.txt"),
]


async def seed_companies(session: AsyncSession, deps: AppDeps, log: Logger) -> list[str]:
    """Creates the demo companies and enqueues ingestion of their sample guideline files.
    Idempotent: companies that already exist are left alone."""
    count = await session.scalar(select(func.count()).select_from(Company))
    if count:
        return []
    owner = await session.scalar(select(User).where(User.username == "agent1"))
    owner = owner or await session.scalar(select(User).limit(1))
    if owner is None:
        raise RuntimeError("cannot seed companies: no users exist")

    guidelines = GuidelinesService(
        session, deps.queue, max_upload_bytes=deps.config.max_upload_bytes
    )
    available = (
        {p.name for p in SEED_GUIDELINES_DIR.iterdir()} if SEED_GUIDELINES_DIR.is_dir() else set()
    )
    created: list[str] = []
    for sample in SAMPLE_COMPANIES:
        company = Company(name=sample.name, description=sample.description, created_by=owner.id)
        session.add(company)
        await session.commit()
        created.append(sample.name)
        if sample.file not in available:
            log.warning(
                "sample guideline file missing; company created without guidelines",
                file=sample.file,
            )
            continue
        await guidelines.upload(
            UploadInput(
                company_id=str(company.id),
                filename=sample.file,
                file_content_type="text/plain",
                body=(SEED_GUIDELINES_DIR / sample.file).read_bytes(),
                user_id=str(owner.id),
            )
        )
    return created


async def run_seed(session: AsyncSession, deps: AppDeps, log: Logger, seed_users_spec: str) -> None:
    users = await seed_users(session, seed_users_spec)
    if users:
        log.info("seeded users", users=users)
    companies = await seed_companies(session, deps, log)
    if companies:
        log.info("seeded companies (guideline ingestion queued)", companies=companies)


if __name__ == "__main__":
    import asyncio

    from app.config import load_config, load_dotenv_if_present
    from app.db.session import create_engine, create_session_factory
    from app.jobs.queue import create_procrastinate_queue
    from app.logging import configure_logging, get_logger
    from app.main import build_deps
    from app.observability.tracer import create_noop_tracer
    from app.rag.embeddings import FakeEmbedder
    from app.rag.llm import FakeChatModel

    async def _main() -> None:
        load_dotenv_if_present()
        cfg = load_config()
        configure_logging(cfg.LOG_LEVEL, cfg.LOG_PRETTY)
        log = get_logger("seed")
        engine = create_engine(cfg.DATABASE_URL)
        queue = await create_procrastinate_queue(cfg.DATABASE_URL, log)
        deps = build_deps(
            cfg,
            sessions=create_session_factory(engine),
            queue=queue,
            embedder=FakeEmbedder(),
            chat_model=FakeChatModel(),
            tracer=create_noop_tracer(),
            log=log,
        )
        async with deps.sessions() as session:
            await run_seed(session, deps, log, cfg.SEED_USERS)
        await queue.stop()
        await engine.dispose()

    asyncio.run(_main())
