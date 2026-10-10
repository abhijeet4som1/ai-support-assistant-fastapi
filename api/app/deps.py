"""Application dependencies: the injected collaborators (`AppDeps`, set by `create_app`) and the
FastAPI `Depends` helpers that hand a request its session, user and services."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import TokenSigner
from app.auth.service import AuthService
from app.auth.users import AuthUser
from app.config import Config
from app.db.session import SessionFactory
from app.errors import UnauthorizedError
from app.jobs.queue import JobQueue
from app.logging import Logger
from app.observability.tracer import Tracer
from app.rag.embeddings import Embedder
from app.rag.llm import ChatModel

READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


@dataclass
class AppDeps:
    config: Config
    sessions: SessionFactory
    queue: JobQueue
    embedder: Embedder
    chat_model: ChatModel
    tracer: Tracer
    log: Logger
    signer: TokenSigner
    # AUTOCOMMIT sessions for read-only requests and the auth lookup; falls back to `sessions`.
    read_sessions: SessionFactory | None = None

    def sessions_for(self, method: str) -> SessionFactory:
        if self.read_sessions is not None and method.upper() in READ_METHODS:
            return self.read_sessions
        return self.sessions

    @asynccontextmanager
    async def auth_session(self) -> AsyncIterator[AuthService]:
        """An AuthService on its own short-lived read session (used by the auth middleware)."""
        async with (self.read_sessions or self.sessions)() as session:
            yield AuthService(session, self.signer, self.config.REFRESH_TOKEN_TTL_DAYS)


def deps_of(request: Request) -> AppDeps:
    deps: AppDeps = request.app.state.deps
    return deps


Deps = Annotated[AppDeps, Depends(deps_of)]


async def get_session(request: Request, deps: Deps) -> AsyncIterator[AsyncSession]:
    """One session per request: committed when the handler succeeds, rolled back otherwise.
    Read-only methods get an AUTOCOMMIT session, which skips the transaction round trips."""
    async with deps.sessions_for(request.method)() as session:
        try:
            yield session
            if session.in_transaction():
                await session.commit()
        except BaseException:
            if session.in_transaction():
                await session.rollback()
            raise


Session = Annotated[AsyncSession, Depends(get_session)]


def current_user(request: Request) -> AuthUser:
    """The authenticated agent (the auth middleware answered 401 before routing otherwise)."""
    user: AuthUser | None = getattr(request.state, "user", None)
    if user is None:
        bad: bool = getattr(request.state, "bad_token", False)
        raise UnauthorizedError(
            "Your session is invalid or has expired. Please log in again."
            if bad
            else "Authentication required"
        )
    return user


CurrentUser = Annotated[AuthUser, Depends(current_user)]


def auth_service(session: Session, deps: Deps) -> AuthService:
    return AuthService(session, deps.signer, deps.config.REFRESH_TOKEN_TTL_DAYS)


def responses(*errors: type[Any]) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses` for an operation: the given modelled errors plus the ones every
    operation can return (400, 401, 429, 500), each with its documented body schema."""
    from app import schemas

    out: dict[int | str, dict[str, Any]] = {
        400: {"model": schemas.ValidationExceptionResponseContent},
        401: {"model": schemas.UnauthorizedErrorResponseContent},
        429: {"model": schemas.RateLimitedErrorResponseContent},
        500: {"model": schemas.InternalServerErrorResponseContent},
    }
    for err in errors:
        out[err.status] = {"model": getattr(schemas, f"{err.name}ResponseContent")}
    return out


PUBLIC: dict[str, Any] = {"security": []}


def respond(model: BaseModel, status_code: int = 200) -> Response:
    """Serialises a response model once, with pydantic-core, and hands FastAPI a finished
    `Response`, which skips its second validation pass over the `response_model`. Optional members
    left unset are omitted, as the contract expects."""
    return Response(
        content=model.model_dump_json(exclude_none=True),
        media_type="application/json",
        status_code=status_code,
    )
