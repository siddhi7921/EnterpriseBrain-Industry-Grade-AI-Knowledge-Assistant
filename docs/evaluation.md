# Retrieval & RAG Evaluation Methodology

Run the reproducible benchmark suite:
```bash
python scripts/run_evaluation.py
```

The runner evaluates four retrieval configurations on the exact same dataset:
1. **Vector-only**: Dense cosine similarity search.
2. **Keyword-only**: PostgreSQL full-text `ts_rank_cd` search.
3. **Hybrid (RRF)**: Reciprocal Rank Fusion (`k=60`) combining vector and keyword ranks.
4. **Hybrid + Reranking**: RRF candidates reordered by cross-encoder relevance scoring.

Metrics computed per run: `Recall@K`, `Precision@K`, `MRR`, `nDCG@K`, `Faithfulness`, `Answer Relevance`, `Citation Correctness`, and `Avg Latency (ms)`.
