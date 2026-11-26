from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Document, DocumentChunk, EvaluationRun
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse
from app.services.permission_service import accessible_documents_subquery, require_admin_or_403
from packages.rag.embeddings.bge import get_embedder
from packages.rag.evaluation.dataset import EvalSample, load_eval_dataset
from packages.rag.evaluation.runner import EvaluationRunner
from packages.rag.generation.providers import get_llm_provider
from packages.rag.retrieval.pipeline import HybridRetrievalPipeline
from packages.rag.retrieval.reranker import get_reranker


def _resolve_dataset(dataset_name: str) -> list[EvalSample]:
    candidates = [
        Path("datasets") / f"{dataset_name}.json",
        Path(__file__).resolve().parents[4] / "datasets" / f"{dataset_name}.json",
    ]
    for path in candidates:
        if path.exists():
            return load_eval_dataset(path)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Evaluation dataset '{dataset_name}' not found.",
    )


async def run_evaluation_benchmark(
    db: Session,
    user_id: UUID,
    payload: EvaluationRunRequest,
) -> EvaluationRunResponse:
    membership = require_admin_or_403(db, payload.organization_id, user_id)
    samples = _resolve_dataset(payload.dataset_name)

    embedder = get_embedder(
        provider=settings.EMBEDDING_PROVIDER,
        model_name=settings.EMBEDDING_MODEL,
        dimension=settings.EMBEDDING_DIMENSION,
    )
    reranker = get_reranker(
        provider=settings.RERANKER_PROVIDER,
        model_name=settings.RERANKER_MODEL,
    )
    llm = get_llm_provider(
        provider=settings.LLM_PROVIDER,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
    )

    pipeline = HybridRetrievalPipeline(embedder=embedder, reranker=reranker)
    runner = EvaluationRunner(retrieval_pipeline=pipeline, llm_provider=llm, top_k=payload.top_k)

    allowed_subq = accessible_documents_subquery(payload.organization_id, user_id, membership.role)
    matrix = await runner.run_matrix(
        db=db,
        chunk_model=DocumentChunk,
        document_model=Document,
        allowed_doc_ids_subquery=allowed_subq,
        organization_id=payload.organization_id,
        samples=samples,
    )

    run = EvaluationRun(
        organization_id=payload.organization_id,
        dataset_name=payload.dataset_name,
        model_name=f"{settings.EMBEDDING_MODEL} + {settings.RERANKER_MODEL}",
        metrics=matrix,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return EvaluationRunResponse(
        id=run.id,
        organization_id=run.organization_id,
        dataset_name=run.dataset_name,
        model_name=run.model_name,
        metrics=run.metrics,
        created_at=run.created_at,
    )


def get_evaluation_run(db: Session, run_id: UUID, user_id: UUID) -> EvaluationRunResponse:
    run = db.execute(select(EvaluationRun).where(EvaluationRun.id == run_id)).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found.")
    if run.organization_id is not None:
        require_admin_or_403(db, run.organization_id, user_id)

    return EvaluationRunResponse(
        id=run.id,
        organization_id=run.organization_id,
        dataset_name=run.dataset_name,
        model_name=run.model_name,
        metrics=run.metrics,
        created_at=run.created_at,
    )
