from __future__ import annotations

import math
import re
from typing import List, Sequence


def recall_at_k(relevances: Sequence[bool], total_relevant: int, k: int) -> float:
    if total_relevant <= 0:
        return 0.0
    hits = sum(1 for r in list(relevances)[:k] if r)
    return round(min(1.0, hits / total_relevant), 4)


def precision_at_k(relevances: Sequence[bool], k: int) -> float:
    if k <= 0:
        return 0.0
    slice_k = list(relevances)[:k]
    if not slice_k:
        return 0.0
    return round(sum(1 for r in slice_k if r) / len(slice_k), 4)


def mean_reciprocal_rank(relevances: Sequence[bool]) -> float:
    for idx, is_rel in enumerate(relevances, start=1):
        if is_rel:
            return round(1.0 / idx, 4)
    return 0.0


def ndcg_at_k(relevances: Sequence[bool], k: int) -> float:
    slice_k = [1.0 if r else 0.0 for r in list(relevances)[:k]]
    if not slice_k or sum(slice_k) == 0:
        return 0.0
    dcg = sum(rel / math.log2(idx + 2) for idx, rel in enumerate(slice_k))
    ideal = sorted(slice_k, reverse=True)
    idcg = sum(rel / math.log2(idx + 2) for idx, rel in enumerate(ideal))
    return round(dcg / idcg, 4) if idcg > 0 else 0.0


def faithfulness_score(answer: str, evidence_texts: List[str]) -> float:
    """Measures proportion of content tokens in the generated answer grounded in retrieved evidence."""
    ans_tokens = set(re.findall(r"[a-z0-9]{4,}", answer.lower()))
    if not ans_tokens:
        return 0.0
    ev_tokens = set(re.findall(r"[a-z0-9]{4,}", " ".join(evidence_texts).lower()))
    if not ev_tokens:
        return 0.0
    grounded = len(ans_tokens & ev_tokens)
    return round(grounded / len(ans_tokens), 4)


def citation_correctness_score(cited_chunk_ids: List[str], retrieved_chunk_ids: List[str]) -> float:
    if not cited_chunk_ids:
        return 0.0
    valid = set(retrieved_chunk_ids)
    correct = sum(1 for cid in cited_chunk_ids if cid in valid)
    return round(correct / len(cited_chunk_ids), 4)


def answer_relevance_score(question: str, answer: str, expected_answer: str) -> float:
    ref_tokens = set(re.findall(r"[a-z0-9]{3,}", (question + " " + expected_answer).lower()))
    ans_tokens = set(re.findall(r"[a-z0-9]{3,}", answer.lower()))
    if not ref_tokens or not ans_tokens:
        return 0.0
    return round(len(ref_tokens & ans_tokens) / len(ref_tokens), 4)
