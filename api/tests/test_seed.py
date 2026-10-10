from __future__ import annotations

from app.db.seed import seed_companies
from app.logging import get_logger
from tests.conftest import AppHarness


async def test_creates_the_two_sample_companies_and_ingests_their_guidelines(t: AppHarness) -> None:
    log = get_logger("test")
    async with t.sessions() as session:
        created = await seed_companies(session, t.deps, log)
    assert created == ["Bookshop", "VPN SaaS"]
    await t.run_jobs()
    auth = await t.auth()
    items = (await t.client.get("/api/companies", headers=auth)).json()["items"]
    assert [(c["name"], c["activeGuidelines"]["chunksTotal"]) for c in items] == [
        ("Bookshop", 7),
        ("VPN SaaS", 10),
    ]
    async with t.sessions() as session:
        assert await seed_companies(session, t.deps, log) == []
