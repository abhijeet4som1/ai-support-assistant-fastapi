"""Assembles the prompt for a chat turn. All fixed wording comes from the templates in
`api/prompts/` (see `templates.py`); this module only adds the dynamic parts: retrieved sections,
corrections, the rolling summary, history and the latest message."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field, replace
from typing import Literal

from app.rag.retrieval_types import RetrievedChunk, RetrievedCorrection
from app.rag.templates import render_template

HistoryRole = Literal["customer", "instruction", "assistant"]
LatestKind = Literal["customer", "instruction"]


@dataclass
class HistoryTurn:
    role: HistoryRole
    content: str


@dataclass
class LatestMessage:
    kind: LatestKind
    content: str


@dataclass
class PromptInput:
    companyName: str
    sections: list[RetrievedChunk]
    corrections: list[RetrievedCorrection]
    history: list[HistoryTurn]
    latest: LatestMessage
    # Rolling summary of messages older than the history window, if any.
    summary: str | None = None


@dataclass
class ChatTurn:
    role: Literal["user", "model"]
    text: str


@dataclass
class SectionId:
    id: str
    chunk: RetrievedChunk


@dataclass
class BuiltPrompt:
    system: str
    turns: list[ChatTurn]
    # Section ids as shown to the model, mapped back to chunks.
    sectionIds: list[SectionId] = field(default_factory=list)


def build_system_prompt(company_name: str) -> str:
    return render_template("chat-system", {"companyName": company_name})


_CUSTOMER_TAG = re.compile(r"</?customer_message>")


def wrap_customer(text: str) -> str:
    return f"<customer_message>\n{_CUSTOMER_TAG.sub('', text)}\n</customer_message>"


def wrap_instruction(text: str) -> str:
    return f"<agent_instruction>\n{text}\n</agent_instruction>"


def build_prompt(inp: PromptInput) -> BuiltPrompt:
    section_ids = [SectionId(f"S{i + 1}", chunk) for i, chunk in enumerate(inp.sections)]
    context: list[str] = []

    if section_ids:
        context.append("<guideline_sections>")
        for s in section_ids:
            context.append(f"[{s.id}] {s.chunk.title or 'Untitled section'}\n{s.chunk.content}")
        context.append("</guideline_sections>")
    else:
        context.append(render_template("chat-no-sections"))

    if inp.corrections:
        context.append('<corrections note="from senior agents; lower authority than the sections">')
        for i, c in enumerate(inp.corrections):
            lines = [f"[C{i + 1}] Customer message: {c.queryText}"]
            if c.rating == "down":
                if c.whatWasWrong:
                    lines.append(f"What was wrong in a previous answer: {c.whatWasWrong}")
                if c.correctedAnswer:
                    lines.append(f"Correct answer: {c.correctedAnswer}")
            else:
                lines.append("A previous answer to this was rated helpful by an agent.")
            context.append("\n".join(lines))
        context.append("</corrections>")

    turns: list[ChatTurn] = []
    if inp.summary:
        turns.append(
            ChatTurn("user", f"<conversation_summary>\n{inp.summary}\n</conversation_summary>")
        )
        turns.append(ChatTurn("model", render_template("chat-summary-ack")))
    for h in inp.history:
        if h.role == "assistant":
            turns.append(ChatTurn("model", h.content))
        elif h.role == "customer":
            turns.append(ChatTurn("user", wrap_customer(h.content)))
        else:
            turns.append(ChatTurn("user", wrap_instruction(h.content)))
    latest = (
        wrap_customer(inp.latest.content)
        if inp.latest.kind == "customer"
        else wrap_instruction(inp.latest.content)
    )
    turns.append(ChatTurn("user", "\n\n".join(context) + "\n\n" + latest))

    return BuiltPrompt(build_system_prompt(inp.companyName), turns, section_ids)


def estimate_tokens(text: str) -> int:
    """Cheap token estimate (≈4 chars/token). Mirrors the ingestion chunker."""
    return max(1, math.ceil(len(text) / 4))


def estimate_prompt_tokens(prompt: BuiltPrompt) -> int:
    return estimate_tokens(prompt.system) + sum(estimate_tokens(t.text) for t in prompt.turns)


SUMMARY_SYSTEM_PROMPT = render_template("summary-system")


def transcript_for_summary(previous_summary: str | None, turns: list[HistoryTurn]) -> str:
    """Formats older turns for the summariser (and for appending to an existing summary)."""
    lines = "\n".join(f"[{t.role}] {t.content}" for t in turns)
    if previous_summary:
        return f"Previous summary:\n{previous_summary}\n\nNew messages:\n{lines}"
    return lines


def fit_history_to_budget(inp: PromptInput, budget_tokens: int) -> tuple[BuiltPrompt, int]:
    """Drops the oldest history turns until the assembled prompt fits the token budget. The
    latest turn (which carries the retrieved context) is never dropped. Returns (prompt, dropped)."""
    history = list(inp.history)
    dropped = 0
    prompt = build_prompt(replace(inp, history=history))
    while history and estimate_prompt_tokens(prompt) > budget_tokens:
        history = history[1:]
        dropped += 1
        prompt = build_prompt(replace(inp, history=history))
    return prompt, dropped


def retrieval_query(history: list[HistoryTurn], latest: LatestMessage) -> str:
    """Retrieval query for a turn: latest customer message plus the previous one (handles
    "yes, that one")."""
    customers = [h.content for h in history if h.role == "customer"]
    if latest.kind == "customer":
        prev = customers[-1] if customers else None
        if prev and len(latest.content) < 120:
            return f"{prev}\n{latest.content}"
        return latest.content
    return customers[-1] if customers else latest.content
