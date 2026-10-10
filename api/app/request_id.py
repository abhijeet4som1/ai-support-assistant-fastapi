"""Request id middleware (pure ASGI): honours an incoming `X-Request-Id` (nginx sets one), else a
uuid4; echoes it on every response and binds it into the structlog context."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.logging import bind_request_context, clear_request_context


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        incoming = next(
            (v.decode("latin-1") for k, v in scope["headers"] if k == b"x-request-id"), ""
        )
        request_id = incoming.strip() or str(uuid4())
        state: dict[str, Any] = scope.setdefault("state", {})
        state["request_id"] = request_id
        clear_request_context()
        bind_request_context(requestId=request_id)

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k != b"x-request-id"]
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            clear_request_context()
