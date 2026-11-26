from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=60)


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    role: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberInviteRequest(BaseModel):
    email: EmailStr
    role: Literal["owner", "admin", "member"] = "member"


class MemberRoleUpdateRequest(BaseModel):
    role: Literal["owner", "admin", "member"]


class MemberResponse(BaseModel):
    user_id: UUID
    email: str
    role: str
