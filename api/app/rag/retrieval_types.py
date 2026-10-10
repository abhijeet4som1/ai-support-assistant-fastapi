"""Shapes shared by retrieval, prompt assembly and the tracer (kept free of SQLAlchemy)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class RetrievedChunk:
    chunkId: str
    ordinal: int
    title: str | None
    content: str
    score: float
    # Set when the section was not found by the live query's vector ranking: through a matching
    # correction's original question, or through a distinctive keyword of the message.
    via: Literal["correction", "keyword"] | None = None


@dataclass
class RetrievedCorrection:
    correctionId: str
    rating: Literal["up", "down"]
    queryText: str
    whatWasWrong: str | None
    correctedAnswer: str | None
    score: float
    # Stored embedding of the original customer message (reused for correction-anchored retrieval).
    queryEmbedding: list[float] | None
