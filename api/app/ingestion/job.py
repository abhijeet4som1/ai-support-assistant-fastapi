"""Background ingestion of one guideline version: parse → chunk → embed → ready.
Each stage re-reads the version and stops quietly if it was superseded. Embedding is
resumable: chunks are inserted with NULL embeddings and filled in batches."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GuidelineChunk, GuidelineVersion, utcnow
from app.deps import AppDeps
from app.guidelines.service import set_active_version
from app.ingestion.chunker import chunk_text
from app.ingestion.parsers import detect_file_kind, extract_text
from app.lib import provider_error_message
from app.logging import Logger
from app.observability.tracer import EmbeddedBatch, IngestionEnd, IngestionMeta, IngestionRecorder
from app.schemas import GuidelineStatus


def describe_error(err: BaseException | str) -> str:
    """Human-readable failure reason; unwraps the JSON envelope Gemini puts in APIError messages."""
    message = provider_error_message(err) or str(err)
    return message[:500] + "…" if len(message) > 500 else message


class IngestionJob:
    def __init__(self, deps: AppDeps, *, embed_batch_size: int = 50) -> None:
        self.deps = deps
        self.embed_batch_size = embed_batch_size

    async def _load(self, session: AsyncSession, version_id: UUID) -> GuidelineVersion | None:
        session.expire_all()
        return await session.get(GuidelineVersion, version_id)

    async def _set_status(
        self, session: AsyncSession, version_id: UUID, status: GuidelineStatus, **extra: Any
    ) -> None:
        await session.execute(
            update(GuidelineVersion)
            .where(GuidelineVersion.id == version_id)
            .values(status=status, updated_at=utcnow(), **extra)
        )
        await session.commit()

    async def _advance(
        self, session: AsyncSession, log: Logger, version_id: UUID, nxt: GuidelineStatus
    ) -> bool:
        """Advances to `nxt` unless the version was superseded meanwhile. Returns False to stop."""
        v = await self._load(session, version_id)
        if v is None:
            return False
        if v.status == GuidelineStatus.superseded:
            log.info("ingestion stopped: version superseded", versionId=str(version_id))
            return False
        await self._set_status(session, version_id, nxt)
        return True

    async def run(self, payload: dict[str, Any]) -> None:
        version_id = UUID(str(payload["versionId"]))
        log = self.deps.log.bind(versionId=str(version_id))
        async with self.deps.sessions() as session:
            version = await self._load(session, version_id)
            if version is None:
                log.warning("ingestion skipped: version no longer exists")
                return
            if version.status in (GuidelineStatus.superseded, GuidelineStatus.ready):
                return
            meta = IngestionMeta(
                versionId=str(version_id),
                companyId=str(version.company_id),
                filename=version.filename,
                userId=str(version.created_by),
            )

            async def body(rec: IngestionRecorder) -> None:
                await self._run(session, version, rec, log)

            await self.deps.tracer.run_ingestion(meta, body)

    async def _run(
        self,
        session: AsyncSession,
        version: GuidelineVersion,
        rec: IngestionRecorder,
        log: Logger,
    ) -> None:
        version_id = version.id
        company_id = version.company_id
        embedder = self.deps.embedder
        try:
            # 1. Parse (skipped when resuming after the text was already extracted).
            text = version.raw_text
            if not text:
                if not await self._advance(session, log, version_id, GuidelineStatus.parsing):
                    rec.end(IngestionEnd("superseded"))
                    return
                detected = detect_file_kind(
                    version.filename, version.file_bytes, version.content_type
                )
                text = extract_text(detected.kind, version.file_bytes).strip()
                if not text:
                    raise RuntimeError("No readable text found in the file")
                await self._set_status(session, version_id, GuidelineStatus.parsing, raw_text=text)
                rec.step("parse", {"kind": detected.kind, "characters": len(text)})

            # 2. Chunk (skipped when chunks already exist from a previous attempt).
            existing = await session.scalar(
                select(func.count()).where(GuidelineChunk.version_id == version_id)
            )
            if not existing:
                if not await self._advance(session, log, version_id, GuidelineStatus.chunking):
                    rec.end(IngestionEnd("superseded"))
                    return
                chunks = chunk_text(text)
                if not chunks:
                    raise RuntimeError("The document produced no chunks")
                session.add_all(
                    GuidelineChunk(
                        version_id=version_id,
                        company_id=company_id,
                        ordinal=c.ordinal,
                        title=c.title,
                        content=c.content,
                        token_count=c.tokenCount,
                    )
                    for c in chunks
                )
                await session.commit()
                await self._set_status(
                    session,
                    version_id,
                    GuidelineStatus.chunking,
                    chunks_total=len(chunks),
                    chunks_embedded=0,
                )
                rec.step(
                    "chunk",
                    {"chunks": len(chunks), "tokens": sum(c.tokenCount for c in chunks)},
                )

            # 3. Embed in batches; resumable.
            if not await self._advance(session, log, version_id, GuidelineStatus.embedding):
                rec.end(IngestionEnd("superseded"))
                return
            while True:
                batch = (
                    await session.execute(
                        select(GuidelineChunk.id, GuidelineChunk.title, GuidelineChunk.content)
                        .where(
                            GuidelineChunk.version_id == version_id,
                            GuidelineChunk.embedding.is_(None),
                        )
                        .order_by(GuidelineChunk.ordinal.asc())
                        .limit(self.embed_batch_size)
                    )
                ).all()
                if not batch:
                    break
                started = time.monotonic()
                vectors = await embedder.embed_documents(
                    [f"{title}\n{content}" if title else content for _, title, content in batch]
                )
                rec.embedded(
                    EmbeddedBatch(
                        count=len(batch),
                        model=embedder.model,
                        dimensions=embedder.dimensions,
                        latencyMs=int((time.monotonic() - started) * 1000),
                    )
                )
                for (chunk_id, _, _), vector in zip(batch, vectors, strict=True):
                    await session.execute(
                        update(GuidelineChunk)
                        .where(GuidelineChunk.id == chunk_id)
                        .values(embedding=vector)
                    )
                await session.execute(
                    update(GuidelineVersion)
                    .where(GuidelineVersion.id == version_id)
                    .values(
                        chunks_embedded=GuidelineVersion.chunks_embedded + len(batch),
                        updated_at=utcnow(),
                    )
                )
                await session.commit()
                fresh = await self._load(session, version_id)
                if fresh is not None and fresh.status == GuidelineStatus.superseded:
                    log.info("ingestion stopped during embedding: version superseded")
                    rec.end(IngestionEnd("superseded"))
                    return

            # 4. Ready + activate (never overwrites a newer active version).
            if not await self._advance(session, log, version_id, GuidelineStatus.ready):
                rec.end(IngestionEnd("superseded"))
                return
            await self._set_status(
                session, version_id, GuidelineStatus.ready, ready_at=utcnow(), error=None
            )
            await set_active_version(session, company_id, version_id, force=False)
            rec.end(IngestionEnd("ready"))
            log.info("ingestion complete")
        except Exception as err:
            message = describe_error(err)
            log.error("ingestion failed", err=message)
            await session.rollback()
            await self._set_status(session, version_id, GuidelineStatus.failed, error=message)
            rec.end(IngestionEnd("failed", error=message))
            raise  # let the queue retry with backoff
