from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Conversation, Document, DocumentChunk, Feedback, Message
from app.schemas.analytics import AnalyticsOverview, AuditLogItem
from app.services.permission_service import get_membership_or_403


def get_organization_analytics(db: Session, organization_id: UUID, user_id: UUID) -> AnalyticsOverview:
    get_membership_or_403(db, organization_id, user_id)

    total_docs = db.execute(
        select(func.count(Document.id)).where(Document.organization_id == organization_id)
    ).scalar_one()
    indexed_docs = db.execute(
        select(func.count(Document.id)).where(
            Document.organization_id == organization_id,
            Document.status == "indexed",
        )
    ).scalar_one()
    total_chunks = db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.organization_id == organization_id)
    ).scalar_one()
    total_convs = db.execute(
        select(func.count(Conversation.id)).where(Conversation.organization_id == organization_id)
    ).scalar_one()

    assistant_msgs = (
        db.execute(
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.organization_id == organization_id, Message.role == "assistant")
        )
        .scalars()
        .all()
    )

    total_queries = len(assistant_msgs)
    latencies = [m.latency_ms for m in assistant_msgs if m.latency_ms is not None]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    total_in = sum(int((m.token_usage or {}).get("input_tokens", 0)) for m in assistant_msgs)
    total_out = sum(int((m.token_usage or {}).get("output_tokens", 0)) for m in assistant_msgs)

    avg_rating = db.execute(
        select(func.avg(Feedback.rating))
        .join(Message, Feedback.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.organization_id == organization_id)
    ).scalar_one()

    return AnalyticsOverview(
        organization_id=organization_id,
        total_documents=int(total_docs or 0),
        indexed_documents=int(indexed_docs or 0),
        total_chunks=int(total_chunks or 0),
        total_conversations=int(total_convs or 0),
        total_queries=total_queries,
        avg_latency_ms=avg_latency,
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        avg_feedback_rating=round(float(avg_rating), 2) if avg_rating is not None else None,
    )


def list_organization_audit_logs(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    limit: int = 100,
) -> list[AuditLogItem]:
    get_membership_or_403(db, organization_id, user_id)
    logs = (
        db.execute(
            select(AuditLog)
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        AuditLogItem(
            id=item.id,
            organization_id=item.organization_id,
            actor_id=item.actor_id,
            action=item.action,
            resource_id=item.resource_id,
            metadata_json=item.metadata_json,
            created_at=item.created_at,
        )
        for item in logs
    ]
