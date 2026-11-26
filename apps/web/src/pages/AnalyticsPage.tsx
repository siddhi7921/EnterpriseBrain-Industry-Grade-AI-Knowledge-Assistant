import React, { useEffect, useState } from "react";
import { Activity, ShieldAlert } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import type { AnalyticsOverview, AuditLogItem } from "../types/api";

export const AnalyticsPage: React.FC = () => {
  const { activeOrg } = useAuth();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);

  useEffect(() => {
    if (!activeOrg) return;
    api.getAnalytics(activeOrg.id).then(setOverview).catch(() => {});
    api.getAuditLogs(activeOrg.id).then(setLogs).catch(() => {});
  }, [activeOrg?.id]);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Activity className="w-6 h-6 text-indigo-400" />
          Observability, Usage &amp; Security Audit Trail
        </h1>
        <p className="text-sm text-slate-400">
          Real-time telemetry for RAG latency, token consumption, user ratings, and security events.
        </p>
      </div>

      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs text-slate-400">Indexed Documents</div>
            <div className="text-2xl font-bold text-white mt-1">
              {overview.indexed_documents} / {overview.total_documents}
            </div>
            <div className="text-xs text-indigo-400 mt-1">{overview.total_chunks} vector chunks</div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs text-slate-400">Total RAG Queries</div>
            <div className="text-2xl font-bold text-white mt-1">{overview.total_queries}</div>
            <div className="text-xs text-slate-400 mt-1">
              Across {overview.total_conversations} threads
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs text-slate-400">Avg End-to-End Latency</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {overview.avg_latency_ms} ms
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {overview.total_input_tokens + overview.total_output_tokens} total tokens
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs text-slate-400">User Answer Rating</div>
            <div className="text-2xl font-bold text-amber-400 mt-1">
              {overview.avg_feedback_rating ? `${overview.avg_feedback_rating} / 5.0` : "N/A"}
            </div>
            <div className="text-xs text-slate-400 mt-1">Verified citation feedback</div>
          </div>
        </div>
      )}

      {/* Immutable Security Audit Log */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-emerald-400" />
          Immutable Workspace Audit Log
        </h2>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Timestamp (UTC)</th>
                <th className="px-4 py-3">Event Action</th>
                <th className="px-4 py-3">Actor ID</th>
                <th className="px-4 py-3">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/30">
                  <td className="px-4 py-2.5 text-slate-400 font-mono">
                    {new Date(log.created_at).toISOString()}
                  </td>
                  <td className="px-4 py-2.5 font-semibold text-indigo-300">{log.action}</td>
                  <td className="px-4 py-2.5 text-slate-400 font-mono">
                    {log.actor_id ? log.actor_id.slice(0, 8) + "..." : "system"}
                  </td>
                  <td className="px-4 py-2.5 text-slate-300 font-mono">
                    {JSON.stringify(log.metadata_json)}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                    No audit events recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
