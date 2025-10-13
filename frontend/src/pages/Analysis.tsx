import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

import { API_BASE_URL } from "../utils/api";
import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { useStore } from "../store/useStore";
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

interface MonthMultiSelectProps {
  value: number[];
  onChange: (months: number[]) => void;
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

  const { formatCurrency, formatPercent } = useNumberFormatter();
  const theme = useStore((state) => state.theme);

  const allMonthsSelected =
    selectedMonths.length === 0 || selectedMonths.length === MONTH_OPTIONS.length;

  const chartPalette = useMemo(() => {
    if (typeof window === "undefined") {
      return {
        text: "#0f172a",
        grid: "rgba(100, 116, 139, 0.2)",
        gridStrong: "rgba(100, 116, 139, 0.35)",
      };
    }
    const styles = getComputedStyle(document.documentElement);
    const text = styles.getPropertyValue("--app-chart-text").trim() || "#0f172a";
    const grid = styles.getPropertyValue("--app-chart-grid").trim() || "rgba(100, 116, 139, 0.2)";
    const gridStrong =
      styles.getPropertyValue("--app-chart-grid-strong").trim() || "rgba(100, 116, 139, 0.35)";
    return { text, grid, gridStrong };
  }, [theme]);

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
          `${API_BASE_URL}/analysis`,
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
          labels: { color: chartPalette.text },
        },
      },
      scales: {
        x: {
          ticks: { color: chartPalette.text },
          grid: { color: chartPalette.grid },
        },
        y: {
          ticks: { color: chartPalette.text },
          grid: { color: chartPalette.grid },
        },
      },
    }),
    [chartPalette]
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
          ticks: { color: chartPalette.text },
          grid: { color: chartPalette.grid },
        },
        y: {
          ticks: {
            color: chartPalette.text,
            callback: (value: string | number) => `${value}%`,
          },
          beginAtZero: true,
          max: 100,
          grid: { color: chartPalette.grid },
        },
      },
    }),
    [chartPalette]
  );

  const lineOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: chartPalette.text },
        },
      },
      scales: {
        x: {
          ticks: { color: chartPalette.text },
          grid: { color: chartPalette.grid },
        },
        y: {
          ticks: { color: chartPalette.text },
          grid: { color: chartPalette.gridStrong },
        },
      },
    }),
    [chartPalette]
  );

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--app-text)]">Análisis financiero</h1>
          <p className="text-sm text-muted">
            Visualiza tendencias anuales, compara tu presupuesto y proyecta tu flujo de efectivo.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={year}
            onChange={(event) => setYear(Number(event.target.value))}
            className="rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-[var(--app-text)] shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
          >
            {years.map((optionYear) => (
              <option key={optionYear} value={optionYear}>
                {optionYear}
              </option>
            ))}
          </select>
          <MonthMultiSelect value={selectedMonths} onChange={setSelectedMonths} />
          <div className="flex items-center gap-2 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-[var(--app-text)] dark:text-slate-100">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted">Proyección</span>
            <select
              value={projectionMonths}
              onChange={(event) => setProjectionMonths(Number(event.target.value))}
              className="rounded-lg border border-transparent bg-transparent px-2 py-1 text-sm text-[var(--app-text)] focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
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
                ? "bg-gradient-to-r from-sky-500 to-indigo-500 text-white shadow shadow-sky-500/30"
                : "border border-[var(--app-border)] bg-[var(--app-surface)] text-muted hover:border-sky-400 hover:text-sky-600 dark:bg-[var(--app-surface-muted)] dark:hover:text-sky-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {loading ? (
        <div className="app-card border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)] p-6 text-sm text-muted">
          Cargando análisis financiero...
        </div>
      ) : error ? (
        <div className="app-card border border-rose-500/40 bg-rose-50 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-200">
          {error}
        </div>
      ) : analysisData ? (
        <section className="space-y-6">
          {activeTab === "expenses" && (
            <div className="app-card overflow-hidden">
              <header className="border-b border-[var(--app-border)] bg-[var(--app-surface-muted)] px-6 py-4">
                <h2 className="text-lg font-semibold text-[var(--app-text)]">
                  Reporte anual de gastos por categoría
                </h2>
                <p className="text-xs text-muted">
                  Suma los gastos reales por categoría a lo largo del periodo seleccionado.
                </p>
              </header>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-[var(--app-border)] text-sm">
                  <thead className="bg-[var(--app-surface-muted)] text-muted">
                    <tr>
                      <th className="px-6 py-3 text-left font-semibold text-[var(--app-text)]">Categoría</th>
                      {analysisData.annual_expense_report.months.map((month) => (
                        <th key={month.number} className="px-4 py-3 text-right font-semibold text-[var(--app-text)]">
                          {month.label}
                        </th>
                      ))}
                      <th className="px-6 py-3 text-right font-semibold text-[var(--app-text)]">Total anual</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--app-border)]">
                    {analysisData.annual_expense_report.rows.length > 0 ? (
                      analysisData.annual_expense_report.rows.map((row) => (
                        <tr key={row.category} className="text-[var(--app-text)]">
                          <td className="px-6 py-3 text-left font-medium text-[var(--app-text)]">
                            {row.category}
                          </td>
                          {row.values.map((value, index) => (
                            <td key={`${row.category}-${index}`} className="px-4 py-3 text-right">
                              {value ? formatCurrency(value) : "-"}
                            </td>
                          ))}
                          <td className="px-6 py-3 text-right font-semibold text-[var(--app-text)]">
                            {formatCurrency(row.total)}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={analysisData.annual_expense_report.months.length + 2}
                          className="px-6 py-6 text-center text-muted"
                        >
                          No se registraron gastos en el periodo seleccionado.
                        </td>
                      </tr>
                    )}
                  </tbody>
                  <tfoot className="bg-[var(--app-surface-muted)] text-muted">
                    <tr>
                      <th className="px-6 py-3 text-left font-semibold text-[var(--app-text)]">Total mensual</th>
                      {analysisData.annual_expense_report.monthly_totals.map((total, index) => (
                        <th key={`total-${index}`} className="px-4 py-3 text-right font-semibold text-[var(--app-text)]">
                          {total ? formatCurrency(total) : "-"}
                        </th>
                      ))}
                      <th className="px-6 py-3 text-right font-semibold text-sky-500 dark:text-sky-300">
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
              <div className="app-card overflow-hidden">
                <header className="border-b border-[var(--app-border)] bg-[var(--app-surface-muted)] px-6 py-4">
                  <h2 className="text-lg font-semibold text-[var(--app-text)]">
                    Comparativa anual: Presupuesto vs. Real por reglas
                  </h2>
                  <p className="text-xs text-muted">
                    Contrasta lo asignado en tu presupuesto con lo ejecutado durante el periodo.
                  </p>
                </header>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-[var(--app-border)] text-sm">
                    <thead className="bg-[var(--app-surface-muted)] text-muted">
                      <tr>
                        <th className="px-6 py-3 text-left font-semibold text-[var(--app-text)]">Regla</th>
                        <th className="px-4 py-3 text-right font-semibold text-[var(--app-text)]">Presupuesto (Anual)</th>
                        <th className="px-4 py-3 text-right font-semibold text-[var(--app-text)]">Gasto real (Anual)</th>
                        <th className="px-4 py-3 text-right font-semibold text-[var(--app-text)]">Diferencia</th>
                        <th className="px-4 py-3 text-right font-semibold text-[var(--app-text)]">Cumplimiento</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--app-border)]">
                      {analysisData.budget_analysis.rows.length > 0 ? (
                        analysisData.budget_analysis.rows.map((row) => {
                          const differenceClass =
                            row.difference > 0
                              ? "text-emerald-600 dark:text-emerald-300"
                              : row.difference < 0
                              ? "text-rose-600 dark:text-rose-300"
                              : "text-[var(--app-text)]";
                          return (
                            <tr key={row.name} className="text-[var(--app-text)]">
                              <td className="px-6 py-3 text-left font-medium text-[var(--app-text)]">{row.name}</td>
                              <td className="px-4 py-3 text-right text-[var(--app-text)]">{formatCurrency(row.budgeted)}</td>
                              <td className="px-4 py-3 text-right text-[var(--app-text)]">{formatCurrency(row.actual)}</td>
                              <td className={`px-4 py-3 text-right font-semibold ${differenceClass}`}>
                                {formatCurrency(row.difference)}
                              </td>
                              <td className="px-4 py-3 text-right text-[var(--app-text)]">
                                {formatPercent(row.compliance)}
                              </td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={5} className="px-6 py-6 text-center text-muted">
                            Aún no hay presupuesto registrado para este periodo.
                          </td>
                        </tr>
                      )}
                    </tbody>
                    <tfoot className="bg-[var(--app-surface-muted)] text-[var(--app-text)]">
                      <tr>
                        <th className="px-6 py-3 text-left font-semibold text-[var(--app-text)]">Totales</th>
                        <th className="px-4 py-3 text-right font-semibold text-[var(--app-text)]">
                          {formatCurrency(analysisData.budget_analysis.total_budgeted)}
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[var(--app-text)]">
                          {formatCurrency(analysisData.budget_analysis.total_actual)}
                        </th>
                        <th
                          className={`px-4 py-3 text-right font-semibold ${
                            analysisData.budget_analysis.total_difference > 0
                              ? "text-emerald-600 dark:text-emerald-300"
                              : analysisData.budget_analysis.total_difference < 0
                              ? "text-rose-600 dark:text-rose-300"
                              : "text-[var(--app-text)]"
                          }`}
                        >
                          {formatCurrency(analysisData.budget_analysis.total_difference)}
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-sky-600 dark:text-sky-300">
                          {formatPercent(analysisData.budget_analysis.total_compliance)}
                        </th>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="app-card p-6">
                  <h3 className="text-base font-semibold text-[var(--app-text)]">
                    Gasto real vs. presupuestado
                  </h3>
                  <div className="mt-4 h-72">
                    {budgetChartData ? <Bar data={budgetChartData} options={barOptions} /> : null}
                  </div>
                </div>
                <div className="app-card p-6">
                  <h3 className="text-base font-semibold text-[var(--app-text)]">
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
                <div className="app-card p-6">
                  <h3 className="text-base font-semibold text-[var(--app-text)]">Resumen de proyección</h3>
                  <dl className="mt-4 space-y-3 text-sm text-[var(--app-text)]">
                    <div className="flex items-center justify-between">
                      <dt className="text-muted">Saldo actual proyectado</dt>
                      <dd className="font-semibold text-[var(--app-text)]">
                        {formatCurrency(analysisData.cash_flow_projection.starting_balance)}
                      </dd>
                    </div>
                    <div className="flex items-center justify-between">
                      <dt className="text-muted">Flujo mensual promedio</dt>
                      <dd
                        className={`font-semibold ${
                          analysisData.cash_flow_projection.average_monthly_flow >= 0
                            ? "text-emerald-600 dark:text-emerald-300"
                            : "text-rose-600 dark:text-rose-300"
                        }`}
                      >
                        {formatCurrency(
                          analysisData.cash_flow_projection.average_monthly_flow
                        )}
                      </dd>
                    </div>
                    <div className="flex items-center justify-between">
                      <dt className="text-muted">Horizonte considerado</dt>
                      <dd className="font-semibold text-[var(--app-text)]">
                        {analysisData.cash_flow_projection.projection_months} meses
                      </dd>
                    </div>
                  </dl>
                </div>
                <div className="app-card-muted p-4 text-sm text-muted">
                  La proyección utiliza el promedio mensual de tu flujo de efectivo durante el periodo seleccionado.
                  Ajusta los meses analizados para observar distintos escenarios.
                </div>
              </div>
              <div className="app-card p-6">
                <h3 className="text-base font-semibold text-[var(--app-text)]">
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
        <div className="app-card border border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)] p-6 text-sm text-muted">
          Aún no hay información disponible para mostrar.
        </div>
      )}
    </div>
  );
}

function MonthMultiSelect({ value, onChange }: MonthMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleMonth = (month: number) => {
    const exists = value.includes(month);
    const updated = exists
      ? value.filter((item) => item !== month)
      : [...value, month];
    onChange([...new Set(updated)].sort((a, b) => a - b));
  };

  const toggleAll = () => {
    if (value.length === MONTH_OPTIONS.length) {
      onChange([]);
    } else {
      onChange(MONTH_OPTIONS.map((option) => option.value));
    }
  };

  const label = (() => {
    if (value.length === 0) return "Todo el año";
    if (value.length === MONTH_OPTIONS.length) return "Todos los meses";
    if (value.length === 1) {
      const found = MONTH_OPTIONS.find((month) => month.value === value[0]);
      return found ? found.label : "1 mes";
    }
    return `${value.length} meses seleccionados`;
  })();

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={() => setIsOpen((previous) => !previous)}
        className="flex items-center justify-between gap-3 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-4 py-2 text-sm font-medium text-[var(--app-text)] transition hover:border-sky-400 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
      >
        {label}
        <span className="text-xs text-muted">▼</span>
      </button>
      {isOpen && (
        <div className="absolute right-0 z-30 mt-2 w-56 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] p-4 shadow-xl">
          <button
            onClick={toggleAll}
            className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted transition hover:border-sky-400 hover:text-sky-600 dark:hover:text-sky-300"
          >
            {value.length === MONTH_OPTIONS.length ? "Limpiar selección" : "Seleccionar todo"}
          </button>
          <div className="mt-3 grid max-h-64 grid-cols-2 gap-2 overflow-y-auto pr-1 text-sm">
            {MONTH_OPTIONS.map((month) => (
              <label
                key={month.value}
                className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1 text-[var(--app-text)] hover:bg-sky-50 dark:text-slate-100 dark:hover:bg-slate-800"
              >
                <input
                  type="checkbox"
                  checked={value.includes(month.value)}
                  onChange={() => toggleMonth(month.value)}
                  className="h-4 w-4 rounded border-slate-300 text-sky-500 focus:ring-sky-400 dark:border-slate-600"
                />
                {month.label}
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
