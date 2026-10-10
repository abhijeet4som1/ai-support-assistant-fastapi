"""Heading-aware chunker. Guideline documents are usually organised by topic
("1. Shipping Issues", "## Refunds", "BILLING"), and one topic per chunk gives the best
retrieval units. Long topics and unstructured text fall back to a sliding window over
paragraphs with overlap."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace


@dataclass
class Chunk:
    ordinal: int
    title: str | None
    content: str
    tokenCount: int


@dataclass
class ChunkOptions:
    # Target size for windowed chunks.
    targetTokens: int = 400
    # Hard cap for any chunk; larger topics are split.
    maxTokens: int = 800
    overlapTokens: int = 60


def estimate_tokens(text: str) -> int:
    """Cheap token estimate (≈4 chars/token for English prose)."""
    return max(1, math.ceil(len(text) / 4))


_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize_text(raw: str) -> str:
    text = re.sub(r"\r\n?", "\n", raw)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = _CONTROL.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


_NUMBERED = re.compile(r"^\s*(\d{1,3})[.)]\s+(\S.{0,120})$")
_MARKDOWN = re.compile(r"^\s*#{1,6}\s+(\S.{0,120})$")
_ALL_CAPS = re.compile(r"^\s*([A-Z][A-Z0-9 &/',-]{2,79})\s*$")


def heading_title(line: str) -> str | None:
    """Returns the heading title when the line looks like a section heading."""
    m1 = _MARKDOWN.match(line)
    if m1:
        return m1.group(1).strip()
    m2 = _NUMBERED.match(line)
    if m2:
        title = m2.group(2).strip()
        if not re.search(r"[.!?]$", title) and len(title.split()) <= 12:
            return title
    m3 = _ALL_CAPS.match(line)
    if m3 and re.search(r"[A-Z]{3,}", m3.group(1)):
        return m3.group(1).strip()
    return None


@dataclass
class _Section:
    title: str | None
    lines: list[str]


def _split_sections(text: str) -> list[_Section]:
    sections = [_Section(None, [])]
    for line in text.split("\n"):
        title = heading_title(line)
        if title:
            sections.append(_Section(title, [line.strip()]))
        else:
            sections[-1].lines.append(line)
    return [s for s in sections if "\n".join(s.lines).strip()]


def _windows(paragraphs: list[str], opts: ChunkOptions) -> list[str]:
    out: list[str] = []
    current: list[str] = []
    current_tokens = 0

    def flush() -> None:
        if current:
            out.append("\n\n".join(current))

    for p in paragraphs:
        t = estimate_tokens(p)
        if t > opts.maxTokens:
            # Pathological paragraph (no blank lines): hard-split by sentences.
            flush()
            current = []
            current_tokens = 0
            buf = ""
            for sentence in re.split(r"(?<=[.!?])\s+", p):
                if estimate_tokens(f"{buf} {sentence}") > opts.targetTokens and buf:
                    out.append(buf.strip())
                    buf = ""
                buf += f" {sentence}"
            if buf.strip():
                out.append(buf.strip())
            continue
        if current_tokens + t > opts.targetTokens and current:
            flush()
            # Overlap: carry the tail of the previous window.
            tail: list[str] = []
            tail_tokens = 0
            for i in range(len(current) - 1, -1, -1):
                if tail_tokens >= opts.overlapTokens:
                    break
                tail.insert(0, current[i])
                tail_tokens += estimate_tokens(current[i])
            current = tail
            current_tokens = tail_tokens
        current.append(p)
        current_tokens += t
    flush()
    return out


def chunk_text(raw: str, options: ChunkOptions | None = None) -> list[Chunk]:
    opts = options or ChunkOptions()
    text = normalize_text(raw)
    if not text:
        return []
    chunks: list[Chunk] = []

    def push(title: str | None, content: str) -> None:
        c = content.strip()
        if c:
            chunks.append(Chunk(len(chunks), title, c, estimate_tokens(c)))

    for section in _split_sections(text):
        content = "\n".join(section.lines).strip()
        if estimate_tokens(content) <= opts.maxTokens:
            push(section.title, content)
            continue
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
        for i, part in enumerate(_windows(paragraphs, opts)):
            push(f"{section.title} (part {i + 1})" if section.title else None, part)

    # Merge tiny trailing fragments (e.g. a lone heading) into their neighbour.
    merged: list[Chunk] = []
    for c in chunks:
        prev = merged[-1] if merged else None
        if prev and len(c.content) < 40 and prev.title == c.title:
            prev.content += f"\n{c.content}"
            prev.tokenCount = estimate_tokens(prev.content)
            continue
        merged.append(replace(c, ordinal=len(merged)))
    return merged
