from __future__ import annotations

import re
from typing import List

from packages.rag.chunking.metadata import ChunkMetadata, DocumentChunkData
from packages.rag.ingestion.pipeline import ExtractionResult


def estimate_token_count(text: str) -> int:
    """Approximate token count (~1.3 tokens per whitespace word, aligned with BPE tokenizers)."""
    words = text.split()
    return max(1, int(round(len(words) * 1.3))) if words else 0


class StructureAwareChunker:
    """Splits extracted document sections into overlapping token-bounded chunks while preserving headings and tables."""

    def __init__(self, chunk_size_tokens: int = 500, overlap_tokens: int = 75) -> None:
        if chunk_size_tokens <= 0:
            raise ValueError("chunk_size_tokens must be positive")
        if overlap_tokens < 0 or overlap_tokens >= chunk_size_tokens:
            raise ValueError("overlap_tokens must be >= 0 and < chunk_size_tokens")
        self.chunk_size_tokens = chunk_size_tokens
        self.overlap_tokens = overlap_tokens

    def _split_atomic_blocks(self, text: str) -> List[str]:
        """Split text by paragraphs while keeping markdown/pipe tables intact where possible."""
        raw_blocks = re.split(r"\n\s*\n", text)
        blocks: List[str] = []
        for block in raw_blocks:
            cleaned = block.strip()
            if not cleaned:
                continue
            if estimate_token_count(cleaned) <= self.chunk_size_tokens:
                blocks.append(cleaned)
            else:
                sentences = re.split(r"(?<=[.!?])\s+", cleaned)
                for sent in sentences:
                    if sent.strip():
                        blocks.append(sent.strip())
        return blocks

    def chunk_document(self, extraction: ExtractionResult) -> List[DocumentChunkData]:
        chunks: List[DocumentChunkData] = []
        chunk_idx = 0

        for section in extraction.sections:
            blocks = self._split_atomic_blocks(section.text)
            current_blocks: List[str] = []
            current_tokens = 0

            for block in blocks:
                block_tokens = estimate_token_count(block)

                if current_blocks and (current_tokens + block_tokens > self.chunk_size_tokens):
                    content = "\n\n".join(current_blocks)
                    chunks.append(
                        DocumentChunkData(
                            chunk_index=chunk_idx,
                            content=content,
                            token_count=estimate_token_count(content),
                            metadata=ChunkMetadata(
                                document_id=section.document_id,
                                source_filename=section.source_filename,
                                page_number=section.page_number,
                                section_title=section.section_title,
                            ),
                        )
                    )
                    chunk_idx += 1

                    overlap_blocks: List[str] = []
                    overlap_tok = 0
                    for prev in reversed(current_blocks):
                        pt = estimate_token_count(prev)
                        if overlap_tok + pt <= self.overlap_tokens:
                            overlap_blocks.insert(0, prev)
                            overlap_tok += pt
                        else:
                            break
                    current_blocks = overlap_blocks
                    current_tokens = overlap_tok

                current_blocks.append(block)
                current_tokens += block_tokens

            if current_blocks:
                content = "\n\n".join(current_blocks)
                chunks.append(
                    DocumentChunkData(
                        chunk_index=chunk_idx,
                        content=content,
                        token_count=estimate_token_count(content),
                        metadata=ChunkMetadata(
                            document_id=section.document_id,
                            source_filename=section.source_filename,
                            page_number=section.page_number,
                            section_title=section.section_title,
                        ),
                    )
                )
                chunk_idx += 1

        return chunks
