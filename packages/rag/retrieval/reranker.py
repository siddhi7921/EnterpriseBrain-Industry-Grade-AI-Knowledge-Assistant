from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List

from packages.rag.retrieval.types import RetrievedChunk


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int = 5) -> List[RetrievedChunk]:
        raise NotImplementedError


class LexicalOverlapReranker(BaseReranker):
    """Fast cross-term proximity & exact phrase reranker for lightweight/offline environments."""

    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int = 5) -> List[RetrievedChunk]:
        if not candidates:
            return []
        q_lower = query.lower().strip()
        q_tokens = set(re.findall(r"[a-z0-9]{2,}", q_lower))

        scored: List[RetrievedChunk] = []
        for idx, cand in enumerate(candidates):
            c_lower = cand.content.lower()
            c_tokens = set(re.findall(r"[a-z0-9]{2,}", c_lower))
            overlap = len(q_tokens & c_tokens) / max(1, len(q_tokens))
            exact_phrase_bonus = 0.25 if q_lower and q_lower in c_lower else 0.0
            base_prior = 1.0 / (1.0 + idx) * 0.25
            final_score = min(0.9999, round(0.55 * overlap + exact_phrase_bonus + base_prior, 4))
            cand.rerank_score = final_score
            cand.score = final_score
            scored.append(cand)

        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]


class BGERerankerV2M3(BaseReranker):
    """Cross-encoder reranker backed by BAAI/bge-reranker-v2-m3."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3") -> None:
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int = 5) -> List[RetrievedChunk]:
        if not candidates:
            return []
        model = self._load_model()
        pairs = [(query, cand.content) for cand in candidates]
        raw_scores = model.predict(pairs)
        for cand, s in zip(candidates, raw_scores):
            val = float(s)
            cand.rerank_score = round(val, 4)
            cand.score = round(val, 4)
        ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
        return ranked[:top_k]


_RERANKER_CACHE: dict[str, BaseReranker] = {}


def get_reranker(provider: str = "lexical", model_name: str = "BAAI/bge-reranker-v2-m3") -> BaseReranker:
    key = f"{provider}:{model_name}"
    if key not in _RERANKER_CACHE:
        if provider == "bge_reranker":
            _RERANKER_CACHE[key] = BGERerankerV2M3(model_name=model_name)
        else:
            _RERANKER_CACHE[key] = LexicalOverlapReranker()
    return _RERANKER_CACHE[key]
