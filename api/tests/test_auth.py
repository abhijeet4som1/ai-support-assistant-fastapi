from __future__ import annotations

import pytest
from httpx import Response

from tests.conftest import AppHarness

pytestmark = pytest.mark.usefixtures("tm")


async def login(t: AppHarness, username: str = "agent1", password: str = "agent1pass") -> Response:
    return await t.client.post("/api/auth/login", json={"username": username, "password": password})


async def refresh(t: AppHarness, token: str) -> Response:
    return await t.client.post("/api/auth/refresh", json={"refreshToken": token})


async def me(t: AppHarness, access: str) -> Response:
    return await t.client.get("/api/auth/me", headers={"authorization": f"Bearer {access}"})


async def test_logs_in_a_seeded_user(tm: AppHarness) -> None:
    res = await login(tm)
    assert res.status_code == 200
    body = res.json()
    assert len(body["tokens"]["accessToken"].split(".")) == 3
    assert len(body["tokens"]["refreshToken"]) > 30
    assert body["tokens"]["refreshExpiresAt"] > body["tokens"]["accessExpiresAt"]
    assert body["user"]["username"] == "agent1"


async def test_rejects_wrong_password_and_unknown_user_alike(tm: AppHarness) -> None:
    wrong = await login(tm, "agent1", "nope")
    unknown = await login(tm, "ghost", "nope")
    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.headers["x-amzn-errortype"] == "UnauthorizedError"
    assert wrong.json() == unknown.json()


async def test_returns_validation_exception_with_field_paths(tm: AppHarness) -> None:
    res = await login(tm, "", "")
    assert res.status_code == 400
    assert res.headers["x-amzn-errortype"] == "ValidationException"
    assert sorted(f["path"] for f in res.json()["fieldList"]) == ["/password", "/username"]


async def test_resolves_current_user_from_bearer_token(tm: AppHarness) -> None:
    res = await me(tm, await tm.login())
    assert res.status_code == 200
    assert res.json()["user"]["username"] == "agent1"


async def test_requires_a_token_and_rejects_invalid_ones(tm: AppHarness) -> None:
    none = await tm.client.get("/api/auth/me")
    assert none.status_code == 401
    assert none.json()["message"] == "Authentication required"
    bad = await me(tm, "definitely.not.valid")
    assert bad.status_code == 401
    assert "expired" in bad.json()["message"] or "invalid" in bad.json()["message"]


async def test_rotates_refresh_tokens_and_revokes_the_family_on_reuse(tm: AppHarness) -> None:
    first = (await login(tm)).json()
    rotated = await refresh(tm, first["tokens"]["refreshToken"])
    assert rotated.status_code == 200
    second = rotated.json()
    assert second["tokens"]["refreshToken"] != first["tokens"]["refreshToken"]
    assert second["tokens"]["accessToken"] != first["tokens"]["accessToken"]
    assert (await me(tm, second["tokens"]["accessToken"])).status_code == 200

    # Replaying the rotated token is treated as theft: the whole family is revoked.
    replay = await refresh(tm, first["tokens"]["refreshToken"])
    assert replay.status_code == 401
    assert "reused" in replay.json()["message"]
    assert (await refresh(tm, second["tokens"]["refreshToken"])).status_code == 401


async def test_rejects_unknown_refresh_tokens(tm: AppHarness) -> None:
    res = await refresh(tm, "not-a-real-token")
    assert res.status_code == 401
    assert res.headers["x-amzn-errortype"] == "UnauthorizedError"


async def test_logout_revokes_the_family_only(tm: AppHarness) -> None:
    a = (await login(tm)).json()
    b = (await login(tm)).json()
    out = await tm.client.post(
        "/api/auth/logout", json={"refreshToken": a["tokens"]["refreshToken"]}
    )
    assert out.status_code == 200
    assert out.json()["revoked"] is True
    assert (await refresh(tm, a["tokens"]["refreshToken"])).status_code == 401
    assert (await refresh(tm, b["tokens"]["refreshToken"])).status_code == 200
    again = await tm.client.post("/api/auth/logout", json={"refreshToken": "unknown"})
    assert again.json()["revoked"] is False


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("GET", "/api/companies"),
        ("POST", "/api/companies"),
        ("GET", "/api/conversations"),
        ("POST", "/api/conversations"),
        ("GET", "/api/companies/x/guidelines"),
        ("PUT", "/api/companies/x/guidelines"),
        ("GET", "/api/guideline-versions/x"),
        ("PATCH", "/api/corrections/x"),
        ("PUT", "/api/messages/x/feedback"),
    ],
)
async def test_protects_every_operation_except_health_login_refresh_logout(
    tm: AppHarness, method: str, url: str
) -> None:
    res = await tm.client.request(method, url, json={} if method != "GET" else None)
    assert res.status_code == 401, f"{method} {url}"
