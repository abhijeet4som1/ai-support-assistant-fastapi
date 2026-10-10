"""Retrieval over pgvector: cosine top-k of one guideline version, keyword rescue through
Postgres full-text search, correction retrieval and correction-anchored merging."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Feedback, GuidelineChunk
from app.rag.embeddings import Embedder
from app.rag.retrieval_types import RetrievedChunk, RetrievedCorrection


def to_vector_literal(v: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in v) + "]"


def vector_to_list(value: Any) -> list[float] | None:
    if value is None:
        return None
    if hasattr(value, "tolist"):
        return [float(x) for x in value.tolist()]
    return [float(x) for x in value]


async def retrieve_chunks(
    session: AsyncSession,
    embedder: Embedder,
    *,
    version_id: UUID,
    query: str,
    top_k: int,
    min_score: float,
) -> list[RetrievedChunk]:
    """Top-k guideline sections of one version by cosine similarity, filtered by a minimum score."""
    vector = await embedder.embed_query(query)
    return await retrieve_chunks_by_vector(
        session, version_id=version_id, vector=vector, top_k=top_k, min_score=min_score
    )


async def retrieve_chunks_by_vector(
    session: AsyncSession,
    *,
    version_id: UUID,
    vector: list[float],
    top_k: int,
    min_score: float,
) -> list[RetrievedChunk]:
    """Same as retrieve_chunks with an already computed query vector."""
    score = (1 - GuidelineChunk.embedding.cosine_distance(vector)).label("score")
    rows = await session.execute(
        select(
            GuidelineChunk.id,
            GuidelineChunk.ordinal,
            GuidelineChunk.title,
            GuidelineChunk.content,
            score,
        )
        .where(GuidelineChunk.version_id == version_id, GuidelineChunk.embedding.is_not(None))
        .order_by(score.desc())
        .limit(top_k)
    )
    return [
        RetrievedChunk(
            chunkId=str(chunk_id), ordinal=ordinal, title=title, content=content, score=float(s)
        )
        for chunk_id, ordinal, title, content, s in rows.all()
        if float(s) >= min_score
    ]


_RESCUE_SQL = text("""
    WITH lexemes AS (
      SELECT DISTINCT unnest(tsvector_to_array(to_tsvector('english', :query))) AS lexeme
    ),
    version_chunks AS (
      SELECT id, ordinal, title, content, embedding, search_vector
      FROM guideline_chunks
      WHERE version_id = CAST(:version_id AS uuid) AND embedding IS NOT NULL
    ),
    rare AS (
      SELECT l.lexeme
      FROM lexemes l
      JOIN version_chunks c ON c.search_vector @@ plainto_tsquery('english', l.lexeme)
      GROUP BY l.lexeme
      HAVING count(*) = 1 OR count(*) * 4 <= (SELECT count(*) FROM version_chunks)
    )
    SELECT c.id AS chunk_id, c.ordinal, c.title, c.content,
           1 - (c.embedding <=> CAST(:vec AS vector)) AS score,
           count(r.lexeme) AS hits
    FROM version_chunks c
    JOIN rare r ON c.search_vector @@ plainto_tsquery('english', r.lexeme)
    JOIN LATERAL (
      SELECT max(array_length(u.positions, 1)) AS tf
      FROM unnest(c.search_vector) u WHERE u.lexeme = r.lexeme
    ) t ON t.tf >= 2
    WHERE c.id <> ALL(CAST(:exclude AS uuid[]))
    GROUP BY c.id, c.ordinal, c.title, c.content, c.embedding
    ORDER BY hits DESC, score DESC
    LIMIT 1
""")


async def retrieve_keyword_rescue(
    session: AsyncSession,
    *,
    version_id: UUID,
    query: str,
    vector: list[float],
    exclude: list[str],
) -> RetrievedChunk | None:
    """Keyword rescue: one section the vector ranking missed but that contains a distinctive word
    of the message. Short emotional messages ("Worst VPN ever, cancel everything") embed as "angry
    customer", so every section scores alike and the one that matters (billing) can rank last;
    the word "cancel" still identifies it. The vector ranking is never reordered: the rescued
    section is appended, tagged `via: keyword`, so the evaluated top-k behaviour is unchanged.

    Distinctive = a stemmed content word of the message (stop words removed by Postgres) that
    occurs in at most a quarter of the version's sections, and at least twice in the candidate
    section: a word a section uses repeatedly is one of its topics ("cancel" in billing), a single
    incidental use is not ("could you tell me" in disconnections). Candidates are ranked by the
    number of such words they contain, then by cosine similarity. Returns None when nothing
    qualifies."""
    row = (
        await session.execute(
            _RESCUE_SQL,
            {
                "query": query,
                "version_id": str(version_id),
                "vec": to_vector_literal(vector),
                "exclude": [UUID(x) for x in exclude],
            },
        )
    ).first()
    if row is None:
        return None
    return RetrievedChunk(
        chunkId=str(row.chunk_id),
        ordinal=int(row.ordinal),
        title=row.title,
        content=row.content,
        score=float(row.score),
        via="keyword",
    )


async def retrieve_corrections(
    session: AsyncSession,
    embedder: Embedder,
    *,
    company_id: UUID,
    query: str,
    top_k: int,
    min_score: float,
) -> list[RetrievedCorrection]:
    """Active corrections (agent feedback) of a company similar to the query."""
    if top_k <= 0:
        return []
    vector = await embedder.embed_query(query)
    score = (1 - Feedback.query_embedding.cosine_distance(vector)).label("score")
    rows = await session.execute(
        select(
            Feedback.id,
            Feedback.rating,
            Feedback.query_text,
            Feedback.what_was_wrong,
            Feedback.corrected_answer,
            Feedback.query_embedding,
            score,
        )
        .where(
            Feedback.company_id == company_id,
            Feedback.active.is_(True),
            Feedback.query_embedding.is_not(None),
        )
        .order_by(score.desc())
        .limit(top_k)
    )
    return [
        RetrievedCorrection(
            correctionId=str(fid),
            rating=rating.value,
            queryText=query_text,
            whatWasWrong=what_was_wrong,
            correctedAnswer=corrected_answer,
            score=float(s),
            queryEmbedding=vector_to_list(embedding),
        )
        for fid, rating, query_text, what_was_wrong, corrected_answer, embedding, s in rows.all()
        if float(s) >= min_score
    ]


def merge_retrieved(
    primary: list[RetrievedChunk], via_correction: list[RetrievedChunk], max_extra: int
) -> list[RetrievedChunk]:
    """Correction-anchored retrieval: a customer paraphrase can match a stored correction while
    its wording misses the guideline section the original question retrieved. The sections found
    through the correction's original question are appended so the model can ground the
    corrected answer."""
    seen = {c.chunkId for c in primary}
    extra: list[RetrievedChunk] = []
    for c in via_correction:
        if len(extra) >= max_extra:
            break
        if c.chunkId in seen:
            continue
        seen.add(c.chunkId)
        extra.append(
            RetrievedChunk(
                chunkId=c.chunkId,
                ordinal=c.ordinal,
                title=c.title,
                content=c.content,
                score=c.score,
                via="correction",
            )
        )
    return [*primary, *extra]
