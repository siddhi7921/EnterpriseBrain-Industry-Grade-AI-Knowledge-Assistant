from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Document, DocumentChunk, DocumentPermission, IngestionJob, Membership
from app.schemas.document import DocumentPermissionsUpdateRequest, DocumentResponse, DocumentStatusResponse
from app.services.audit_service import record_audit_event
from app.services.permission_service import (
    accessible_documents_subquery,
    can_access_document,
    can_manage_document,
    get_membership_or_403,
)
from app.services.storage_service import storage_service
from app.workers.ingestion_worker import process_document_task, run_document_ingestion
from packages.rag.ingestion.pipeline import SUPPORTED_MIME_TYPES

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}


def _serialize_document(db: Session, doc: Document) -> DocumentResponse:
    chunk_count = db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == doc.id)
    ).scalar_one()
    return DocumentResponse(
        id=doc.id,
        organization_id=doc.organization_id,
        uploaded_by=doc.uploaded_by,
        filename=doc.filename,
        mime_type=doc.mime_type,
        checksum=doc.checksum,
        status=doc.status,
        access_scope=doc.access_scope,
        version=doc.version,
        chunk_count=int(chunk_count or 0),
        created_at=doc.created_at,
    )


async def upload_document(
    *,
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    file: UploadFile,
    access_scope: str = "organization",
) -> DocumentResponse:
    get_membership_or_403(db, organization_id, user_id)

    if access_scope not in {"organization", "restricted"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="access_scope must be 'organization' or 'restricted'.",
        )

    filename = Path(file.filename or "untitled").name
    ext = Path(filename).suffix.lower()
    mime_type = file.content_type or "application/octet-stream"

    if ext not in ALLOWED_EXTENSIONS and mime_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: PDF, DOCX, TXT, Markdown.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    checksum = hashlib.sha256(content).hexdigest()
    existing = db.execute(
        select(Document).where(
            Document.organization_id == organization_id,
            Document.checksum == checksum,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return _serialize_document(db, existing)

    storage_key = f"orgs/{organization_id}/{checksum}_{filename}"
    storage_service.put_bytes(storage_key, content, content_type=mime_type)

    doc = Document(
        organization_id=organization_id,
        uploaded_by=user_id,
        filename=filename,
        storage_key=storage_key,
        mime_type=mime_type,
        checksum=checksum,
        status="pending",
        access_scope=access_scope,
        version=1,
    )
    db.add(doc)
    db.flush()

    job = IngestionJob(document_id=doc.id, status="queued", attempts=0)
    db.add(job)
    record_audit_event(
        db,
        organization_id=organization_id,
        actor_id=user_id,
        action="document.uploaded",
        resource_id=doc.id,
        metadata={"filename": filename, "access_scope": access_scope},
    )
    db.commit()
    db.refresh(doc)

    if settings.CELERY_TASK_ALWAYS_EAGER:
        run_document_ingestion(db, doc.id)
    else:
        process_document_task.delay(str(doc.id))

    db.refresh(doc)
    return _serialize_document(db, doc)


def list_accessible_documents(db: Session, organization_id: UUID, user_id: UUID) -> list[DocumentResponse]:
    membership = get_membership_or_403(db, organization_id, user_id)
    subq = accessible_documents_subquery(organization_id, user_id, membership.role)
    docs = (
        db.execute(
            select(Document)
            .where(Document.organization_id == organization_id, Document.id.in_(subq))
            .order_by(Document.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [_serialize_document(db, d) for d in docs]


def get_document_detail(db: Session, document_id: UUID, user_id: UUID) -> DocumentResponse:
    doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    membership = get_membership_or_403(db, doc.organization_id, user_id)
    if not can_access_document(db, doc, user_id, membership.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this document.")

    return _serialize_document(db, doc)


def get_document_status(db: Session, document_id: UUID, user_id: UUID) -> DocumentStatusResponse:
    doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    membership = get_membership_or_403(db, doc.organization_id, user_id)
    if not can_access_document(db, doc, user_id, membership.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this document.")

    chunk_count = db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == doc.id)
    ).scalar_one()
    latest_job = db.execute(
        select(IngestionJob)
        .where(IngestionJob.document_id == doc.id)
        .order_by(IngestionJob.created_at.desc())
    ).scalars().first()

    return DocumentStatusResponse(
        document_id=doc.id,
        status=doc.status,
        chunk_count=int(chunk_count or 0),
        latest_job_status=latest_job.status if latest_job else None,
        attempts=latest_job.attempts if latest_job else 0,
        error_message=latest_job.error_message if latest_job else None,
    )


def reindex_document(db: Session, document_id: UUID, user_id: UUID) -> DocumentStatusResponse:
    doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    membership = get_membership_or_403(db, doc.organization_id, user_id)
    if not can_manage_document(db, doc, user_id, membership.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to reindex.")

    doc.version += 1
    doc.status = "pending"
    db.add(IngestionJob(document_id=doc.id, status="queued", attempts=0))
    record_audit_event(
        db,
        organization_id=doc.organization_id,
        actor_id=user_id,
        action="document.reindexed",
        resource_id=doc.id,
        metadata={"version": doc.version},
    )
    db.commit()

    if settings.CELERY_TASK_ALWAYS_EAGER:
        run_document_ingestion(db, doc.id)
    else:
        process_document_task.delay(str(doc.id))

    return get_document_status(db, doc.id, user_id)


def delete_document(db: Session, document_id: UUID, user_id: UUID) -> None:
    doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    membership = get_membership_or_403(db, doc.organization_id, user_id)
    if not can_manage_document(db, doc, user_id, membership.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to delete.")

    storage_key = doc.storage_key
    org_id = doc.organization_id
    doc_uuid = doc.id
    filename = doc.filename

    db.delete(doc)
    record_audit_event(
        db,
        organization_id=org_id,
        actor_id=user_id,
        action="document.deleted",
        resource_id=doc_uuid,
        metadata={"filename": filename},
    )
    db.commit()
    storage_service.delete_object(storage_key)


def update_document_permissions(
    db: Session,
    document_id: UUID,
    user_id: UUID,
    payload: DocumentPermissionsUpdateRequest,
) -> DocumentResponse:
    doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    membership = get_membership_or_403(db, doc.organization_id, user_id)
    if not can_manage_document(db, doc, user_id, membership.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    doc.access_scope = payload.access_scope

    # Replace explicit permission entries for members in the same org
    existing_perms = db.execute(
        select(DocumentPermission).where(DocumentPermission.document_id == doc.id)
    ).scalars().all()
    for ep in existing_perms:
        db.delete(ep)
    db.flush()

    for entry in payload.permissions:
        target_member = db.execute(
            select(Membership).where(
                Membership.organization_id == doc.organization_id,
                Membership.user_id == entry.user_id,
            )
        ).scalar_one_or_none()
        if target_member is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {entry.user_id} is not a member of this organisation.",
            )
        db.add(
            DocumentPermission(
                document_id=doc.id,
                user_id=entry.user_id,
                permission=entry.permission,
            )
        )

    record_audit_event(
        db,
        organization_id=doc.organization_id,
        actor_id=user_id,
        action="document.permissions_updated",
        resource_id=doc.id,
        metadata={
            "access_scope": payload.access_scope,
            "granted_users": [str(p.user_id) for p in payload.permissions],
        },
    )
    db.commit()
    db.refresh(doc)
    return _serialize_document(db, doc)
