from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """Abstract interface for dense text embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> List[float]:
        vectors = self.embed_documents([query])
        return vectors[0]
