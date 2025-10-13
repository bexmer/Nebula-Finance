import { useState, useEffect, useMemo } from "react";
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
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"goal" | "debt">("goal");
  const [selectedItem, setSelectedItem] = useState<GoalData | DebtData | null>(
    null
  );

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [goalsRes, debtsRes] = await Promise.all([
        axios.get("http://127.0.0.1:8000/api/goals"),
        axios.get("http://127.0.0.1:8000/api/debts"),
      ]);
      setGoals(
        goalsRes.data.map((goal: any) => ({
          id: goal.id,
          name: goal.name,
          current_amount: goal.current_amount ?? 0,
          target_amount: goal.target_amount ?? 0,
          percentage: goal.percentage ?? goal.completion_percentage ?? goal.progress ?? 0,
        }))
      );
      setDebts(
        debtsRes.data.map((debt: any) => ({
          ...debt,
          minimum_payment: debt.minimum_payment ?? 0,
          interest_rate: debt.interest_rate ?? 0,
          current_balance: debt.current_balance ?? 0,
          total_amount: debt.total_amount ?? 0,
          percentage:
            debt.percentage ?? debt.completion_percentage ?? debt.progress ?? 0,
        }))
      );
    } catch (error) {
      console.error("Error al obtener datos:", error);
      setError("No pudimos cargar tus metas y deudas. Inténtalo nuevamente.");
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

  const goalsSummary = useMemo(() => {
    const totalTarget = goals.reduce((acc, goal) => acc + goal.target_amount, 0);
    const totalCurrent = goals.reduce((acc, goal) => acc + goal.current_amount, 0);
    const progress = totalTarget > 0 ? (totalCurrent / totalTarget) * 100 : 0;
    const topGoal = goals
      .slice()
      .sort((a, b) => b.percentage - a.percentage)[0];

    return {
      count: goals.length,
      totalTarget,
      totalCurrent,
      progress,
      topGoal,
    };
  }, [goals]);

  const debtsSummary = useMemo(() => {
    const totalDebt = debts.reduce((acc, debt) => acc + debt.total_amount, 0);
    const totalBalance = debts.reduce(
      (acc, debt) => acc + debt.current_balance,
      0
    );
    const paid = totalDebt - totalBalance;
    const coverage = totalDebt > 0 ? (paid / totalDebt) * 100 : 0;
    const highestPayment = debts
      .slice()
      .sort((a, b) => b.minimum_payment - a.minimum_payment)[0];

    return {
      count: debts.length,
      totalDebt,
      totalBalance,
      paid,
      coverage,
      highestPayment,
    };
  }, [debts]);

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency: "MXN",
      minimumFractionDigits: 2,
    }).format(value || 0);

  return (
    <div className="space-y-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Metas y Deudas</h1>
          <p className="text-sm text-slate-400">
            Controla tus objetivos financieros y mantén al día los compromisos de pago.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleOpenModal("goal", null)}
            className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-sky-500"
          >
            Añadir meta
          </button>
          <button
            onClick={() => handleOpenModal("debt", null)}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500"
          >
            Añadir deuda
          </button>
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Metas activas</p>
          <p className="mt-2 text-3xl font-semibold text-white">{goalsSummary.count}</p>
          <p className="mt-1 text-xs text-slate-400">
            {goalsSummary.count === 0
              ? "Comienza creando tu primera meta"
              : `${goalsSummary.progress.toFixed(1)}% del objetivo global cubierto`}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Ahorro acumulado</p>
          <p className="mt-2 text-3xl font-semibold text-white">
            {formatCurrency(goalsSummary.totalCurrent)}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Meta conjunta: {formatCurrency(goalsSummary.totalTarget)}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Deudas activas</p>
          <p className="mt-2 text-3xl font-semibold text-white">{debtsSummary.count}</p>
          <p className="mt-1 text-xs text-slate-400">
            Cobertura actual: {debtsSummary.coverage.toFixed(1)}%
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Saldo pendiente</p>
          <p className="mt-2 text-3xl font-semibold text-white">
            {formatCurrency(debtsSummary.totalBalance)}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Pagado a la fecha: {formatCurrency(debtsSummary.paid)}
          </p>
        </article>
      </section>

      <div className="flex flex-col gap-6 lg:flex-row">
        <section className="flex-1 space-y-6">
          <div className="border-b border-slate-800">
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
            <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-400">
              Cargando tus registros...
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-200">
              {error}
            </div>
          ) : activeTab === "goals" ? (
            goals.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {goals.map((g) => (
                  <GoalProgressCard
                    key={g.id}
                    goal={g}
                    onEdit={() => handleOpenModal("goal", g)}
                    onDelete={() => handleDelete("goal", g.id)}
                  />
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-400">
                Aún no tienes metas registradas. Agrega tu primera meta para comenzar a monitorear tu progreso.
              </div>
            )
          ) : debts.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2">
              {debts.map((d) => (
                <DebtProgressCard
                  key={d.id}
                  debt={d}
                  onEdit={() => handleOpenModal("debt", d)}
                  onDelete={() => handleDelete("debt", d.id)}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-400">
              No tienes deudas activas. Mantente así registrando tus pagos a tiempo.
            </div>
          )}
        </section>

        <aside className="w-full max-w-xl space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900/80 to-sky-900/40 p-6 shadow">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
              Panorama de metas
            </h3>
            <p className="mt-3 text-2xl font-semibold text-white">
              {goalsSummary.topGoal ? goalsSummary.topGoal.name : "Sin metas"}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              {goalsSummary.topGoal
                ? `${goalsSummary.topGoal.percentage.toFixed(1)}% completado`
                : "Añade una meta para comenzar"}
            </p>
            <div className="mt-4 space-y-2 text-xs text-slate-300">
              <p>
                Aportado: {formatCurrency(goalsSummary.totalCurrent)} | Restante: {formatCurrency(
                  Math.max(goalsSummary.totalTarget - goalsSummary.totalCurrent, 0)
                )}
              </p>
              <p>
                Ritmo sugerido: {(
                  goalsSummary.totalTarget > 0
                    ? goalsSummary.totalTarget / Math.max(goalsSummary.count, 1)
                    : 0
                ).toLocaleString("es-MX", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })} por meta
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
              Próximo pago recomendado
            </h3>
            {debtsSummary.highestPayment ? (
              <div className="mt-3 space-y-2 text-sm text-slate-200">
                <p className="text-lg font-semibold text-white">
                  {debtsSummary.highestPayment.name}
                </p>
                <p className="text-sm text-slate-400">
                  Pago mínimo: {formatCurrency(debtsSummary.highestPayment.minimum_payment)}
                </p>
                <p className="text-sm text-slate-400">
                  Saldo restante: {formatCurrency(debtsSummary.highestPayment.current_balance)}
                </p>
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-400">
                Registra tus deudas para recibir recordatorios de seguimiento.
              </p>
            )}
          </div>
        </aside>
      </div>

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
