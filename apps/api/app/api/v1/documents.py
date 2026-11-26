from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.document import (
    DocumentPermissionsUpdateRequest,
    DocumentResponse,
    DocumentStatusResponse,
)
from app.services.document_service import (
    delete_document,
    get_document_detail,
    get_document_status,
    list_accessible_documents,
    reindex_document,
    update_document_permissions,
    upload_document,
)

router = APIRouter(tags=["Documents"])


@router.post(
    "/organizations/{org_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_org_document(
    org_id: UUID,
    file: UploadFile = File(...),
    access_scope: str = Form("organization"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    return await upload_document(
        db=db,
        organization_id=org_id,
        user_id=current_user.id,
        file=file,
        access_scope=access_scope,
    )


@router.get("/organizations/{org_id}/documents", response_model=list[DocumentResponse])
def list_org_documents(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentResponse]:
    return list_accessible_documents(db, org_id, current_user.id)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    return get_document_detail(db, document_id, current_user.id)


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
def get_doc_status(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentStatusResponse:
    return get_document_status(db, document_id, current_user.id)


@router.post("/documents/{document_id}/reindex", response_model=DocumentStatusResponse)
def reindex_doc(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentStatusResponse:
    return reindex_document(db, document_id, current_user.id)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    delete_document(db, document_id, current_user.id)


@router.patch("/documents/{document_id}/permissions", response_model=DocumentResponse)
def patch_document_permissions(
    document_id: UUID,
    payload: DocumentPermissionsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    return update_document_permissions(db, document_id, current_user.id, payload)
