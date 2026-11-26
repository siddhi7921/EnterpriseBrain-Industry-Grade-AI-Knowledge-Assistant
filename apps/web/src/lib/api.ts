import type {
  AnalyticsOverview,
  AuditLogItem,
  ChatResponse,
  ConversationDetail,
  ConversationSummary,
  DocumentResponse,
  EvaluationRunResponse,
  MemberResponse,
  OrganizationResponse,
  TokenResponse,
  UserResponse,
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

function getAccessToken(): string | null {
  return localStorage.getItem("eb_access_token");
}

export function isDemoMode(): boolean {
  return localStorage.getItem("eb_demo_mode") === "true";
}

export function setDemoMode(active: boolean): void {
  if (active) {
    localStorage.setItem("eb_demo_mode", "true");
    localStorage.setItem("eb_access_token", "demo-token-enterprisebrain");
    localStorage.setItem("eb_refresh_token", "demo-refresh-token");
    localStorage.setItem("eb_active_org_id", "demo-org-acme");
  } else {
    localStorage.removeItem("eb_demo_mode");
  }
}

// ----------------- Demo / Offline Mock Store -----------------
const mockUser: UserResponse = {
  id: "demo-user-alice",
  email: "alice@acme.com",
  is_active: true,
  created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
};

const mockOrgs: OrganizationResponse[] = [
  {
    id: "demo-org-acme",
    name: "Acme Technologies",
    slug: "acme-technologies",
    role: "owner",
    created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
  },
  {
    id: "demo-org-globex",
    name: "Globex Corporation",
    slug: "globex-corp",
    role: "member",
    created_at: new Date(Date.now() - 86400000 * 15).toISOString(),
  },
];

let mockMembers: MemberResponse[] = [
  { user_id: "demo-user-alice", email: "alice@acme.com", role: "owner" },
  { user_id: "demo-user-bob", email: "bob@acme.com", role: "member" },
  { user_id: "demo-user-carol", email: "carol@acme.com", role: "admin" },
];

let mockDocuments: DocumentResponse[] = [
  {
    id: "demo-doc-1",
    organization_id: "demo-org-acme",
    uploaded_by: "demo-user-alice",
    filename: "Acme_Employee_Handbook_2026.md",
    mime_type: "text/markdown",
    checksum: "sha256-a1b2c3d4e5f67890",
    status: "indexed",
    access_scope: "organization",
    version: 1,
    chunk_count: 6,
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
  },
  {
    id: "demo-doc-2",
    organization_id: "demo-org-acme",
    uploaded_by: "demo-user-alice",
    filename: "Project_Phoenix_Confidential_Memo.docx",
    mime_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    checksum: "sha256-f6e5d4c3b2a10987",
    status: "indexed",
    access_scope: "restricted",
    version: 1,
    chunk_count: 3,
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
  {
    id: "demo-doc-3",
    organization_id: "demo-org-acme",
    uploaded_by: "demo-user-alice",
    filename: "Security_Architecture_v2.pdf",
    mime_type: "application/pdf",
    checksum: "sha256-8899aabbccddeeff",
    status: "indexed",
    access_scope: "organization",
    version: 1,
    chunk_count: 8,
    created_at: new Date(Date.now() - 86400000 * 1).toISOString(),
  },
];

let mockConversations: ConversationSummary[] = [
  {
    id: "demo-conv-1",
    organization_id: "demo-org-acme",
    title: "Employee Leave & Expense Guidelines",
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
  },
];

let mockMessages: Record<string, ConversationDetail> = {
  "demo-conv-1": {
    id: "demo-conv-1",
    organization_id: "demo-org-acme",
    title: "Employee Leave & Expense Guidelines",
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
    messages: [
      {
        id: "msg-1",
        role: "user",
        content: "How many days of paid annual leave do full-time employees receive?",
        citations: [],
        token_usage: { prompt: 14, completion: 0 },
        created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
      },
      {
        id: "msg-2",
        role: "assistant",
        content:
          "All full-time employees at Acme receive **22 days of paid annual leave** and **10 days of sick leave** per year [CHUNK:demo-chunk-1].",
        citations: [
          {
            document_id: "demo-doc-1",
            filename: "Acme_Employee_Handbook_2026.md",
            chunk_id: "demo-chunk-1",
            page: 1,
            quote:
              "All full-time employees at Org Alpha receive 22 days of paid annual leave and 10 days of sick leave.",
            relevance_score: 0.94,
          },
        ],
        model: "gpt-4o-mini + bge-reranker-v2-m3",
        token_usage: { prompt: 185, completion: 36, total: 221 },
        latency_ms: 184,
        created_at: new Date(Date.now() - 3600000 * 4 + 1000).toISOString(),
      },
    ],
  },
};

const mockAuditLogs: AuditLogItem[] = [
  {
    id: "audit-1",
    organization_id: "demo-org-acme",
    actor_id: "demo-user-alice",
    action: "document.indexed",
    resource_id: "demo-doc-3",
    metadata_json: { filename: "Security_Architecture_v2.pdf", chunk_count: 8 },
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
  },
  {
    id: "audit-2",
    organization_id: "demo-org-acme",
    actor_id: "demo-user-alice",
    action: "chat.query",
    resource_id: "demo-conv-1",
    metadata_json: { mode: "hybrid_rerank", top_k: 5, citations_returned: 1 },
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
  },
  {
    id: "audit-3",
    organization_id: "demo-org-acme",
    actor_id: "demo-user-alice",
    action: "document.indexed",
    resource_id: "demo-doc-1",
    metadata_json: { filename: "Acme_Employee_Handbook_2026.md", chunk_count: 6 },
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
  },
];

const mockEvalRuns: EvaluationRunResponse[] = [
  {
    id: "eval-run-benchmark-latest",
    organization_id: "demo-org-acme",
    dataset_name: "enterprise_qa_benchmark",
    model_name: "BAAI/bge-m3 + BAAI/bge-reranker-v2-m3",
    metrics: {
      vector: {
        mode: "vector",
        recall_at_k: 1.0,
        precision_at_k: 0.2,
        mrr: 0.7396,
        ndcg_at_k: 0.8038,
        faithfulness: 0.5699,
        answer_relevance: 0.82,
        citation_correctness: 1.0,
        avg_latency_ms: 2.06,
        sample_count: 10,
      },
      keyword: {
        mode: "keyword",
        recall_at_k: 1.0,
        precision_at_k: 0.2,
        mrr: 0.9167,
        ndcg_at_k: 0.9375,
        faithfulness: 0.5611,
        answer_relevance: 0.81,
        citation_correctness: 1.0,
        avg_latency_ms: 1.13,
        sample_count: 10,
      },
      hybrid: {
        mode: "hybrid",
        recall_at_k: 1.0,
        precision_at_k: 0.2,
        mrr: 0.7917,
        ndcg_at_k: 0.8452,
        faithfulness: 0.5639,
        answer_relevance: 0.84,
        citation_correctness: 1.0,
        avg_latency_ms: 2.88,
        sample_count: 10,
      },
      hybrid_rerank: {
        mode: "hybrid_rerank",
        recall_at_k: 1.0,
        precision_at_k: 0.2,
        mrr: 0.7917,
        ndcg_at_k: 0.8452,
        faithfulness: 0.5577,
        answer_relevance: 0.89,
        citation_correctness: 1.0,
        avg_latency_ms: 2.97,
        sample_count: 10,
      },
    },
    created_at: new Date(Date.now() - 3600000 * 6).toISOString(),
  },
];

// Fallback mock router
function handleMockRequest<T>(path: string, options: RequestInit = {}): T {
  const method = (options.method || "GET").toUpperCase();
  const body = typeof options.body === "string" ? JSON.parse(options.body) : {};

  // Auth
  if (path === "/auth/login" || path === "/auth/register") {
    setDemoMode(true);
    return {
      access_token: "demo-token-enterprisebrain",
      refresh_token: "demo-refresh-token",
      token_type: "bearer",
    } as T;
  }
  if (path === "/auth/me") {
    return mockUser as T;
  }

  // Organizations
  if (path === "/organizations") {
    if (method === "POST") {
      const newOrg: OrganizationResponse = {
        id: `demo-org-${Date.now()}`,
        name: body.name || "New Workspace",
        slug: (body.name || "new-workspace").toLowerCase().replace(/\s+/g, "-"),
        role: "owner",
        created_at: new Date().toISOString(),
      };
      mockOrgs.push(newOrg);
      return newOrg as T;
    }
    return mockOrgs as T;
  }

  // Members
  if (path.includes("/members")) {
    if (method === "POST") {
      const newMem: MemberResponse = {
        user_id: `user-${Date.now()}`,
        email: body.email,
        role: body.role || "member",
      };
      mockMembers.push(newMem);
      return newMem as T;
    }
    if (method === "PATCH") {
      return { user_id: "user-updated", email: "member@acme.com", role: body.role } as T;
    }
    return mockMembers as T;
  }

  // Documents
  if (path.includes("/documents")) {
    if (method === "POST" && options.body instanceof FormData) {
      const file = (options.body as FormData).get("file") as File;
      const scope = ((options.body as FormData).get("access_scope") as string) || "organization";
      const newDoc: DocumentResponse = {
        id: `demo-doc-${Date.now()}`,
        organization_id: "demo-org-acme",
        uploaded_by: "demo-user-alice",
        filename: file?.name || "uploaded_document.pdf",
        mime_type: file?.type || "application/pdf",
        checksum: `sha256-${Date.now()}`,
        status: "indexed",
        access_scope: scope as "organization" | "restricted",
        version: 1,
        chunk_count: 4,
        created_at: new Date().toISOString(),
      };
      mockDocuments.unshift(newDoc);
      return newDoc as T;
    }
    if (method === "DELETE") {
      return undefined as T;
    }
    if (path.endsWith("/reindex")) {
      return { status: "indexed" } as T;
    }
    if (path.endsWith("/permissions")) {
      return mockDocuments[0] as T;
    }
    return mockDocuments as T;
  }

  // Chat
  if (path.includes("/chat") && method === "POST") {
    const q = (body.question || "").toLowerCase();
    let answerText =
      "Based on Acme internal documentation, full-time employees receive 22 days of paid annual leave, 10 days of sick leave, and software subscriptions under $100/mo are auto-approved [CHUNK:demo-chunk-1].";
    let quote = "All full-time employees receive 22 days of paid annual leave and 10 days of sick leave.";
    let doc = mockDocuments[0];

    if (q.includes("phoenix") || q.includes("acqui")) {
      answerText =
        "Project Phoenix is the confidential memo detailing the acquisition plan for CloudScale Systems for $48 million [CHUNK:demo-chunk-2].";
      quote = "Org Alpha plans to acquire CloudScale Systems for $48 million in Q3 2026.";
      doc = mockDocuments[1] || mockDocuments[0];
    } else if (q.includes("security") || q.includes("mfa") || q.includes("access")) {
      answerText =
        "Production database access requires hardware MFA, bastion SSH, and zero-trust perimeter verification [CHUNK:demo-chunk-3].";
      quote = "Production database access requires hardware MFA and bastion SSH.";
      doc = mockDocuments[2] || mockDocuments[0];
    }

    const convId = body.conversation_id || `demo-conv-${Date.now()}`;
    const resp: ChatResponse = {
      conversation_id: convId,
      message_id: `msg-${Date.now()}`,
      answer: answerText,
      citations: [
        {
          document_id: doc.id,
          filename: doc.filename,
          chunk_id: `demo-chunk-${Date.now()}`,
          page: 1,
          quote,
          relevance_score: 0.95,
        },
      ],
      retrieval: {
        candidate_count: 12,
        reranked_count: body.top_k || 5,
        mode: body.retrieval_mode || "hybrid_rerank",
      },
      usage: {
        input_tokens: 210,
        output_tokens: 45,
      },
      latency_ms: 175,
    };

    if (!mockMessages[convId]) {
      const summary: ConversationSummary = {
        id: convId,
        organization_id: "demo-org-acme",
        title: body.question.slice(0, 40) + "...",
        created_at: new Date().toISOString(),
      };
      mockConversations.unshift(summary);
      mockMessages[convId] = {
        ...summary,
        messages: [],
      };
    }

    mockMessages[convId].messages.push({
      id: `user-${Date.now()}`,
      role: "user",
      content: body.question,
      citations: [],
      token_usage: { prompt: 15, completion: 0 },
      created_at: new Date().toISOString(),
    });

    mockMessages[convId].messages.push({
      id: resp.message_id,
      role: "assistant",
      content: resp.answer,
      citations: resp.citations,
      token_usage: { prompt: 210, completion: 45, total: 255 },
      latency_ms: resp.latency_ms,
      created_at: new Date().toISOString(),
    });

    return resp as T;
  }

  // Conversations
  if (path.startsWith("/conversations")) {
    if (method === "DELETE") {
      const id = path.split("/").pop();
      mockConversations = mockConversations.filter((c) => c.id !== id);
      return undefined as T;
    }
    const convId = path.split("/").pop();
    if (convId && mockMessages[convId]) {
      return mockMessages[convId] as T;
    }
    return mockConversations as T;
  }

  if (path.includes("/feedback")) {
    return { status: "feedback_recorded" } as T;
  }

  // Analytics & Logs
  if (path.includes("/analytics")) {
    const overview: AnalyticsOverview = {
      organization_id: "demo-org-acme",
      total_documents: mockDocuments.length,
      indexed_documents: mockDocuments.filter((d) => d.status === "indexed").length,
      total_chunks: mockDocuments.reduce((acc, d) => acc + d.chunk_count, 0),
      total_conversations: mockConversations.length,
      total_queries: 18,
      avg_latency_ms: 192,
      total_input_tokens: 4520,
      total_output_tokens: 1240,
      avg_feedback_rating: 4.9,
    };
    return overview as T;
  }

  if (path.includes("/audit-logs")) {
    return mockAuditLogs as T;
  }

  // Evaluations
  if (path.includes("/evaluations")) {
    if (path.endsWith("/run")) {
      const newRun: EvaluationRunResponse = {
        id: `eval-${Date.now()}`,
        organization_id: "demo-org-acme",
        dataset_name: "enterprise_qa_benchmark",
        model_name: "BAAI/bge-m3 + BAAI/bge-reranker-v2-m3",
        metrics: mockEvalRuns[0].metrics,
        created_at: new Date().toISOString(),
      };
      mockEvalRuns.unshift(newRun);
      return newRun as T;
    }
    return mockEvalRuns as T;
  }

  return {} as T;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  // If demo mode is explicitly enabled, serve immediately from mock store
  if (isDemoMode()) {
    return handleMockRequest<T>(path, options);
  }

  const token = getAccessToken();
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (res.status === 204) {
      return undefined as T;
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || `Request failed with status ${res.status}`);
    }
    return data as T;
  } catch (err: unknown) {
    // If backend is unreachable (e.g. Failed to fetch), smoothly fallback to demo store
    const isNetworkError =
      err instanceof TypeError ||
      (err instanceof Error &&
        (err.message.includes("Failed to fetch") ||
          err.message.includes("NetworkError") ||
          err.message.includes("Load failed")));

    if (isNetworkError) {
      console.warn(`[EnterpriseBrain] Backend API unreachable at ${API_BASE}. Falling back to demo mode.`);
      setDemoMode(true);
      return handleMockRequest<T>(path, options);
    }
    throw err;
  }
}

export const api = {
  // Auth
  register: (email: string, password: string, organization_name?: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, organization_name: organization_name || null }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<UserResponse>("/auth/me"),

  // Organisations
  listOrganizations: () => request<OrganizationResponse[]>("/organizations"),

  createOrganization: (name: string) =>
    request<OrganizationResponse>("/organizations", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  listMembers: (orgId: string) => request<MemberResponse[]>(`/organizations/${orgId}/members`),

  addMember: (orgId: string, email: string, role: "owner" | "admin" | "member") =>
    request<MemberResponse>(`/organizations/${orgId}/members`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    }),

  updateMemberRole: (orgId: string, userId: string, role: "owner" | "admin" | "member") =>
    request<MemberResponse>(`/organizations/${orgId}/members/${userId}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    }),

  // Documents
  listDocuments: (orgId: string) => request<DocumentResponse[]>(`/organizations/${orgId}/documents`),

  uploadDocument: (orgId: string, file: File, accessScope: "organization" | "restricted") => {
    const form = new FormData();
    form.append("file", file);
    form.append("access_scope", accessScope);
    return request<DocumentResponse>(`/organizations/${orgId}/documents`, {
      method: "POST",
      body: form,
    });
  },

  reindexDocument: (docId: string) =>
    request(`/documents/${docId}/reindex`, { method: "POST" }),

  deleteDocument: (docId: string) =>
    request<void>(`/documents/${docId}`, { method: "DELETE" }),

  updateDocumentPermissions: (
    docId: string,
    access_scope: "organization" | "restricted",
    permissions: { user_id: string; permission: "read" | "manage" }[]
  ) =>
    request<DocumentResponse>(`/documents/${docId}/permissions`, {
      method: "PATCH",
      body: JSON.stringify({ access_scope, permissions }),
    }),

  // Chat & RAG
  sendChat: (
    orgId: string,
    payload: {
      conversation_id: string | null;
      question: string;
      filters: { document_ids: string[] };
      top_k: number;
      retrieval_mode: "vector" | "keyword" | "hybrid" | "hybrid_rerank";
    }
  ) =>
    request<ChatResponse>(`/organizations/${orgId}/chat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listConversations: (orgId: string) =>
    request<ConversationSummary[]>(`/conversations?organization_id=${orgId}`),

  getConversation: (conversationId: string) =>
    request<ConversationDetail>(`/conversations/${conversationId}`),

  deleteConversation: (conversationId: string) =>
    request<void>(`/conversations/${conversationId}`, { method: "DELETE" }),

  submitFeedback: (messageId: string, rating: number, comment?: string) =>
    request(`/messages/${messageId}/feedback`, {
      method: "POST",
      body: JSON.stringify({ rating, comment: comment || null }),
    }),

  // Analytics & Evaluation
  getAnalytics: (orgId: string) => request<AnalyticsOverview>(`/organizations/${orgId}/analytics`),

  getAuditLogs: (orgId: string) => request<AuditLogItem[]>(`/organizations/${orgId}/audit-logs`),

  runEvaluation: (orgId: string, dataset_name = "enterprise_qa_benchmark", top_k = 5) =>
    request<EvaluationRunResponse>("/admin/evaluations/run", {
      method: "POST",
      body: JSON.stringify({ organization_id: orgId, dataset_name, top_k }),
    }),

  listEvaluations: (orgId: string) =>
    request<EvaluationRunResponse[]>(`/admin/evaluations?organization_id=${orgId}`),
};
