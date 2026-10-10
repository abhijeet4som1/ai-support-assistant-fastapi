"""Minimal job-queue abstraction (two methods). Production uses Procrastinate on the existing
Postgres; tests use the in-memory implementation. An SQS adapter would implement the same
interface for a cloud deployment."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from app.logging import Logger, get_logger

JobHandler = Callable[[dict[str, Any], str], Awaitable[None]]

INGEST_GUIDELINES = "ingest-guidelines"


class JobQueue(Protocol):
    async def enqueue(
        self, name: str, payload: dict[str, Any], *, singleton_key: str | None = None
    ) -> str | None:
        """Returns the job id, or None when a job with the same singleton key is already pending."""
        ...

    async def subscribe(self, name: str, handler: JobHandler) -> None: ...

    async def stop(self) -> None: ...


@dataclass
class PendingJob:
    name: str
    payload: dict[str, Any]
    id: str
    key: str | None


class InMemoryQueue:
    """In-process queue for tests: jobs run when `drain()` is called (deterministic)."""

    def __init__(self) -> None:
        self.handlers: dict[str, JobHandler] = {}
        self.pending: list[PendingJob] = []
        self._seq = 0

    async def enqueue(
        self, name: str, payload: dict[str, Any], *, singleton_key: str | None = None
    ) -> str | None:
        if singleton_key and any(p.name == name and p.key == singleton_key for p in self.pending):
            return None
        self._seq += 1
        job_id = f"job-{self._seq}"
        self.pending.append(PendingJob(name, payload, job_id, singleton_key))
        return job_id

    async def subscribe(self, name: str, handler: JobHandler) -> None:
        self.handlers[name] = handler

    async def stop(self) -> None:
        return None

    async def drain(self) -> None:
        while self.pending:
            job = self.pending.pop(0)
            handler = self.handlers.get(job.name)
            if handler is None:
                raise RuntimeError(f"no handler for queue {job.name}")
            await handler(job.payload, job.id)


class ProcrastinateQueue:
    """Procrastinate-backed queue. `singleton_key` maps to `queueing_lock`: a second job with the
    same lock while one is still queued is dropped (`AlreadyEnqueued`), like pg-boss' singletonKey.
    Jobs retry up to 5 times with exponential backoff."""

    def __init__(self, connection_string: str, log: Logger | None = None) -> None:
        import procrastinate

        from app.db.session import to_sync_url

        self.log = log or get_logger("queue")
        self._pr = procrastinate
        self.app = procrastinate.App(
            connector=procrastinate.PsycopgConnector(conninfo=to_sync_url(connection_string)),
        )
        self._tasks: dict[str, Any] = {}
        self._worker: asyncio.Task[None] | None = None
        self._handlers: dict[str, JobHandler] = {}
        self._opened = False

    async def start(self) -> ProcrastinateQueue:
        await self.app.open_async()
        await self.app.schema_manager.apply_schema_async()
        self._opened = True
        return self

    def _task(self, name: str) -> Any:
        if name in self._tasks:
            return self._tasks[name]
        queue = self

        @self.app.task(
            name=name,
            queue=name,
            retry=self._pr.RetryStrategy(max_attempts=5, wait=5, exponential_wait=2),
            pass_context=True,
        )
        async def run(context: Any, **payload: Any) -> None:
            handler = queue._handlers.get(name)
            if handler is None:
                raise RuntimeError(f"no handler for queue {name}")
            await handler(payload, str(context.job.id))

        self._tasks[name] = run
        return run

    async def enqueue(
        self, name: str, payload: dict[str, Any], *, singleton_key: str | None = None
    ) -> str | None:
        task = self._task(name)
        try:
            job = await task.configure(queueing_lock=singleton_key).defer_async(**payload)
        except self._pr.exceptions.AlreadyEnqueued:
            return None
        return str(job)

    async def subscribe(self, name: str, handler: JobHandler) -> None:
        self._handlers[name] = handler
        self._task(name)
        if self._worker is None:
            self._worker = asyncio.create_task(
                self.app.run_worker_async(queues=list(self._handlers), concurrency=1)
            )
        self.log.info("subscribed", queue=name)

    async def stop(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._worker
            self._worker = None
        if self._opened:
            await self.app.close_async()
            self._opened = False


async def create_procrastinate_queue(connection_string: str, log: Logger) -> ProcrastinateQueue:
    return await ProcrastinateQueue(connection_string, log).start()
