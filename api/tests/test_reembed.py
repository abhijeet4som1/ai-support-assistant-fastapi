"""`reembed_all` on a real database: guidelines are ingested through the normal upload path with
the fake embedder, a correction is stored, then everything is re-embedded with a different
embedder and every stored vector must come from the new one."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.db.models import Feedback, GuidelineChunk
from app.db.reembed import ReembedResult, reembed_all
from app.rag.embeddings import FakeEmbedder
from app.rag.retrieval import vector_to_list
from tests.conftest import AppHarness
from tests.helpers import company_with_guidelines, create_conversation, send


class FlippedEmbedder:
    """The fake embedder with every vector negated: still unit length, never equal to the original."""

    model = "fake-flipped"

    def __init__(self) -> None:
        self._base = FakeEmbedder()
        self.dimensions = self._base.dimensions

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[-x for x in v] for v in await self._base.embed_documents(texts)]

    async def embed_query(self, text: str) -> list[float]:
        return [-x for x in await self._base.embed_query(text)]


async def test_replaces_every_chunk_and_correction_vector(t: AppHarness) -> None:
    auth = await t.auth()
    company, version_id = await company_with_guidelines(t, auth)
    conversation = await create_conversation(t, auth, company)
    sent = await send(t, auth, conversation, "The wrong book arrived, what do I do?")
    assistant_id = sent.json()["assistantMessage"]["id"]
    res = await t.client.put(
        f"/api/messages/{assistant_id}/feedback",
        headers=auth,
        json={"rating": "down", "correctedAnswer": "Apologise and send the right book."},
    )
    assert res.status_code == 200

    async with t.sessions() as session:
        before = {
            c.id: vector_to_list(c.embedding)
            for c in (
                await session.scalars(
                    select(GuidelineChunk).where(GuidelineChunk.version_id == UUID(version_id))
                )
            ).all()
        }
        feedback_before = vector_to_list((await session.scalar(select(Feedback))).query_embedding)  # type: ignore[union-attr]
    assert len(before) > 1 and all(before.values())

    progress: list[str] = []
    async with t.sessions() as session:
        result = await reembed_all(
            session,
            FlippedEmbedder(),
            batch_size=3,
            on_progress=lambda done, total, what: progress.append(f"{what} {done}/{total}"),
        )
    assert result == ReembedResult(chunks=len(before), feedback=1)
    assert progress[-1] == "corrections 1/1"
    assert f"chunks {len(before)}/{len(before)}" in progress
    assert len([p for p in progress if p.startswith("chunks")]) == -(-len(before) // 3)

    async with t.sessions() as session:
        after = (
            await session.scalars(
                select(GuidelineChunk).where(GuidelineChunk.version_id == UUID(version_id))
            )
        ).all()
        for chunk in after:
            old = before[chunk.id]
            new = vector_to_list(chunk.embedding)
            assert old is not None and new is not None and len(new) == len(old)
            assert all(abs(x + y) < 1e-6 for x, y in zip(new, old, strict=True))
        feedback_after = vector_to_list((await session.scalar(select(Feedback))).query_embedding)  # type: ignore[union-attr]
    assert feedback_before is not None and feedback_after is not None
    assert all(abs(x + y) < 1e-6 for x, y in zip(feedback_after, feedback_before, strict=True))


async def test_is_a_no_op_on_an_empty_database(t: AppHarness) -> None:
    async with t.sessions() as session:
        assert await reembed_all(session, FlippedEmbedder()) == ReembedResult(chunks=0, feedback=0)
