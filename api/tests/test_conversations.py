from __future__ import annotations

from typing import Any

import pytest

from tests.conftest import AppHarness
from tests.helpers import company_with_guidelines, create_company, create_conversation, send

s: dict[str, Any] = {}


@pytest.fixture(scope="module")
async def auth(tm: AppHarness) -> dict[str, str]:
    headers = await tm.auth()
    s["auth2"] = await tm.auth("agent2", "agent2pass")
    s["bookshop"], _ = await company_with_guidelines(tm, headers)
    s["empty"] = await create_company(tm, headers, "Empty Co")
    return headers


async def get(tm: AppHarness, url: str, headers: dict[str, str]) -> Any:
    return await tm.client.get(url, headers=headers)


async def test_refuses_to_start_a_chat_without_processed_guidelines(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await tm.client.post("/api/conversations", headers=auth, json={"companyId": s["empty"]})
    assert res.status_code == 409
    assert res.headers["x-amzn-errortype"] == "GuidelinesNotReadyError"


async def test_creates_a_conversation(tm: AppHarness, auth: dict[str, str]) -> None:
    res = await tm.client.post(
        "/api/conversations", headers=auth, json={"companyId": s["bookshop"]}
    )
    assert res.status_code == 201
    summary = res.json()["conversation"]["summary"]
    assert summary["companyName"] == "Bookshop"
    assert summary["messageCount"] == 0
    assert res.json()["conversation"]["messages"] == []
    s["conversation"] = summary["id"]


async def test_answers_a_covered_question_with_grounded_cited_guidance(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await send(
        tm,
        auth,
        s["conversation"],
        "Hi, my order was supposed to arrive last week and the shipping tracking has not updated. Where is my package?",
    )
    assert res.status_code == 201, res.text
    body = res.json()
    user_message, assistant = body["userMessage"], body["assistantMessage"]
    assert user_message["role"] == "customer" and user_message["status"] == "ok"
    assert assistant["status"] == "ok"
    assert assistant["guidance"]["coverage"] == "covered"
    assert assistant["retrieval"][0]["title"] == "Shipping Issues"
    assert assistant["guidance"]["citations"][0]["title"] == "Shipping Issues"
    assert "[Name]" in assistant["guidance"]["recommendedReply"]
    assert assistant["promptTokens"] == 100
    assert assistant["completionTokens"] == 50
    assert assistant["thinkingTokens"] == 20
    assert assistant["totalTokens"] == 170
    assert assistant["model"] == "fake-chat"
    assert "error" not in assistant
    # The model received the section text and the customer message.
    last_turn = tm.chat_model.calls[-1].turns[-1].text
    assert "[S1] Shipping Issues" in last_turn
    assert "Where is my package?" in last_turn

    # The turn was traced: retrieval + generation with usage and context-window share.
    trace = tm.tracer.turns[-1]
    assert trace.meta.conversationId == s["conversation"]
    assert trace.meta.kind == "customer"
    assert trace.meta.companyName == "Bookshop"
    assert trace.retrieval is not None
    assert trace.retrieval[1].sections[0].title == "Shipping Issues"
    g = trace.generation
    assert g is not None
    assert (g.model, g.promptTokens, g.completionTokens, g.thinkingTokens, g.totalTokens) == (
        "fake-chat",
        100,
        50,
        20,
        170,
    )
    assert g.droppedHistoryTurns == 0
    assert 0 < g.contextUsedPct < 1
    assert "<customer_message>" in g.turns[-1].text
    assert trace.end is not None
    assert (trace.end.status, trace.end.coverage, trace.end.messageId) == (
        "ok",
        "covered",
        assistant["id"],
    )


async def test_carries_context_into_follow_ups_and_revises_on_instructions(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await send(
        tm, auth, s["conversation"], "Make it shorter and more formal.", kind="instruction"
    )
    assert res.status_code == 201
    assert "(revised)" in res.json()["assistantMessage"]["guidance"]["recommendedReply"]
    call = tm.chat_model.calls[-1]
    # history: customer, compacted assistant turn, then latest instruction turn
    assert [x.role for x in call.turns] == ["user", "model", "user"]
    assert call.turns[1].text.startswith("coverage: covered\nrecommendedReply: ")
    assert "<agent_instruction>" in call.turns[2].text


async def test_reports_not_covered_with_escalation(tm: AppHarness, auth: dict[str, str]) -> None:
    fresh = await create_conversation(tm, auth, s["bookshop"])
    res = await send(tm, auth, fresh, "Zxqv blorptastic quux fnord wibble?")
    assistant = res.json()["assistantMessage"]
    assert assistant["guidance"]["coverage"] == "not_covered"
    assert assistant["guidance"]["escalation"]["recommended"] is True
    assert assistant["retrieval"] == []


async def test_persists_a_failed_turn_and_retries_without_duplicating(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    tm.chat_model.fail_next = RuntimeError("quota exceeded")
    failed = await send(tm, auth, s["conversation"], "Can I return a damaged book?")
    assert failed.status_code == 201
    assert failed.json()["assistantMessage"]["status"] == "failed"
    assert failed.json()["assistantMessage"]["error"] == "quota exceeded"
    assert tm.tracer.turns[-1].generation is not None
    assert tm.tracer.turns[-1].generation.error == "quota exceeded"
    assert tm.tracer.turns[-1].end is not None and tm.tracer.turns[-1].end.status == "failed"
    before = len(
        (await get(tm, f"/api/conversations/{s['conversation']}", auth)).json()["conversation"][
            "messages"
        ]
    )

    retried = await send(tm, auth, s["conversation"], "Can I return a damaged book?")
    body = retried.json()
    assert body["assistantMessage"]["status"] == "ok"
    assert any(
        "Damaged" in (r.get("title") or "") or "Returns" in (r.get("title") or "")
        for r in body["assistantMessage"]["retrieval"]
    )
    after = (await get(tm, f"/api/conversations/{s['conversation']}", auth)).json()["conversation"][
        "messages"
    ]
    assert len(after) == before  # failed turn replaced, user message reused
    assert len([m for m in after if m["content"] == "Can I return a damaged book?"]) == 1


async def test_returns_the_full_conversation_with_a_title(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await get(tm, f"/api/conversations/{s['conversation']}", auth)
    conv = res.json()["conversation"]
    assert conv["summary"]["title"].startswith("Hi, my order was supposed")
    assert conv["summary"]["messageCount"] == len(conv["messages"])
    assert conv["messages"][0]["role"] == "customer"
    assert conv["messages"][1]["role"] == "assistant"
    assert "olderCursor" not in res.json()


async def test_keeps_conversations_private_to_the_agent(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    auth2 = s["auth2"]
    theirs = await create_conversation(tm, auth2, s["bookshop"])
    await send(tm, auth2, theirs, "Payment failed twice, what now?")

    agent2_ids = [c["id"] for c in (await get(tm, "/api/conversations", auth2)).json()["items"]]
    assert agent2_ids == [theirs]
    agent1_ids = [c["id"] for c in (await get(tm, "/api/conversations", auth)).json()["items"]]
    assert s["conversation"] in agent1_ids
    assert theirs not in agent1_ids

    # Reading, continuing or rating another agent's thread answers 404 (existence not revealed).
    assert (await get(tm, f"/api/conversations/{theirs}", auth)).status_code == 404
    assert (await send(tm, auth, theirs, "hi")).status_code == 404
    their_answer = (await get(tm, f"/api/conversations/{theirs}", auth2)).json()["conversation"][
        "messages"
    ][1]
    rate = await tm.client.put(
        f"/api/messages/{their_answer['id']}/feedback", headers=auth, json={"rating": "up"}
    )
    assert rate.status_code == 404

    # Company conversation counts are per agent as well.
    company = (await get(tm, f"/api/companies/{s['bookshop']}", auth2)).json()["company"]
    assert company["conversationCount"] == 1


async def test_filters_by_coverage_and_paginates_with_a_cursor(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    third = await create_conversation(tm, auth, s["bookshop"])
    await send(tm, auth, third, "Payment failed twice, what now?")

    all_ids = [c["id"] for c in (await get(tm, "/api/conversations", auth)).json()["items"]]
    assert all_ids[0] == third  # most recent activity first
    assert len(all_ids) == 3

    covered = (await get(tm, "/api/conversations?coverage=covered", auth)).json()["items"]
    assert third in [c["id"] for c in covered]
    bad = await get(tm, "/api/conversations?coverage=nope", auth)
    assert bad.status_code == 400
    assert bad.json()["fieldList"][0]["path"] == "/coverage"
    assert (await get(tm, "/api/conversations?limit=0", auth)).status_code == 400

    p1 = (await get(tm, "/api/conversations?limit=2", auth)).json()
    assert len(p1["items"]) == 2
    assert p1["nextCursor"]
    p2 = (await get(tm, f"/api/conversations?limit=2&cursor={p1['nextCursor']}", auth)).json()
    assert len(p2["items"]) == 1
    assert sorted(c["id"] for c in p1["items"] + p2["items"]) == sorted(all_ids)
    assert "nextCursor" not in p2
    by_company = (await get(tm, f"/api/conversations?companyId={s['empty']}", auth)).json()["items"]
    assert by_company == []


async def test_404s_for_unknown_conversations(tm: AppHarness, auth: dict[str, str]) -> None:
    res = await get(tm, "/api/conversations/00000000-0000-0000-0000-000000000000", auth)
    assert res.status_code == 404
    assert res.headers["x-amzn-errortype"] == "NotFoundError"
    assert (await get(tm, "/api/conversations/nope", auth)).status_code == 404


async def test_validates_the_message_body(tm: AppHarness, auth: dict[str, str]) -> None:
    res = await tm.client.post(
        f"/api/conversations/{s['conversation']}/messages",
        headers=auth,
        json={"kind": "bogus", "content": ""},
    )
    assert res.status_code == 400
    assert sorted(f["path"] for f in res.json()["fieldList"]) == ["/content", "/kind"]
