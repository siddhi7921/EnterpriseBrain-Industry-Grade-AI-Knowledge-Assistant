from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.orm import Session

from packages.rag.embeddings.base import BaseEmbedder
from packages.rag.retrieval.fusion import reciprocal_rank_fusion
from packages.rag.retrieval.keyword_search import search_keyword_chunks
from packages.rag.retrieval.reranker import BaseReranker
from packages.rag.retrieval.types import RetrievedChunk
from packages.rag.retrieval.vector_search import search_vector_chunks

RetrievalMode = Literal["vector", "keyword", "hybrid", "hybrid_rerank"]


@dataclass
class RetrievalOutcome:
    chunks: List[RetrievedChunk]
    candidate_count: int
    reranked_count: int
    mode: RetrievalMode


class HybridRetrievalPipeline:
    """
    Orchestrates permission-aware retrieval across 4 benchmarkable modes:
    - vector: dense embedding search only
    - keyword: full-text lexical search only
    - hybrid: vector + keyword combined via Reciprocal Rank Fusion (RRF)
    - hybrid_rerank: hybrid RRF candidates reordered by a cross-encoder reranker
    """

    def __init__(self, embedder: BaseEmbedder, reranker: BaseReranker, rrf_k: int = 60) -> None:
        self.embedder = embedder
        self.reranker = reranker
        self.rrf_k = rrf_k

    def retrieve(
        self,
        *,
        db: Session,
        chunk_model,
        document_model,
        allowed_doc_ids_subquery: Select,
        organization_id: UUID,
        query: str,
        document_ids: List[UUID] | None = None,
        candidate_limit: int = 20,
        top_k: int = 5,
        mode: RetrievalMode = "hybrid_rerank",
    ) -> RetrievalOutcome:
        if mode == "vector":
            q_emb = self.embedder.embed_query(query)
            vec_hits = search_vector_chunks(
                db=db,
                chunk_model=chunk_model,
                document_model=document_model,
                allowed_doc_ids_subquery=allowed_doc_ids_subquery,
                organization_id=organization_id,
                query_embedding=q_emb,
                document_ids=document_ids,
                limit=candidate_limit,
            )
            final = vec_hits[:top_k]
            return RetrievalOutcome(chunks=final, candidate_count=len(vec_hits), reranked_count=len(final), mode=mode)

        if mode == "keyword":
            kw_hits = search_keyword_chunks(
                db=db,
                chunk_model=chunk_model,
                document_model=document_model,
                allowed_doc_ids_subquery=allowed_doc_ids_subquery,
                organization_id=organization_id,
                query_text=query,
                document_ids=document_ids,
                limit=candidate_limit,
            )
            final = kw_hits[:top_k]
            return RetrievalOutcome(chunks=final, candidate_count=len(kw_hits), reranked_count=len(final), mode=mode)

        # Hybrid (and Hybrid + Rerank)
        q_emb = self.embedder.embed_query(query)
        vec_hits = search_vector_chunks(
            db=db,
            chunk_model=chunk_model,
            document_model=document_model,
            allowed_doc_ids_subquery=allowed_doc_ids_subquery,
            organization_id=organization_id,
            query_embedding=q_emb,
            document_ids=document_ids,
            limit=candidate_limit,
        )
        kw_hits = search_keyword_chunks(
            db=db,
            chunk_model=chunk_model,
            document_model=document_model,
            allowed_doc_ids_subquery=allowed_doc_ids_subquery,
            organization_id=organization_id,
            query_text=query,
            document_ids=document_ids,
            limit=candidate_limit,
        )

        fused = reciprocal_rank_fusion([vec_hits, kw_hits], k=self.rrf_k)
        candidates = fused[:candidate_limit]

        if mode == "hybrid":
            final = candidates[:top_k]
            return RetrievalOutcome(
                chunks=final,
                candidate_count=len(candidates),
                reranked_count=len(final),
                mode=mode,
            )

        reranked = self.reranker.rerank(query=query, candidates=candidates, top_k=top_k)
        return RetrievalOutcome(
            chunks=reranked,
            candidate_count=len(candidates),
            reranked_count=len(reranked),
            mode=mode,
        )
