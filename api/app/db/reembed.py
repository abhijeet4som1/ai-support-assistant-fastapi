"""Re-embeds every stored vector with the configured embedding model.

Run once after changing `GEMINI_EMBEDDING_MODEL`: chunk vectors and query vectors must come from
the same model, otherwise similarity scores are meaningless and retrieval silently degrades. The
dimension must stay the same (a dimension change also needs a schema migration). The api and
worker can keep running; each row is replaced in place and retrieval keeps working throughout,
mixing old and new vectors only until the run finishes.

CLI usage: uv run python -m app.db.reembed"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Feedback, GuidelineChunk, GuidelineVersion
from app.rag.embeddings import Embedder
from app.schemas import GuidelineStatus

Progress = Callable[[int, int, str], None]


@dataclass
class ReembedResult:
    chunks: int
    feedback: int


async def reembed_all(
    session: AsyncSession,
    embedder: Embedder,
    *,
    batch_size: int = 50,
    on_progress: Progress | None = None,
) -> ReembedResult:
    def progress(done: int, total: int, what: str) -> None:
        if on_progress:
            on_progress(done, total, what)

    # Guideline sections of every ready version (superseded and failed versions are never retrieved).
    version_ids = list(
        (
            await session.scalars(
                select(GuidelineVersion.id).where(GuidelineVersion.status == GuidelineStatus.ready)
            )
        ).all()
    )
    chunks = (
        (
            await session.execute(
                select(GuidelineChunk.id, GuidelineChunk.title, GuidelineChunk.content)
                .where(
                    GuidelineChunk.version_id.in_(version_ids),
                    GuidelineChunk.embedding.is_not(None),
                )
                .order_by(GuidelineChunk.version_id.asc(), GuidelineChunk.ordinal.asc())
            )
        ).all()
        if version_ids
        else []
    )
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        # Same text shape as the ingestion job, so re-embedding is equivalent to a fresh ingest.
        vectors = await embedder.embed_documents(
            [f"{title}\n{content}" if title else content for _, title, content in batch]
        )
        for (chunk_id, _, _), vector in zip(batch, vectors, strict=True):
            await session.execute(
                update(GuidelineChunk).where(GuidelineChunk.id == chunk_id).values(embedding=vector)
            )
        await session.commit()
        progress(min(i + batch_size, len(chunks)), len(chunks), "chunks")

    # Correction queries (embedded as queries, like the customer messages they are matched against).
    corrections = (
        await session.execute(
            select(Feedback.id, Feedback.query_text)
            .where(Feedback.query_embedding.is_not(None))
            .order_by(Feedback.created_at.asc())
        )
    ).all()
    for i, (fid, query_text) in enumerate(corrections):
        vector = await embedder.embed_query(query_text)
        await session.execute(
            update(Feedback).where(Feedback.id == fid).values(query_embedding=vector)
        )
        await session.commit()
        progress(i + 1, len(corrections), "corrections")

    return ReembedResult(chunks=len(chunks), feedback=len(corrections))


if __name__ == "__main__":
    import asyncio

    from app.config import load_config, load_dotenv_if_present
    from app.db.models import EMBEDDING_DIMENSIONS
    from app.db.session import create_engine, create_session_factory
    from app.logging import configure_logging, get_logger
    from app.rag.embeddings import GeminiEmbedder

    async def _main() -> None:
        load_dotenv_if_present()
        cfg = load_config()
        if cfg.GEMINI_EMBEDDING_DIMENSIONS != EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                f"GEMINI_EMBEDDING_DIMENSIONS={cfg.GEMINI_EMBEDDING_DIMENSIONS} does not match the "
                f"database vector size ({EMBEDDING_DIMENSIONS}); a dimension change needs a "
                "migration, not a re-embed."
            )
        configure_logging(cfg.LOG_LEVEL, cfg.LOG_PRETTY)
        log = get_logger("reembed", service="reembed")
        embedder = GeminiEmbedder(
            api_key=cfg.GEMINI_API_KEY,
            model=cfg.GEMINI_EMBEDDING_MODEL,
            dimensions=cfg.GEMINI_EMBEDDING_DIMENSIONS,
            timeout_ms=cfg.GEMINI_TIMEOUT_MS,
            log=log,
        )
        engine = create_engine(cfg.DATABASE_URL)
        log.info("re-embedding all vectors", model=embedder.model, dimensions=embedder.dimensions)
        async with create_session_factory(engine)() as session:
            result = await reembed_all(
                session,
                embedder,
                on_progress=lambda done, total, what: log.info(
                    "progress", done=done, total=total, what=what
                ),
            )
        await engine.dispose()
        log.info("re-embedding complete", chunks=result.chunks, feedback=result.feedback)

    asyncio.run(_main())
