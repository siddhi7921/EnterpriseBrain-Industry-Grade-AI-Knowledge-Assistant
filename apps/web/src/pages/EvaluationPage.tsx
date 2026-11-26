import React, { useEffect, useState } from "react";
import { FlaskConical, Play } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import type { EvaluationRunResponse } from "../types/api";

export const EvaluationPage: React.FC = () => {
  const { activeOrg } = useAuth();
  const [runs, setRuns] = useState<EvaluationRunResponse[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRuns = async () => {
    if (!activeOrg) return;
    const list = await api.listEvaluations(activeOrg.id);
    setRuns(list);
  };

  useEffect(() => {
    loadRuns().catch(() => {});
  }, [activeOrg?.id]);

  const handleRunBenchmark = async () => {
    if (!activeOrg) return;
    setRunning(true);
    setError(null);
    try {
      const latest = await api.runEvaluation(activeOrg.id);
      setRuns((prev) => [latest, ...prev]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Benchmark execution failed");
    } finally {
      setRunning(false);
    }
  };

  const latestRun = runs[0];

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-indigo-400" />
            ML Retrieval &amp; RAG Evaluation Lab
          </h1>
          <p className="text-sm text-slate-400">
            Benchmark Vector-only, Keyword-only, Hybrid RRF, and Hybrid + Reranking on the same
            QA dataset.
          </p>
        </div>

        <button
          onClick={handleRunBenchmark}
          disabled={running}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2.5 text-sm font-semibold text-white transition"
        >
          <Play className="w-4 h-4" />
          {running ? "Running 4-Mode Benchmark..." : "Run Evaluation Suite"}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-950/50 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {latestRun ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between text-xs text-slate-400">
            <span>
              Dataset: <strong className="text-white">{latestRun.dataset_name}</strong> | Models:{" "}
              <strong className="text-indigo-300">{latestRun.model_name}</strong>
            </span>
            <span>Run ID: {latestRun.id}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950 text-slate-400 text-xs uppercase border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Retrieval Configuration</th>
                  <th className="px-4 py-3">Recall@5</th>
                  <th className="px-4 py-3">Precision@5</th>
                  <th className="px-4 py-3">MRR</th>
                  <th className="px-4 py-3">nDCG@5</th>
                  <th className="px-4 py-3">Faithfulness</th>
                  <th className="px-4 py-3">Citation Acc</th>
                  <th className="px-4 py-3">Avg Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {Object.entries(latestRun.metrics).map(([mode, m]) => (
                  <tr key={mode} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-semibold text-white">{mode}</td>
                    <td className="px-4 py-3 text-emerald-400 font-mono">
                      {(m.recall_at_k * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 font-mono">{(m.precision_at_k * 100).toFixed(1)}%</td>
                    <td className="px-4 py-3 font-mono">{m.mrr.toFixed(3)}</td>
                    <td className="px-4 py-3 font-mono">{m.ndcg_at_k.toFixed(3)}</td>
                    <td className="px-4 py-3 text-indigo-300 font-mono">
                      {(m.faithfulness * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 font-mono">
                      {(m.citation_correctness * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono">{m.avg_latency_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400 text-sm">
          Click <strong>Run Evaluation Suite</strong> to benchmark all four retrieval pipelines
          against your workspace documents.
        </div>
      )}
    </div>
  );
};
