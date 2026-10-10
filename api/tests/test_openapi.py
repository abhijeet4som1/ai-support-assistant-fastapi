"""The exported OpenAPI document is the contract: it must match the committed file (run
`uv run python -m app.openapi_export` after changing a schema) and stay wire-compatible with the
Smithy-generated reference the web app was built against."""

from __future__ import annotations

import json
from typing import Any

from app.openapi_export import OPENAPI_PATH, build_openapi_document, render

REFERENCE = OPENAPI_PATH.parent / "reference-smithy.json"
METHODS = ("get", "put", "post", "patch", "delete")


def test_committed_document_matches_the_application() -> None:
    assert OPENAPI_PATH.read_text() == render(), (
        "packages/openapi/openapi.json is stale: run `uv run python -m app.openapi_export`"
    )


def _resolve(doc: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    while "$ref" in schema:
        schema = doc["components"]["schemas"][schema["$ref"].rsplit("/", 1)[1]]
    return schema


def _shape(doc: dict[str, Any], schema: dict[str, Any]) -> tuple[set[str], set[str]]:
    s = _resolve(doc, schema)
    return set(s.get("properties", {})), set(s.get("required", []))


def test_compatible_with_the_smithy_reference() -> None:
    ref = json.loads(REFERENCE.read_text())
    doc = build_openapi_document()
    assert set(ref["paths"]) == set(doc["paths"])
    for path, ops in ref["paths"].items():
        for method, op in ops.items():
            if method not in METHODS:
                continue
            ours = doc["paths"][path].get(method)
            assert ours, f"{method.upper()} {path} missing"
            assert ours["operationId"] == op["operationId"]
            assert ours.get("security") == op.get("security"), f"{method} {path} security"
            assert {
                (p["name"], p["in"], p.get("required", False)) for p in op.get("parameters", [])
            } == {
                (p["name"], p["in"], p.get("required", False)) for p in ours.get("parameters", [])
            }, f"{method} {path} parameters"
            assert set(op["responses"]) == set(ours["responses"]), f"{method} {path} status codes"
            for code, response in op["responses"].items():
                for ctype, media in response.get("content", {}).items():
                    theirs = ours["responses"][code]["content"][ctype]["schema"]
                    assert _shape(ref, media["schema"]) == _shape(doc, theirs), (
                        f"{method} {path} {code} response"
                    )
            body = op.get("requestBody")
            assert bool(body) == bool(ours.get("requestBody")), f"{method} {path} body"
            if body:
                for ctype, media in body["content"].items():
                    theirs = ours["requestBody"]["content"][ctype]["schema"]
                    assert _shape(ref, media["schema"]) == _shape(doc, theirs), (
                        f"{method} {path} request body"
                    )
    for name, schema in ref["components"]["schemas"].items():
        ours = doc["components"]["schemas"].get(name)
        assert ours is not None, f"schema {name} missing"
        if "enum" in schema:
            assert ours.get("enum") == schema["enum"], f"enum {name}"
        if "properties" in schema:
            assert _shape(ref, schema) == _shape(doc, ours), f"schema {name}"
