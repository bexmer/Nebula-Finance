import { useState, useEffect } from "react";
import axios from "axios";
import { GoalProgressCard } from "../components/GoalProgressCard";
import { DebtProgressCard } from "../components/DebtProgressCard";
import { GoalDebtModal } from "../components/GoalDebtModal";

interface GoalData {
  id: number;
  name: string;
  current_amount: number;
  target_amount: number;
  percentage: number;
}

interface DebtData {
  id: number;
  name: string;
  total_amount: number;
  current_balance: number;
  minimum_payment: number;
  interest_rate: number;
  percentage: number;
}

export function GoalsAndDebts() {
  const [activeTab, setActiveTab] = useState<"goals" | "debts">("goals");
  const [goals, setGoals] = useState<GoalData[]>([]);
  const [debts, setDebts] = useState<DebtData[]>([]);
  const [loading, setLoading] = useState(true);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"goal" | "debt">("goal");
  const [selectedItem, setSelectedItem] = useState<GoalData | DebtData | null>(
    null
  );

  const fetchData = async () => {
    setLoading(true);
    try {
      const [goalsRes, debtsRes] = await Promise.all([
        axios.get("http://127.0.0.1:8000/api/dashboard-goals"),
        axios.get("http://127.0.0.1:8000/api/debts"),
      ]);
      setGoals(goalsRes.data);
      setDebts(debtsRes.data);
    } catch (error) {
      console.error("Error al obtener datos:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenModal = (mode: "goal" | "debt", item: any | null) => {
    setModalMode(mode);
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleSave = () => {
    fetchData();
  };

  const handleDelete = async (type: "goal" | "debt", id: number) => {
    const endpoint = type === "goal" ? "goals" : "debts";
    if (
      window.confirm(
        `¿Estás seguro de que quieres eliminar est${
          type === "goal" ? "a meta" : "a deuda"
        }?`
      )
    ) {
      try {
        await axios.delete(`http://127.0.0.1:8000/api/${endpoint}/${id}`);
        fetchData();
      } catch (error) {
        console.error(`Error al eliminar ${type}:`, error);
      }
    }
  };

  const tabButtonClasses = (tabName: "goals" | "debts") =>
    `px-4 py-2 text-sm font-medium rounded-md transition-colors ${
      activeTab === tabName
        ? "bg-blue-600 text-white"
        : "text-gray-300 hover:bg-gray-700"
    }`;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Metas y Deudas</h1>
        <div className="space-x-4">
          <button
            onClick={() => handleOpenModal("goal", null)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md"
          >
            Añadir Meta
          </button>
          <button
            onClick={() => handleOpenModal("debt", null)}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md"
          >
            Añadir Deuda
          </button>
        </div>
      </div>

      <div className="mb-6 border-b border-gray-700">
        <nav className="flex space-x-2" aria-label="Tabs">
          <button
            className={tabButtonClasses("goals")}
            onClick={() => setActiveTab("goals")}
          >
            Metas
          </button>
          <button
            className={tabButtonClasses("debts")}
            onClick={() => setActiveTab("debts")}
          >
            Deudas
          </button>
        </nav>
      </div>

      {loading ? (
        <p className="text-gray-400">Cargando...</p>
      ) : (
        <div>
          {activeTab === "goals" && (
            <div className="space-y-4">
              {goals.length > 0 ? (
                goals.map((g) => (
                  <GoalProgressCard
                    key={g.id}
                    goal={g}
                    onEdit={() => handleOpenModal("goal", g)}
                    onDelete={() => handleDelete("goal", g.id)}
                  />
                ))
              ) : (
                <p className="text-gray-400">No hay metas activas.</p>
              )}
            </div>
          )}
          {activeTab === "debts" && (
            <div className="space-y-4">
              {debts.length > 0 ? (
                debts.map((d) => (
                  <DebtProgressCard
                    key={d.id}
                    debt={d}
                    onEdit={() => handleOpenModal("debt", d)}
                    onDelete={() => handleDelete("debt", d.id)}
                  />
                ))
              ) : (
                <p className="text-gray-400">No hay deudas activas.</p>
              )}
            </div>
          )}
        </div>
      )}

      <GoalDebtModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        mode={modalMode}
        item={selectedItem}
      />
    </div>
  );
}
