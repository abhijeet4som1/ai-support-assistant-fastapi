"""Environment configuration. Mirrors api/src/config.ts: same variable names, defaults and limits."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError

LogLevel = Literal["fatal", "error", "warn", "info", "debug", "trace", "silent"]
ThinkingLevel = Literal["minimal", "low", "medium", "high"]


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value) in ("true", "1")


def _blank_to_none(value: object) -> object:
    return None if isinstance(value, str) and value == "" else value


OptionalStr = Annotated[str | None, BeforeValidator(_blank_to_none)]


class Config(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    NODE_ENV: Literal["development", "test", "production"] = "development"
    PORT: int = Field(default=3000, gt=0)
    LOG_LEVEL: LogLevel = "info"
    LOG_PRETTY: Annotated[bool, BeforeValidator(_bool)] = False

    DATABASE_URL: str = Field(min_length=1)

    JWT_SECRET: str = Field(min_length=16)
    ACCESS_TOKEN_TTL_MINUTES: float = Field(default=15, gt=0)
    REFRESH_TOKEN_TTL_DAYS: float = Field(default=7, gt=0)
    SEED_USERS: str = "agent1:agent1pass,agent2:agent2pass"

    GEMINI_API_KEY: str = Field(min_length=1)
    GEMINI_CHAT_MODEL: str = "gemini-3.8-flash"
    # Thinking tokens are billed as output and count against max_output_tokens; "medium" matched
    # the previous model on quality at similar latency (docs/evaluation-report.md §7.1).
    GEMINI_THINKING_LEVEL: ThinkingLevel = "medium"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"
    GEMINI_EMBEDDING_DIMENSIONS: int = Field(default=768, gt=0)
    # Context window of the chat model, used to report how much of it each call consumes.
    GEMINI_CONTEXT_WINDOW_TOKENS: int = Field(default=1_048_576, gt=0)
    # Per-request timeout for every Gemini call; a hung call fails the turn instead of holding it.
    GEMINI_TIMEOUT_MS: int = Field(default=60_000, gt=0)
    # Upper bound (estimated tokens) for an assembled prompt; older history is dropped beyond it.
    CHAT_PROMPT_TOKEN_BUDGET: int = Field(default=120_000, gt=0)

    # Optional Langfuse tracing; enabled when both keys are present.
    LANGFUSE_PUBLIC_KEY: OptionalStr = None
    LANGFUSE_SECRET_KEY: OptionalStr = None
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"

    RAG_TOP_K: int = Field(default=4, gt=0)
    RAG_MIN_SCORE: float = Field(default=0.55, ge=0, le=1)
    RAG_CORRECTIONS_TOP_K: int = Field(default=3, ge=0)
    RAG_CORRECTIONS_MIN_SCORE: float = Field(default=0.65, ge=0, le=1)
    CHAT_HISTORY_WINDOW: int = Field(default=12, gt=0)

    MAX_UPLOAD_MB: float = Field(default=10, gt=0)

    @property
    def max_upload_bytes(self) -> int:
        import math

        return math.ceil(self.MAX_UPLOAD_MB * 1024 * 1024)


_MESSAGES = {
    "JWT_SECRET": "JWT_SECRET must be at least 16 characters",
    "GEMINI_API_KEY": "GEMINI_API_KEY is required",
}


def load_config(env: Mapping[str, str] | None = None) -> Config:
    """Parse and validate the environment once. Fails fast with a readable list of problems."""
    source = os.environ if env is None else env
    try:
        return Config.model_validate(dict(source))
    except ValidationError as err:
        lines = []
        for issue in err.errors():
            path = ".".join(str(p) for p in issue["loc"]) or "(root)"
            message = (
                _MESSAGES.get(path, issue["msg"]) if issue["type"] != "missing" else "Required"
            )
            lines.append(f"  - {path}: {message}")
        raise ValueError("Invalid environment configuration:\n" + "\n".join(lines)) from None


def load_dotenv_if_present(path: str | None = None) -> None:
    """Loads a .env file (repository root by default) without overriding real variables."""
    from pathlib import Path

    from dotenv import load_dotenv

    candidate = Path(path) if path else Path(__file__).resolve().parents[2] / ".env"
    if candidate.is_file():
        load_dotenv(candidate, override=False)
