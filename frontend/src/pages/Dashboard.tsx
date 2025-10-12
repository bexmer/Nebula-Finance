import { useState, useEffect } from "react";
import axios from "axios";
import { KpiCard } from "../components/KpiCard";
import { IncomeExpenseChart } from "../components/IncomeExpenseChart";
import { GoalProgressCard } from "../components/GoalProgressCard";

// Define KPI data type (adjust fields as needed based on your API response)
interface KpiData {
  total_balance: number;
  income: number;
  expenses: number;
  net_income: number;
}

// Define ChartData type (adjust fields as needed based on your API response)
interface ChartData {
  labels: string[];
  income_data: number[];
  expense_data: number[];
}

interface GoalData {
  name: string;
  current_amount: number;
  target_amount: number;
  percentage: number;
}

export function Dashboard() {
  const [kpiData, setKpiData] = useState<KpiData | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [goalsData, setGoalsData] = useState<GoalData[] | null>(null); // <-- 3. Nuevo estado

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Pedimos todos los datos del dashboard al mismo tiempo
        const [kpiRes, chartRes, goalsRes] = await Promise.all([
          axios.get("http://127.0.0.1:8000/api/dashboard-kpis"),
          axios.get("http://127.0.0.1:8000/api/charts/income-expense"),
          axios.get("http://127.0.0.1:8000/api/dashboard-goals"), // <-- 4. Nueva petición
        ]);
        setKpiData(kpiRes.data);
        setChartData(chartRes.data);
        setGoalsData(goalsRes.data); // <-- 5. Guardar los datos
      } catch (error) {
        console.error("Error al obtener los datos del dashboard:", error);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-white">Dashboard</h1>

      {/* Sección de KPIs */}
      {!kpiData ? (
        <p>Cargando KPIs...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KpiCard
            title="Balance Total"
            value={kpiData.total_balance.toString()}
          />
          <KpiCard title="Ingresos (Mes)" value={kpiData.income.toString()} />
          <KpiCard title="Gastos (Mes)" value={kpiData.expenses.toString()} />
          <KpiCard
            title="Ahorro Neto (Mes)"
            value={kpiData.net_income.toString()}
          />
        </div>
      )}

      {/* Sección de Gráficos y Metas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {!chartData ? (
            <p>Cargando gráfico...</p>
          ) : (
            <IncomeExpenseChart
              data={{
                labels: chartData.labels,
                income_data: chartData.income_data,
                expense_data: chartData.expense_data,
              }}
            />
          )}
        </div>

        {/* --- 6. NUEVA Sección de Metas --- */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white">
            Metas Financieras
          </h2>
          {!goalsData ? (
            <p>Cargando metas...</p>
          ) : goalsData.length > 0 ? (
            goalsData.map((goal) => (
              <GoalProgressCard key={goal.name} {...goal} />
            ))
          ) : (
            <p className="text-gray-400">No hay metas activas.</p>
          )}
        </div>
      </div>
    </div>
  );
}
