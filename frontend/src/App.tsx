import { useEffect } from "react";
import { Command } from "@tauri-apps/plugin-shell";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
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
    const startBackend = async () => {
      const command = Command.sidecar("run-backend");
      await command.spawn();
    };
    startBackend();
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/accounts" element={<Accounts />} />
          <Route path="/budget" element={<Budget />} />
          <Route path="/dashboard-goals" element={<GoalsAndDebts />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
