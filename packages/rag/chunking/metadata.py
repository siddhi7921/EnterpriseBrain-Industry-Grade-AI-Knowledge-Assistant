from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ChunkMetadata:
    document_id: str
    source_filename: str
    page_number: int | None = None
    section_title: str | None = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "document_id": self.document_id,
            "source_filename": self.source_filename,
            "page_number": self.page_number,
            "section_title": self.section_title,
        }
        payload.update(self.extra)
        return payload


@dataclass
class DocumentChunkData:
    chunk_index: int
    content: str
    token_count: int
    metadata: ChunkMetadata
