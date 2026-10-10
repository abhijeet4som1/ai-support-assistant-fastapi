"""Authentication before routing (pure ASGI): resolves the bearer token to a user and rejects
unauthenticated requests to protected `/api` routes *before* any body is parsed or validated, so
callers cannot probe validation rules without a token. Public routes are the operations marked
`security: []` in the OpenAPI document (Health, Login, RefreshToken, Logout) plus the docs."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth.service import bearer_from_header
from app.auth.users import AuthUser
from app.logging import bind_request_context

BAD_TOKEN_MESSAGE = "Your session is invalid or has expired. Please log in again."
NO_TOKEN_MESSAGE = "Authentication required"


@dataclass
class RouteMatcher:
    method: str
    template: str
    pattern: re.Pattern[str]


def template_to_pattern(template: str) -> re.Pattern[str]:
    escaped = "/".join(
        "[^/]+" if re.fullmatch(r"\{[^}]+\}", seg) else re.escape(seg)
        for seg in template.split("/")
    )
    return re.compile(f"^{escaped}/?$")


def public_routes_from_openapi(doc: dict[str, Any]) -> list[RouteMatcher]:
    """An operation with `security: []` is public; everything else is protected."""
    out: list[RouteMatcher] = []
    for template, ops in doc.get("paths", {}).items():
        for method, op in ops.items():
            if method not in ("get", "put", "post", "delete", "patch", "head", "options"):
                continue
            security = op.get("security") if isinstance(op, dict) else None
            if isinstance(security, list) and len(security) == 0:
                out.append(RouteMatcher(method.upper(), template, template_to_pattern(template)))
    return out


def is_public_route(routes: list[RouteMatcher], method: str, path: str) -> bool:
    return any(r.method == method.upper() and r.pattern.match(path) for r in routes)


USER_CACHE_TTL_SECONDS = 30.0


class AuthMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        auth_service: Callable[[], Any],
        public_routes: Callable[[], list[RouteMatcher]],
        verify: Callable[[str], Any] | None = None,
        docs_prefixes: tuple[str, ...] = ("/api/docs", "/api/openapi.json"),
    ) -> None:
        self.app = app
        self._auth_service = auth_service
        self._public_routes = public_routes
        self._verify = verify
        self._docs = docs_prefixes
        # The signature and expiry are checked on every request; the database lookup that follows
        # only detects a deleted user, so its result is kept for a short while per token subject.
        self._users: dict[str, tuple[float, AuthUser]] = {}

    async def _authenticate(self, bearer: str) -> AuthUser | None:
        if self._verify is None:
            async with self._auth_service() as auth:
                return await auth.authenticate(bearer)  # type: ignore[no-any-return]
        claims = self._verify(bearer)
        if claims is None:
            return None
        now = time.monotonic()
        cached = self._users.get(claims.sub)
        if cached and cached[0] > now:
            return cached[1]
        async with self._auth_service() as auth:
            user: AuthUser | None = await auth.authenticate(bearer)
        if user is not None:
            if len(self._users) > 10_000:
                self._users.clear()
            self._users[claims.sub] = (now + USER_CACHE_TTL_SECONDS, user)
        else:
            self._users.pop(claims.sub, None)
        return user

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path: str = scope["path"]
        method: str = scope["method"]
        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope["headers"]}
        authorization = headers.get("authorization")
        state: dict[str, Any] = scope.setdefault("state", {})
        user: AuthUser | None = None
        bearer = bearer_from_header(authorization)
        if bearer:
            user = await self._authenticate(bearer)
        state["user"] = user
        state["bad_token"] = bool(authorization) and user is None
        if user:
            bind_request_context(userId=user.id)

        is_docs = any(path == p or path.startswith(p + "/") for p in self._docs)
        if (
            user is None
            and path.startswith("/api")
            and not is_docs
            and not is_public_route(self._public_routes(), method, path)
        ):
            body = json.dumps(
                {
                    "message": BAD_TOKEN_MESSAGE if state["bad_token"] else NO_TOKEN_MESSAGE,
                    "requestId": state.get("request_id"),
                }
            ).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                        (b"x-amzn-errortype", b"UnauthorizedError"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)
