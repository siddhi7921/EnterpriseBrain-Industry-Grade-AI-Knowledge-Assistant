from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from sqlalchemy import select

from app.core.config import settings
from app.db.models import Document, DocumentChunk, Organization
from app.db.session import SessionLocal
from packages.rag.embeddings.bge import get_embedder
from packages.rag.evaluation.dataset import load_eval_dataset
from packages.rag.evaluation.runner import EvaluationRunner
from packages.rag.generation.providers import get_llm_provider
from packages.rag.retrieval.pipeline import HybridRetrievalPipeline
from packages.rag.retrieval.reranker import get_reranker
from scripts.seed_demo_data import seed


async def main() -> None:
    seed()
    db = SessionLocal()
    try:
        acme = db.execute(select(Organization).where(Organization.slug == "acme-tech")).scalar_one()
        samples = load_eval_dataset(ROOT_DIR / "datasets" / "enterprise_qa_benchmark.json")

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
        runner = EvaluationRunner(retrieval_pipeline=pipeline, llm_provider=llm, top_k=5)

        all_org_docs = select(Document.id).where(Document.organization_id == acme.id)
        matrix = await runner.run_matrix(
            db=db,
            chunk_model=DocumentChunk,
            document_model=Document,
            allowed_doc_ids_subquery=all_org_docs,
            organization_id=acme.id,
            samples=samples,
        )

        print("\n=== EnterpriseBrain Retrieval & RAG Evaluation Matrix ===")
        header = f"{'Mode':<16} | {'Recall@5':<8} | {'Prec@5':<8} | {'MRR':<8} | {'nDCG@5':<8} | {'Faithful':<8} | {'CitCorr':<8} | {'Latency(ms)':<11}"
        print(header)
        print("-" * len(header))
        for mode, m in matrix.items():
            print(
                f"{mode:<16} | {m['recall_at_k']:<8.4f} | {m['precision_at_k']:<8.4f} | "
                f"{m['mrr']:<8.4f} | {m['ndcg_at_k']:<8.4f} | {m['faithfulness']:<8.4f} | "
                f"{m['citation_correctness']:<8.4f} | {m['avg_latency_ms']:<11.2f}"
            )

        out_path = ROOT_DIR / "datasets" / "latest_eval_results.json"
        out_path.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
        print(f"\nSaved full benchmark results to {out_path}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
