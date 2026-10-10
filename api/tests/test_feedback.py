from __future__ import annotations

from typing import Any

import pytest

from tests.conftest import AppHarness
from tests.helpers import company_with_guidelines, create_conversation, send

s: dict[str, Any] = {}


@pytest.fixture(scope="module")
async def auth(tm: AppHarness) -> dict[str, str]:
    headers = await tm.auth()
    s["company"], _ = await company_with_guidelines(tm, headers)
    s["conversation"] = await create_conversation(tm, headers, s["company"])
    sent = await send(
        tm,
        headers,
        s["conversation"],
        "My order arrived with the wrong book inside, what should I do?",
    )
    s["assistant"] = sent.json()["assistantMessage"]["id"]
    return headers


async def put(tm: AppHarness, auth: dict[str, str], url: str, body: dict[str, Any]) -> Any:
    return await tm.client.put(url, headers=auth, json=body)


async def test_requires_a_corrected_answer_for_a_thumbs_down(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await put(
        tm,
        auth,
        f"/api/messages/{s['assistant']}/feedback",
        {"rating": "down", "whatWasWrong": "Too vague"},
    )
    assert res.status_code == 400
    assert res.headers["x-amzn-errortype"] == "ValidationException"
    assert res.json()["fieldList"][0]["path"] == "/correctedAnswer"


async def test_stores_a_thumbs_down_with_query_and_version(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await put(
        tm,
        auth,
        f"/api/messages/{s['assistant']}/feedback",
        {
            "rating": "down",
            "whatWasWrong": "Did not ask the customer to confirm the title received",
            "correctedAnswer": "Hello [Name], I apologise for the mix-up. Could you confirm the title you received versus your order? I will ship the correct book today with a prepaid return label.",
        },
    )
    assert res.status_code == 200, res.text
    correction = res.json()["correction"]
    assert correction["rating"] == "down" and correction["active"] is True
    assert "wrong book" in correction["queryText"]
    assert correction["guidelineVersionId"]
    assert correction["user"]["username"] == "agent1"
    # The verdict is attached to the answer's trace as Langfuse scores.
    trace_id = next(
        x.trace_id for x in tm.tracer.turns if x.end and x.end.messageId == s["assistant"]
    )
    assert trace_id
    assert [(x.traceId, x.name, x.value, x.dataType) for x in tm.tracer.scores] == [
        (trace_id, "agent-rating", 0, "BOOLEAN"),
        (trace_id, "agent-correction", correction["correctedAnswer"], "TEXT"),
    ]


async def test_is_idempotent_per_user_and_message(tm: AppHarness, auth: dict[str, str]) -> None:
    res = await put(tm, auth, f"/api/messages/{s['assistant']}/feedback", {"rating": "up"})
    assert res.status_code == 200
    assert "correctedAnswer" not in res.json()["correction"]
    lst = await tm.client.get(f"/api/companies/{s['company']}/corrections", headers=auth)
    assert len(lst.json()["items"]) == 1
    conv = await tm.client.get(f"/api/conversations/{s['conversation']}", headers=auth)
    msg = next(m for m in conv.json()["conversation"]["messages"] if m["id"] == s["assistant"])
    assert len(msg["feedback"]) == 1
    assert msg["feedback"][0]["rating"] == "up"
    assert msg["feedback"][0]["user"]["username"] == "agent1"


async def test_feeds_similar_corrections_into_later_prompts(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    await put(
        tm,
        auth,
        f"/api/messages/{s['assistant']}/feedback",
        {
            "rating": "down",
            "whatWasWrong": "Missing confirmation step",
            "correctedAnswer": "Ask the customer to confirm the received title first.",
        },
    )
    fresh = await create_conversation(tm, auth, s["company"])
    res = await send(tm, auth, fresh, "I received the wrong book in my order, help!")
    assistant = res.json()["assistantMessage"]
    assert len(assistant["correctionsUsed"]) == 1
    # Correction-anchored retrieval ran: sections are unique and the trace carries the merged list.
    traced = tm.tracer.turns[-1].retrieval[1].sections  # type: ignore[index]
    assert len({x.chunkId for x in traced}) == len(traced)
    assert len(traced) >= 1
    last_turn = tm.chat_model.calls[-1].turns[-1].text
    assert "<corrections" in last_turn
    assert "Correct answer: Ask the customer to confirm the received title first." in last_turn


async def test_refuses_feedback_on_non_assistant_or_failed_messages(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    conv = await tm.client.get(f"/api/conversations/{s['conversation']}", headers=auth)
    customer = next(m for m in conv.json()["conversation"]["messages"] if m["role"] == "customer")
    res = await put(tm, auth, f"/api/messages/{customer['id']}/feedback", {"rating": "up"})
    assert res.status_code == 409
    assert (await put(tm, auth, "/api/messages/nope/feedback", {"rating": "up"})).status_code == 404


async def test_deactivates_corrections_when_guidelines_are_replaced_and_lets_agents_toggle(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await tm.client.put(
        f"/api/companies/{s['company']}/guidelines",
        headers={**auth, "content-type": "application/octet-stream", "x-filename": "v2.txt"},
        content=b"1. Wrong Product Delivered\nApologize and ship the correct item.\n\n2. Refunds\nRefund within 14 days.\n",
    )
    assert res.status_code == 202
    await tm.run_jobs()

    active = await tm.client.get(f"/api/companies/{s['company']}/corrections", headers=auth)
    assert active.json()["items"] == []
    allc = await tm.client.get(
        f"/api/companies/{s['company']}/corrections?includeInactive=true", headers=auth
    )
    items = allc.json()["items"]
    assert len(items) == 1 and items[0]["active"] is False

    reactivated = await tm.client.patch(
        f"/api/corrections/{items[0]['id']}", headers=auth, json={"active": True}
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["correction"]["active"] is True
    again = await tm.client.get(f"/api/companies/{s['company']}/corrections", headers=auth)
    assert len(again.json()["items"]) == 1
    assert (
        await tm.client.patch("/api/corrections/nope", headers=auth, json={"active": True})
    ).status_code == 404
