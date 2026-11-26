# EnterpriseBrain 🧠

**Your Organisation's Knowledge, Intelligently Connected.**

EnterpriseBrain is a secure, multi-tenant enterprise AI knowledge assistant that enables employees to ask natural-language questions across internal company documents and receive evidence-backed answers with validated citations.

Built with **Retrieval-Augmented Generation (RAG)**, **hybrid vector + keyword search**, **Reciprocal Rank Fusion (RRF)**, **cross-encoder reranking**, **SQL-enforced document-level access control**, and a **reproducible ML evaluation harness**.

`Applied AI Engineering` · `Machine Learning` · `NLP` · `RAG` · `Information Retrieval` · `FastAPI` · `React + TypeScript`

---

## 🚀 Key Capabilities

- **Multi-Format Document Ingestion**: Asynchronous Celery + Redis pipeline supporting **PDF** (PyMuPDF + OCR fallback), **DOCX**, **TXT**, and **Markdown** with SHA-256 deduplication and status tracking.
- **Structure-Aware Chunking**: Preserves section headings, page numbers, and tables with configurable token budgets (`500` tokens, `75`-token overlap).
- **Hybrid Retrieval + Neural Reranking**: Combines `pgvector` dense semantic search (`BAAI/bge-m3`) and PostgreSQL full-text keyword search via **Reciprocal Rank Fusion**, followed by cross-encoder reranking (`BAAI/bge-reranker-v2-m3`).
- **Validated Source Citations**: Every answer links to exact document filenames, page numbers, relevance scores, and supporting quotes—hallucinated or unauthorized citation IDs are automatically stripped.
- **Enterprise Multi-Tenancy & RBAC**: Workspace isolation (`owner`, `admin`, `member`), document-level ACLs (`organization` vs `restricted`), SQL-level retrieval filtering, prompt-injection neutralization, and audit logs.
- **Reproducible Evaluation Lab**: Built-in benchmarking matrix comparing **Vector-only**, **Keyword-only**, **Hybrid (RRF)**, and **Hybrid + Reranking** across `Recall@K`, `Precision@K`, `MRR`, `nDCG@K`, `Faithfulness`, `Citation Correctness`, and latency.

---

## 🏗️ System Architecture

```text
React + TypeScript Frontend (Vite + Tailwind CSS)
                      │
                   FastAPI
                      │
      JWT Auth + RBAC + Rate Limiting
                      │
        +-------------+-------------+
        │             │             │
 Document Service  Chat Service  Analytics & Eval
        │             │
   Redis + Celery     ├── Query Embedding (BGE-M3)
        │             ├── SQL Permission Subquery
   Extraction         ├── Vector Search + Keyword Search
   Cleaning           ├── Reciprocal Rank Fusion (RRF)
   Chunking           ├── Cross-Encoder Reranking
   Embeddings         ├── Grounded LLM Provider
        │             └── Citation Validator
        ▼
PostgreSQL + pgvector  &  S3 / MinIO Object Storage
```

---

## 📂 Repository Structure

```text
enterprisebrain/
├── apps/
│   ├── api/                 # FastAPI backend, SQLAlchemy models, Alembic migrations, Celery workers, Pytest suite
│   └── web/                 # React 18 + TypeScript + Vite + Tailwind CSS workspace UI
├── packages/
│   └── rag/                 # Decoupled ML/RAG core (ingestion, chunking, embeddings, retrieval, generation, evaluation)
├── scripts/                 # Demo data seeder & reproducible evaluation CLI runner
├── datasets/                # Evaluation benchmark dataset & JSON reports
├── docs/                    # Architecture, API, Security Threat Model, and Evaluation guides
├── .github/workflows/       # GitHub Actions CI pipeline
└── docker-compose.yml       # Full-stack PostgreSQL+pgvector, Redis, MinIO, API, Worker, and Web stack
```

---

## ⚙️ Quick Start

### Option A: Full Stack with Docker Compose (Recommended)
```bash
git clone https://github.com/siddhi7921/enterprisebrain.git
cd enterprisebrain
cp .env.example .env
docker compose up -d --build
```
- **Frontend UI**: `http://localhost:5173`
- **FastAPI Swagger Docs**: `http://localhost:8000/docs`
- **MinIO Console**: `http://localhost:9001`

Seed demo workspaces, documents, and users:
```bash
docker compose exec api python scripts/seed_demo_data.py
```

### Option B: Local Development (Windows PowerShell / Linux / macOS)
1. **Start Backend API** (runs out-of-the-box with zero external API keys using local SQLite + deterministic fallback providers, or connect PostgreSQL + OpenAI/Ollama in `.env`):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r apps/api/requirements.txt
   copy .env.example .env
   $env:PYTHONPATH=".;apps/api"
   python scripts/seed_demo_data.py
   uvicorn app.main:app --reload --port 8000 --app-dir apps/api
   ```
2. **Start Frontend UI**:
   ```powershell
   cd apps/web
   npm install
   npm run dev
   ```

### Demo Credentials (after running `seed_demo_data.py`)
| Workspace | Email | Password | Role | Access |
| :--- | :--- | :--- | :--- | :--- |
| **Acme Technologies** | `alice@acme.com` | `DemoPass123!` | `owner` | Full access including restricted M&A docs |
| **Acme Technologies** | `bob@acme.com` | `DemoPass123!` | `member` | Standard org docs only (restricted docs blocked in SQL) |
| **Globex Inc** | `mallory@globex.com` | `DemoPass123!` | `owner` | Isolated tenant workspace |

---

## 🧪 Testing & ML Benchmarking

Run the automated backend & security test suite:
```bash
PYTHONPATH=.:apps/api pytest apps/api/tests -v
```

Run the 4-configuration retrieval & RAG evaluation benchmark:
```bash
PYTHONPATH=.:apps/api python scripts/run_evaluation.py
```

---

## 📄 License

Released under the [MIT License](LICENSE).
