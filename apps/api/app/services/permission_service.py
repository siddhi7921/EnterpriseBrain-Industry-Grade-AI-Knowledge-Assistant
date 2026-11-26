from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, exists, or_, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentPermission, Membership


def get_membership_or_403(db: Session, organization_id: UUID, user_id: UUID) -> Membership:
    membership = db.execute(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user_id,
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organisation.",
        )
    return membership


def require_admin_or_403(db: Session, organization_id: UUID, user_id: UUID) -> Membership:
    membership = get_membership_or_403(db, organization_id, user_id)
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator or owner role is required for this operation.",
        )
    return membership


def accessible_documents_subquery(organization_id: UUID, user_id: UUID, role: str) -> Select:
    """
    SQL subquery returning document IDs within `organization_id` that `user_id` is authorized to read.
    Applied directly inside vector and keyword retrieval queries so unauthorized chunks are never scored.
    """
    if role in {"owner", "admin"}:
        return select(Document.id).where(Document.organization_id == organization_id)

    explicit_grant = exists(
        select(DocumentPermission.id).where(
            DocumentPermission.document_id == Document.id,
            DocumentPermission.user_id == user_id,
        )
    )
    return select(Document.id).where(
        Document.organization_id == organization_id,
        or_(
            Document.access_scope == "organization",
            Document.uploaded_by == user_id,
            explicit_grant,
        ),
    )


def can_access_document(db: Session, document: Document, user_id: UUID, role: str) -> bool:
    if role in {"owner", "admin"}:
        return True
    if document.access_scope == "organization" or document.uploaded_by == user_id:
        return True
    perm = db.execute(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == user_id,
        )
    ).scalar_one_or_none()
    return perm is not None


def can_manage_document(db: Session, document: Document, user_id: UUID, role: str) -> bool:
    if role in {"owner", "admin"} or document.uploaded_by == user_id:
        return True
    perm = db.execute(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == user_id,
            DocumentPermission.permission == "manage",
        )
    ).scalar_one_or_none()
    return perm is not None
