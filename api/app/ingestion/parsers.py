"""File-kind detection (extension sanity-checked against magic bytes) and text extraction."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Literal

from app.errors import UnsupportedMediaTypeError

SupportedKind = Literal["text", "markdown", "pdf", "docx"]

SUPPORTED_EXTENSIONS = [".txt", ".md", ".markdown", ".pdf", ".docx"]

CONTENT_TYPES: dict[str, str] = {
    "text": "text/plain",
    "markdown": "text/markdown",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass
class DetectedFile:
    kind: SupportedKind
    content_type: str


_EXT = re.compile(r"\.[a-z0-9]+$")


def detect_file_kind(filename: str, data: bytes, declared_type: str | None = None) -> DetectedFile:
    """Picks the parser from the file extension, sanity-checked against magic bytes."""
    m = _EXT.search(filename.lower())
    ext = m.group(0) if m else ""
    is_pdf = len(data) > 4 and data[:4] == b"%PDF"
    is_zip = len(data) > 2 and data[:2] == b"PK"

    kind: SupportedKind | None = None
    if ext == ".pdf" or (is_pdf and not ext):
        kind = "pdf"
    elif ext == ".docx" or (is_zip and declared_type == CONTENT_TYPES["docx"]):
        kind = "docx"
    elif ext in (".md", ".markdown"):
        kind = "markdown"
    elif ext == ".txt" or (declared_type or "").startswith("text/"):
        kind = "text"

    if kind == "pdf" and not is_pdf:
        kind = None
    if kind == "docx" and not is_zip:
        kind = None
    if kind is None:
        raise UnsupportedMediaTypeError(
            f'Unsupported file type "{ext or declared_type or "unknown"}". '
            f"Upload a {', '.join(SUPPORTED_EXTENSIONS)} file.",
            supported=list(SUPPORTED_EXTENSIONS),
        )
    return DetectedFile(kind, CONTENT_TYPES[kind])


def extract_text(kind: SupportedKind, data: bytes) -> str:
    if kind in ("text", "markdown"):
        return data.decode("utf-8", errors="replace")
    if kind == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    import mammoth

    result = mammoth.extract_raw_text(io.BytesIO(data))
    return str(result.value)
