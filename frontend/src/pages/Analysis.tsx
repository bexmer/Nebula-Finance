import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Bar,
  Line,
} from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Tooltip,
  Legend
);

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

const MONTH_OPTIONS = [
  { value: 1, label: "Ene" },
  { value: 2, label: "Feb" },
  { value: 3, label: "Mar" },
  { value: 4, label: "Abr" },
  { value: 5, label: "May" },
  { value: 6, label: "Jun" },
  { value: 7, label: "Jul" },
  { value: 8, label: "Ago" },
  { value: 9, label: "Sep" },
  { value: 10, label: "Oct" },
  { value: 11, label: "Nov" },
  { value: 12, label: "Dic" },
] as const;

type TabKey = "expenses" | "budget" | "projection";

interface MonthHeader {
  number: number;
  label: string;
}

interface AnnualExpenseRow {
  category: string;
  values: number[];
  total: number;
}

interface AnnualExpenseReport {
  months: MonthHeader[];
  rows: AnnualExpenseRow[];
  monthly_totals: number[];
  grand_total: number;
}

interface BudgetRow {
  name: string;
  budgeted: number;
  actual: number;
  difference: number;
  compliance: number | null;
  ideal_percent: number | null;
}

interface BudgetAnalysis {
  rows: BudgetRow[];
  total_budgeted: number;
  total_actual: number;
  total_difference: number;
  total_compliance: number | null;
}

interface ProjectionPoint {
  label: string;
  balance: number;
}

interface CashFlowProjection {
  starting_balance: number;
  average_monthly_flow: number;
  projection_months: number;
  points: ProjectionPoint[];
}

interface AnalysisResponse {
  year: number;
  months: number[];
  annual_expense_report: AnnualExpenseReport;
  budget_analysis: BudgetAnalysis;
  cash_flow_projection: CashFlowProjection;
}

const years = Array.from({ length: 10 }, (_, index) => new Date().getFullYear() - index);

const paramsSerializer = (params: Record<string, unknown>) => {
  const searchParams = new URLSearchParams();
  if (params.year) {
    searchParams.append("year", String(params.year));
  }
  if (params.projectionMonths) {
    searchParams.append("projectionMonths", String(params.projectionMonths));
  }
  if (Array.isArray(params.months)) {
    params.months.forEach((month) => {
      searchParams.append("months", String(month));
    });
  }
  return searchParams.toString();
};

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    minimumFractionDigits: 2,
  }).format(value || 0);

const formatPercent = (value: number | null | undefined) =>
  typeof value === "number" && Number.isFinite(value)
    ? `${value.toFixed(1)}%`
    : "-";

export function Analysis() {
  const [activeTab, setActiveTab] = useState<TabKey>("expenses");
  const [year, setYear] = useState(() => new Date().getFullYear());
  const [selectedMonths, setSelectedMonths] = useState<number[]>(() =>
    MONTH_OPTIONS.map((month) => month.value)
  );
  const [projectionMonths, setProjectionMonths] = useState(12);
  const [analysisData, setAnalysisData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allMonthsSelected = selectedMonths.length === MONTH_OPTIONS.length;

  useEffect(() => {
    const controller = new AbortController();

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const params: Record<string, unknown> = {
          year,
          projectionMonths,
        };
        if (!allMonthsSelected) {
          params.months = selectedMonths;
        }

        const response = await axios.get<AnalysisResponse>(
          `${API_BASE_URL}/api/analysis`,
          {
            params,
            paramsSerializer,
            signal: controller.signal,
          }
        );
        setAnalysisData(response.data);
      } catch (err) {
        if (axios.isCancel && axios.isCancel(err)) {
          return;
        }
        console.error("Error al cargar análisis", err);
        setError("No fue posible obtener los datos de análisis. Intenta nuevamente.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    return () => controller.abort();
  }, [year, selectedMonths, projectionMonths, allMonthsSelected]);

  const toggleMonth = (value: number) => {
    setSelectedMonths((prev) => {
      const exists = prev.includes(value);
      if (exists) {
        return prev.filter((month) => month !== value);
      }
      return [...prev, value].sort((a, b) => a - b);
    });
  };

  const handleSelectAllMonths = () => {
    setSelectedMonths(MONTH_OPTIONS.map((month) => month.value));
  };

  const budgetChartData = useMemo(() => {
    if (!analysisData) return null;
    const labels = analysisData.budget_analysis.rows.map((row) => row.name);
    return {
      labels,
      datasets: [
        {
          label: "Presupuestado",
          data: analysisData.budget_analysis.rows.map((row) => row.budgeted),
          backgroundColor: "rgba(59, 130, 246, 0.6)",
          borderRadius: 8,
        },
        {
          label: "Gasto real",
          data: analysisData.budget_analysis.rows.map((row) => row.actual),
          backgroundColor: "rgba(14, 165, 233, 0.6)",
          borderRadius: 8,
        },
      ],
    };
  }, [analysisData]);

  const budgetDistributionData = useMemo(() => {
    if (!analysisData) return null;
    const totalActual = analysisData.budget_analysis.total_actual || 0;
    const labels = analysisData.budget_analysis.rows.map((row) => row.name);
    const values = analysisData.budget_analysis.rows.map((row) =>
      totalActual ? (row.actual / totalActual) * 100 : 0
    );
    return {
      labels,
      datasets: [
        {
          label: "% del gasto real",
          data: values,
          backgroundColor: "rgba(16, 185, 129, 0.65)",
          borderRadius: 8,
        },
      ],
    };
  }, [analysisData]);

  const projectionChartData = useMemo(() => {
    if (!analysisData) return null;
    return {
      labels: analysisData.cash_flow_projection.points.map((point) => point.label),
      datasets: [
        {
          label: "Saldo proyectado",
          data: analysisData.cash_flow_projection.points.map((point) => point.balance),
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56, 189, 248, 0.25)",
          tension: 0.25,
          fill: true,
        },
      ],
    };
  }, [analysisData]);

  const barOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#cbd5f5" },
        },
      },
      scales: {
        x: {
          ticks: { color: "#cbd5f5" },
          grid: { color: "rgba(148, 163, 184, 0.15)" },
        },
        y: {
          ticks: { color: "#cbd5f5" },
          grid: { color: "rgba(148, 163, 184, 0.15)" },
        },
      },
    }),
    []
  );

  const percentBarOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: (context: any) => `${context.raw.toFixed(1)}%`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#cbd5f5" },
          grid: { color: "rgba(148, 163, 184, 0.15)" },
        },
        y: {
          ticks: {
            color: "#cbd5f5",
            callback: (value: string | number) => `${value}%`,
          },
          beginAtZero: true,
          max: 100,
          grid: { color: "rgba(148, 163, 184, 0.15)" },
        },
      },
    }),
    []
  );

  const lineOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#cbd5f5" },
        },
      },
      scales: {
        x: {
          ticks: { color: "#cbd5f5" },
          grid: { color: "rgba(148, 163, 184, 0.15)" },
        },
        y: {
          ticks: { color: "#cbd5f5" },
          grid: { color: "rgba(148, 163, 184, 0.15)" },
        },
      },
    }),
    []
  );

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Análisis financiero</h1>
          <p className="text-sm text-slate-400">
            Visualiza tendencias anuales, compara tu presupuesto y proyecta tu flujo de efectivo.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={year}
            onChange={(event) => setYear(Number(event.target.value))}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white shadow"
          >
            {years.map((optionYear) => (
              <option key={optionYear} value={optionYear}>
                {optionYear}
              </option>
            ))}
          </select>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleSelectAllMonths}
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                allMonthsSelected
                  ? "bg-sky-600 text-white"
                  : "border border-slate-700 bg-slate-900 text-slate-300 hover:border-sky-500"
              }`}
            >
              Todos
            </button>
            {MONTH_OPTIONS.map((month) => {
              const isActive = selectedMonths.includes(month.value);
              return (
                <button
                  key={month.value}
                  onClick={() => toggleMonth(month.value)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                    isActive
                      ? "bg-slate-100 text-slate-900"
                      : "border border-slate-700 bg-slate-900 text-slate-300 hover:border-sky-500"
                  }`}
                >
                  {month.label}
                </button>
              );
            })}
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200">
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Proyección
            </span>
            <select
              value={projectionMonths}
              onChange={(event) => setProjectionMonths(Number(event.target.value))}
              className="bg-transparent text-sm focus:outline-none"
            >
              {[6, 12, 18, 24].map((option) => (
                <option key={option} value={option}>
                  {option} meses
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <nav className="flex flex-wrap gap-2" aria-label="Tabs">
        {[
          { key: "expenses", label: "Reporte anual de gastos" },
          { key: "budget", label: "Análisis de presupuesto" },
          { key: "projection", label: "Proyección de flujo de efectivo" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as TabKey)}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              activeTab === tab.key
                ? "bg-sky-600 text-white"
                : "border border-slate-700 bg-slate-900 text-slate-300 hover:border-sky-500"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {loading ? (
        <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/60 p-6 text-sm text-slate-300">
          Cargando análisis financiero...
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-100">
          {error}
        </div>
      ) : analysisData ? (
        <section className="space-y-6">
          {activeTab === "expenses" && (
            <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60">
              <header className="border-b border-slate-800 bg-slate-900/80 px-6 py-4">
                <h2 className="text-lg font-semibold text-white">
                  Reporte anual de gastos por categoría
                </h2>
                <p className="text-xs text-slate-400">
                  Suma los gastos reales por categoría a lo largo del periodo seleccionado.
                </p>
              </header>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-800 text-sm">
                  <thead className="bg-slate-900/80 text-slate-300">
                    <tr>
                      <th className="px-6 py-3 text-left font-semibold">Categoría</th>
                      {analysisData.annual_expense_report.months.map((month) => (
                        <th key={month.number} className="px-4 py-3 text-right font-semibold">
                          {month.label}
                        </th>
                      ))}
                      <th className="px-6 py-3 text-right font-semibold">Total anual</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {analysisData.annual_expense_report.rows.length > 0 ? (
                      analysisData.annual_expense_report.rows.map((row) => (
                        <tr key={row.category} className="text-slate-200">
                          <td className="px-6 py-3 text-left font-medium text-white">
                            {row.category}
                          </td>
                          {row.values.map((value, index) => (
                            <td key={`${row.category}-${index}`} className="px-4 py-3 text-right">
                              {value ? formatCurrency(value) : "-"}
                            </td>
                          ))}
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            {formatCurrency(row.total)}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={analysisData.annual_expense_report.months.length + 2}
                          className="px-6 py-6 text-center text-slate-400"
                        >
                          No se registraron gastos en el periodo seleccionado.
                        </td>
                      </tr>
                    )}
                  </tbody>
                  <tfoot className="bg-slate-900/80 text-slate-200">
                    <tr>
                      <th className="px-6 py-3 text-left font-semibold">Total mensual</th>
                      {analysisData.annual_expense_report.monthly_totals.map((total, index) => (
                        <th key={`total-${index}`} className="px-4 py-3 text-right font-semibold">
                          {total ? formatCurrency(total) : "-"}
                        </th>
                      ))}
                      <th className="px-6 py-3 text-right text-sky-300">
                        {formatCurrency(analysisData.annual_expense_report.grand_total)}
                      </th>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}

          {activeTab === "budget" && (
            <div className="space-y-6">
              <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60">
                <header className="border-b border-slate-800 bg-slate-900/80 px-6 py-4">
                  <h2 className="text-lg font-semibold text-white">Comparativa anual: Presupuesto vs. Real por reglas</h2>
                  <p className="text-xs text-slate-400">
                    Contrasta lo asignado en tu presupuesto con lo ejecutado durante el periodo.
                  </p>
                </header>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-800 text-sm">
                    <thead className="bg-slate-900/80 text-slate-300">
                      <tr>
                        <th className="px-6 py-3 text-left font-semibold">Regla</th>
                        <th className="px-4 py-3 text-right font-semibold">Presupuesto (Anual)</th>
                        <th className="px-4 py-3 text-right font-semibold">Gasto real (Anual)</th>
                        <th className="px-4 py-3 text-right font-semibold">Diferencia</th>
                        <th className="px-4 py-3 text-right font-semibold">Cumplimiento</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {analysisData.budget_analysis.rows.length > 0 ? (
                        analysisData.budget_analysis.rows.map((row) => {
                          const differenceClass =
                            row.difference > 0
                              ? "text-emerald-300"
                              : row.difference < 0
                              ? "text-rose-300"
                              : "text-slate-200";
                          return (
                            <tr key={row.name} className="text-slate-200">
                              <td className="px-6 py-3 text-left font-medium text-white">{row.name}</td>
                              <td className="px-4 py-3 text-right">{formatCurrency(row.budgeted)}</td>
                              <td className="px-4 py-3 text-right">{formatCurrency(row.actual)}</td>
                              <td className={`px-4 py-3 text-right font-semibold ${differenceClass}`}>
                                {formatCurrency(row.difference)}
                              </td>
                              <td className="px-4 py-3 text-right">{formatPercent(row.compliance)}</td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={5} className="px-6 py-6 text-center text-slate-400">
                            Aún no hay presupuesto registrado para este periodo.
                          </td>
                        </tr>
                      )}
                    </tbody>
                    <tfoot className="bg-slate-900/80 text-slate-200">
                      <tr>
                        <th className="px-6 py-3 text-left font-semibold">Totales</th>
                        <th className="px-4 py-3 text-right font-semibold">
                          {formatCurrency(analysisData.budget_analysis.total_budgeted)}
                        </th>
                        <th className="px-4 py-3 text-right font-semibold">
                          {formatCurrency(analysisData.budget_analysis.total_actual)}
                        </th>
                        <th
                          className={`px-4 py-3 text-right font-semibold ${
                            analysisData.budget_analysis.total_difference > 0
                              ? "text-emerald-300"
                              : analysisData.budget_analysis.total_difference < 0
                              ? "text-rose-300"
                              : "text-slate-200"
                          }`}
                        >
                          {formatCurrency(analysisData.budget_analysis.total_difference)}
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-sky-300">
                          {formatPercent(analysisData.budget_analysis.total_compliance)}
                        </th>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
                  <h3 className="text-base font-semibold text-white">
                    Gasto real vs. presupuestado
                  </h3>
                  <div className="mt-4 h-72">
                    {budgetChartData ? <Bar data={budgetChartData} options={barOptions} /> : null}
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
                  <h3 className="text-base font-semibold text-white">
                    Distribución del gasto real por regla
                  </h3>
                  <div className="mt-4 h-72">
                    {budgetDistributionData ? (
                      <Bar data={budgetDistributionData} options={percentBarOptions} />
                    ) : null}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "projection" && (
            <div className="grid gap-6 lg:grid-cols-[2fr,3fr]">
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
                  <h3 className="text-base font-semibold text-white">Resumen de proyección</h3>
                  <dl className="mt-4 space-y-3 text-sm text-slate-300">
                    <div className="flex items-center justify-between">
                      <dt className="text-slate-400">Saldo actual proyectado</dt>
                      <dd className="font-semibold text-white">
                        {formatCurrency(analysisData.cash_flow_projection.starting_balance)}
                      </dd>
                    </div>
                    <div className="flex items-center justify-between">
                      <dt className="text-slate-400">Flujo mensual promedio</dt>
                      <dd
                        className={`font-semibold ${
                          analysisData.cash_flow_projection.average_monthly_flow >= 0
                            ? "text-emerald-300"
                            : "text-rose-300"
                        }`}
                      >
                        {formatCurrency(
                          analysisData.cash_flow_projection.average_monthly_flow
                        )}
                      </dd>
                    </div>
                    <div className="flex items-center justify-between">
                      <dt className="text-slate-400">Horizonte considerado</dt>
                      <dd className="font-semibold text-white">
                        {analysisData.cash_flow_projection.projection_months} meses
                      </dd>
                    </div>
                  </dl>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4 text-xs text-slate-300">
                  La proyección utiliza el promedio mensual de tu flujo de efectivo
                  durante el periodo seleccionado. Ajusta los meses analizados para
                  observar distintos escenarios.
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
                <h3 className="text-base font-semibold text-white">
                  Proyección de saldo total de cuentas
                </h3>
                <div className="mt-4 h-96">
                  {projectionChartData ? <Line data={projectionChartData} options={lineOptions} /> : null}
                </div>
              </div>
            </div>
          )}
        </section>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/60 p-6 text-sm text-slate-300">
          Aún no hay información disponible para mostrar.
        </div>
      )}
    </div>
  );
}
