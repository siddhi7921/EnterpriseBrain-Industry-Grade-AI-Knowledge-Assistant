import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { OrganizationResponse, UserResponse } from "../types/api";

interface AuthContextValue {
  user: UserResponse | null;
  organizations: OrganizationResponse[];
  activeOrg: OrganizationResponse | null;
  loading: boolean;
  setActiveOrgId: (orgId: string) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, orgName?: string) => Promise<void>;
  logout: () => void;
  refreshWorkspaces: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationResponse[]>([]);
  const [activeOrgId, setActiveOrgIdState] = useState<string | null>(
    localStorage.getItem("eb_active_org_id")
  );
  const [loading, setLoading] = useState(true);

  const refreshWorkspaces = async () => {
    const orgs = await api.listOrganizations();
    setOrganizations(orgs);
    if (orgs.length > 0) {
      const stillValid = orgs.some((o) => o.id === activeOrgId);
      const chosen = stillValid && activeOrgId ? activeOrgId : orgs[0].id;
      setActiveOrgIdState(chosen);
      localStorage.setItem("eb_active_org_id", chosen);
    } else {
      setActiveOrgIdState(null);
      localStorage.removeItem("eb_active_org_id");
    }
  };

  const bootstrap = async () => {
    const token = localStorage.getItem("eb_access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const me = await api.me();
      setUser(me);
      await refreshWorkspaces();
    } catch {
      localStorage.removeItem("eb_access_token");
      localStorage.removeItem("eb_refresh_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    bootstrap();
  }, []);

  const login = async (email: string, password: string) => {
    const tokens = await api.login(email, password);
    localStorage.setItem("eb_access_token", tokens.access_token);
    localStorage.setItem("eb_refresh_token", tokens.refresh_token);
    const me = await api.me();
    setUser(me);
    await refreshWorkspaces();
  };

  const register = async (email: string, password: string, orgName?: string) => {
    const tokens = await api.register(email, password, orgName);
    localStorage.setItem("eb_access_token", tokens.access_token);
    localStorage.setItem("eb_refresh_token", tokens.refresh_token);
    const me = await api.me();
    setUser(me);
    await refreshWorkspaces();
  };

  const logout = () => {
    localStorage.removeItem("eb_access_token");
    localStorage.removeItem("eb_refresh_token");
    localStorage.removeItem("eb_active_org_id");
    setUser(null);
    setOrganizations([]);
    setActiveOrgIdState(null);
  };

  const setActiveOrgId = (orgId: string) => {
    setActiveOrgIdState(orgId);
    localStorage.setItem("eb_active_org_id", orgId);
  };

  const activeOrg = organizations.find((o) => o.id === activeOrgId) || organizations[0] || null;

  return (
    <AuthContext.Provider
      value={{
        user,
        organizations,
        activeOrg,
        loading,
        setActiveOrgId,
        login,
        register,
        logout,
        refreshWorkspaces,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
