export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface OrganizationResponse {
  id: string;
  name: string;
  slug: string;
  role: "owner" | "admin" | "member" | string;
  created_at: string;
}

export interface MemberResponse {
  user_id: string;
  email: string;
  role: "owner" | "admin" | "member";
}

export interface DocumentResponse {
  id: string;
  organization_id: string;
  uploaded_by: string;
  filename: string;
  mime_type: string;
  checksum: string;
  status: "pending" | "processing" | "indexed" | "failed" | string;
  access_scope: "organization" | "restricted";
  version: number;
  chunk_count: number;
  created_at: string;
}

export interface CitationItem {
  document_id: string;
  filename: string;
  chunk_id: string;
  page: number | null;
  quote: string;
  relevance_score: number;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  citations: CitationItem[];
  retrieval: {
    candidate_count: number;
    reranked_count: number;
    mode: string;
  };
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
  latency_ms: number;
}

export interface ConversationSummary {
  id: string;
  organization_id: string;
  title: string;
  created_at: string;
}

export interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: CitationItem[];
  model?: string | null;
  token_usage: Record<string, number>;
  latency_ms?: number | null;
  created_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: MessageItem[];
}

export interface AnalyticsOverview {
  organization_id: string;
  total_documents: number;
  indexed_documents: number;
  total_chunks: number;
  total_conversations: number;
  total_queries: number;
  avg_latency_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
  avg_feedback_rating: number | null;
}

export interface AuditLogItem {
  id: string;
  organization_id: string;
  actor_id: string | null;
  action: string;
  resource_id: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface ModeMetric {
  mode: string;
  recall_at_k: number;
  precision_at_k: number;
  mrr: number;
  ndcg_at_k: number;
  faithfulness: number;
  answer_relevance: number;
  citation_correctness: number;
  avg_latency_ms: number;
  sample_count: number;
}

export interface EvaluationRunResponse {
  id: string;
  organization_id: string | null;
  dataset_name: string;
  model_name: string;
  metrics: Record<string, ModeMetric>;
  created_at: string;
}
