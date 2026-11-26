from __future__ import annotations

import re
from typing import List
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from packages.rag.retrieval.types import RetrievedChunk


def search_keyword_chunks(
    *,
    db: Session,
    chunk_model,
    document_model,
    allowed_doc_ids_subquery: Select,
    organization_id: UUID,
    query_text: str,
    document_ids: List[UUID] | None = None,
    limit: int = 20,
) -> List[RetrievedChunk]:
    """
    Tenant-isolated, permission-filtered keyword search.
    Uses PostgreSQL GIN full-text search (ts_rank_cd) on Postgres and TF-weighted keyword match on SQLite.
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
        ts_vector = func.to_tsvector("english", chunk_model.content)
        ts_query = func.plainto_tsquery("english", query_text)
        rank_expr = func.ts_rank_cd(ts_vector, ts_query)
        stmt = (
            base_stmt.add_columns(rank_expr.label("kw_score"))
            .where(ts_vector.op("@@")(ts_query))
            .order_by(rank_expr.desc())
            .limit(limit)
        )
        rows = db.execute(stmt).all()
        results: List[RetrievedChunk] = []
        for rank_idx, (chunk, filename, kw_score) in enumerate(rows, start=1):
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
                    score=round(float(kw_score or 0.0), 6),
                    keyword_rank=rank_idx,
                    metadata=meta,
                )
            )
        return results

    # SQLite fallback for CI & local tests
    q_terms = re.findall(r"[a-z0-9]{2,}", query_text.lower())
    if not q_terms:
        return []
    rows = db.execute(base_stmt).all()
    scored = []
    for chunk, filename in rows:
        content_lower = chunk.content.lower()
        hits = sum(content_lower.count(term) for term in q_terms)
        unique_hits = sum(1 for term in set(q_terms) if term in content_lower)
        if hits > 0:
            score = unique_hits * 2.0 + hits * 0.25
            scored.append((score, chunk, filename))
    scored.sort(key=lambda item: item[0], reverse=True)

    results = []
    for rank_idx, (score, chunk, filename) in enumerate(scored[:limit], start=1):
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
                score=round(score, 6),
                keyword_rank=rank_idx,
                metadata=meta,
            )
        )
    return results
