import React, { useState } from "react";
import { BrainCircuit, Lock, Mail, Building2, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { setDemoMode } from "../lib/api";

export const AuthPage: React.FC = () => {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("alice@acme.com");
  const [password, setPassword] = useState("DemoPass123!");
  const [orgName, setOrgName] = useState("Acme Technologies");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, orgName);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-xl bg-indigo-600/20 border border-indigo-500/40 text-indigo-400">
            <BrainCircuit className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold text-white">EnterpriseBrain</h1>
          <p className="text-sm text-slate-400">
            Your organisation&apos;s knowledge, intelligently connected.
          </p>
        </div>

        <div className="grid grid-cols-2 rounded-lg bg-slate-950 p-1 border border-slate-800">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`py-1.5 text-sm font-medium rounded-md transition ${
              mode === "login" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`py-1.5 text-sm font-medium rounded-md transition ${
              mode === "register" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Create Workspace
          </button>
        </div>

        {error && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-950/50 px-3.5 py-2.5 text-sm text-rose-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Organisation Workspace Name
              </label>
              <div className="relative">
                <Building2 className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full rounded-lg bg-slate-950 border border-slate-700 pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  placeholder="Acme Technologies"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Work Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-700 pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                placeholder="alice@acme.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-700 pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-2.5 text-sm font-semibold text-white transition"
          >
            {submitting
              ? "Please wait..."
              : mode === "login"
              ? "Sign In to Workspace"
              : "Create Workspace & Account"}
          </button>

          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-slate-800"></div>
            <span className="flex-shrink mx-3 text-xs text-slate-500 uppercase tracking-wider">or</span>
            <div className="flex-grow border-t border-slate-800"></div>
          </div>

          <button
            type="button"
            onClick={async () => {
              setError(null);
              setSubmitting(true);
              try {
                setDemoMode(true);
                await login("alice@acme.com", "DemoPass123!");
              } catch (err: unknown) {
                setError(err instanceof Error ? err.message : "Failed to load demo");
              } finally {
                setSubmitting(false);
              }
            }}
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 rounded-lg border border-indigo-500/30 bg-indigo-950/40 hover:bg-indigo-900/50 py-2.5 text-sm font-medium text-indigo-300 transition"
          >
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Explore Live Demo Workspace
          </button>
        </form>
      </div>
    </div>
  );
};
