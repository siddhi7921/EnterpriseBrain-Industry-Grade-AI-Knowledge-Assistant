# API Reference (`/api/v1`)

Interactive OpenAPI/Swagger documentation is served at `/docs` when the FastAPI server is running.

## Key Endpoints
- **Auth**: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`
- **Organisations**: `POST /organizations`, `GET /organizations`, `GET/POST /organizations/{org_id}/members`, `PATCH /organizations/{org_id}/members/{user_id}`
- **Documents**: `POST/GET /organizations/{org_id}/documents`, `GET/DELETE /documents/{document_id}`, `POST /documents/{document_id}/reindex`, `GET /documents/{document_id}/status`, `PATCH /documents/{document_id}/permissions`
- **Chat & RAG**: `POST /organizations/{org_id}/chat`, `POST /organizations/{org_id}/chat/stream`, `GET /conversations`, `GET/DELETE /conversations/{id}`, `POST /messages/{message_id}/feedback`
- **Analytics & Evaluation**: `GET /organizations/{org_id}/analytics`, `GET /organizations/{org_id}/audit-logs`, `POST /admin/evaluations/run`, `GET /admin/evaluations/{run_id}`
