"""Prompt templates: the fixed text sent to the model lives in `api/prompts/*.md` (see the README
there) so wording changes are reviewable on their own. This module reads them once at import and
fills `{{placeholders}}`, failing loudly on a missing or unknown placeholder."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

TEMPLATE_NAMES: tuple[str, ...] = (
    "chat-system",
    "chat-no-sections",
    "chat-summary-ack",
    "summary-system",
)
TemplateName = Literal["chat-system", "chat-no-sections", "chat-summary-ack", "summary-system"]

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def _load(name: str) -> str:
    # Trailing newline is an artefact of the editor, not part of the prompt.
    return re.sub(r"\n+$", "", (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8"))


_templates: dict[str, str] = {name: _load(name) for name in TEMPLATE_NAMES}


def placeholders_of(name: TemplateName) -> list[str]:
    """Names of the `{{placeholders}}` a template expects."""
    return [m.group(1) for m in _PLACEHOLDER.finditer(_templates[name])]


def render_template(name: TemplateName, values: dict[str, str] | None = None) -> str:
    """Fills the template's placeholders. Raises when a placeholder has no value or a value has no
    placeholder, so a renamed variable cannot silently send `{{companyName}}` to the model."""
    values = values or {}
    expected = set(placeholders_of(name))
    for key in values:
        if key not in expected:
            raise ValueError(f'prompt template "{name}" has no placeholder {{{{{key}}}}}')

    def sub(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in values:
            raise ValueError(f'prompt template "{name}": missing value for {{{{{key}}}}}')
        return values[key]

    return _PLACEHOLDER.sub(sub, _templates[name])
