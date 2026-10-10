"""Placeholder until step 3 ports the ingestion job."""

from __future__ import annotations

from typing import Any


class IngestionJob:
    def __init__(self, deps: Any, *, embed_batch_size: int = 50) -> None:
        self.deps = deps
        self.embed_batch_size = embed_batch_size

    async def run(self, payload: dict[str, Any]) -> None:
        raise NotImplementedError
