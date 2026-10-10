from __future__ import annotations

from typing import Any

import pytest

from tests.conftest import AppHarness, sample

state: dict[str, Any] = {}


@pytest.fixture(scope="module")
async def auth(tm: AppHarness) -> dict[str, str]:
    headers = await tm.auth()
    res = await tm.client.post("/api/companies", headers=headers, json={"name": "Bookshop"})
    state["companyId"] = res.json()["company"]["id"]
    return headers


async def upload(
    tm: AppHarness, auth: dict[str, str], body: bytes | str, filename: str, **extra: str
):
    return await tm.client.put(
        f"/api/companies/{state['companyId']}/guidelines",
        headers={
            **auth,
            "content-type": "application/octet-stream",
            "x-filename": filename,
            **extra,
        },
        content=body.encode() if isinstance(body, str) else body,
    )


async def version(tm: AppHarness, auth: dict[str, str], vid: str) -> dict[str, Any]:
    res = await tm.client.get(f"/api/guideline-versions/{vid}", headers=auth)
    assert res.status_code == 200
    return res.json()["version"]


async def test_reports_guidelines_not_ready_before_any_upload(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await tm.client.get(f"/api/companies/{state['companyId']}/guidelines", headers=auth)
    assert res.status_code == 409
    assert res.headers["x-amzn-errortype"] == "GuidelinesNotReadyError"
    assert res.json()["companyId"] == state["companyId"]
    assert "latestStatus" not in res.json()


async def test_rejects_unsupported_and_oversized_files(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    bad = await upload(tm, auth, "MZ...", "setup.exe")
    assert bad.status_code == 415
    assert bad.headers["x-amzn-errortype"] == "UnsupportedMediaTypeError"
    big = await upload(tm, auth, b"a" * (1024 * 1024 + 1), "big.txt")
    assert big.status_code == 413
    assert big.headers["x-amzn-errortype"] == "PayloadTooLargeError"
    assert big.json()["maxBytes"] == 1024 * 1024
    missing = await tm.client.put(
        f"/api/companies/{state['companyId']}/guidelines", headers=auth, content=b"x"
    )
    assert missing.status_code == 400
    assert missing.json()["fieldList"][0]["path"] == "/X-Filename"


async def test_accepts_an_upload_and_processes_it_to_ready(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await upload(
        tm, auth, sample("bookshop_support_guidelines.txt"), "bookshop_support_guidelines.txt"
    )
    assert res.status_code == 202, res.text
    v = res.json()["version"]
    assert v["status"] == "queued"
    assert len(tm.queue.pending) == 1

    await tm.run_jobs()

    after = await version(tm, auth, v["id"])
    assert after["status"] == "ready"
    assert after["chunksTotal"] == 7
    assert after["chunksEmbedded"] == 7
    assert after["isActive"] is True
    assert after["readyAt"]
    trace = tm.tracer.ingestions[-1]
    assert [s[0] for s in trace.steps] == ["parse", "chunk"]
    assert sum(b.count for b in trace.batches) == 7
    assert trace.end is not None and trace.end.status == "ready"

    active = await tm.client.get(f"/api/companies/{state['companyId']}/guidelines", headers=auth)
    assert active.status_code == 200
    body = active.json()
    assert body["version"]["id"] == v["id"]
    assert "Shipping Issues" in body["text"]
    assert "Returns and Refunds" in [c.get("title") for c in body["chunks"]]


async def test_is_a_no_op_when_the_same_file_is_uploaded_again(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    res = await upload(
        tm, auth, sample("bookshop_support_guidelines.txt"), "bookshop_support_guidelines.txt"
    )
    assert res.status_code == 202
    assert res.json()["version"]["status"] == "ready"
    assert len(tm.queue.pending) == 0


async def test_rejects_an_upload_when_a_newer_version_exists_than_the_client_saw(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    lst = await tm.client.get(
        f"/api/companies/{state['companyId']}/guidelines/versions", headers=auth
    )
    latest_id = lst.json()["items"][0]["id"]
    conflict = await upload(
        tm,
        auth,
        sample("vpn_support_guidelines.txt"),
        "vpn.txt",
        **{"x-expected-version": "stale-id"},
    )
    assert conflict.status_code == 409
    assert conflict.headers["x-amzn-errortype"] == "GuidelinesConflictError"
    assert conflict.json()["latestVersionId"] == latest_id
    assert conflict.json()["uploadedBy"]["username"] == "agent1"
    ok = await upload(
        tm,
        auth,
        sample("vpn_support_guidelines.txt"),
        "vpn.txt",
        **{"x-expected-version": latest_id},
    )
    assert ok.status_code == 202


async def test_keeps_the_previous_version_active_until_the_new_one_is_ready(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    c = (await tm.client.get(f"/api/companies/{state['companyId']}", headers=auth)).json()[
        "company"
    ]
    assert c["activeGuidelines"]["filename"] == "bookshop_support_guidelines.txt"
    assert c["latestGuidelines"]["status"] == "queued"
    await tm.run_jobs()
    c2 = (await tm.client.get(f"/api/companies/{state['companyId']}", headers=auth)).json()[
        "company"
    ]
    assert c2["activeGuidelines"]["filename"] == "vpn.txt"
    assert c2["activeGuidelines"]["chunksTotal"] == 10


async def test_supersedes_an_in_flight_version_when_a_newer_upload_arrives(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    first = await upload(tm, auth, "1. Topic A\nSome guidance.\n", "a.txt")
    second = await upload(tm, auth, "1. Topic B\nOther guidance.\n", "b.txt")
    first_id = first.json()["version"]["id"]
    second_id = second.json()["version"]["id"]
    v1 = await version(tm, auth, first_id)
    assert v1["status"] == "superseded"
    assert v1["supersededBy"] == second_id
    await tm.run_jobs()
    assert (await version(tm, auth, first_id))["status"] == "superseded"
    v2 = await version(tm, auth, second_id)
    assert v2["status"] == "ready"
    assert v2["isActive"] is True


async def test_can_reactivate_an_older_ready_version_and_lists_newest_first(
    tm: AppHarness, auth: dict[str, str]
) -> None:
    items = (
        await tm.client.get(
            f"/api/companies/{state['companyId']}/guidelines/versions", headers=auth
        )
    ).json()["items"]
    assert items[0]["filename"] == "b.txt"
    vpn = next(v for v in items if v["filename"] == "vpn.txt")
    assert vpn["status"] == "ready"
    act = await tm.client.post(f"/api/guideline-versions/{vpn['id']}/activate", headers=auth)
    assert act.status_code == 200
    assert act.json()["version"]["isActive"] is True
    superseded = next(v for v in items if v["filename"] == "a.txt")
    bad = await tm.client.post(f"/api/guideline-versions/{superseded['id']}/activate", headers=auth)
    assert bad.status_code == 409
    assert bad.headers["x-amzn-errortype"] == "ConflictError"


async def test_marks_a_version_failed_when_the_embedder_breaks_and_allows_a_retry(
    tm: AppHarness, auth: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def broken(texts: list[str]) -> list[list[float]]:
        raise RuntimeError("quota exceeded")

    monkeypatch.setattr(tm.embedder, "embed_documents", broken)
    res = await upload(tm, auth, "1. Topic C\nGuidance C.\n", "c.txt")
    vid = res.json()["version"]["id"]
    with pytest.raises(RuntimeError, match="quota exceeded"):
        await tm.run_jobs()
    failed = await version(tm, auth, vid)
    assert failed["status"] == "failed"
    assert failed["error"] == "quota exceeded"
    assert tm.tracer.ingestions[-1].end is not None
    assert tm.tracer.ingestions[-1].end.status == "failed"

    monkeypatch.undo()
    retry = await tm.client.post(f"/api/guideline-versions/{vid}/retry", headers=auth)
    assert retry.status_code == 200
    assert retry.json()["version"]["status"] == "queued"
    await tm.run_jobs()
    done = await version(tm, auth, vid)
    assert done["status"] == "ready"
    assert done["chunksTotal"] == 1
    assert done["chunksEmbedded"] == 1
    again = await tm.client.post(f"/api/guideline-versions/{vid}/retry", headers=auth)
    assert again.status_code == 409


async def test_unknown_versions_and_companies_are_404(tm: AppHarness, auth: dict[str, str]) -> None:
    res = await tm.client.get(
        "/api/guideline-versions/00000000-0000-0000-0000-000000000000", headers=auth
    )
    assert res.status_code == 404
    assert res.json()["resource"] == "guidelineVersion"
    res = await tm.client.get("/api/companies/nope/guidelines/versions", headers=auth)
    assert res.status_code == 404
