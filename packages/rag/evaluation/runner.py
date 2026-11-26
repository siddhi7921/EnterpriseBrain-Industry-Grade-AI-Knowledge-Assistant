from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, List
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.orm import Session

from packages.rag.evaluation.dataset import EvalSample
from packages.rag.evaluation.metrics import (
    answer_relevance_score,
    citation_correctness_score,
    faithfulness_score,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from packages.rag.generation.citations import CitationValidator
from packages.rag.generation.prompts import build_rag_prompt
from packages.rag.generation.providers import BaseLLMProvider
from packages.rag.retrieval.pipeline import HybridRetrievalPipeline, RetrievalMode


@dataclass
class ConfigBenchmarkResult:
    mode: str
    recall_at_k: float
    precision_at_k: float
    mrr: float
    ndcg_at_k: float
    faithfulness: float
    answer_relevance: float
    citation_correctness: float
    avg_latency_ms: float
    sample_count: int

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "recall_at_k": self.recall_at_k,
            "precision_at_k": self.precision_at_k,
            "mrr": self.mrr,
            "ndcg_at_k": self.ndcg_at_k,
            "faithfulness": self.faithfulness,
            "answer_relevance": self.answer_relevance,
            "citation_correctness": self.citation_correctness,
            "avg_latency_ms": self.avg_latency_ms,
            "sample_count": self.sample_count,
        }


class EvaluationRunner:
    """Benchmarks vector, keyword, hybrid, and hybrid_rerank retrieval + RAG quality on a fixed dataset."""

    def __init__(
        self,
        retrieval_pipeline: HybridRetrievalPipeline,
        llm_provider: BaseLLMProvider,
        top_k: int = 5,
    ) -> None:
        self.retrieval_pipeline = retrieval_pipeline
        self.llm_provider = llm_provider
        self.validator = CitationValidator()
        self.top_k = top_k

    @staticmethod
    def _is_chunk_relevant(chunk_content: str, chunk_filename: str, sample: EvalSample) -> bool:
        lower_c = chunk_content.lower()
        kw_match = any(kw.lower() in lower_c for kw in sample.relevant_keywords)
        fn_match = (
            not sample.relevant_filenames
            or any(fn.lower() in chunk_filename.lower() for fn in sample.relevant_filenames)
        )
        return kw_match and fn_match

    async def evaluate_mode(
        self,
        *,
        db: Session,
        chunk_model,
        document_model,
        allowed_doc_ids_subquery: Select,
        organization_id: UUID,
        samples: List[EvalSample],
        mode: RetrievalMode,
    ) -> ConfigBenchmarkResult:
        recalls, precisions, mrrs, ndcgs = [], [], [], []
        faiths, relevances, cit_scores, latencies = [], [], [], []

        for sample in samples:
            t0 = time.perf_counter()
            outcome = self.retrieval_pipeline.retrieve(
                db=db,
                chunk_model=chunk_model,
                document_model=document_model,
                allowed_doc_ids_subquery=allowed_doc_ids_subquery,
                organization_id=organization_id,
                query=sample.question,
                candidate_limit=20,
                top_k=self.top_k,
                mode=mode,
            )
            rel_flags = [
                self._is_chunk_relevant(ch.content, ch.filename, sample)
                for ch in outcome.chunks
            ]
            recalls.append(recall_at_k(rel_flags, total_relevant=1, k=self.top_k))
            precisions.append(precision_at_k(rel_flags, k=self.top_k))
            mrrs.append(mean_reciprocal_rank(rel_flags))
            ndcgs.append(ndcg_at_k(rel_flags, k=self.top_k))

            sys_p, usr_p = build_rag_prompt(sample.question, outcome.chunks)
            llm_resp = await self.llm_provider.generate(sys_p, usr_p)
            answer, citations = self.validator.validate(llm_resp.content, outcome.chunks)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            faiths.append(faithfulness_score(answer, [c.content for c in outcome.chunks]))
            relevances.append(answer_relevance_score(sample.question, answer, sample.expected_answer))
            cit_scores.append(
                citation_correctness_score(
                    [c.chunk_id for c in citations],
                    [c.chunk_id for c in outcome.chunks],
                )
            )
            latencies.append(elapsed_ms)

        n = max(1, len(samples))
        return ConfigBenchmarkResult(
            mode=mode,
            recall_at_k=round(sum(recalls) / n, 4),
            precision_at_k=round(sum(precisions) / n, 4),
            mrr=round(sum(mrrs) / n, 4),
            ndcg_at_k=round(sum(ndcgs) / n, 4),
            faithfulness=round(sum(faiths) / n, 4),
            answer_relevance=round(sum(relevances) / n, 4),
            citation_correctness=round(sum(cit_scores) / n, 4),
            avg_latency_ms=round(sum(latencies) / n, 2),
            sample_count=len(samples),
        )

    async def run_matrix(
        self,
        *,
        db: Session,
        chunk_model,
        document_model,
        allowed_doc_ids_subquery: Select,
        organization_id: UUID,
        samples: List[EvalSample],
    ) -> Dict[str, dict]:
        modes: List[RetrievalMode] = ["vector", "keyword", "hybrid", "hybrid_rerank"]
        results: Dict[str, dict] = {}
        for mode in modes:
            res = await self.evaluate_mode(
                db=db,
                chunk_model=chunk_model,
                document_model=document_model,
                allowed_doc_ids_subquery=allowed_doc_ids_subquery,
                organization_id=organization_id,
                samples=samples,
                mode=mode,
            )
            results[mode] = res.to_dict()
        return results
