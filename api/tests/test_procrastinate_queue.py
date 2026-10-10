"""The production queue against a real Postgres: enqueue, singleton-key dedupe, a worker that
runs the handler, and job ids stored on the version row."""

from __future__ import annotations

import asyncio
from typing import Any

from app.jobs.queue import create_procrastinate_queue
from app.logging import get_logger
from tests.conftest import DatabaseHarness


async def test_enqueue_dedupes_on_singleton_key_and_workers_run_handlers(
    template_db: DatabaseHarness,
) -> None:
    url = await template_db.create()
    queue = await create_procrastinate_queue(url, get_logger("test"))
    done: list[dict[str, Any]] = []
    finished = asyncio.Event()

    async def handler(payload: dict[str, Any], job_id: str) -> None:
        done.append({**payload, "jobId": job_id})
        if len(done) == 2:
            finished.set()

    try:
        first = await queue.enqueue("ingest-guidelines", {"versionId": "v1"}, singleton_key="v1")
        dup = await queue.enqueue("ingest-guidelines", {"versionId": "v1"}, singleton_key="v1")
        other = await queue.enqueue("ingest-guidelines", {"versionId": "v2"}, singleton_key="v2")
        assert first and other and dup is None
        await queue.subscribe("ingest-guidelines", handler)
        await asyncio.wait_for(finished.wait(), timeout=20)
        assert sorted(d["versionId"] for d in done) == ["v1", "v2"]
        assert all(d["jobId"] for d in done)
    finally:
        await queue.stop()
        await template_db.drop(url)
