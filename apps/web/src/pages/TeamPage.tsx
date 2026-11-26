import React, { useEffect, useState } from "react";
import { Building2, UserPlus } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import type { MemberResponse } from "../types/api";

export const TeamPage: React.FC = () => {
  const { activeOrg, refreshWorkspaces } = useAuth();
  const [members, setMembers] = useState<MemberResponse[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"member" | "admin" | "owner">("member");
  const [newOrgName, setNewOrgName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadMembers = async () => {
    if (!activeOrg) return;
    const list = await api.listMembers(activeOrg.id);
    setMembers(list);
  };

  useEffect(() => {
    loadMembers().catch(() => {});
  }, [activeOrg?.id]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrg || !inviteEmail.trim()) return;
    setError(null);
    setMessage(null);
    try {
      await api.addMember(activeOrg.id, inviteEmail.trim(), inviteRole);
      setInviteEmail("");
      setMessage("Member added to workspace.");
      await loadMembers();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add member");
    }
  };

  const handleRoleChange = async (userId: string, role: "member" | "admin" | "owner") => {
    if (!activeOrg) return;
    setError(null);
    try {
      await api.updateMemberRole(activeOrg.id, userId, role);
      await loadMembers();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update role");
    }
  };

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    await api.createOrganization(newOrgName.trim());
    setNewOrgName("");
    await refreshWorkspaces();
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Workspaces & Role-Based Access Control</h1>
        <p className="text-sm text-slate-400">
          Manage multi-tenant organisation isolation, member invitations, and workspace roles.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-950/50 px-4 py-2.5 text-sm text-rose-300">
          {error}
        </div>
      )}
      {message && (
        <div className="rounded-lg border border-emerald-500/40 bg-emerald-950/50 px-4 py-2.5 text-sm text-emerald-300">
          {message}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {/* Invite Member */}
        <form
          onSubmit={handleInvite}
          className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4"
        >
          <div className="flex items-center gap-2 text-white font-semibold">
            <UserPlus className="w-4 h-4 text-indigo-400" />
            Add Member to {activeOrg?.name}
          </div>
          <input
            type="email"
            required
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="colleague@company.com"
            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-white"
          />
          <div className="flex gap-2">
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as "member" | "admin" | "owner")}
              className="rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-slate-200"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
              <option value="owner">Owner</option>
            </select>
            <button
              type="submit"
              className="flex-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 py-2 text-sm font-semibold text-white"
            >
              Add Member
            </button>
          </div>
        </form>

        {/* Create New Tenant Workspace */}
        <form
          onSubmit={handleCreateOrg}
          className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4"
        >
          <div className="flex items-center gap-2 text-white font-semibold">
            <Building2 className="w-4 h-4 text-emerald-400" />
            Create Isolated Organisation Workspace
          </div>
          <input
            type="text"
            required
            value={newOrgName}
            onChange={(e) => setNewOrgName(e.target.value)}
            placeholder="New Subsidiary / Client Org"
            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-white"
          />
          <button
            type="submit"
            className="w-full rounded-lg bg-emerald-600 hover:bg-emerald-500 py-2 text-sm font-semibold text-white"
          >
            Create Workspace
          </button>
        </form>
      </div>

      {/* Members Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400 text-xs uppercase border-b border-slate-800">
            <tr>
              <th className="px-4 py-3">User Email</th>
              <th className="px-4 py-3">User ID</th>
              <th className="px-4 py-3">Workspace Role</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {members.map((m) => (
              <tr key={m.user_id}>
                <td className="px-4 py-3 text-white font-medium">{m.email}</td>
                <td className="px-4 py-3 text-xs text-slate-500 font-mono">{m.user_id}</td>
                <td className="px-4 py-3">
                  <select
                    value={m.role}
                    onChange={(e) =>
                      handleRoleChange(m.user_id, e.target.value as "member" | "admin" | "owner")
                    }
                    className="rounded-lg bg-slate-950 border border-slate-700 px-2.5 py-1 text-xs text-slate-200"
                  >
                    <option value="member">member</option>
                    <option value="admin">admin</option>
                    <option value="owner">owner</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
