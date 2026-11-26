from __future__ import annotations

import math
from typing import List, Sequence
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from packages.rag.retrieval.types import RetrievedChunk


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def search_vector_chunks(
    *,
    db: Session,
    chunk_model,
    document_model,
    allowed_doc_ids_subquery: Select,
    organization_id: UUID,
    query_embedding: List[float],
    document_ids: List[UUID] | None = None,
    limit: int = 20,
) -> List[RetrievedChunk]:
    """
    Tenant-isolated, permission-filtered vector similarity search.
    Uses native pgvector cosine distance on PostgreSQL and exact cosine fallback on SQLite.
    """
    dialect = db.bind.dialect.name if db.bind is not None else "sqlite"

    base_stmt = (
        select(chunk_model, document_model.filename)
        .join(document_model, chunk_model.document_id == document_model.id)
        .where(
            chunk_model.organization_id == organization_id,
            document_model.organization_id == organization_id,
            document_model.status == "indexed",
            document_model.id.in_(allowed_doc_ids_subquery),
        )
    )
    if document_ids:
        base_stmt = base_stmt.where(document_model.id.in_(document_ids))

    if dialect == "postgresql":
        distance_expr = chunk_model.embedding.cosine_distance(query_embedding)
        stmt = base_stmt.order_by(distance_expr.asc()).limit(limit)
        rows = db.execute(stmt).all()
        results: List[RetrievedChunk] = []
        for rank_idx, (chunk, filename) in enumerate(rows, start=1):
            meta = chunk.metadata_json or {}
            sim = max(0.0, 1.0 - _cosine_similarity(query_embedding, chunk.embedding or []))
            results.append(
                RetrievedChunk(
                    chunk_id=str(chunk.id),
                    document_id=str(chunk.document_id),
                    filename=filename,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    page_number=meta.get("page_number"),
                    section_title=meta.get("section_title"),
                    score=round(1.0 - sim, 6),
                    vector_rank=rank_idx,
                    metadata=meta,
                )
            )
        return results

    # SQLite fallback for local unit/integration tests
    rows = db.execute(base_stmt).all()
    scored = []
    for chunk, filename in rows:
        emb = chunk.embedding or []
        sim = _cosine_similarity(query_embedding, emb)
        scored.append((sim, chunk, filename))
    scored.sort(key=lambda item: item[0], reverse=True)

    results = []
    for rank_idx, (sim, chunk, filename) in enumerate(scored[:limit], start=1):
        meta = chunk.metadata_json or {}
        results.append(
            RetrievedChunk(
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                filename=filename,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=meta.get("page_number"),
                section_title=meta.get("section_title"),
                score=round(sim, 6),
                vector_rank=rank_idx,
                metadata=meta,
            )
        )
    return results
