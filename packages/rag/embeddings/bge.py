from __future__ import annotations

import hashlib
import math
import re
from typing import List

from packages.rag.embeddings.base import BaseEmbedder


class HashDeterministicEmbedder(BaseEmbedder):
    """
    Lightweight, deterministic 1024-dim L2-normalized semantic-hash embedder.
    Used in CI, offline tests, and low-memory environments when BAAI/bge-m3 weights are not loaded.
    Captures unigram and bigram lexical overlap with cosine similarity semantics.
    """

    def __init__(self, dim: int = 1024) -> None:
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _embed_single(self, text: str) -> List[float]:
        vec = [0.0] * self._dim
        tokens = re.findall(r"[a-z0-9]{2,}", text.lower())
        if not tokens:
            vec[0] = 1.0
            return vec

        features = list(tokens)
        for i in range(len(tokens) - 1):
            features.append(f"{tokens[i]}_{tokens[i + 1]}")

        for feat in features:
            digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
            val = int.from_bytes(digest, "big")
            idx = val % self._dim
            sign = 1.0 if ((val >> 63) & 1) == 0 else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]


class BGEM3Embedder(BaseEmbedder):
    """Production multilingual dense embedder backed by BAAI/bge-m3 (1024 dimensions)."""

    def __init__(self, model_name: str = "BAAI/bge-m3", dim: int = 1024) -> None:
        self.model_name = model_name
        self._dim = dim
        self._model = None

    @property
    def dimension(self) -> int:
        return self._dim

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._load_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return [row.tolist() for row in embeddings]


_EMBEDDER_CACHE: dict[str, BaseEmbedder] = {}


def get_embedder(
    provider: str = "local_hash",
    model_name: str = "BAAI/bge-m3",
    dimension: int = 1024,
) -> BaseEmbedder:
    key = f"{provider}:{model_name}:{dimension}"
    if key not in _EMBEDDER_CACHE:
        if provider == "bge_m3":
            _EMBEDDER_CACHE[key] = BGEM3Embedder(model_name=model_name, dim=dimension)
        else:
            _EMBEDDER_CACHE[key] = HashDeterministicEmbedder(dim=dimension)
    return _EMBEDDER_CACHE[key]
