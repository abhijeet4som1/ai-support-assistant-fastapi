"""`create_app(deps)` wires the FastAPI application from injected collaborators (tests pass fakes
exactly like the TypeScript `buildApp`); `production_app()` builds it from the environment with a
lifespan that migrates, seeds and connects the job queue. uvicorn entry: `app.main:app`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.auth.jwt import TokenSigner
from app.auth.middleware import AuthMiddleware, public_routes_from_openapi
from app.config import Config, load_config, load_dotenv_if_present
from app.deps import AppDeps
from app.errors import install_error_handlers
from app.logging import Logger, configure_logging, get_logger
from app.request_id import RequestIdMiddleware

API_TITLE = "AI Support Assistant API"
API_VERSION = "2026-09-13"
SECURITY_SCHEME = "smithy.api.httpBearerAuth"


def _custom_openapi(app: FastAPI) -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    doc = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description="Generated from the Pydantic models in api/app/schemas.py. Do not edit by hand.",
        routes=app.routes,
    )
    doc["security"] = [{SECURITY_SCHEME: []}]
    doc.setdefault("components", {}).setdefault("securitySchemes", {})[SECURITY_SCHEME] = {
        "type": "http",
        "description": "HTTP Bearer authentication",
        "scheme": "Bearer",
    }
    schemas = doc["components"].get("schemas", {})
    for name in ("HTTPValidationError", "ValidationError"):
        schemas.pop(name, None)
    for ops in doc["paths"].values():
        for op in ops.values():
            op.get("responses", {}).pop("422", None)
    app.openapi_schema = doc
    return doc


def create_app(deps: AppDeps, *, lifespan: Any = None) -> FastAPI:
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        swagger_ui_parameters={"docExpansion": "list", "persistAuthorization": True},
        lifespan=lifespan,
    )
    app.state.deps = deps
    app.openapi = lambda: _custom_openapi(app)  # type: ignore[method-assign]
    install_error_handlers(app)

    from app.routers import (
        auth,
        companies,
        conversations,
        feedback,
        guidelines,
        health,
    )

    for module in (health, auth, companies, guidelines, conversations, feedback):
        app.include_router(module.router)

    public_routes = public_routes_from_openapi(app.openapi())
    app.add_middleware(
        AuthMiddleware,
        auth_service=deps.auth_session,
        public_routes=lambda: public_routes,
        verify=deps.signer.verify,
    )
    app.add_middleware(RequestIdMiddleware)
    return app


def build_deps(
    config: Config,
    *,
    sessions: Any,
    queue: Any,
    embedder: Any,
    chat_model: Any,
    tracer: Any,
    log: Logger | None = None,
    read_sessions: Any = None,
) -> AppDeps:
    return AppDeps(
        config=config,
        sessions=sessions,
        queue=queue,
        embedder=embedder,
        chat_model=chat_model,
        tracer=tracer,
        log=log or get_logger("api"),
        signer=TokenSigner(config.JWT_SECRET, config.ACCESS_TOKEN_TTL_MINUTES),
        read_sessions=read_sessions,
    )


def check_embedding_dimensions(config: Config) -> None:
    from app.db.models import EMBEDDING_DIMENSIONS

    if config.GEMINI_EMBEDDING_DIMENSIONS != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"GEMINI_EMBEDDING_DIMENSIONS={config.GEMINI_EMBEDDING_DIMENSIONS} does not match the "
            f"database vector size ({EMBEDDING_DIMENSIONS}). Changing the embedding size requires "
            "a migration and re-ingesting all guidelines (see README.md)."
        )


def production_app() -> FastAPI:
    """The api entry: migrations, seed, serve. Refuses to start on an embedding-size mismatch."""
    from app.db.migrate import run_migrations
    from app.db.seed import run_seed
    from app.db.session import (
        create_engine,
        create_read_session_factory,
        create_session_factory,
        startup_lock,
    )
    from app.jobs.queue import create_procrastinate_queue
    from app.observability.tracer import create_tracer_from_config
    from app.rag.embeddings import GeminiEmbedder
    from app.rag.llm import GeminiChatModel

    load_dotenv_if_present()
    config = load_config()
    check_embedding_dimensions(config)
    configure_logging(config.LOG_LEVEL, config.LOG_PRETTY)
    log = get_logger("api")
    engine = create_engine(config.DATABASE_URL)
    sessions = create_session_factory(engine)
    read_sessions = create_read_session_factory(engine)
    embedder = GeminiEmbedder(
        api_key=config.GEMINI_API_KEY,
        model=config.GEMINI_EMBEDDING_MODEL,
        dimensions=config.GEMINI_EMBEDDING_DIMENSIONS,
        timeout_ms=config.GEMINI_TIMEOUT_MS,
        log=log,
    )
    chat_model = GeminiChatModel(
        api_key=config.GEMINI_API_KEY,
        model=config.GEMINI_CHAT_MODEL,
        thinking_level=config.GEMINI_THINKING_LEVEL,
        timeout_ms=config.GEMINI_TIMEOUT_MS,
        log=log,
    )
    tracer = create_tracer_from_config(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        base_url=config.LANGFUSE_BASE_URL,
        log=log,
    )

    class LazyQueue:
        """Opened in the lifespan; the deps object exists before the event loop does."""

        inner: Any = None

        async def enqueue(
            self, name: str, payload: dict[str, Any], *, singleton_key: str | None = None
        ) -> str | None:
            return await self.inner.enqueue(name, payload, singleton_key=singleton_key)  # type: ignore[no-any-return]

        async def subscribe(self, name: str, handler: Any) -> None:
            await self.inner.subscribe(name, handler)

        async def stop(self) -> None:
            if self.inner is not None:
                await self.inner.stop()

    queue = LazyQueue()
    deps = build_deps(
        config,
        sessions=sessions,
        queue=queue,
        embedder=embedder,
        chat_model=chat_model,
        tracer=tracer,
        log=log,
        read_sessions=read_sessions,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # Several uvicorn workers start at once: migrations, the queue schema and the seed run
        # under one advisory lock so the second worker waits and then finds everything in place.
        async with startup_lock(engine):
            await run_migrations(engine)
            log.info("database migrations applied")
            queue.inner = await create_procrastinate_queue(config.DATABASE_URL, log)
            async with sessions() as session:
                await run_seed(session, deps, log, config.SEED_USERS)
        try:
            yield
        finally:
            log.info("shutting down")
            await tracer.shutdown()
            await queue.stop()
            await engine.dispose()

    return create_app(deps, lifespan=lifespan)


def __getattr__(name: str) -> Any:
    # `uvicorn app.main:app` resolves the production application lazily (PEP 562).
    if name == "app":
        return production_app()
    raise AttributeError(name)
