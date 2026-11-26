from __future__ import annotations

from datetime import datetime
from typing import List, Literal
from uuid import UUID
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    uploaded_by: UUID
    filename: str
    mime_type: str
    checksum: str
    status: str
    access_scope: str
    version: int
    chunk_count: int = 0
    created_at: datetime


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    status: str
    chunk_count: int
    latest_job_status: str | None = None
    attempts: int = 0
    error_message: str | None = None


class PermissionEntry(BaseModel):
    user_id: UUID
    permission: Literal["read", "manage"] = "read"


class DocumentPermissionsUpdateRequest(BaseModel):
    access_scope: Literal["organization", "restricted"]
    permissions: List[PermissionEntry] = []
