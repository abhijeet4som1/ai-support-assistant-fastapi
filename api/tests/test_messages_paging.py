"""Message paging on GET /api/conversations/{id}: the newest page first, older pages through
`before`, and the denormalised `lastCoverage` that backs the history coverage filter."""

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
    for content in ["Where is my order?", "Can I get a refund instead?", "Thanks a lot"]:
        assert (await send(tm, headers, s["conversation"], content)).status_code == 201
    return headers


async def page(tm: AppHarness, auth: dict[str, str], query: str = "") -> Any:
    res = await tm.client.get(f"/api/conversations/{s['conversation']}{query}", headers=auth)
    assert res.status_code == 200, res.text
    return res.json()


async def test_returns_every_message_by_default_with_no_older_cursor(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    p = await page(tm, auth)
    assert len(p["conversation"]["messages"]) == 6
    assert p["conversation"]["summary"]["messageCount"] == 6
    assert "olderCursor" not in p
    assert [m["role"] for m in p["conversation"]["messages"]] == ["customer", "assistant"] * 3


async def test_pages_from_the_newest_message_backwards(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    first = await page(tm, auth, "?limit=4")
    msgs = first["conversation"]["messages"]
    assert len(msgs) == 4
    assert msgs[0]["content"] == "Can I get a refund instead?"
    assert msgs[-2]["content"] == "Thanks a lot"
    assert msgs[-1]["role"] == "assistant"
    assert first["olderCursor"]

    older = await page(tm, auth, f"?limit=4&before={first['olderCursor']}")
    contents = [m["content"] for m in older["conversation"]["messages"]]
    assert len(contents) == 2 and contents[0] == "Where is my order?"
    assert "olderCursor" not in older
    seen = {m["id"] for m in msgs + older["conversation"]["messages"]}
    assert len(seen) == 6


async def test_rejects_an_invalid_cursor_gracefully(tm: AppHarness, auth: dict[str, str]) -> None:
    p = await page(tm, auth, "?limit=2&before=not-a-cursor")
    assert len(p["conversation"]["messages"]) == 2
    assert p["olderCursor"]


async def test_keeps_last_coverage_and_filters_the_list_by_it(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    p = await page(tm, auth, "?limit=1")
    coverage = p["conversation"]["summary"]["lastCoverage"]
    assert coverage
    lst = await tm.client.get(
        f"/api/conversations?companyId={s['company']}&coverage={coverage}", headers=auth
    )
    assert s["conversation"] in [c["id"] for c in lst.json()["items"]]
    other = "not_covered" if coverage == "covered" else "covered"
    none = await tm.client.get(
        f"/api/conversations?companyId={s['company']}&coverage={other}", headers=auth
    )
    assert s["conversation"] not in [c["id"] for c in none.json()["items"]]
