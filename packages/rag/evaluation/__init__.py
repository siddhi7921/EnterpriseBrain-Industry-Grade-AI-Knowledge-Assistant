from __future__ import annotations

from packages.rag.evaluation.dataset import EvalSample, load_eval_dataset
from packages.rag.evaluation.metrics import (
    answer_relevance_score,
    citation_correctness_score,
    faithfulness_score,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)

__all__ = [
    "EvalSample",
    "load_eval_dataset",
    "recall_at_k",
    "precision_at_k",
    "mean_reciprocal_rank",
    "ndcg_at_k",
    "faithfulness_score",
    "citation_correctness_score",
    "answer_relevance_score",
    "EvaluationRunner",
]

def __getattr__(name: str):
    if name == "EvaluationRunner":
        from packages.rag.evaluation.runner import EvaluationRunner
        return EvaluationRunner
    raise AttributeError(name)
