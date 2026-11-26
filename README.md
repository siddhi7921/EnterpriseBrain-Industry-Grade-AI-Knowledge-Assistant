# EnterpriseBrain 🧠

### Your Organisation's Knowledge, Intelligently Connected.

EnterpriseBrain is an AI-powered enterprise knowledge assistant that enables teams to search, understand, and interact with organisational documents through secure, evidence-backed conversations.

Built with Retrieval-Augmented Generation (RAG), hybrid search, vector embeddings, cross-encoder reranking, and permission-aware retrieval, EnterpriseBrain transforms scattered documents into an accessible organisational knowledge system.

> **Project focus:** Applied AI Engineering · Machine Learning · NLP · RAG · Information Retrieval · Backend Engineering

---

## 🚀 Key Features

- **Intelligent Document Ingestion:** Upload and process PDF, DOCX, TXT, and Markdown documents.
- **Semantic Search:** Retrieve relevant passages using dense vector embeddings.
- **Hybrid Retrieval:** Combine semantic and keyword search using Reciprocal Rank Fusion.
- **Neural Reranking:** Improve search relevance using a cross-encoder reranker.
- **Grounded AI Answers:** Generate answers based on retrieved document evidence.
- **Source Citations:** Display document names, page references, and supporting excerpts.
- **Multi-Tenant Workspaces:** Separate organisations and their knowledge bases.
- **Role-Based Access Control:** Control access through organisation roles and document permissions.
- **Conversation History:** Store and revisit previous conversations.
- **AI Evaluation:** Benchmark retrieval quality, answer faithfulness, and citation correctness.
- **Observability:** Track errors, latency, token usage, and ingestion status.

## 🏗️ Architecture

```text
React + TypeScript Frontend
          |
       FastAPI
          |
 Authentication + RBAC
          |
   EnterpriseBrain Services
          |
  +-------+---------+
  |       |         |
Documents Chat   Analytics
  |       |
  |       v
  |   RAG Pipeline
  |       |
  |   Query Embedding
  |       |
  |   Hybrid Retrieval
  |       |
  |   RRF + Reranking
  |       |
  |   Context Builder
  |       |
  |   LLM Generation
  |       |
  |   Validated Citations
  |
Redis + Celery Workers
  |
Extraction -> Chunking -> Embeddings
  |
PostgreSQL + pgvector
  |
S3-Compatible Object Storage
```

## 🧰 Technology Stack

| Category | Technologies |
|---|---|
| Language | Python, TypeScript |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Frontend | React, Vite, Tailwind CSS |
| Database | PostgreSQL, pgvector |
| Background Jobs | Celery, Redis |
| Embeddings | BAAI BGE-M3 |
| Reranking | BGE Reranker v2 M3 |
| LLM | Configurable provider interface |
| Document Processing | PyMuPDF, python-docx |
| Evaluation | RAGAS, custom retrieval metrics |
| Testing | Pytest, Vitest, Playwright |
| Deployment | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## 📂 Project Structure

```text
enterprisebrain/
├── apps/
│   ├── api/
│   └── web/
├── packages/
│   └── rag/
│       ├── ingestion/
│       ├── chunking/
│       ├── embeddings/
│       ├── retrieval/
│       ├── generation/
│       └── evaluation/
├── migrations/
├── scripts/
├── datasets/
├── docs/
├── tests/
├── .github/
├── docker-compose.yml
├── .env.example
├── README.md
└── LICENSE
```

## ⚙️ Getting Started

### Prerequisites

- Python 3.12+
- Node.js LTS
- Docker and Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/enterprisebrain.git
cd enterprisebrain
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Update the database, storage, Redis, embedding, and LLM configuration.

### 3. Start infrastructure

```bash
docker compose up -d db redis minio
```

### 4. Install backend dependencies

```bash
cd apps/api
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
pip install -r requirements.txt
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

API documentation:

```text
http://localhost:8000/docs
```

### 7. Start the background worker

From the backend directory:

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

### 8. Start the frontend

```bash
cd ../../apps/web
npm install
npm run dev
```

Open the local frontend URL printed by Vite.

> The commands above describe the intended development workflow. Update them if your final dependency files, Compose configuration, or service entry points differ.

## 🧠 How RAG Works

1. A user uploads a document.
2. The ingestion worker extracts and cleans its content.
3. The document is divided into context-aware chunks.
4. An embedding model converts chunks into vectors.
5. Vectors and searchable text are stored in PostgreSQL.
6. The user submits a question.
7. EnterpriseBrain performs vector and keyword retrieval.
8. Reciprocal Rank Fusion combines the candidate results.
9. A cross-encoder reranks the retrieved passages.
10. The LLM generates an answer using the selected evidence.
11. Citation validation checks the returned source references.

## 📊 Evaluation

EnterpriseBrain is designed to evaluate both retrieval and generation quality.

| Metric | Purpose |
|---|---|
| Recall@K | Relevant evidence retrieval |
| Precision@K | Retrieval precision |
| MRR | First relevant result ranking |
| nDCG@K | Overall ranking quality |
| Faithfulness | Evidence-grounded generation |
| Answer Relevance | Relevance to the user's question |
| Citation Correctness | Source attribution quality |
| Latency | System response time |

Benchmark vector-only, keyword-only, hybrid, and hybrid-plus-reranking configurations using the same evaluation dataset.

**Measured results:** To be published after running the reproducible evaluation suite.

## 🔐 Security

- Organisation-level data isolation.
- Role-based access control.
- Document-level permissions.
- Authenticated API endpoints.
- Input and file validation.
- Secure secret management.
- Audit logging.
- Retrieval-time permission enforcement.

## 🧪 Testing

Run backend tests:

```bash
pytest
```

Run frontend tests:

```bash
npm test
```

Run browser tests:

```bash
npx playwright test
```

Run the RAG evaluation suite:

```bash
python scripts/run_evaluation.py
```

## 🗺️ Roadmap

- [ ] Authentication and organisation management
- [ ] Document upload and ingestion
- [ ] Embedding generation and vector indexing
- [ ] Hybrid search and RRF
- [ ] Cross-encoder reranking
- [ ] Grounded answer generation
- [ ] Citation validation
- [ ] Multi-tenant access control
- [ ] Conversation history
- [ ] Evaluation and benchmarking
- [ ] Monitoring and observability
- [ ] Automated CI/CD
- [ ] Cloud deployment
- [ ] Demo and documentation

## 🎯 Engineering Goals

The project aims to demonstrate:

- End-to-end RAG system development.
- Practical NLP and embedding model integration.
- Search and ranking optimisation.
- ML evaluation and reproducibility.
- Secure multi-tenant application design.
- Production-oriented API and background-job architecture.
- Containerisation, testing, and deployment.

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome. Please open an issue before submitting major architectural changes.

## 📄 License

Released under the MIT License. See [LICENSE](LICENSE).

---

**Built as an applied AI engineering portfolio project.**
