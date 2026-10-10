from __future__ import annotations

import pytest

from app.auth.jwt import TokenClaims, TokenSigner
from app.auth.middleware import is_public_route, public_routes_from_openapi, template_to_pattern
from app.auth.users import SeedUser, parse_seed_users
from app.config import load_config

signer = TokenSigner("test-secret-at-least-16-chars", 15)


def test_token_round_trips_claims() -> None:
    signed = signer.sign(TokenClaims(sub="u1", username="agent1"))
    assert signer.verify(signed.token) == TokenClaims(sub="u1", username="agent1")


def test_token_rejects_other_secret_garbage_and_expired() -> None:
    other = TokenSigner("another-secret-at-least-16", 1)
    assert signer.verify(other.sign(TokenClaims("u1", "agent1")).token) is None
    assert signer.verify("not-a-jwt") is None
    expired = TokenSigner("test-secret-at-least-16-chars", -1)
    assert signer.verify(expired.sign(TokenClaims("u1", "agent1")).token) is None


def test_parse_seed_users() -> None:
    assert parse_seed_users(" a:1 , b:pa:ss ") == [SeedUser("a", "1"), SeedUser("b", "pa:ss")]
    with pytest.raises(ValueError, match="username:password"):
        parse_seed_users("nocolon")
    with pytest.raises(ValueError, match="username:password"):
        parse_seed_users("a:")


MINIMAL = {
    "DATABASE_URL": "postgres://x:y@localhost/db",
    "JWT_SECRET": "a-sufficiently-long-secret",
    "GEMINI_API_KEY": "key",
}


def test_config_applies_defaults() -> None:
    cfg = load_config(MINIMAL)
    assert cfg.PORT == 3000
    assert cfg.RAG_TOP_K == 4
    assert cfg.GEMINI_EMBEDDING_DIMENSIONS == 768
    assert cfg.LOG_PRETTY is False


def test_config_lists_every_missing_variable() -> None:
    with pytest.raises(ValueError, match=r"DATABASE_URL[\s\S]*JWT_SECRET[\s\S]*GEMINI_API_KEY"):
        load_config({})


def test_config_rejects_out_of_range_scores_and_short_secrets() -> None:
    with pytest.raises(ValueError, match="RAG_MIN_SCORE"):
        load_config({**MINIMAL, "RAG_MIN_SCORE": "1.5"})
    with pytest.raises(ValueError, match="at least 16 characters"):
        load_config({**MINIMAL, "JWT_SECRET": "short"})


def test_public_routes_patterns() -> None:
    assert template_to_pattern("/api/companies/{companyId}/guidelines").match(
        "/api/companies/abc-1/guidelines"
    )
    assert not template_to_pattern("/api/companies/{companyId}").match(
        "/api/companies/abc/guidelines"
    )
    assert template_to_pattern("/api/health").match("/api/health/")
    routes = public_routes_from_openapi(
        {
            "paths": {
                "/a": {"get": {"security": []}, "post": {}},
                "/b": {"get": {"security": [{"bearer": []}]}},
            }
        }
    )
    assert is_public_route(routes, "GET", "/a")
    assert not is_public_route(routes, "POST", "/a")
    assert not is_public_route(routes, "GET", "/b")


def test_public_routes_derived_from_the_app_document() -> None:
    from app.jobs.queue import InMemoryQueue
    from app.main import build_deps, create_app
    from app.observability.tracer import create_recording_tracer
    from app.rag.embeddings import FakeEmbedder
    from app.rag.llm import FakeChatModel

    app = create_app(
        build_deps(
            load_config(MINIMAL),
            sessions=None,
            queue=InMemoryQueue(),
            embedder=FakeEmbedder(),
            chat_model=FakeChatModel(),
            tracer=create_recording_tracer(),
        )
    )
    routes = sorted(f"{r.method} {r.template}" for r in public_routes_from_openapi(app.openapi()))
    assert routes == [
        "GET /api/health",
        "POST /api/auth/login",
        "POST /api/auth/logout",
        "POST /api/auth/refresh",
    ]
