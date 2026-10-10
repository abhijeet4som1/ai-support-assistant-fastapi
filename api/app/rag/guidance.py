"""Response schema handed to Gemini and the server-side gate applied to its output."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.rag.prompt import SectionId
from app.schemas import AssistantGuidance, Citation, Coverage, Escalation

# JSON schema handed to Gemini as `response_schema` (structured output).
GUIDANCE_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "coverage": {"type": "STRING", "enum": ["covered", "partial", "not_covered"]},
        "recommendedReply": {"type": "STRING"},
        "handlingSteps": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Internal steps for the agent, in order",
        },
        "clarifications": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Questions the customer must answer before the case can be resolved "
            "(preferences, missing details)",
        },
        "agentDecisions": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Decisions the guidelines leave to the agent (e.g. whether to offer "
            "compensation); never questions for the customer",
        },
        "escalation": {
            "type": "OBJECT",
            "properties": {
                "recommended": {"type": "BOOLEAN"},
                "to": {"type": "STRING", "nullable": True},
                "reason": {"type": "STRING", "nullable": True},
            },
            "required": ["recommended"],
        },
        "citations": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": 'Section ids (e.g. "S2") actually used',
        },
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": [
        "coverage",
        "recommendedReply",
        "handlingSteps",
        "agentDecisions",
        "escalation",
        "citations",
    ],
    "propertyOrdering": [
        "coverage",
        "recommendedReply",
        "handlingSteps",
        "agentDecisions",
        "escalation",
        "citations",
        "notes",
    ],
}


def _str_list(value: Any) -> list[str]:
    return value if isinstance(value, list) and all(isinstance(x, str) for x in value) else []


class _RawEscalation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    recommended: bool = False
    to: str | None = None
    reason: str | None = None


class _RawGuidance(BaseModel):
    """Lenient parse of the model output: every member falls back to a safe default (zod `.catch`)."""

    model_config = ConfigDict(extra="ignore")
    coverage: Coverage = Coverage.partial
    recommendedReply: str = ""
    handlingSteps: list[str] = Field(default_factory=list)
    clarifications: list[str] = Field(default_factory=list)
    agentDecisions: list[str] = Field(default_factory=list)
    escalation: _RawEscalation = Field(default_factory=_RawEscalation)
    citations: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("coverage", mode="wrap")
    @classmethod
    def _coverage(cls, v: Any, handler: Any) -> Any:
        try:
            return handler(v)
        except ValidationError:
            return Coverage.partial

    @field_validator("recommendedReply", mode="before")
    @classmethod
    def _reply(cls, v: Any) -> str:
        return v if isinstance(v, str) else ""

    @field_validator("handlingSteps", "clarifications", "agentDecisions", mode="before")
    @classmethod
    def _lists(cls, v: Any) -> list[str]:
        return _str_list(v)

    @field_validator("citations", mode="before")
    @classmethod
    def _citations(cls, v: Any) -> list[str]:
        if not isinstance(v, list):
            return []
        out: list[str] = []
        for item in v:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict) and isinstance(item.get("sectionId"), str):
                out.append(item["sectionId"])
        return out

    @field_validator("escalation", mode="before")
    @classmethod
    def _escalation(cls, v: Any) -> Any:
        if not isinstance(v, dict):
            return _RawEscalation()
        return {
            "recommended": v.get("recommended")
            if isinstance(v.get("recommended"), bool)
            else False,
            "to": v.get("to") if isinstance(v.get("to"), str) else None,
            "reason": v.get("reason") if isinstance(v.get("reason"), str) else None,
        }

    @field_validator("notes", mode="before")
    @classmethod
    def _notes(cls, v: Any) -> str | None:
        return v if isinstance(v, str) else None


class GuidanceParseError(Exception):
    pass


_FENCE = re.compile(r"^\s*```(?:json)?\s*([\s\S]*?)\s*```\s*$")
_CODE_LINE = re.compile(
    r"^\s*(def |class |import |from \w+ import |function |const |let |var |#include|public |print\(|console\.log\()",
    re.MULTILINE,
)


def strip_code_fence(text: str) -> str:
    m = _FENCE.match(text)
    return m.group(1) if m else text


def looks_like_code(text: str) -> bool:
    """Heuristic: fenced code blocks or typical source-code line starts."""
    return "```" in text or bool(_CODE_LINE.search(text))


def finalize_guidance(raw: str, sections: list[SectionId]) -> AssistantGuidance:
    """Parses the model output and applies the server-side coverage gate:
    - no retrieved sections ⇒ coverage is forced to not_covered with escalation,
    - citations are restricted to sections that were actually provided,
    - a reply containing source code is downgraded (defence in depth against prompt injection)."""
    try:
        data = json.loads(strip_code_fence(raw))
    except (json.JSONDecodeError, TypeError):
        raise GuidanceParseError("Model returned invalid JSON") from None
    if not isinstance(data, dict):
        raise GuidanceParseError("Model output did not match the guidance schema")
    try:
        g = _RawGuidance.model_validate(data)
    except ValidationError:
        raise GuidanceParseError("Model output did not match the guidance schema") from None

    by_id = {s.id: s.chunk for s in sections}
    cited: list[Citation] = []
    seen: set[str] = set()
    for cid in g.citations:
        if cid in by_id and cid not in seen:
            seen.add(cid)
            cited.append(Citation(chunkId=by_id[cid].chunkId, title=by_id[cid].title))

    coverage = g.coverage
    escalation = Escalation(
        recommended=g.escalation.recommended, to=g.escalation.to, reason=g.escalation.reason
    )
    notes = g.notes
    if not sections:
        coverage = Coverage.not_covered
        escalation = Escalation(
            recommended=True,
            to=escalation.to or "Team lead / senior agent",
            reason=escalation.reason or "The guidelines do not cover this request",
        )
        notes = notes or "No relevant guideline section was found for this message."

    if looks_like_code(g.recommendedReply) or any(looks_like_code(s) for s in g.handlingSteps):
        coverage = Coverage.not_covered
        escalation = Escalation(
            recommended=True,
            to=escalation.to or "Team lead / senior agent",
            reason="The request appears to be out of scope",
        )
        notes = " ".join(
            part
            for part in (
                notes,
                "The generated reply contained code and was flagged as out of scope for "
                "customer support.",
            )
            if part
        )

    return AssistantGuidance(
        coverage=coverage,
        recommendedReply=g.recommendedReply,
        handlingSteps=g.handlingSteps,
        clarifications=g.clarifications,
        agentDecisions=g.agentDecisions,
        escalation=escalation,
        citations=cited,
        notes=notes,
    )
