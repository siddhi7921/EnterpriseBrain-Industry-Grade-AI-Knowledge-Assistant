import React, { useEffect, useState } from "react";
import {
  FileText,
  Lock,
  RefreshCw,
  Shield,
  Trash2,
  UploadCloud,
  Globe,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import type { DocumentResponse, MemberResponse } from "../types/api";

export const DocumentsPage: React.FC = () => {
  const { activeOrg } = useAuth();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [members, setMembers] = useState<MemberResponse[]>([]);
  const [accessScope, setAccessScope] = useState<"organization" | "restricted">("organization");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Permission Modal State
  const [permDoc, setPermDoc] = useState<DocumentResponse | null>(null);
  const [modalScope, setModalScope] = useState<"organization" | "restricted">("organization");
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);

  const loadData = async () => {
    if (!activeOrg) return;
    const [docs, mems] = await Promise.all([
      api.listDocuments(activeOrg.id),
      api.listMembers(activeOrg.id),
    ]);
    setDocuments(docs);
    setMembers(mems);
  };

  useEffect(() => {
    loadData().catch(() => {});
  }, [activeOrg?.id]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activeOrg) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadDocument(activeOrg.id, file, accessScope);
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleReindex = async (docId: string) => {
    await api.reindexDocument(docId);
    await loadData();
  };

  const handleDelete = async (docId: string) => {
    await api.deleteDocument(docId);
    await loadData();
  };

  const openPermModal = (doc: DocumentResponse) => {
    setPermDoc(doc);
    setModalScope(doc.access_scope);
    setSelectedUserIds([]);
  };

  const savePermissions = async () => {
    if (!permDoc) return;
    await api.updateDocumentPermissions(
      permDoc.id,
      modalScope,
      selectedUserIds.map((uid) => ({ user_id: uid, permission: "read" }))
    );
    setPermDoc(null);
    await loadData();
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Document Vault</h1>
          <p className="text-sm text-slate-400">
            Upload PDF, DOCX, TXT, or Markdown files and manage document-level access permissions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={accessScope}
            onChange={(e) => setAccessScope(e.target.value as "organization" | "restricted")}
            className="rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-xs text-slate-200"
          >
            <option value="organization">Access: Whole Organisation</option>
            <option value="restricted">Access: Restricted (ACL Only)</option>
          </select>

          <label className="cursor-pointer inline-flex items-center gap-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-sm font-semibold text-white transition">
            <UploadCloud className="w-4 h-4" />
            {uploading ? "Ingesting..." : "Upload Document"}
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.markdown"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-950/50 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400 text-xs uppercase border-b border-slate-800">
            <tr>
              <th className="px-4 py-3">Document</th>
              <th className="px-4 py-3">Access Scope</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Chunks</th>
              <th className="px-4 py-3">Version</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-slate-800/40">
                <td className="px-4 py-3.5 font-medium text-white flex items-center gap-2.5">
                  <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                  <span className="truncate max-w-xs">{doc.filename}</span>
                </td>
                <td className="px-4 py-3.5">
                  {doc.access_scope === "restricted" ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/30 px-2.5 py-0.5 text-xs text-amber-300">
                      <Lock className="w-3 h-3" /> Restricted
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 text-xs text-emerald-300">
                      <Globe className="w-3 h-3" /> Organisation
                    </span>
                  )}
                </td>
                <td className="px-4 py-3.5">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      doc.status === "indexed"
                        ? "bg-emerald-500/15 text-emerald-300"
                        : doc.status === "failed"
                        ? "bg-rose-500/15 text-rose-300"
                        : "bg-sky-500/15 text-sky-300"
                    }`}
                  >
                    {doc.status}
                  </span>
                </td>
                <td className="px-4 py-3.5 text-slate-300">{doc.chunk_count}</td>
                <td className="px-4 py-3.5 text-slate-400">v{doc.version}</td>
                <td className="px-4 py-3.5 text-right space-x-2">
                  <button
                    onClick={() => openPermModal(doc)}
                    title="Manage Permissions"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-slate-800"
                  >
                    <Shield className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleReindex(doc.id)}
                    title="Re-index Document"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-sky-400 hover:bg-slate-800"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    title="Delete Document"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                  No documents indexed yet. Upload a PDF, DOCX, TXT, or Markdown file above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Document Permissions Modal */}
      {permDoc && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-700 p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white">
              Access Control: {permDoc.filename}
            </h3>
            <div className="space-y-2">
              <label className="text-xs text-slate-400">Visibility Scope</label>
              <select
                value={modalScope}
                onChange={(e) => setModalScope(e.target.value as "organization" | "restricted")}
                className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-white"
              >
                <option value="organization">All Workspace Members</option>
                <option value="restricted">Restricted (Admins + Granted Users Only)</option>
              </select>
            </div>

            {modalScope === "restricted" && (
              <div className="space-y-2">
                <div className="text-xs text-slate-400">Grant Read Access to Specific Members:</div>
                <div className="max-h-40 overflow-y-auto space-y-1.5 border border-slate-800 rounded-lg p-2.5 bg-slate-950">
                  {members.map((m) => (
                    <label key={m.user_id} className="flex items-center gap-2 text-xs text-slate-200">
                      <input
                        type="checkbox"
                        checked={selectedUserIds.includes(m.user_id)}
                        onChange={(e) =>
                          setSelectedUserIds((prev) =>
                            e.target.checked
                              ? [...prev, m.user_id]
                              : prev.filter((id) => id !== m.user_id)
                          )
                        }
                      />
                      <span>
                        {m.email} ({m.role})
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setPermDoc(null)}
                className="px-4 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={savePermissions}
                className="px-4 py-2 rounded-lg text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white"
              >
                Save Permissions
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
