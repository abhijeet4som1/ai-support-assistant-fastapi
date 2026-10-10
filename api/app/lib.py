"""Small helpers for values of unknown shape (errors, JSON, external objects)."""

from __future__ import annotations

import json
from typing import Any


def error_status(err: BaseException) -> int | None:
    """HTTP-ish status carried by SDK errors (Gemini's APIError, httpx errors), if any."""
    for attr in ("status_code", "code", "status"):
        value = getattr(err, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(err, "response", None)
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) else None


def try_parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def provider_error_message(err: BaseException | str) -> str | None:
    """Provider errors (Gemini) put a JSON envelope in the message:
    `{"error":{"message":..,"status":..}}`. Returns the inner message with its status."""
    raw = err if isinstance(err, str) else (str(err) if str(err) else None)
    if not raw:
        return None
    parsed = try_parse_json(raw)
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        inner = parsed["error"]
        if isinstance(inner.get("message"), str):
            status = f" ({inner['status']})" if isinstance(inner.get("status"), str) else ""
            return f"{inner['message']}{status}"
    # google-genai's APIError stringifies as "<code> <STATUS>. {'error': {...}}"; prefer its fields.
    message = getattr(err, "message", None)
    status = getattr(err, "status", None)
    if isinstance(message, str) and message and not isinstance(err, str):
        return f"{message} ({status})" if isinstance(status, str) and status else message
    return raw
