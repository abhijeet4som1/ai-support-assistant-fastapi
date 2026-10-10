"""LLM observability. One trace per chat turn:
  chat-turn (session = conversation, user = agent)
  ├── history-summary    (only when older turns were folded into the rolling summary)
  ├── retrieval          query → sections with scores, corrections
  └── gemini.generate    full prompt, raw output, token usage, latency, % of context window
One trace per guideline ingestion (parse → chunk → embedding batches), and agent feedback is
attached to the chat-turn trace as Langfuse scores.

Langfuse is optional (enabled by LANGFUSE_* keys); the protocol keeps the services free of any
vendor types and lets tests record calls in memory."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from app.logging import Logger
from app.rag.prompt import ChatTurn
from app.rag.retrieval_types import RetrievedChunk, RetrievedCorrection


@dataclass
class TurnMeta:
    conversationId: str
    userId: str
    companyId: str
    companyName: str
    guidelineVersionId: str
    kind: Literal["customer", "instruction"]
    content: str


@dataclass
class GenerationRecord:
    model: str
    system: str
    turns: list[ChatTurn]
    estimatedPromptTokens: int
    contextWindowTokens: int
    # promptTokens (or the estimate when the provider reported none) / contextWindowTokens * 100
    contextUsedPct: float
    droppedHistoryTurns: int
    latencyMs: int
    raw: str | None = None
    error: str | None = None
    promptTokens: int | None = None
    completionTokens: int | None = None
    thinkingTokens: int | None = None
    totalTokens: int | None = None
    finishReason: str | None = None


@dataclass
class SummaryRecord:
    model: str
    # Number of history messages folded into the summary in this turn.
    messages: int
    input: str
    latencyMs: int
    output: str | None = None
    error: str | None = None


@dataclass
class IngestionMeta:
    versionId: str
    companyId: str
    filename: str
    userId: str


@dataclass
class EmbeddedBatch:
    count: int
    model: str
    dimensions: int
    latencyMs: int


@dataclass
class ScoreInput:
    traceId: str
    name: str
    value: float | str
    dataType: Literal["BOOLEAN", "NUMERIC", "TEXT"]
    comment: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class RetrievalOut:
    sections: list[RetrievedChunk]
    corrections: list[RetrievedCorrection]


@dataclass
class TurnEnd:
    status: Literal["ok", "failed"]
    coverage: str | None = None
    messageId: str | None = None


@dataclass
class IngestionEnd:
    status: Literal["ready", "failed", "superseded", "skipped"]
    error: str | None = None


class TurnRecorder(Protocol):
    # Trace id to store with the answer so later feedback can be attached as a score.
    trace_id: str | None

    def summary(self, s: SummaryRecord) -> None: ...
    def retrieval(self, query: str, out: RetrievalOut) -> None: ...
    def generation(self, g: GenerationRecord) -> None: ...
    def end(self, out: TurnEnd) -> None: ...


class IngestionRecorder(Protocol):
    def step(self, name: Literal["parse", "chunk"], data: dict[str, int | str]) -> None: ...
    def embedded(self, batch: EmbeddedBatch) -> None: ...
    def end(self, out: IngestionEnd) -> None: ...


class Tracer(Protocol):
    async def run_turn[T](
        self, meta: TurnMeta, fn: Callable[[TurnRecorder], Awaitable[T]]
    ) -> T: ...
    async def run_ingestion[T](
        self, meta: IngestionMeta, fn: Callable[[IngestionRecorder], Awaitable[T]]
    ) -> T: ...
    def score(self, inp: ScoreInput) -> None:
        """Attaches a score (agent thumbs, corrections) to an earlier trace. Fire-and-forget."""
        ...

    async def flush(self) -> None: ...
    async def shutdown(self) -> None: ...


# --- no-op ---------------------------------------------------------------------------------------


class _NoopTurn:
    trace_id: str | None = None

    def summary(self, s: SummaryRecord) -> None:
        return None

    def retrieval(self, query: str, out: RetrievalOut) -> None:
        return None

    def generation(self, g: GenerationRecord) -> None:
        return None

    def end(self, out: TurnEnd) -> None:
        return None


class _NoopIngestion:
    def step(self, name: Literal["parse", "chunk"], data: dict[str, int | str]) -> None:
        return None

    def embedded(self, batch: EmbeddedBatch) -> None:
        return None

    def end(self, out: IngestionEnd) -> None:
        return None


class NoopTracer:
    async def run_turn[T](self, meta: TurnMeta, fn: Callable[[TurnRecorder], Awaitable[T]]) -> T:
        return await fn(_NoopTurn())

    async def run_ingestion[T](
        self, meta: IngestionMeta, fn: Callable[[IngestionRecorder], Awaitable[T]]
    ) -> T:
        return await fn(_NoopIngestion())

    def score(self, inp: ScoreInput) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None


def create_noop_tracer() -> NoopTracer:
    return NoopTracer()


# --- recording (tests) ---------------------------------------------------------------------------


@dataclass
class RecordedTurn:
    meta: TurnMeta
    trace_id: str
    summary: SummaryRecord | None = None
    retrieval: tuple[str, RetrievalOut] | None = None
    generation: GenerationRecord | None = None
    end: TurnEnd | None = None


@dataclass
class RecordedIngestion:
    meta: IngestionMeta
    steps: list[tuple[str, dict[str, int | str]]] = field(default_factory=list)
    batches: list[EmbeddedBatch] = field(default_factory=list)
    end: IngestionEnd | None = None


class RecordingTracer:
    """Test double: records everything in memory."""

    def __init__(self) -> None:
        self.turns: list[RecordedTurn] = []
        self.ingestions: list[RecordedIngestion] = []
        self.scores: list[ScoreInput] = []

    async def run_turn[T](self, meta: TurnMeta, fn: Callable[[TurnRecorder], Awaitable[T]]) -> T:
        entry = RecordedTurn(meta=meta, trace_id=f"trace-{len(self.turns) + 1}")
        self.turns.append(entry)

        class Rec:
            trace_id = entry.trace_id

            def summary(self, s: SummaryRecord) -> None:
                entry.summary = s

            def retrieval(self, query: str, out: RetrievalOut) -> None:
                entry.retrieval = (query, out)

            def generation(self, g: GenerationRecord) -> None:
                entry.generation = g

            def end(self, out: TurnEnd) -> None:
                entry.end = out

        return await fn(Rec())

    async def run_ingestion[T](
        self, meta: IngestionMeta, fn: Callable[[IngestionRecorder], Awaitable[T]]
    ) -> T:
        entry = RecordedIngestion(meta=meta)
        self.ingestions.append(entry)

        class Rec:
            def step(self, name: Literal["parse", "chunk"], data: dict[str, int | str]) -> None:
                entry.steps.append((name, data))

            def embedded(self, batch: EmbeddedBatch) -> None:
                entry.batches.append(batch)

            def end(self, out: IngestionEnd) -> None:
                entry.end = out

        return await fn(Rec())

    def score(self, inp: ScoreInput) -> None:
        self.scores.append(inp)

    async def flush(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None


def create_recording_tracer() -> RecordingTracer:
    return RecordingTracer()


# --- Langfuse ------------------------------------------------------------------------------------


class LangfuseTracer:
    def __init__(self, *, public_key: str, secret_key: str, base_url: str, log: Logger) -> None:
        from langfuse import Langfuse

        self._client = Langfuse(public_key=public_key, secret_key=secret_key, base_url=base_url)
        self._log = log
        log.info("Langfuse tracing enabled", baseUrl=base_url)

    async def run_turn[T](self, meta: TurnMeta, fn: Callable[[TurnRecorder], Awaitable[T]]) -> T:
        from langfuse import propagate_attributes

        with propagate_attributes(
            user_id=meta.userId,
            session_id=meta.conversationId,
            metadata={
                "companyId": meta.companyId,
                "companyName": meta.companyName,
                "guidelineVersionId": meta.guidelineVersionId,
            },
            tags=[meta.kind],
        ):
            root = self._client.start_observation(
                name="chat-turn",
                input={"kind": meta.kind, "content": meta.content},
                metadata={
                    "companyName": meta.companyName,
                    "guidelineVersionId": meta.guidelineVersionId,
                },
            )

            class Rec:
                trace_id = root.trace_id

                def summary(self, s: SummaryRecord) -> None:
                    root.start_observation(
                        name="history-summary",
                        as_type="generation",
                        model=s.model,
                        input=s.input,
                        output=s.output,
                        metadata={"messages": s.messages, "latencyMs": s.latencyMs},
                        level="ERROR" if s.error else None,
                        status_message=s.error,
                    ).end()

                def retrieval(self, query: str, out: RetrievalOut) -> None:
                    root.start_observation(
                        name="retrieval",
                        as_type="retriever",
                        input={"query": query},
                        output={
                            "sections": [
                                {
                                    "chunkId": s.chunkId,
                                    "title": s.title,
                                    "score": s.score,
                                    "via": s.via,
                                }
                                for s in out.sections
                            ],
                            "corrections": [
                                {
                                    "correctionId": c.correctionId,
                                    "rating": c.rating,
                                    "score": c.score,
                                }
                                for c in out.corrections
                            ],
                        },
                        metadata={
                            "sectionCount": len(out.sections),
                            "correctionCount": len(out.corrections),
                        },
                    ).end()

                def generation(self, g: GenerationRecord) -> None:
                    usage = None
                    if g.promptTokens is not None or g.completionTokens is not None:
                        # Thinking tokens are billed as output; `total` is the provider's figure.
                        usage = {
                            "input": g.promptTokens or 0,
                            "output": g.completionTokens or 0,
                            "reasoning": g.thinkingTokens or 0,
                            "total": g.totalTokens
                            if g.totalTokens is not None
                            else (g.promptTokens or 0)
                            + (g.completionTokens or 0)
                            + (g.thinkingTokens or 0),
                        }
                    root.start_observation(
                        name="gemini.generateContent",
                        as_type="generation",
                        model=g.model,
                        input=[
                            {"role": "system", "content": g.system},
                            *({"role": t.role, "content": t.text} for t in g.turns),
                        ],
                        output=g.raw,
                        usage_details=usage,
                        metadata={
                            "finishReason": g.finishReason,
                            "estimatedPromptTokens": g.estimatedPromptTokens,
                            "contextWindowTokens": g.contextWindowTokens,
                            "contextUsedPct": g.contextUsedPct,
                            "droppedHistoryTurns": g.droppedHistoryTurns,
                            "latencyMs": g.latencyMs,
                        },
                        level="ERROR" if g.error else None,
                        status_message=g.error,
                    ).end()

                def end(self, out: TurnEnd) -> None:
                    root.update(
                        output=out.__dict__, level="ERROR" if out.status == "failed" else None
                    )

            try:
                return await fn(Rec())
            finally:
                root.end()

    async def run_ingestion[T](
        self, meta: IngestionMeta, fn: Callable[[IngestionRecorder], Awaitable[T]]
    ) -> T:
        from langfuse import propagate_attributes

        with propagate_attributes(
            user_id=meta.userId, metadata={"companyId": meta.companyId}, tags=["ingestion"]
        ):
            root = self._client.start_observation(
                name="guideline-ingestion",
                input={"versionId": meta.versionId, "filename": meta.filename},
                metadata={"companyId": meta.companyId},
            )

            class Rec:
                def step(self, name: Literal["parse", "chunk"], data: dict[str, int | str]) -> None:
                    root.start_observation(name=name, output=data).end()

                def embedded(self, batch: EmbeddedBatch) -> None:
                    root.start_observation(
                        name="gemini.embedContent",
                        as_type="embedding",
                        model=batch.model,
                        input={"chunks": batch.count},
                        metadata={"dimensions": batch.dimensions, "latencyMs": batch.latencyMs},
                    ).end()

                def end(self, out: IngestionEnd) -> None:
                    root.update(
                        output=out.__dict__, level="ERROR" if out.status == "failed" else None
                    )

            try:
                return await fn(Rec())
            finally:
                root.end()

    def score(self, inp: ScoreInput) -> None:
        self._client.create_score(
            trace_id=inp.traceId,
            name=inp.name,
            value=inp.value,
            data_type=inp.dataType,
            comment=inp.comment,
            metadata=inp.metadata,
        )

    async def flush(self) -> None:
        self._client.flush()

    async def shutdown(self) -> None:
        self._client.flush()
        self._client.shutdown()


def create_tracer_from_config(
    *, public_key: str | None, secret_key: str | None, base_url: str, log: Logger
) -> Tracer:
    """Langfuse when the keys are configured, otherwise a no-op."""
    if public_key and secret_key:
        return LangfuseTracer(
            public_key=public_key, secret_key=secret_key, base_url=base_url, log=log
        )
    log.info("Langfuse tracing disabled (LANGFUSE_* not set)")
    return create_noop_tracer()
