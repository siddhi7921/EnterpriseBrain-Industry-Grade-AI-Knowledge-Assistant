from __future__ import annotations

from packages.rag.retrieval.fusion import reciprocal_rank_fusion
from packages.rag.retrieval.reranker import BaseReranker, BGERerankerV2M3, LexicalOverlapReranker, get_reranker
from packages.rag.retrieval.types import RetrievedChunk

__all__ = [
    "RetrievedChunk",
    "reciprocal_rank_fusion",
    "BaseReranker",
    "BGERerankerV2M3",
    "LexicalOverlapReranker",
    "get_reranker",
    "HybridRetrievalPipeline",
]

def __getattr__(name: str):
    if name == "HybridRetrievalPipeline":
        from packages.rag.retrieval.pipeline import HybridRetrievalPipeline
        return HybridRetrievalPipeline
    raise AttributeError(name)
