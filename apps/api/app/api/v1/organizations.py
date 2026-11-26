from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Membership, Organization, User
from app.db.session import get_db
from app.schemas.organization import (
    MemberInviteRequest,
    MemberResponse,
    MemberRoleUpdateRequest,
    OrganizationCreate,
    OrganizationResponse,
)
from app.services.audit_service import record_audit_event
from app.services.permission_service import get_membership_or_403, require_admin_or_403

router = APIRouter(prefix="/organizations", tags=["Organisations"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workspace"


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationResponse:
    base_slug = _slugify(payload.slug or payload.name)
    slug = base_slug
    counter = 1
    while db.execute(select(Organization).where(Organization.slug == slug)).scalar_one_or_none() is not None:
        counter += 1
        slug = f"{base_slug}-{counter}"

    org = Organization(name=payload.name.strip(), slug=slug)
    db.add(org)
    db.flush()

    db.add(Membership(organization_id=org.id, user_id=current_user.id, role="owner"))
    record_audit_event(
        db,
        organization_id=org.id,
        actor_id=current_user.id,
        action="organization.created",
        resource_id=org.id,
        metadata={"name": org.name, "slug": org.slug},
    )
    db.commit()
    db.refresh(org)
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        role="owner",
        created_at=org.created_at,
    )


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrganizationResponse]:
    rows = db.execute(
        select(Organization, Membership.role)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == current_user.id)
        .order_by(Organization.created_at.asc())
    ).all()
    return [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            role=role,
            created_at=org.created_at,
        )
        for org, role in rows
    ]


@router.get("/{org_id}/members", response_model=list[MemberResponse])
def list_members(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MemberResponse]:
    get_membership_or_403(db, org_id, current_user.id)
    rows = db.execute(
        select(User.id, User.email, Membership.role)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.organization_id == org_id)
    ).all()
    return [MemberResponse(user_id=uid, email=email, role=role) for uid, email, role in rows]


@router.post("/{org_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    org_id: UUID,
    payload: MemberInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberResponse:
    require_admin_or_403(db, org_id, current_user.id)
    target_user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered user found with that email address.",
        )

    existing = db.execute(
        select(Membership).where(
            Membership.organization_id == org_id,
            Membership.user_id == target_user.id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a workspace member.")

    db.add(Membership(organization_id=org_id, user_id=target_user.id, role=payload.role))
    record_audit_event(
        db,
        organization_id=org_id,
        actor_id=current_user.id,
        action="member.added",
        resource_id=target_user.id,
        metadata={"email": target_user.email, "role": payload.role},
    )
    db.commit()
    return MemberResponse(user_id=target_user.id, email=target_user.email, role=payload.role)


@router.patch("/{org_id}/members/{user_id}", response_model=MemberResponse)
def update_member_role(
    org_id: UUID,
    user_id: UUID,
    payload: MemberRoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberResponse:
    require_admin_or_403(db, org_id, current_user.id)
    membership = db.execute(
        select(Membership).where(
            Membership.organization_id == org_id,
            Membership.user_id == user_id,
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in organisation.")

    target_user = db.execute(select(User).where(User.id == user_id)).scalar_one()
    membership.role = payload.role
    record_audit_event(
        db,
        organization_id=org_id,
        actor_id=current_user.id,
        action="member.role_updated",
        resource_id=user_id,
        metadata={"role": payload.role},
    )
    db.commit()
    return MemberResponse(user_id=target_user.id, email=target_user.email, role=membership.role)
