import React, { useEffect, useState } from "react";
import {
  BookOpen,
  Clock,
  FileText,
  Plus,
  Send,
  Sparkles,
  Star,
  Trash2,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import type {
  ConversationSummary,
  DocumentResponse,
  MessageItem,
} from "../types/api";

export const ChatPage: React.FC = () => {
  const { activeOrg } = useAuth();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [retrievalMode, setRetrievalMode] = useState<
    "hybrid_rerank" | "hybrid" | "vector" | "keyword"
  >("hybrid_rerank");
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ratedMessages, setRatedMessages] = useState<Record<string, number>>({});

  useEffect(() => {
    if (!activeOrg) return;
    setActiveConvId(null);
    setMessages([]);
    api.listConversations(activeOrg.id).then(setConversations).catch(() => {});
    api.listDocuments(activeOrg.id).then(setDocuments).catch(() => {});
  }, [activeOrg?.id]);

  const loadConversation = async (convId: string) => {
    setActiveConvId(convId);
    setError(null);
    try {
      const detail = await api.getConversation(convId);
      setMessages(detail.messages);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load conversation");
    }
  };

  const handleDeleteConversation = async (convId: string) => {
    await api.deleteConversation(convId);
    setConversations((prev) => prev.filter((c) => c.id !== convId));
    if (activeConvId === convId) {
      setActiveConvId(null);
      setMessages([]);
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrg || !question.trim() || sending) return;

    const currentQ = question.trim();
    setQuestion("");
    setError(null);
    setSending(true);

    const tempUserMsg: MessageItem = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: currentQ,
      citations: [],
      token_usage: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await api.sendChat(activeOrg.id, {
        conversation_id: activeConvId,
        question: currentQ,
        filters: { document_ids: selectedDocIds },
        top_k: 5,
        retrieval_mode: retrievalMode,
      });

      setActiveConvId(res.conversation_id);
      const assistantMsg: MessageItem = {
        id: res.message_id,
        role: "assistant",
        content: res.answer,
        citations: res.citations,
        token_usage: res.usage,
        latency_ms: res.latency_ms,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      const updatedConvs = await api.listConversations(activeOrg.id);
      setConversations(updatedConvs);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get answer");
    } finally {
      setSending(false);
    }
  };

  const handleRate = async (messageId: string, rating: number) => {
    await api.submitFeedback(messageId, rating);
    setRatedMessages((prev) => ({ ...prev, [messageId]: rating }));
  };

  const toggleDocFilter = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  return (
    <div className="h-screen flex">
      {/* Conversation History Drawer */}
      <div className="w-64 border-r border-slate-800 bg-slate-900/40 p-3 flex flex-col">
        <button
          onClick={() => {
            setActiveConvId(null);
            setMessages([]);
          }}
          className="w-full flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 py-2 text-sm font-medium text-white transition mb-3"
        >
          <Plus className="w-4 h-4" />
          New Research Thread
        </button>

        <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 px-2 mb-2">
          Recent Threads
        </div>

        <div className="flex-1 overflow-y-auto space-y-1">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center justify-between rounded-lg px-2.5 py-2 text-xs cursor-pointer ${
                activeConvId === conv.id
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
                  : "text-slate-300 hover:bg-slate-800/70"
              }`}
              onClick={() => loadConversation(conv.id)}
            >
              <span className="truncate pr-2">{conv.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConversation(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-400"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          {conversations.length === 0 && (
            <p className="text-xs text-slate-500 px-2 py-4">No conversations yet.</p>
          )}
        </div>
      </div>

      {/* Main Chat Pane */}
      <div className="flex-1 flex flex-col bg-slate-950">
        {/* Top Controls Bar */}
        <div className="border-b border-slate-800 px-6 py-3 flex flex-wrap items-center justify-between gap-3 bg-slate-900/30">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-semibold text-white">
              {activeOrg?.name} Knowledge Assistant
            </span>
          </div>

          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400">Retrieval Strategy:</label>
            <select
              value={retrievalMode}
              onChange={(e) =>
                setRetrievalMode(
                  e.target.value as "hybrid_rerank" | "hybrid" | "vector" | "keyword"
                )
              }
              className="rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="hybrid_rerank">Hybrid RRF + Cross-Encoder Rerank</option>
              <option value="hybrid">Hybrid (Vector + Keyword RRF)</option>
              <option value="vector">Dense Vector Search Only</option>
              <option value="keyword">Full-Text Keyword Search Only</option>
            </select>
          </div>
        </div>

        {/* Document Scope Filter Pills */}
        {documents.length > 0 && (
          <div className="border-b border-slate-800/70 px-6 py-2 flex items-center gap-2 overflow-x-auto bg-slate-950">
            <span className="text-[11px] text-slate-400 shrink-0">Scope filter:</span>
            {documents
              .filter((d) => d.status === "indexed")
              .map((doc) => {
                const selected = selectedDocIds.includes(doc.id);
                return (
                  <button
                    key={doc.id}
                    onClick={() => toggleDocFilter(doc.id)}
                    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] border transition shrink-0 ${
                      selected
                        ? "bg-indigo-600/20 border-indigo-500 text-indigo-300"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <FileText className="w-3 h-3" />
                    {doc.filename}
                  </button>
                );
              })}
          </div>
        )}

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="max-w-xl mx-auto text-center py-16 space-y-3">
              <BookOpen className="w-10 h-10 text-indigo-400 mx-auto opacity-80" />
              <h2 className="text-lg font-semibold text-white">
                Ask a question across your organisation&apos;s documents
              </h2>
              <p className="text-sm text-slate-400">
                Answers are strictly grounded in authorized passages with verifiable source
                citations, page references, and relevance scores.
              </p>
              <div className="pt-3 flex flex-wrap justify-center gap-2">
                {[
                  "How many days of paid annual leave do employees receive?",
                  "What authentication is required for production databases?",
                  "What is the home office equipment stipend?",
                ].map((sampleQ) => (
                  <button
                    key={sampleQ}
                    onClick={() => setQuestion(sampleQ)}
                    className="text-xs rounded-lg border border-slate-800 bg-slate-900/80 hover:border-indigo-500/50 px-3 py-2 text-slate-300 transition"
                  >
                    {sampleQ}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-3xl ${msg.role === "user" ? "ml-auto" : "mr-auto"}`}
            >
              <div
                className={`rounded-2xl px-4 py-3.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-900 border border-slate-800 text-slate-100"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Citations & Telemetry for Assistant */}
                {msg.role === "assistant" && (
                  <div className="mt-4 pt-3 border-t border-slate-800 space-y-3">
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400">
                          Verified Evidence Citations ({msg.citations.length})
                        </div>
                        <div className="grid gap-2">
                          {msg.citations.map((cit, idx) => (
                            <div
                              key={`${cit.chunk_id}-${idx}`}
                              className="rounded-lg bg-slate-950 border border-slate-800 p-2.5 text-xs space-y-1"
                            >
                              <div className="flex items-center justify-between text-slate-300 font-medium">
                                <span>
                                  [{idx + 1}] {cit.filename}
                                  {cit.page ? ` • Page ${cit.page}` : ""}
                                </span>
                                <span className="text-[11px] text-emerald-400">
                                  Score: {cit.relevance_score.toFixed(3)}
                                </span>
                              </div>
                              <p className="text-slate-400 italic">&ldquo;{cit.quote}&rdquo;</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <div className="flex items-center gap-3">
                        {msg.latency_ms != null && (
                          <span className="inline-flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {msg.latency_ms} ms
                          </span>
                        )}
                        {msg.token_usage?.input_tokens != null && (
                          <span>
                            Tokens: {msg.token_usage.input_tokens} in /{" "}
                            {msg.token_usage.output_tokens} out
                          </span>
                        )}
                      </div>

                      {/* 1-5 Star Rating Feedback */}
                      <div className="flex items-center gap-1">
                        <span>Rate:</span>
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            onClick={() => handleRate(msg.id, star)}
                            className={`p-0.5 transition ${
                              (ratedMessages[msg.id] || 0) >= star
                                ? "text-amber-400"
                                : "text-slate-600 hover:text-amber-300"
                            }`}
                          >
                            <Star className="w-3.5 h-3.5 fill-current" />
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {error && (
          <div className="mx-6 mb-2 rounded-lg border border-rose-500/40 bg-rose-950/50 px-3 py-2 text-xs text-rose-300">
            {error}
          </div>
        )}

        {/* Prompt Input */}
        <form onSubmit={handleAsk} className="border-t border-slate-800 p-4 bg-slate-900/30">
          <div className="max-w-3xl mx-auto flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question grounded in your workspace knowledge base..."
              className="flex-1 rounded-xl bg-slate-900 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={sending || !question.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-5 py-2.5 text-sm font-semibold text-white transition"
            >
              <Send className="w-4 h-4" />
              {sending ? "Retrieving..." : "Ask"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
