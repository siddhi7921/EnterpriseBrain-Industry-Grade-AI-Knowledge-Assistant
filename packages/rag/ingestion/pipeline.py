from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from packages.rag.ingestion.cleaning import clean_text, neutralize_prompt_injection
from packages.rag.ingestion.extractors import (
    extract_docx_bytes,
    extract_pdf_bytes,
    extract_text_or_markdown_bytes,
)


@dataclass
class ExtractedSection:
    document_id: str
    source_filename: str
    page_number: int | None
    section_title: str | None
    text: str


@dataclass
class ExtractionResult:
    document_id: str
    source_filename: str
    sections: List[ExtractedSection] = field(default_factory=list)

    @property
    def total_characters(self) -> int:
        return sum(len(s.text) for s in self.sections)


SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
}


def extract_document(
    *,
    document_id: str,
    filename: str,
    mime_type: str,
    file_bytes: bytes,
) -> ExtractionResult:
    """Extract and normalize structured sections from PDF, DOCX, TXT, or Markdown."""
    lower_name = filename.lower()
    if mime_type == "application/pdf" or lower_name.endswith(".pdf"):
        raw_segments = extract_pdf_bytes(file_bytes)
    elif (
        mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or lower_name.endswith(".docx")
    ):
        raw_segments = extract_docx_bytes(file_bytes)
    elif mime_type in {"text/plain", "text/markdown", "text/x-markdown"} or lower_name.endswith(
        (".txt", ".md", ".markdown")
    ):
        raw_segments = extract_text_or_markdown_bytes(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: {mime_type} ({filename})")

    sections: List[ExtractedSection] = []
    for seg in raw_segments:
        cleaned = neutralize_prompt_injection(clean_text(seg.text))
        if cleaned:
            sections.append(
                ExtractedSection(
                    document_id=document_id,
                    source_filename=filename,
                    page_number=seg.page_number,
                    section_title=seg.section_title,
                    text=cleaned,
                )
            )

    if not sections:
        raise ValueError("No readable text could be extracted from the uploaded document.")

    return ExtractionResult(
        document_id=document_id,
        source_filename=filename,
        sections=sections,
    )
