from __future__ import annotations

from typing import Any

from tests.conftest import AppHarness, sample


async def create_company(t: AppHarness, auth: dict[str, str], name: str) -> str:
    res = await t.client.post("/api/companies", headers=auth, json={"name": name})
    assert res.status_code == 201, res.text
    return str(res.json()["company"]["id"])


async def upload_guidelines(
    t: AppHarness, auth: dict[str, str], company_id: str, body: bytes, filename: str
) -> dict[str, Any]:
    res = await t.client.put(
        f"/api/companies/{company_id}/guidelines",
        headers={**auth, "content-type": "application/octet-stream", "x-filename": filename},
        content=body,
    )
    assert res.status_code == 202, res.text
    return dict(res.json()["version"])


async def company_with_guidelines(
    t: AppHarness,
    auth: dict[str, str],
    name: str = "Bookshop",
    file: str = "bookshop_support_guidelines.txt",
) -> tuple[str, str]:
    company_id = await create_company(t, auth, name)
    version = await upload_guidelines(t, auth, company_id, sample(file), file)
    await t.run_jobs()
    return company_id, str(version["id"])


async def create_conversation(t: AppHarness, auth: dict[str, str], company_id: str) -> str:
    res = await t.client.post("/api/conversations", headers=auth, json={"companyId": company_id})
    assert res.status_code == 201, res.text
    return str(res.json()["conversation"]["summary"]["id"])


async def send(
    t: AppHarness, auth: dict[str, str], conversation_id: str, content: str, kind: str = "customer"
) -> Any:
    return await t.client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth,
        json={"kind": kind, "content": content},
    )
