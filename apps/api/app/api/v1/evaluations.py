from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import EvaluationRun, User
from app.db.session import get_db
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse
from app.services.evaluation_service import get_evaluation_run, run_evaluation_benchmark
from app.services.permission_service import get_membership_or_403

router = APIRouter(prefix="/admin/evaluations", tags=["Evaluation"])


@router.post("/run", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
async def trigger_evaluation(
    payload: EvaluationRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvaluationRunResponse:
    return await run_evaluation_benchmark(db, current_user.id, payload)


@router.get("", response_model=list[EvaluationRunResponse])
def list_evaluation_runs(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EvaluationRunResponse]:
    get_membership_or_403(db, organization_id, current_user.id)
    runs = (
        db.execute(
            select(EvaluationRun)
            .where(EvaluationRun.organization_id == organization_id)
            .order_by(EvaluationRun.created_at.desc())
            .limit(20)
        )
        .scalars()
        .all()
    )
    return [
        EvaluationRunResponse(
            id=r.id,
            organization_id=r.organization_id,
            dataset_name=r.dataset_name,
            model_name=r.model_name,
            metrics=r.metrics,
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get("/{run_id}", response_model=EvaluationRunResponse)
def retrieve_evaluation(
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvaluationRunResponse:
    return get_evaluation_run(db, run_id, current_user.id)
