"""Modelled API errors (the names the web app switches on) and the FastAPI exception handlers that
render them with the Smithy-compatible envelope: `x-amzn-errortype: <Name>` plus a JSON body."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging import get_logger

log = get_logger("errors")


class ApiError(Exception):
    """Base of every modelled error. `extra` holds the error-specific body members."""

    name = "InternalServerError"
    status = 500

    def __init__(self, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.message = message
        self.extra = {k: v for k, v in extra.items() if v is not None}

    def body(self) -> dict[str, Any]:
        return {"message": self.message, **self.extra}


class ValidationException(ApiError):
    name = "ValidationException"
    status = 400

    def __init__(self, message: str, field_list: list[dict[str, str]] | None = None) -> None:
        super().__init__(message, fieldList=field_list)


class UnauthorizedError(ApiError):
    name = "UnauthorizedError"
    status = 401


class NotFoundError(ApiError):
    name = "NotFoundError"
    status = 404

    def __init__(self, message: str, resource: str | None = None, id: str | None = None) -> None:
        super().__init__(message, resource=resource, id=id)


class ConflictError(ApiError):
    name = "ConflictError"
    status = 409


class GuidelinesNotReadyError(ApiError):
    name = "GuidelinesNotReadyError"
    status = 409

    def __init__(self, message: str, company_id: str, latest_status: str | None = None) -> None:
        super().__init__(message, companyId=company_id, latestStatus=latest_status)


class GuidelinesConflictError(ApiError):
    name = "GuidelinesConflictError"
    status = 409

    def __init__(
        self,
        message: str,
        latest_version_id: str,
        uploaded_by: dict[str, str],
        uploaded_at: datetime,
    ) -> None:
        super().__init__(
            message,
            latestVersionId=latest_version_id,
            uploadedBy=uploaded_by,
            uploadedAt=uploaded_at.isoformat().replace("+00:00", "Z"),
        )


class PayloadTooLargeError(ApiError):
    name = "PayloadTooLargeError"
    status = 413

    def __init__(self, message: str, max_bytes: int) -> None:
        super().__init__(message, maxBytes=max_bytes)


class UnsupportedMediaTypeError(ApiError):
    name = "UnsupportedMediaTypeError"
    status = 415

    def __init__(self, message: str, supported: list[str]) -> None:
        super().__init__(message, supported=supported)


class RateLimitedError(ApiError):
    name = "RateLimitedError"
    status = 429

    def __init__(self, message: str, retry_after_seconds: int | None = None) -> None:
        super().__init__(message, retryAfterSeconds=retry_after_seconds)


class AiProviderError(ApiError):
    name = "AiProviderError"
    status = 502

    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__(message, provider=provider)


class InternalServerError(ApiError):
    name = "InternalServerError"
    status = 500

    def __init__(
        self, message: str = "Internal server error", request_id: str | None = None
    ) -> None:
        super().__init__(message, requestId=request_id)


def error_response(
    status: int, name: str, body: dict[str, Any], request_id: str | None
) -> JSONResponse:
    headers = {"x-amzn-errortype": name}
    if request_id:
        headers["x-request-id"] = request_id
    return JSONResponse(status_code=status, content=body, headers=headers)


def request_id_of(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def field_path(loc: tuple[int | str, ...]) -> str:
    """Pydantic `loc` → JSON pointer: ("body", "correctedAnswer") → "/correctedAnswer"."""
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "header", "cookie")]
    return "/" + "/".join(parts) if parts else "/"


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def on_api_error(request: Request, err: ApiError) -> JSONResponse:
        return error_response(err.status, err.name, err.body(), request_id_of(request))

    @app.exception_handler(RequestValidationError)
    async def on_validation(request: Request, err: RequestValidationError) -> JSONResponse:
        fields = [
            {"path": field_path(tuple(e["loc"])), "message": str(e["msg"])} for e in err.errors()
        ]
        body = {
            "message": "1 validation error detected"
            if len(fields) == 1
            else f"{len(fields)} validation errors detected",
            "fieldList": fields,
        }
        return error_response(400, "ValidationException", body, request_id_of(request))

    @app.exception_handler(StarletteHTTPException)
    async def on_http(request: Request, err: StarletteHTTPException) -> JSONResponse:
        status = err.status_code
        if status == 404:
            name, message = "UnknownOperationException", "Unknown operation"
        elif status == 405:
            name, message = "UnknownOperationException", "Method not allowed"
        elif status == 401:
            name, message = "UnauthorizedError", str(err.detail)
        elif status >= 500:
            name, message = "InternalServerError", "Internal server error"
        else:
            name, message = "BadRequestError", str(err.detail)
        body: dict[str, Any] = {"message": message}
        if status >= 500:
            body["requestId"] = request_id_of(request)
        return error_response(status, name, body, request_id_of(request))

    @app.exception_handler(Exception)
    async def on_unhandled(request: Request, err: Exception) -> JSONResponse:
        log.error("unhandled error", exc_info=err, path=request.url.path)
        return error_response(
            500,
            "InternalServerError",
            {"message": "Internal server error", "requestId": request_id_of(request)},
            request_id_of(request),
        )
