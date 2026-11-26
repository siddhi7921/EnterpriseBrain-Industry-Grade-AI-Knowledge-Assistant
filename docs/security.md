# Enterprise Security & Threat Model

1. **Tenant Isolation**: Every table (`documents`, `document_chunks`, `conversations`, `audit_logs`) is scoped by `organization_id`. Membership is verified on every endpoint.
2. **SQL-Level Document ACL**: Restricted documents (`access_scope = 'restricted'`) are excluded inside SQL retrieval queries unless the user is an `owner`/`admin`, the uploader, or holds an explicit `document_permissions` grant.
3. **Prompt Injection Defense**:
   - Ingestion strips known instruction-override patterns from document text.
   - System prompt explicitly instructs the LLM to treat retrieved passages as untrusted data.
4. **Citation Integrity**: `CitationValidator` discards any citation ID not present in the user's authorized retrieval results.
5. **Immutable Audit Trail**: Uploads, deletions, permission edits, membership changes, and chat queries are recorded in `audit_logs`.
