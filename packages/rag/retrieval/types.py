from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    content: str
    page_number: int | None = None
    section_title: str | None = None
    score: float = 0.0
    vector_rank: int | None = None
    keyword_rank: int | None = None
    rerank_score: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
