"""Keyword rescue on a real database: the VPN guidelines are ingested through the normal upload
path, then the rescue query is exercised directly with the fake embedder's vectors."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest

from app.rag.retrieval import retrieve_keyword_rescue
from tests.conftest import AppHarness
from tests.helpers import company_with_guidelines

s: dict[str, Any] = {}


@pytest.fixture(scope="module")
async def version_id(tm: AppHarness) -> UUID:
    auth = await tm.auth()
    _, vid = await company_with_guidelines(tm, auth, "VPN SaaS", "vpn_support_guidelines.txt")
    return UUID(vid)


async def rescue(
    tm: AppHarness, version_id: UUID, query: str, exclude: list[str] | None = None
) -> Any:
    async with tm.sessions() as session:
        return await retrieve_keyword_rescue(
            session,
            version_id=version_id,
            query=query,
            vector=await tm.embedder.embed_query(query),
            exclude=exclude or [],
        )


async def test_finds_the_section_a_distinctive_word_points_at(
    tm: AppHarness, version_id: UUID
) -> None:
    hit = await rescue(tm, version_id, "Worst VPN I've ever paid for. Cancel everything.")
    assert hit is not None
    assert hit.title == "Billing and Subscription Issues"
    assert hit.via == "keyword"
    assert hit.score > 0


async def test_matches_stemmed_forms(tm: AppHarness, version_id: UUID) -> None:
    hit = await rescue(tm, version_id, "I am cancelling, this is useless")
    assert hit is not None and hit.title == "Billing and Subscription Issues"


async def test_ignores_common_words_and_returns_none_when_nothing_is_distinctive(
    tm: AppHarness, version_id: UUID
) -> None:
    # "vpn", "server" and "connect" appear in most VPN sections; none identifies one section.
    assert await rescue(tm, version_id, "vpn server connect") is None
    assert await rescue(tm, version_id, "hello there, thanks") is None


async def test_never_returns_a_section_already_in_the_retrieved_set(
    tm: AppHarness, version_id: UUID
) -> None:
    first = await rescue(tm, version_id, "cancel my subscription")
    assert first is not None
    second = await rescue(tm, version_id, "cancel my subscription", [first.chunkId])
    assert second is None or second.chunkId != first.chunkId
