from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.analytics import AnalyticsOverview, AuditLogItem
from app.services.analytics_service import get_organization_analytics, list_organization_audit_logs

router = APIRouter(tags=["Analytics & Audit"])


@router.get("/organizations/{org_id}/analytics", response_model=AnalyticsOverview)
def organization_analytics(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsOverview:
    return get_organization_analytics(db, org_id, current_user.id)


@router.get("/organizations/{org_id}/audit-logs", response_model=list[AuditLogItem])
def organization_audit_logs(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AuditLogItem]:
    return list_organization_audit_logs(db, org_id, current_user.id)
