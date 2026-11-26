from __future__ import annotations

from datetime import datetime
from typing import List, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class ChatFilters(BaseModel):
    document_ids: List[UUID] = []


class ChatRequest(BaseModel):
    conversation_id: UUID | None = None
    question: str = Field(min_length=2, max_length=4000)
    filters: ChatFilters = Field(default_factory=ChatFilters)
    top_k: int = Field(default=5, ge=1, le=15)
    retrieval_mode: Literal["vector", "keyword", "hybrid", "hybrid_rerank"] = "hybrid_rerank"


class CitationItem(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    page: int | None = None
    quote: str
    relevance_score: float


class RetrievalMeta(BaseModel):
    candidate_count: int
    reranked_count: int
    mode: str


class TokenUsageMeta(BaseModel):
    input_tokens: int
    output_tokens: int


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    citations: List[CitationItem]
    retrieval: RetrievalMeta
    usage: TokenUsageMeta
    latency_ms: float


class MessageItem(BaseModel):
    id: UUID
    role: str
    content: str
    citations: list[dict]
    model: str | None = None
    token_usage: dict
    latency_ms: float | None = None
    created_at: datetime


class ConversationSummary(BaseModel):
    id: UUID
    organization_id: UUID
    title: str
    created_at: datetime


class ConversationDetail(ConversationSummary):
    messages: List[MessageItem]


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: UUID
    message_id: UUID
    rating: int
    comment: str | None = None
    created_at: datetime
