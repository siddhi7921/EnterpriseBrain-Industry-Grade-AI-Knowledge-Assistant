from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class EvaluationRunRequest(BaseModel):
    organization_id: UUID
    dataset_name: str = Field(default="enterprise_qa_benchmark")
    top_k: int = Field(default=5, ge=1, le=10)


class EvaluationRunResponse(BaseModel):
    id: UUID
    organization_id: UUID | None = None
    dataset_name: str
    model_name: str
    metrics: dict[str, Any]
    created_at: datetime
