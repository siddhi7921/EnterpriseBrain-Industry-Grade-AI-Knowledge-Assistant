from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from packages.rag.retrieval.types import RetrievedChunk


@dataclass
class ValidatedCitation:
    document_id: str
    filename: str
    chunk_id: str
    page: int | None
    quote: str
    relevance_score: float

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "chunk_id": self.chunk_id,
            "page": self.page,
            "quote": self.quote,
            "relevance_score": self.relevance_score,
        }


class CitationValidator:
    """
    Ensures every citation returned to the client maps to an actual retrieved, authorized chunk.
    Strips hallucinated or unauthorized chunk IDs from the generated text.
    """

    _CHUNK_TAG_PATTERN = re.compile(r"\[CHUNK:([a-zA-Z0-9\-]+)\]")

    def validate(
        self,
        raw_answer: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> tuple[str, List[ValidatedCitation]]:
        if not retrieved_chunks:
            safe_msg = (
                "I could not find sufficient authorized evidence in your organisation's documents "
                "to answer this question."
            )
            return safe_msg, []

        valid_map: Dict[str, RetrievedChunk] = {c.chunk_id: c for c in retrieved_chunks}
        found_ids = self._CHUNK_TAG_PATTERN.findall(raw_answer)

        seen: set[str] = set()
        citations: List[ValidatedCitation] = []
        cleaned_answer = raw_answer

        for cid in found_ids:
            if cid not in valid_map:
                # Strip hallucinated / unauthorized citation tag
                cleaned_answer = cleaned_answer.replace(f"[CHUNK:{cid}]", "")
                continue
            if cid in seen:
                continue
            seen.add(cid)
            ch = valid_map[cid]
            quote = ch.content[:240].strip()
            if len(ch.content) > 240:
                quote += "..."
            citations.append(
                ValidatedCitation(
                    document_id=ch.document_id,
                    filename=ch.filename,
                    chunk_id=ch.chunk_id,
                    page=ch.page_number,
                    quote=quote,
                    relevance_score=round(float(ch.score), 4),
                )
            )

        cleaned_answer = re.sub(r"\s{2,}", " ", cleaned_answer).strip()

        # If model answered with factual text but forgot explicit tags, attach top retrieved source if relevant
        if not citations and retrieved_chunks and "could not find sufficient" not in cleaned_answer.lower():
            top = retrieved_chunks[0]
            if top.score >= 0.25:
                quote = top.content[:240].strip() + ("..." if len(top.content) > 240 else "")
                citations.append(
                    ValidatedCitation(
                        document_id=top.document_id,
                        filename=top.filename,
                        chunk_id=top.chunk_id,
                        page=top.page_number,
                        quote=quote,
                        relevance_score=round(float(top.score), 4),
                    )
                )

        return cleaned_answer, citations
