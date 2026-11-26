# System Architecture

## Overview
EnterpriseBrain separates core ML/RAG logic (`packages/rag`) from API transport and persistence (`apps/api`) and the React frontend (`apps/web`).

### 1. Asynchronous Ingestion Pipeline
1. Client uploads PDF, DOCX, TXT, or Markdown to `POST /api/v1/organizations/{org_id}/documents`.
2. File extension, MIME type, and size are validated; SHA-256 checksum prevents duplicate storage within a workspace.
3. Original bytes are stored in S3/MinIO (with local fallback) and a Celery job is enqueued via Redis.
4. Worker extracts text + page/section metadata, neutralizes prompt-injection patterns, runs structure-aware token chunking (500 tokens, 75-token overlap), generates 1024-d embeddings, and atomically writes `document_chunks` to PostgreSQL + `pgvector`.

### 2. Permission-Aware Hybrid Retrieval + Reranking
1. User submits a question to `POST /api/v1/organizations/{org_id}/chat`.
2. `accessible_documents_subquery` resolves authorized document IDs for the caller's `organization_id`, role (`owner`/`admin`/`member`), and `document_permissions` rows.
3. Vector search (`pgvector` cosine distance) and Keyword search (`PostgreSQL GIN tsvector`) both filter against `organization_id` and `allowed_doc_ids_subquery` **inside SQL**.
4. Reciprocal Rank Fusion (`k=60`) merges candidate rankings, followed by cross-encoder reranking (`BAAI/bge-reranker-v2-m3`).
5. `CitationValidator` verifies every `[CHUNK:<uuid>]` reference against the retrieved set and strips any unverified references.
