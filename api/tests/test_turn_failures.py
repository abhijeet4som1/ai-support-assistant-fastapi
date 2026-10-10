"""A provider failure at any point after the agent's message is stored must produce a failed
assistant turn (201, status "failed", reason kept), never a 500 that leaves the message without
an answer; and retrying the same message must reuse it instead of storing a duplicate."""

from __future__ import annotations

import pytest

from tests.conftest import AppHarness
from tests.helpers import company_with_guidelines, create_conversation, send


async def test_stores_a_failed_turn_when_embedding_fails_and_the_retry_reuses_the_message(
    t: AppHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    auth = await t.auth()
    company, _ = await company_with_guidelines(t, auth)
    conversation = await create_conversation(t, auth, company)

    async def failing(text: str) -> list[float]:
        raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr(t.embedder, "embed_query", failing)
    res = await send(t, auth, conversation, "Where is my order? It is two weeks late.")
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["userMessage"]["role"] == "customer" and body["userMessage"]["status"] == "ok"
    assert (
        body["assistantMessage"]["role"] == "assistant"
        and body["assistantMessage"]["status"] == "failed"
    )
    assert "embedding service unavailable" in body["assistantMessage"]["error"]
    monkeypatch.undo()

    retry = await send(t, auth, conversation, "Where is my order? It is two weeks late.")
    assert retry.status_code == 201
    assert retry.json()["assistantMessage"]["status"] == "ok"
    thread = (await t.client.get(f"/api/conversations/{conversation}", headers=auth)).json()[
        "conversation"
    ]["messages"]
    assert [(m["role"], m["status"]) for m in thread] == [("customer", "ok"), ("assistant", "ok")]
