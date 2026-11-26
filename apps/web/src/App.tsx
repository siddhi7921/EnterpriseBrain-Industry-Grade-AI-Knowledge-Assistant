import React, { useState } from "react";
import { Layout, type NavTab } from "./components/Layout";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { AuthPage } from "./pages/AuthPage";
import { ChatPage } from "./pages/ChatPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { TeamPage } from "./pages/TeamPage";

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>("chat");

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-400 text-sm">
        Initializing EnterpriseBrain...
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return (
    <Layout activeTab={activeTab} onSelectTab={setActiveTab}>
      {activeTab === "chat" && <ChatPage />}
      {activeTab === "documents" && <DocumentsPage />}
      {activeTab === "team" && <TeamPage />}
      {activeTab === "evaluation" && <EvaluationPage />}
      {activeTab === "analytics" && <AnalyticsPage />}
    </Layout>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
