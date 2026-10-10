from __future__ import annotations

import pytest

from app.ingestion.chunker import ChunkOptions, chunk_text, heading_title, normalize_text
from app.ingestion.job import describe_error
from app.ingestion.parsers import detect_file_kind, extract_text
from tests.conftest import sample


def test_heading_title_recognises_numbered_markdown_and_all_caps() -> None:
    assert heading_title("1. Shipping Issues") == "Shipping Issues"
    assert heading_title("10) Account Access or Permission Problems") == (
        "Account Access or Permission Problems"
    )
    assert heading_title("## Refunds") == "Refunds"
    assert heading_title("BILLING AND PAYMENTS") == "BILLING AND PAYMENTS"


def test_heading_title_ignores_sentences_and_list_items() -> None:
    assert heading_title("1. Verify the order and contact the courier for an updated ETA.") is None
    assert heading_title("- Acknowledge the delay or problem.") is None
    assert heading_title("Hello [Name],") is None


def test_chunk_text_one_chunk_per_topic_for_the_bookshop_file() -> None:
    chunks = chunk_text(sample("bookshop_support_guidelines.txt").decode())
    assert [c.title for c in chunks] == [
        "Shipping Issues",
        "Wrong Product Delivered",
        "Damaged Product Received",
        "Returns and Refunds",
        "Payment and Billing Issues",
        "Order Modifications and Cancellations",
        "Product Availability and Backorders",
    ]
    assert all("Sample reply" in c.content for c in chunks)
    assert [c.ordinal for c in chunks] == list(range(7))


def test_chunk_text_ten_topics_for_the_vpn_file() -> None:
    chunks = chunk_text(sample("vpn_support_guidelines.txt").decode())
    assert len(chunks) == 10
    assert chunks[0].title == "Connection Failures"
    assert chunks[9].title == "Account Access or Permission Problems"


def test_chunk_text_splits_unstructured_text_into_overlapping_windows() -> None:
    para = "Customers may ask about delivery times, refunds and account access. " * 12
    text = "\n\n".join([para.strip()] * 8)
    chunks = chunk_text(text, ChunkOptions(targetTokens=400, maxTokens=800, overlapTokens=60))
    assert len(chunks) > 1
    assert all(c.title is None for c in chunks)
    assert all(c.tokenCount <= 800 for c in chunks)


def test_chunk_text_splits_an_oversized_section_into_titled_parts() -> None:
    body = "\n\n".join(
        f"Paragraph {i} about refunds and their processing timelines in detail." for i in range(30)
    )
    chunks = chunk_text(
        f"1. Refunds\n{body}", ChunkOptions(targetTokens=100, maxTokens=150, overlapTokens=20)
    )
    assert len(chunks) > 1
    assert chunks[0].title == "Refunds (part 1)"


def test_chunk_text_empty_input_and_line_endings() -> None:
    assert chunk_text("   \n\n ") == []
    assert normalize_text("a\r\nb\r\n\r\n\r\nc") == "a\nb\n\nc"


def test_describe_error_unwraps_provider_json_envelopes() -> None:
    err = RuntimeError(
        '{"error":{"code":400,"message":"API key not valid. Please pass a valid API key.","status":"INVALID_ARGUMENT"}}'
    )
    assert (
        describe_error(err) == "API key not valid. Please pass a valid API key. (INVALID_ARGUMENT)"
    )
    assert describe_error(RuntimeError("quota exceeded")) == "quota exceeded"
    assert len(describe_error("x" * 600)) == 501


def test_detect_file_kind_maps_extensions_to_parsers() -> None:
    assert detect_file_kind("a.txt", b"hi").kind == "text"
    assert detect_file_kind("a.MD", b"# hi").kind == "markdown"
    assert detect_file_kind("a.pdf", b"%PDF-1.4 ...").kind == "pdf"
    assert detect_file_kind("a.docx", bytes([0x50, 0x4B, 3, 4])).kind == "docx"
    assert detect_file_kind("notes", b"hi", "text/plain").kind == "text"


def test_detect_file_kind_rejects_unknown_types_and_mislabeled_binaries() -> None:
    with pytest.raises(Exception, match="Unsupported file type"):
        detect_file_kind("a.exe", b"MZ")
    with pytest.raises(Exception, match="Unsupported file type"):
        detect_file_kind("a.pdf", b"not a pdf")


def test_extract_text_decodes_text_markdown_pdf_and_docx() -> None:
    assert extract_text("text", b"hello\nworld") == "hello\nworld"
    assert extract_text("markdown", b"# T\nbody") == "# T\nbody"
    import io

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    assert extract_text("pdf", buf.getvalue()) == ""
    import zipfile

    docx = io.BytesIO()
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        )
        z.writestr(
            "word/document.xml",
            '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello docx</w:t></w:r></w:p></w:body></w:document>',
        )
    assert extract_text("docx", docx.getvalue()).strip() == "Hello docx"
