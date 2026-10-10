from __future__ import annotations

import pytest

from tests.conftest import AppHarness


@pytest.fixture(scope="module")
async def auth(tm: AppHarness) -> dict[str, str]:
    return await tm.auth()


async def test_starts_empty(tm: AppHarness, auth: dict[str, str]) -> None:
    res = await tm.client.get("/api/companies", headers=auth)
    assert res.status_code == 200
    assert res.json()["items"] == []


async def test_creates_a_company_and_normalises_whitespace(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await tm.client.post(
        "/api/companies",
        headers=auth,
        json={"name": "  Bookshop   Ltd ", "description": "Online bookstore"},
    )
    assert res.status_code == 201
    company = res.json()["company"]
    assert company["name"] == "Bookshop Ltd"
    assert company["description"] == "Online bookstore"
    assert company["conversationCount"] == 0
    assert "activeGuidelines" not in company


async def test_rejects_duplicate_name_case_insensitively(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await tm.client.post("/api/companies", headers=auth, json={"name": "bookshop ltd"})
    assert res.status_code == 409
    assert res.headers["x-amzn-errortype"] == "ConflictError"
    assert "already exists" in res.json()["message"]


async def test_validates_the_name(tm: AppHarness, auth: dict[str, str]) -> None:
    res = await tm.client.post("/api/companies", headers=auth, json={"name": ""})
    assert res.status_code == 400
    assert res.json()["fieldList"][0]["path"] == "/name"


async def test_lists_gets_and_updates(tm: AppHarness, auth: dict[str, str]) -> None:
    items = (await tm.client.get("/api/companies", headers=auth)).json()["items"]
    assert [c["name"] for c in items] == ["Bookshop Ltd"]
    cid = items[0]["id"]
    get = await tm.client.get(f"/api/companies/{cid}", headers=auth)
    assert get.status_code == 200
    assert get.json()["company"]["id"] == cid
    upd = await tm.client.patch(
        f"/api/companies/{cid}", headers=auth, json={"description": "Books and more"}
    )
    assert upd.status_code == 200
    assert upd.json()["company"]["name"] == "Bookshop Ltd"
    assert upd.json()["company"]["description"] == "Books and more"


async def test_returns_not_found_for_unknown_ids(tm: AppHarness, auth: dict[str, str]) -> None:
    res = await tm.client.get("/api/companies/00000000-0000-0000-0000-000000000000", headers=auth)
    assert res.status_code == 404
    assert res.headers["x-amzn-errortype"] == "NotFoundError"
    assert (await tm.client.get("/api/companies/not-a-uuid", headers=auth)).status_code == 404
