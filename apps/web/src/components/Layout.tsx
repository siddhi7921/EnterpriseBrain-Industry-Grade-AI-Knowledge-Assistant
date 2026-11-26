import React from "react";
import {
  BarChart3,
  BrainCircuit,
  FileText,
  FlaskConical,
  LogOut,
  MessageSquare,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export type NavTab = "chat" | "documents" | "team" | "evaluation" | "analytics";

interface LayoutProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ activeTab, onSelectTab, children }) => {
  const { user, organizations, activeOrg, setActiveOrgId, logout } = useAuth();

  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: "chat", label: "Knowledge Chat", icon: <MessageSquare className="w-4 h-4" /> },
    { id: "documents", label: "Document Vault", icon: <FileText className="w-4 h-4" /> },
    { id: "team", label: "Workspaces & RBAC", icon: <Users className="w-4 h-4" /> },
    { id: "evaluation", label: "ML Evaluation Lab", icon: <FlaskConical className="w-4 h-4" /> },
    { id: "analytics", label: "Analytics & Audit", icon: <BarChart3 className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/70 flex flex-col justify-between p-4">
        <div className="space-y-6">
          <div className="flex items-center gap-2.5 px-2">
            <div className="p-2 rounded-lg bg-indigo-600/20 border border-indigo-500/40 text-indigo-400">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <div className="font-semibold tracking-tight text-white">EnterpriseBrain</div>
              <div className="text-[11px] text-slate-400">Permission-Aware RAG</div>
            </div>
          </div>

          {/* Active Workspace Switcher */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium uppercase tracking-wider text-slate-400 px-1">
              Active Workspace
            </label>
            <select
              value={activeOrg?.id || ""}
              onChange={(e) => setActiveOrgId(e.target.value)}
              className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name} ({org.role})
                </option>
              ))}
            </select>
          </div>

          {/* Navigation */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                    active
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                  }`}
                >
                  {item.icon}
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User Footer */}
        <div className="pt-4 border-t border-slate-800 space-y-3">
          <div className="flex items-center gap-2 px-2 text-xs text-emerald-400">
            <ShieldCheck className="w-4 h-4 shrink-0" />
            <span>SQL Tenant Isolation Active</span>
          </div>
          <div className="flex items-center justify-between px-2">
            <div className="truncate">
              <div className="text-xs font-medium text-slate-200 truncate">{user?.email}</div>
              <div className="text-[11px] text-slate-400 capitalize">
                Role: {activeOrg?.role || "member"}
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign out"
              className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
};
