from __future__ import annotations

from tests.conftest import TestApp


async def test_health_responds_without_auth_and_echoes_request_id(t: TestApp) -> None:
    res = await t.client.get("/api/health", headers={"x-request-id": "abc-123"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "api"
    assert body["time"].endswith("Z")
    assert res.headers["x-request-id"] == "abc-123"


async def test_generates_a_request_id_when_none_is_sent(t: TestApp) -> None:
    res = await t.client.get("/api/health")
    assert len(res.headers["x-request-id"]) == 36


async def test_serves_the_openapi_document_and_swagger_ui(t: TestApp) -> None:
    doc = await t.client.get("/api/openapi.json")
    assert doc.status_code == 200
    assert doc.json()["info"]["title"] == "AI Support Assistant API"
    ui = await t.client.get("/api/docs")
    assert ui.status_code == 200
    assert ui.headers["content-type"].startswith("text/html")


async def test_unknown_routes_answer_with_an_error_envelope(t: TestApp) -> None:
    res = await t.client.get("/api/nope", headers={"authorization": "Bearer nope"})
    assert res.status_code == 401
    assert res.headers["x-amzn-errortype"] == "UnauthorizedError"
