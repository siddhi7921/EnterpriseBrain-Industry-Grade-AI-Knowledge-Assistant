from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import List


@dataclass
class RawSegment:
    page_number: int | None
    section_title: str | None
    text: str


def extract_pdf_bytes(data: bytes) -> List[RawSegment]:
    """Extract text per page from PDF using PyMuPDF (fitz), with optional Tesseract OCR fallback."""
    import fitz  # PyMuPDF

    segments: List[RawSegment] = []
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text("text") or ""
            if not text.strip():
                try:
                    import pytesseract
                    from PIL import Image

                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    text = pytesseract.image_to_string(img)
                except Exception:
                    text = ""

            if text.strip():
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                candidate_heading = lines[0][:120] if lines and len(lines[0]) < 90 else None
                segments.append(
                    RawSegment(
                        page_number=page_idx + 1,
                        section_title=candidate_heading,
                        text=text,
                    )
                )
    finally:
        doc.close()
    return segments


def extract_docx_bytes(data: bytes) -> List[RawSegment]:
    """Extract paragraphs and tables from DOCX preserving heading hierarchy."""
    import docx

    document = docx.Document(io.BytesIO(data))
    segments: List[RawSegment] = []
    current_heading: str | None = None
    buffer: List[str] = []

    def flush_buffer() -> None:
        if buffer:
            segments.append(
                RawSegment(
                    page_number=1,
                    section_title=current_heading,
                    text="\n".join(buffer),
                )
            )
            buffer.clear()

    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style_name = (para.style.name or "").lower() if para.style else ""
        if style_name.startswith("heading"):
            flush_buffer()
            current_heading = text[:140]
        else:
            buffer.append(text)

    for table in document.tables:
        rows_text = []
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            if any(cells):
                rows_text.append(" | ".join(cells))
        if rows_text:
            buffer.append("\n".join(rows_text))

    flush_buffer()
    return segments


def extract_text_or_markdown_bytes(data: bytes) -> List[RawSegment]:
    """Extract Markdown or plain text split by Markdown headings when present."""
    decoded = data.decode("utf-8", errors="replace")
    heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)
    matches = list(heading_pattern.finditer(decoded))

    if not matches:
        return [RawSegment(page_number=1, section_title=None, text=decoded)] if decoded.strip() else []

    segments: List[RawSegment] = []
    if matches[0].start() > 0:
        preamble = decoded[: matches[0].start()].strip()
        if preamble:
            segments.append(RawSegment(page_number=1, section_title="Introduction", text=preamble))

    for idx, match in enumerate(matches):
        title = match.group(2).strip()[:140]
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(decoded)
        body = decoded[start:end].strip()
        if body:
            segments.append(RawSegment(page_number=1, section_title=title, text=body))

    return segments
