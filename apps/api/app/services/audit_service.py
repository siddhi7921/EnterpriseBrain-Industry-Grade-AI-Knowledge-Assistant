from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def record_audit_event(
    db: Session,
    *,
    organization_id: UUID,
    actor_id: UUID | None,
    action: str,
    resource_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        organization_id=organization_id,
        actor_id=actor_id,
        action=action,
        resource_id=resource_id,
        metadata_json=metadata or {},
    )
    db.add(entry)
    db.flush()
    return entry
