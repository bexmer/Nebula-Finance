import { useEffect } from "react";
import { Command } from "@tauri-apps/plugin-shell";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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
    // La lógica para iniciar el backend se queda aquí,
    // ya que la aplicación principal es responsable de ello.
    const startBackend = async () => {
      const command = Command.sidecar("run-backend");
      await command.spawn();
    };
    startBackend();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/accounts" element={<Accounts />} />
          <Route path="/budget" element={<Budget />} />
          <Route path="/goals-and-debts" element={<GoalsAndDebts />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
