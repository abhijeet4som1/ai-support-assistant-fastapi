"""Gemini embeddings behind a small `Embedder` protocol, plus the deterministic fake for tests."""

from __future__ import annotations

import asyncio
import math
import re
from typing import Literal, Protocol

from app.lib import error_status
from app.logging import Logger, get_logger

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]


class Embedder(Protocol):
    model: str
    dimensions: int

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


# batchEmbedContents accepts up to 100 requests per call.
BATCH = 100


def normalize(v: list[float]) -> list[float]:
    """Unit-length vectors so cosine distance == 1 - dot product and thresholds are stable."""
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


class GeminiEmbedder:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        timeout_ms: int | None = None,
        log: Logger | None = None,
    ) -> None:
        from google import genai
        from google.genai import types

        self.model = model
        self.dimensions = dimensions
        self.log = log or get_logger("embeddings")
        self._types = types
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_ms) if timeout_ms else None,
        )

    async def _embed(self, texts: list[str], task_type: TaskType) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]

            async def call(batch: list[str] = batch) -> object:
                return await self._client.aio.models.embed_content(
                    model=self.model,
                    # One Content per text. Passing plain strings makes the SDK merge the batch
                    # into a single multi-part content, which gemini-embedding-2 embeds as ONE
                    # document (one vector for the whole batch); explicit contents give one
                    # vector per text.
                    contents=[
                        self._types.Content(role="user", parts=[self._types.Part(text=t)])
                        for t in batch
                    ],
                    config=self._types.EmbedContentConfig(
                        task_type=task_type, output_dimensionality=self.dimensions
                    ),
                )

            res = await with_retry(call, self.log)
            embeddings = getattr(res, "embeddings", None) or []
            vectors = [list(e.values or []) for e in embeddings]
            if len(vectors) != len(batch):
                raise RuntimeError(f"embedding count mismatch: {len(vectors)} != {len(batch)}")
            out.extend(normalize(v) for v in vectors)
        return out

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts, "RETRIEVAL_DOCUMENT")

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([text], "RETRIEVAL_QUERY"))[0]


async def with_retry[T](fn: object, log: Logger, attempts: int = 4) -> T:
    """Retries 429/500/503 with a doubling delay (1 s, 2 s, 4 s)."""
    delay = 1.0
    attempt = 1
    while True:
        try:
            return await fn()  # type: ignore[operator, no-any-return]
        except Exception as err:
            status = error_status(err)
            retryable = status in (429, 503, 500)
            if not retryable or attempt >= attempts:
                raise
            log.warning("embedding call throttled; retrying", status=status, attempt=attempt)
            await asyncio.sleep(delay)
            delay *= 2
            attempt += 1


_WORD = re.compile(r"[a-z0-9]{3,}")


def _fnv1a(word: str) -> int:
    h = 2166136261
    for ch in word:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


class FakeEmbedder:
    """Deterministic fake embedder for tests: hashed bag-of-words into `dimensions`, normalised.
    Similar texts share tokens and therefore direction, so similarity search behaves sensibly.
    Same hash (FNV-1a over UTF-16 code units) as the TypeScript fake."""

    model = "fake"

    def __init__(self, dimensions: int = 768) -> None:
        self.dimensions = dimensions

    def vec(self, text: str) -> list[float]:
        v = [0.0] * self.dimensions
        for word in _WORD.findall(text.lower()):
            v[_fnv1a(word) % self.dimensions] += 1
        return normalize(v)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.vec(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self.vec(text)
