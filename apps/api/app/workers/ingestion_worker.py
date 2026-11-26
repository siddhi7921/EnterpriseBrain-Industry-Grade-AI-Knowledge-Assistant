from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Document, DocumentChunk, IngestionJob
from app.db.session import SessionLocal
from app.services.audit_service import record_audit_event
from app.services.storage_service import storage_service
from app.workers.celery_app import celery_app
from packages.rag.chunking.strategies import StructureAwareChunker
from packages.rag.embeddings.bge import get_embedder
from packages.rag.ingestion.pipeline import extract_document

logger = logging.getLogger(__name__)


def run_document_ingestion(db: Session, document_id: UUID) -> None:
    """Idempotent document extraction, chunking, embedding generation, and pgvector persistence."""
    doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if doc is None:
        logger.warning("Document %s not found during ingestion.", document_id)
        return

    job = db.execute(
        select(IngestionJob)
        .where(IngestionJob.document_id == doc.id)
        .order_by(IngestionJob.created_at.desc())
    ).scalars().first()

    if job is None:
        job = IngestionJob(document_id=doc.id, status="processing", attempts=1)
        db.add(job)
    else:
        job.status = "processing"
        job.attempts += 1
        job.error_message = None

    doc.status = "processing"
    db.commit()

    try:
        raw_bytes = storage_service.get_bytes(doc.storage_key)
        extraction = extract_document(
            document_id=str(doc.id),
            filename=doc.filename,
            mime_type=doc.mime_type,
            file_bytes=raw_bytes,
        )

        chunker = StructureAwareChunker(chunk_size_tokens=500, overlap_tokens=75)
        chunks = chunker.chunk_document(extraction)
        if not chunks:
            raise ValueError("Document produced zero chunks after parsing.")

        embedder = get_embedder(
            provider=settings.EMBEDDING_PROVIDER,
            model_name=settings.EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIMENSION,
        )
        vectors = embedder.embed_documents([ch.content for ch in chunks])

        # Replace existing chunks idempotently
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        db.flush()

        for ch, vec in zip(chunks, vectors):
            db.add(
                DocumentChunk(
                    organization_id=doc.organization_id,
                    document_id=doc.id,
                    chunk_index=ch.chunk_index,
                    content=ch.content,
                    token_count=ch.token_count,
                    embedding=vec,
                    metadata_json=ch.metadata.to_dict(),
                )
            )

        doc.status = "indexed"
        job.status = "completed"
        job.error_message = None
        record_audit_event(
            db,
            organization_id=doc.organization_id,
            actor_id=doc.uploaded_by,
            action="document.indexed",
            resource_id=doc.id,
            metadata={"filename": doc.filename, "chunk_count": len(chunks)},
        )
        db.commit()
        logger.info("Successfully indexed document %s (%d chunks).", doc.id, len(chunks))
    except Exception as exc:
        db.rollback()
        logger.exception("Ingestion failed for document %s: %s", document_id, exc)
        doc_fail = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
        if doc_fail is not None:
            doc_fail.status = "failed"
        job_fail = db.execute(
            select(IngestionJob)
            .where(IngestionJob.document_id == document_id)
            .order_by(IngestionJob.created_at.desc())
        ).scalars().first()
        if job_fail is not None:
            job_fail.status = "failed"
            job_fail.error_message = str(exc)[:1000]
        db.commit()


@celery_app.task(name="enterprisebrain.process_document", bind=True, max_retries=3)
def process_document_task(self, document_id_str: str) -> str:
    db = SessionLocal()
    try:
        run_document_ingestion(db, UUID(document_id_str))
        return f"processed:{document_id_str}"
    finally:
        db.close()


process_document_ingestion = process_document_task
