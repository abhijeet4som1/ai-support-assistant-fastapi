"""Gemini chat model behind a small `ChatModel` protocol, plus the deterministic fake for tests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Literal, Protocol

from app.lib import error_status, provider_error_message
from app.logging import Logger, get_logger
from app.rag.guidance import GUIDANCE_RESPONSE_SCHEMA
from app.rag.prompt import ChatTurn

ChatThinkingLevel = Literal["minimal", "low", "medium", "high"]


@dataclass
class GenerateResult:
    raw: str
    promptTokens: int | None = None
    # Visible answer tokens; the provider reports reasoning tokens separately.
    completionTokens: int | None = None
    # Reasoning ("thinking") tokens, billed as output.
    thinkingTokens: int | None = None
    # Provider-reported total for the call: prompt + thinking + answer.
    totalTokens: int | None = None
    # Provider finish reason (STOP, MAX_TOKENS, SAFETY, ...) for diagnostics.
    finishReason: str | None = None


class ChatModel(Protocol):
    model: str

    async def generate_guidance(self, system: str, turns: list[ChatTurn]) -> GenerateResult: ...

    async def summarize(self, system: str, text: str) -> str:
        """Plain-text summary used to compress conversation history that no longer fits."""
        ...


class ChatModelError(Exception):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class GeminiChatModel:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        thinking_level: ChatThinkingLevel | None = None,
        timeout_ms: int | None = None,
        log: Logger | None = None,
    ) -> None:
        from google import genai
        from google.genai import types

        self.model = model
        self.thinking_level = thinking_level
        self.log = log or get_logger("llm")
        self._types = types
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_ms) if timeout_ms else None,
        )

    async def generate_guidance(self, system: str, turns: list[ChatTurn]) -> GenerateResult:
        t = self._types
        try:
            config = t.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=GUIDANCE_RESPONSE_SCHEMA,
                temperature=0.3,
                # Thinking models spend part of this budget on reasoning before the JSON; 2048
                # was truncating ~25% of answers mid-JSON (see docs/evaluation-report.md).
                max_output_tokens=8192,
                thinking_config=(
                    t.ThinkingConfig(thinking_level=t.ThinkingLevel(self.thinking_level.upper()))
                    if self.thinking_level
                    else None
                ),
            )
            res = await self._client.aio.models.generate_content(
                model=self.model,
                contents=[t.Content(role=x.role, parts=[t.Part(text=x.text)]) for x in turns],
                config=config,
            )
            candidates = res.candidates or []
            finish = candidates[0].finish_reason if candidates else None
            finish_name = finish.name if finish is not None else None
            if finish in (t.FinishReason.MAX_TOKENS, t.FinishReason.SAFETY):
                raise ChatModelError(
                    "The model ran out of output tokens before finishing the answer"
                    if finish == t.FinishReason.MAX_TOKENS
                    else "The provider blocked the answer for safety reasons"
                )
            raw = res.text
            if not raw:
                raise ChatModelError("The model returned an empty response")
            usage = res.usage_metadata
            return GenerateResult(
                raw=raw,
                promptTokens=usage.prompt_token_count if usage else None,
                completionTokens=usage.candidates_token_count if usage else None,
                thinkingTokens=usage.thoughts_token_count if usage else None,
                totalTokens=usage.total_token_count if usage else None,
                finishReason=finish_name,
            )
        except ChatModelError:
            raise
        except Exception as err:
            status = error_status(err)
            message = provider_error_message(err) or "Unknown provider error"
            self.log.error("chat model call failed", err=str(err), status=status)
            raise ChatModelError(message, status) from err

    async def summarize(self, system: str, text: str) -> str:
        t = self._types
        try:
            res = await self._client.aio.models.generate_content(
                model=self.model,
                contents=[t.Content(role="user", parts=[t.Part(text=text)])],
                config=t.GenerateContentConfig(
                    system_instruction=system, temperature=0.2, max_output_tokens=512
                ),
            )
            return (res.text or "").strip()
        except Exception as err:
            self.log.error("summary call failed", err=str(err))
            raise ChatModelError(
                provider_error_message(err) or "Unknown provider error", error_status(err)
            ) from err


_SECTION = re.compile(r"^\[(S\d+)\] (.+)$", re.MULTILINE)


@dataclass
class FakeCall:
    system: str
    turns: list[ChatTurn]


@dataclass
class FakeChatModel:
    """Deterministic fake for tests: covered when sections are present, cites all of them,
    echoes the first section title so assertions can check grounding."""

    model: str = "fake-chat"
    calls: list[FakeCall] = field(default_factory=list)
    summaries: list[str] = field(default_factory=list)
    fail_next: Exception | None = None

    async def summarize(self, system: str, text: str) -> str:
        count = len([line for line in text.split("\n") if line.startswith("[")])
        summary = f"Summary of earlier conversation ({count} messages)."
        self.summaries.append(summary)
        return summary

    async def generate_guidance(self, system: str, turns: list[ChatTurn]) -> GenerateResult:
        self.calls.append(FakeCall(system, turns))
        if self.fail_next is not None:
            err = self.fail_next
            self.fail_next = None
            raise err if isinstance(err, ChatModelError) else ChatModelError(str(err))
        last = turns[-1].text
        sections = [(m.group(1), m.group(2)) for m in _SECTION.finditer(last)]
        is_instruction = "<agent_instruction>" in last
        if sections:
            first_title = sections[0][1]
            reply = f"Hello [Name], regarding {first_title.lower()}: we will take care of it." + (
                " (revised)" if is_instruction else ""
            )
        else:
            reply = (
                "Hello [Name], thank you for reaching out. I am checking this with the team and "
                "will get back to you shortly."
            )
        guidance = {
            "coverage": "covered" if sections else "not_covered",
            "recommendedReply": reply,
            "handlingSteps": [f'Follow the "{sections[0][1]}" procedure']
            if sections
            else ["Escalate to a senior agent"],
            "clarifications": ["Would you prefer a replacement or a refund?"] if sections else [],
            "agentDecisions": ["Offer compensation if appropriate"] if sections else [],
            "escalation": {"recommended": not sections, "to": None, "reason": None},
            "citations": [s[0] for s in sections],
            "notes": None,
        }
        return GenerateResult(
            raw=json.dumps(guidance),
            promptTokens=100,
            completionTokens=50,
            thinkingTokens=20,
            totalTokens=170,
        )
