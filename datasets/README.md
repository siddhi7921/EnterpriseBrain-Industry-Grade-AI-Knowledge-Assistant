# Evaluation Datasets

## `enterprise_qa_benchmark.json`
Contains curated question-answer pairs with ground-truth relevant keywords and expected source document filenames used to benchmark:
1. `vector` (dense embedding retrieval only)
2. `keyword` (full-text lexical retrieval only)
3. `hybrid` (Reciprocal Rank Fusion combining vector + keyword)
4. `hybrid_rerank` (Hybrid RRF + cross-encoder reranking)

To expand this benchmark to 100+ domain-specific Q&A pairs, append entries matching the schema:
```json
{
  "id": "qa-09",
  "question": "...",
  "expected_answer": "...",
  "relevant_keywords": ["keyword1", "keyword2"],
  "relevant_filenames": ["policy.pdf"]
}
```
