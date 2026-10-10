"""Background worker: consumes ingestion jobs from Procrastinate (Postgres) and processes
guideline uploads (parse → chunk → embed). Same image as the api, different entry point:
`python -m app.worker`."""

from __future__ import annotations

import asyncio
import signal
from typing import Any

from app.config import load_config, load_dotenv_if_present
from app.db.session import create_engine, create_session_factory
from app.ingestion.job import IngestionJob
from app.jobs.queue import INGEST_GUIDELINES, create_procrastinate_queue
from app.logging import configure_logging, get_logger
from app.main import build_deps, check_embedding_dimensions
from app.observability.tracer import create_tracer_from_config
from app.rag.embeddings import GeminiEmbedder
from app.rag.llm import FakeChatModel


async def main() -> None:
    load_dotenv_if_present()
    config = load_config()
    check_embedding_dimensions(config)
    configure_logging(config.LOG_LEVEL, config.LOG_PRETTY)
    log = get_logger("worker", service="worker")

    engine = create_engine(config.DATABASE_URL, pool_size=4)
    queue = await create_procrastinate_queue(config.DATABASE_URL, log)
    embedder = GeminiEmbedder(
        api_key=config.GEMINI_API_KEY,
        model=config.GEMINI_EMBEDDING_MODEL,
        dimensions=config.GEMINI_EMBEDDING_DIMENSIONS,
        timeout_ms=config.GEMINI_TIMEOUT_MS,
        log=log,
    )
    tracer = create_tracer_from_config(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        base_url=config.LANGFUSE_BASE_URL,
        log=log,
    )
    deps = build_deps(
        config,
        sessions=create_session_factory(engine),
        queue=queue,
        embedder=embedder,
        chat_model=FakeChatModel(),  # the worker never chats
        tracer=tracer,
        log=log,
    )
    ingest = IngestionJob(deps)

    async def handler(payload: dict[str, Any], job_id: str) -> None:
        log.info("ingestion job started", jobId=job_id, versionId=payload.get("versionId"))
        await ingest.run(payload)

    await queue.subscribe(INGEST_GUIDELINES, handler)
    log.info("worker ready", model=embedder.model, dimensions=embedder.dimensions)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    log.info("worker shutting down")
    await queue.stop()
    await tracer.shutdown()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
