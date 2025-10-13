import { useEffect } from "react";
import { Command } from "@tauri-apps/plugin-shell";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Transactions } from "./pages/Transactions";
import { Accounts } from "./pages/Accounts";
import { Budget } from "./pages/Budget";
import { GoalsAndDebts } from "./pages/GoalsAndDebts";
import { Portfolio } from "./pages/Portfolio";
import { Analysis } from "./pages/Analysis";
import { Settings } from "./pages/Settings";

function App() {
  useEffect(() => {
    const isBrowser = typeof window !== "undefined";
    const hasTauri =
      isBrowser && "__TAURI__" in (window as Window & { __TAURI__?: unknown });
    if (!hasTauri) {
      return;
    }

    const startBackend = async () => {
      try {
        const command = Command.sidecar("run-backend");
        await command.spawn();
      } catch (error) {
        if (import.meta.env.DEV) {
          console.warn("No se pudo iniciar el backend integrado.", error);
        }
      }
    };

    startBackend();
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="accounts" element={<Accounts />} />
          <Route path="budget" element={<Budget />} />
          <Route path="dashboard-goals" element={<GoalsAndDebts />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
