from __future__ import annotations

from typing import Dict, List

from packages.rag.retrieval.types import RetrievedChunk


def reciprocal_rank_fusion(
    ranked_lists: List[List[RetrievedChunk]],
    k: int = 60,
) -> List[RetrievedChunk]:
    """
    Combine multiple ranked candidate lists using Reciprocal Rank Fusion:
        RRF(d) = sum_{r in R} 1 / (k + rank_r(d))
    where rank_r(d) is 1-indexed.
    """
    fused_scores: Dict[str, float] = {}
    chunk_map: Dict[str, RetrievedChunk] = {}

    for list_idx, candidates in enumerate(ranked_lists):
        for zero_rank, item in enumerate(candidates):
            rank = zero_rank + 1
            rrf_increment = 1.0 / (k + rank)
            fused_scores[item.chunk_id] = fused_scores.get(item.chunk_id, 0.0) + rrf_increment

            if item.chunk_id not in chunk_map:
                chunk_map[item.chunk_id] = item
            existing = chunk_map[item.chunk_id]
            if list_idx == 0 and existing.vector_rank is None:
                existing.vector_rank = rank
            elif list_idx == 1 and existing.keyword_rank is None:
                existing.keyword_rank = rank

    ordered_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)
    results: List[RetrievedChunk] = []
    for cid in ordered_ids:
        chunk = chunk_map[cid]
        chunk.score = round(fused_scores[cid], 6)
        results.append(chunk)
    return results
