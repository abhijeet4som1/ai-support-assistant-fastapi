"""structlog configuration: JSON lines to stdout (pretty console when LOG_PRETTY), request id bound
per request through contextvars. Field names follow the TypeScript api where the docs show them."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

_LEVELS = {
    "fatal": logging.CRITICAL,
    "error": logging.ERROR,
    "warn": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "trace": logging.DEBUG,
    "silent": logging.CRITICAL,
}

Logger = structlog.stdlib.BoundLogger


def configure_logging(level: str = "info", pretty: bool = False) -> None:
    numeric = _LEVELS.get(level, logging.INFO)
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer: Any = (
        structlog.dev.ConsoleRenderer(colors=True)
        if pretty
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[*processors, renderer],
        # "silent" keeps only CRITICAL, which nothing in the api emits.
        wrapper_class=structlog.make_filtering_bound_logger(numeric),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=False,
    )
    logging.basicConfig(level=max(numeric, logging.WARNING), stream=sys.stdout, force=True)
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str = "api", **initial: Any) -> Logger:
    return structlog.get_logger().bind(logger=name, **initial)  # type: ignore[no-any-return]


def bind_request_context(**values: Any) -> None:
    structlog.contextvars.bind_contextvars(**values)


def clear_request_context() -> None:
    structlog.contextvars.clear_contextvars()
