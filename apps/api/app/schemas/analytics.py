from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    organization_id: UUID
    total_documents: int
    indexed_documents: int
    total_chunks: int
    total_conversations: int
    total_queries: int
    avg_latency_ms: float
    total_input_tokens: int
    total_output_tokens: int
    avg_feedback_rating: float | None = None


class AuditLogItem(BaseModel):
    id: UUID
    organization_id: UUID
    actor_id: UUID | None = None
    action: str
    resource_id: UUID | None = None
    metadata_json: dict[str, Any]
    created_at: datetime
