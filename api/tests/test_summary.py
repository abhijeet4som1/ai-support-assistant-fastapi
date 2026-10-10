"""Long conversations: turns that leave the history window are folded into a rolling summary."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from sqlalchemy import select

from app.db.models import Conversation
from tests.conftest import AppHarness, DatabaseHarness, make_test_app
from tests.helpers import company_with_guidelines, create_conversation, send

s: dict[str, Any] = {}


@pytest.fixture(scope="module")
async def t2(template_db: DatabaseHarness) -> AsyncIterator[AppHarness]:
    app = await make_test_app(template_db, CHAT_HISTORY_WINDOW=2)
    try:
        yield app
    finally:
        await app.close()


@pytest.fixture(scope="module")
async def auth(t2: AppHarness) -> dict[str, str]:
    headers = await t2.auth()
    company, _ = await company_with_guidelines(t2, headers)
    s["conversation"] = await create_conversation(t2, headers, company)
    return headers


async def test_does_not_summarise_while_the_history_fits(
    t2: AppHarness, auth: dict[str, str]
) -> None:
    assert (
        await send(t2, auth, s["conversation"], "My order 1001 arrived damaged.")
    ).status_code == 201
    assert (
        await send(t2, auth, s["conversation"], "It was a hardcover, the corner is crushed.")
    ).status_code == 201
    assert t2.chat_model.summaries == []


async def test_folds_turns_that_left_the_window_into_a_summary(
    t2: AppHarness, auth: dict[str, str]
) -> None:
    assert (
        await send(t2, auth, s["conversation"], "Can I get a replacement instead of a refund?")
    ).status_code == 201
    assert len(t2.chat_model.summaries) == 1
    call = t2.chat_model.calls[-1]
    assert "<conversation_summary>" in call.turns[0].text
    assert t2.chat_model.summaries[0] in call.turns[0].text
    # summary, ack, then the two-message window, then the latest message
    assert [x.role for x in call.turns] == ["user", "model", "user", "model", "user"]
    async with t2.sessions() as session:
        row = await session.scalar(
            select(Conversation).where(
                Conversation.id == __import__("uuid").UUID(s["conversation"])
            )
        )
    assert row is not None
    assert row.history_summary == t2.chat_model.summaries[0]
    assert row.history_summary_upto is not None
    trace = t2.tracer.turns[-1]
    assert trace.summary is not None
    assert trace.summary.messages == 2
    assert trace.summary.output == t2.chat_model.summaries[0]


async def test_extends_the_existing_summary(t2: AppHarness, auth: dict[str, str]) -> None:
    assert (
        await send(t2, auth, s["conversation"], "Great, how long will the replacement take?")
    ).status_code == 201
    assert len(t2.chat_model.summaries) == 2
    summary = t2.tracer.turns[-1].summary
    assert summary is not None
    assert "Previous summary:" in summary.input
    assert summary.messages == 2


async def test_keeps_answering_when_the_summariser_fails(
    t2: AppHarness, auth: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def down(system: str, text: str) -> str:
        raise RuntimeError("summary down")

    monkeypatch.setattr(t2.chat_model, "summarize", down)
    res = await send(t2, auth, s["conversation"], "Any update?")
    assert res.status_code == 201
    assert res.json()["assistantMessage"]["status"] == "ok"
    assert t2.tracer.turns[-1].summary is not None
    assert t2.tracer.turns[-1].summary.error == "summary failed"
    monkeypatch.undo()
    await send(t2, auth, s["conversation"], "Thanks.")
    # the messages skipped during the failure are folded in now (2 skipped + 2 new)
    assert t2.tracer.turns[-1].summary is not None
    assert t2.tracer.turns[-1].summary.messages == 4
