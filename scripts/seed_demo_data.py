from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.models import Document, IngestionJob, Membership, Organization, User
from app.db.session import SessionLocal, engine
from app.services.storage_service import storage_service
from app.workers.ingestion_worker import run_document_ingestion


DEMO_DOCS = [
    (
        "employee-handbook.md",
        "organization",
        """# Acme Technologies — Employee Handbook (2026)

## Annual & Sick Leave Policy
Full-time employees receive 24 days of paid annual leave per calendar year, accrued monthly at 2 days per month.
In addition, employees receive 12 days of paid sick leave and 10 public holidays. Unused annual leave up to 10 days may be carried over into Q1 of the following year.

## Hybrid & Remote Work Policy
Employees may work remotely up to 3 days per week, with Tuesday and Thursday designated as core in-office collaboration days.
Remote and hybrid employees are eligible for a one-time $750 home office equipment stipend upon completing onboarding.

## Learning & Conference Budget
Every engineer receives an annual $1,500 professional development budget for technical conferences, books, and cloud certifications.
""",
    ),
    (
        "security-architecture.md",
        "organization",
        """# Information Security & Access Control Policy

## Production Infrastructure Access
All production database access requires hardware FIDO2/WebAuthn MFA and short-lived SSH certificates via the bastion host.
Direct public internet ingress to PostgreSQL or Redis instances is strictly prohibited.

## Incident Response & Escalation SLAs
Severity-1 security incidents must be reported to the Security Operations Center immediately and escalated to the CISO within 1 hour.
Post-incident root cause analyses must be published within 48 hours of resolution.

## API Rate Limiting & Tenant Isolation
Unauthenticated login and token endpoints are rate-limited to 30 requests per minute per client IP address.
All retrieval queries enforce organization_id and document_permissions filtering directly in SQL.
""",
    ),
    (
        "engineering-runbook.md",
        "organization",
        """# AI Platform Engineering Runbook

## Service Level Objectives (SLOs)
The production p95 latency SLA for hybrid retrieval plus reranking is under 1,800 milliseconds.
Document ingestion workers retry transient object-storage or embedding errors up to 3 times with exponential backoff.

## Cloud Spend Governance
Monthly cloud spend increases exceeding $2,500 require written approval from the VP of Engineering and FinOps review.
""",
    ),
    (
        "executive-board-strategy.md",
        "restricted",
        """# CONFIDENTIAL — Board Strategy & M&A Pipeline (Restricted)

## Project Orion Acquisition
Acme Technologies is evaluating a strategic acquisition of VectorPulse AI for $32 million in Q4 2026.
Access to this document is restricted exclusively to workspace owners and explicitly authorized executives.
""",
    ),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Create Acme Technologies (Org A)
        acme = db.execute(select(Organization).where(Organization.slug == "acme-tech")).scalar_one_or_none()
        if acme is None:
            acme = Organization(name="Acme Technologies", slug="acme-tech")
            db.add(acme)
            db.flush()

        alice = db.execute(select(User).where(User.email == "alice@acme.com")).scalar_one_or_none()
        if alice is None:
            alice = User(email="alice@acme.com", password_hash=hash_password("DemoPass123!"))
            db.add(alice)
            db.flush()
            db.add(Membership(organization_id=acme.id, user_id=alice.id, role="owner"))

        bob = db.execute(select(User).where(User.email == "bob@acme.com")).scalar_one_or_none()
        if bob is None:
            bob = User(email="bob@acme.com", password_hash=hash_password("DemoPass123!"))
            db.add(bob)
            db.flush()
            db.add(Membership(organization_id=acme.id, user_id=bob.id, role="member"))

        # 2. Create Globex Inc (Org B) for multi-tenant isolation demo
        globex = db.execute(select(Organization).where(Organization.slug == "globex-inc")).scalar_one_or_none()
        if globex is None:
            globex = Organization(name="Globex Inc", slug="globex-inc")
            db.add(globex)
            db.flush()

        mallory = db.execute(select(User).where(User.email == "mallory@globex.com")).scalar_one_or_none()
        if mallory is None:
            mallory = User(email="mallory@globex.com", password_hash=hash_password("DemoPass123!"))
            db.add(mallory)
            db.flush()
            db.add(Membership(organization_id=globex.id, user_id=mallory.id, role="owner"))

        db.commit()

        # 3. Seed & index demo documents in Acme Technologies
        import hashlib

        for filename, scope, text_body in DEMO_DOCS:
            raw = text_body.encode("utf-8")
            checksum = hashlib.sha256(raw).hexdigest()
            existing = db.execute(
                select(Document).where(Document.organization_id == acme.id, Document.checksum == checksum)
            ).scalar_one_or_none()
            if existing is not None:
                continue

            storage_key = f"orgs/{acme.id}/{checksum}_{filename}"
            storage_service.put_bytes(storage_key, raw, content_type="text/markdown")
            doc = Document(
                organization_id=acme.id,
                uploaded_by=alice.id,
                filename=filename,
                storage_key=storage_key,
                mime_type="text/markdown",
                checksum=checksum,
                status="pending",
                access_scope=scope,
            )
            db.add(doc)
            db.flush()
            db.add(IngestionJob(document_id=doc.id, status="queued", attempts=0))
            db.commit()
            run_document_ingestion(db, doc.id)

        print("Demo data seeded successfully!")
        print("  Org 1 (Acme Technologies):")
        print("    Owner : alice@acme.com / DemoPass123!")
        print("    Member: bob@acme.com   / DemoPass123!")
        print("  Org 2 (Globex Inc):")
        print("    Owner : mallory@globex.com / DemoPass123!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
