"""Exports the OpenAPI document generated from the Pydantic models to
`packages/openapi/openapi.json` (committed; the web client types are generated from it).
CLI: `uv run python -m app.openapi_export`. A test fails when the committed file drifts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import load_config
from app.jobs.queue import InMemoryQueue
from app.main import build_deps, create_app
from app.observability.tracer import create_noop_tracer
from app.rag.embeddings import FakeEmbedder
from app.rag.llm import FakeChatModel

OPENAPI_PATH = Path(__file__).resolve().parents[2] / "packages" / "openapi" / "openapi.json"

_EXPORT_ENV = {
    "DATABASE_URL": "postgres://export",
    "JWT_SECRET": "openapi-export-placeholder-secret",
    "GEMINI_API_KEY": "export",
}


def build_openapi_document() -> dict[str, Any]:
    app = create_app(
        build_deps(
            load_config(_EXPORT_ENV),
            sessions=None,
            queue=InMemoryQueue(),
            embedder=FakeEmbedder(),
            chat_model=FakeChatModel(),
            tracer=create_noop_tracer(),
        )
    )
    doc = app.openapi()
    # Binary upload body: the same shape the Smithy build emitted (OpenAPI 3.1 contentEncoding),
    # which web/scripts/gen-api-types.mjs maps to Blob.
    doc["components"]["schemas"]["UploadGuidelinesInputPayload"] = {
        "type": "string",
        "description": "Raw uploaded guideline file bytes.",
        "contentEncoding": "byte",
    }
    doc["components"]["schemas"] = dict(sorted(doc["components"]["schemas"].items()))
    doc["paths"] = dict(sorted(doc["paths"].items()))
    return doc


def render() -> str:
    return json.dumps(build_openapi_document(), indent=2) + "\n"


if __name__ == "__main__":
    OPENAPI_PATH.write_text(render())
    print(f"wrote {OPENAPI_PATH}")
