import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Bar, Doughnut } from "react-chartjs-2";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  PieChart,
  Target,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { KpiCard } from "../components/KpiCard";
import { GoalProgressCard, GoalData } from "../components/GoalProgressCard";
import { API_BASE_URL } from "../utils/api";
import { useNumberFormatter } from "../context/DisplayPreferencesContext";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
);

const MONTH_OPTIONS = [
  { value: 1, label: "Enero" },
  { value: 2, label: "Febrero" },
  { value: 3, label: "Marzo" },
  { value: 4, label: "Abril" },
  { value: 5, label: "Mayo" },
  { value: 6, label: "Junio" },
  { value: 7, label: "Julio" },
  { value: 8, label: "Agosto" },
  { value: 9, label: "Septiembre" },
  { value: 10, label: "Octubre" },
  { value: 11, label: "Noviembre" },
  { value: 12, label: "Diciembre" },
];

const monthFormatter = new Intl.DateTimeFormat("es-MX", {
  month: "short",
  year: "numeric",
});

interface AmountComparison {
  amount: number;
  comparison: number | null;
}

interface BudgetSummary {
  budgeted: number;
  actual: number;
  difference: number;
  remaining: number;
  execution: number | null;
}

interface BudgetRuleItem {
  name: string;
  ideal_percent: number;
  actual_amount: number;
  actual_percent: number;
  state: "ok" | "warning" | "critical" | "neutral";
}

interface AccountSummary {
  id: number;
  name: string;
  account_type: string;
  initial_balance: number;
  current_balance: number;
}

interface DashboardData {
  kpis: {
    income: AmountComparison;
    expense: AmountComparison;
    net: AmountComparison;
  };
  net_worth_chart: {
    dates: string[];
    values: number[];
  };
  cash_flow_chart: {
    months: string[];
    income: number[];
    expense: number[];
  };
  budget_vs_actual: {
    income: BudgetSummary;
    expense: BudgetSummary;
  };
  budget_rule_control: BudgetRuleItem[];
  accounts: AccountSummary[];
  goals: GoalData[];
  expense_distribution: {
    categories: string[];
    amounts: number[];
  };
  expense_type_comparison: {
    labels: string[];
    amounts: number[];
  };
}

interface MonthMultiSelectProps {
  value: number[];
  onChange: (months: number[]) => void;
}

export function Dashboard() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [selectedMonths, setSelectedMonths] = useState<number[]>([
    new Date().getMonth() + 1,
  ]);
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeChart, setActiveChart] = useState<"netWorth" | "cashFlow">(
    "netWorth",
  );
  const [activeAccountIndex, setActiveAccountIndex] = useState(0);
  const [refreshToken, setRefreshToken] = useState(0);
  const { formatCurrency, formatPercent } = useNumberFormatter();

  const formatSignedCurrency = (value: number) => {
    if (!Number.isFinite(value) || value === 0) {
      return formatCurrency(0);
    }
    const absolute = Math.abs(value);
    const formatted = formatCurrency(absolute);
    return `${value > 0 ? "+" : "-"}${formatted}`;
  };

  useEffect(() => {
    let isMounted = true;

    const fetchDashboard = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        params.append("year", year.toString());
        selectedMonths.forEach((month) =>
          params.append("months", month.toString()),
        );

        const response = await axios.get<DashboardData>(
          `${API_BASE_URL}/dashboard?${params.toString()}`,
        );

        if (!isMounted) return;
        setData(response.data);
        setActiveAccountIndex(0);
      } catch (fetchError) {
        if (!isMounted) return;
        console.error("Error al cargar el dashboard:", fetchError);
        setError("No pudimos cargar el dashboard. Intenta nuevamente.");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchDashboard();

    return () => {
      isMounted = false;
    };
  }, [year, selectedMonths, refreshToken]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const triggerRefresh = () => {
      setRefreshToken((previous) => previous + 1);
    };
    window.addEventListener("nebula:transactions-updated", triggerRefresh);
    window.addEventListener("nebula:goals-refresh", triggerRefresh);
    return () => {
      window.removeEventListener("nebula:transactions-updated", triggerRefresh);
      window.removeEventListener("nebula:goals-refresh", triggerRefresh);
    };
  }, []);

  const netWorthChartData = useMemo(() => {
    if (!data) return null;
    const labels = data.net_worth_chart.dates.map((dateString) =>
      monthFormatter.format(new Date(dateString)),
    );
    return {
      labels,
      datasets: [
        {
          label: "Patrimonio Neto",
          data: data.net_worth_chart.values,
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56, 189, 248, 0.2)",
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        },
      ],
    };
  }, [data]);

  const cashFlowChartData = useMemo(() => {
    if (!data) return null;
    const labels = data.cash_flow_chart.months.map((item) => {
      const [yearPart, monthPart] = item.split("-");
      const date = new Date(Number(yearPart), Number(monthPart) - 1, 1);
      return monthFormatter.format(date);
    });

    return {
      labels,
      datasets: [
        {
          label: "Ingresos",
          data: data.cash_flow_chart.income,
          backgroundColor: "rgba(56, 189, 248, 0.7)",
          borderRadius: 8,
          borderSkipped: false as const,
        },
        {
          label: "Gastos",
          data: data.cash_flow_chart.expense,
          backgroundColor: "rgba(248, 113, 113, 0.7)",
          borderRadius: 8,
          borderSkipped: false as const,
        },
      ],
    };
  }, [data]);

  const expenseDistributionChartData = useMemo(() => {
    if (!data || data.expense_distribution.categories.length === 0) {
      return null;
    }
    const palette = [
      "#38bdf8",
      "#f97316",
      "#a855f7",
      "#22c55e",
      "#facc15",
      "#f43f5e",
      "#14b8a6",
    ];
    return {
      labels: data.expense_distribution.categories,
      datasets: [
        {
          label: "Gasto",
          data: data.expense_distribution.amounts,
          backgroundColor: data.expense_distribution.amounts.map(
            (_, index) => palette[index % palette.length],
          ),
          borderRadius: 8,
          borderSkipped: false as const,
        },
      ],
    };
  }, [data]);

  const expenseTypeChartData = useMemo(() => {
    if (!data || data.expense_type_comparison.labels.length === 0) {
      return null;
    }
    const palette = [
      "#38bdf8",
      "#f97316",
      "#a855f7",
      "#22c55e",
      "#facc15",
      "#f43f5e",
      "#14b8a6",
    ];
    return {
      labels: data.expense_type_comparison.labels,
      datasets: [
        {
          label: "Gasto",
          data: data.expense_type_comparison.amounts,
          backgroundColor: data.expense_type_comparison.amounts.map(
            (_, index) => palette[index % palette.length],
          ),
          borderColor: "rgba(30, 41, 59, 0.4)",
          borderWidth: 1,
        },
      ],
    };
  }, [data]);

  const netWorthOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: "#94a3b8",
        },
      },
      tooltip: {
        callbacks: {
          label: (context: any) => formatCurrency(context.parsed.y),
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#94a3b8",
        },
        grid: {
          color: "rgba(148, 163, 184, 0.1)",
        },
      },
      y: {
        ticks: {
          color: "#94a3b8",
          callback: (value: string | number) => formatCurrency(Number(value)),
        },
        grid: {
          color: "rgba(148, 163, 184, 0.1)",
        },
      },
    },
  }), []);

  const barOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: "#94a3b8",
        },
      },
      tooltip: {
        callbacks: {
          label: (context: any) => `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: "#94a3b8" },
        grid: { color: "rgba(148, 163, 184, 0.08)" },
      },
      y: {
        ticks: {
          color: "#94a3b8",
          callback: (value: string | number) => formatCurrency(Number(value)),
        },
        grid: { color: "rgba(148, 163, 184, 0.08)" },
      },
    },
  }), []);

  const doughnutOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom" as const,
        labels: {
          color: "#94a3b8",
          padding: 16,
        },
      },
      tooltip: {
        callbacks: {
          label: (context: any) => `${context.label}: ${formatCurrency(context.parsed)}`,
        },
      },
    },
  }), []);

  const accounts = data?.accounts ?? [];
  const activeAccount = accounts[activeAccountIndex] ?? null;

  return (
    <div className="space-y-6 text-slate-900 dark:text-slate-100">
      <div className="app-card flex flex-col gap-6 p-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Dashboard</h1>
          <p className="mt-1 text-sm text-muted">
            Controla tus finanzas personales con una vista integral de tu patrimonio.
          </p>
        </div>
        <div className="flex w-full flex-col gap-4 sm:flex-row sm:items-end sm:justify-end">
          <div className="flex min-w-[180px] flex-col gap-2">
            <label className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted">
              <Calendar className="h-4 w-4" /> Año
            </label>
            <select
              value={year}
              onChange={(event) => setYear(Number(event.target.value))}
              className="rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-4 py-2 text-sm font-medium text-slate-900 shadow-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            >
              {Array.from({ length: 7 }).map((_, index) => {
                const optionYear = currentYear - 3 + index;
                return (
                  <option key={optionYear} value={optionYear}>
                    {optionYear}
                  </option>
                );
              })}
            </select>
          </div>
          <div className="flex min-w-[220px] flex-col gap-2">
            <label className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted">
              <PieChart className="h-4 w-4" /> Meses
            </label>
            <MonthMultiSelect
              value={selectedMonths}
              onChange={setSelectedMonths}
            />
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="app-card flex min-h-[200px] items-center justify-center text-muted">
          Cargando información...
        </div>
      )}

      {error && !isLoading && (
        <div className="rounded-2xl border border-rose-500/40 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-200">
          {error}
        </div>
      )}

      {!isLoading && !error && data && (
        <>
          <div className="grid gap-6 xl:grid-cols-12">
            <section className="space-y-6 xl:col-span-8">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-12">
                <div className="xl:col-span-4">
                  <KpiCard
                    title="Ganancias"
                    value={formatCurrency(data.kpis.income.amount)}
                    comparison={data.kpis.income.comparison}
                    icon={<TrendingUp className="h-5 w-5" />}
                    variant="emerald"
                  />
                </div>
                <div className="xl:col-span-4">
                  <KpiCard
                    title="Gastos"
                    value={formatCurrency(data.kpis.expense.amount)}
                    comparison={data.kpis.expense.comparison}
                    inverse
                    icon={<TrendingDown className="h-5 w-5" />}
                    variant="rose"
                  />
                </div>
                <div className="xl:col-span-4">
                  <KpiCard
                    title="Ahorro Neto"
                    value={formatCurrency(data.kpis.net.amount)}
                    comparison={data.kpis.net.comparison}
                    icon={<Wallet className="h-5 w-5" />}
                    variant="indigo"
                  />
                </div>
              </div>

              <div className="app-card p-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold">
                      {activeChart === "netWorth"
                        ? "Evolución de Patrimonio Neto"
                        : "Flujo de Efectivo Mensual"}
                    </h2>
                    <p className="text-sm text-muted">
                      Visualiza tendencias y anticipa tus necesidades de efectivo.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setActiveChart("netWorth")}
                      className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                        activeChart === "netWorth"
                          ? "bg-gradient-to-r from-sky-500 to-indigo-500 text-white shadow"
                          : "border border-[var(--app-border)] bg-transparent text-muted hover:border-sky-400 hover:text-slate-700 dark:hover:text-slate-200"
                      }`}
                    >
                      Patrimonio
                    </button>
                    <button
                      onClick={() => setActiveChart("cashFlow")}
                      className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                        activeChart === "cashFlow"
                          ? "bg-gradient-to-r from-sky-500 to-indigo-500 text-white shadow"
                          : "border border-[var(--app-border)] bg-transparent text-muted hover:border-sky-400 hover:text-slate-700 dark:hover:text-slate-200"
                      }`}
                    >
                      Flujo
                    </button>
                  </div>
                </div>
                <div className="mt-6 h-80">
                  {activeChart === "netWorth" ? (
                    netWorthChartData && netWorthChartData.labels.length > 0 ? (
                      <Line data={netWorthChartData} options={netWorthOptions} />
                    ) : (
                      <EmptyState message="Sin movimientos suficientes para mostrar la evolución." />
                    )
                  ) : cashFlowChartData && cashFlowChartData.labels.length > 0 ? (
                    <Bar data={cashFlowChartData} options={barOptions} />
                  ) : (
                    <EmptyState message="Aún no hay flujo de efectivo registrado." />
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <BudgetSummaryCard
                  title="Ingresos PPTO"
                  summary={data.budget_vs_actual.income}
                  accentClass="from-emerald-500/80 to-sky-500/80"
                />
                <BudgetSummaryCard
                  title="Gastos PPTO"
                  summary={data.budget_vs_actual.expense}
                  accentClass="from-rose-500/80 to-orange-500/80"
                />
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="app-card p-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Metas activas</h2>
                    <Target className="h-5 w-5 text-sky-500" />
                  </div>
                  <p className="mt-1 text-sm text-muted">
                    Da seguimiento a tus objetivos financieros y mantén la motivación.
                  </p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                    {data.goals.length > 0 ? (
                      data.goals.map((goal) => (
                        <GoalProgressCard
                          key={goal.id}
                          goal={goal}
                        />
                      ))
                    ) : (
                      <EmptyState message="No has definido metas todavía." />
                    )}
                  </div>
                </div>

                <div className="app-card p-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Distribución de gastos</h2>
                    <PieChart className="h-5 w-5 text-sky-500" />
                  </div>
                  <p className="mt-1 text-sm text-muted">
                    Identifica en qué categorías se concentra tu gasto.
                  </p>
                  <div className="mt-6 h-72">
                    {expenseDistributionChartData ? (
                      <Bar data={expenseDistributionChartData} options={barOptions} />
                    ) : (
                      <EmptyState message="Aún no registras gastos para este periodo." />
                    )}
                  </div>
                </div>
              </div>
            </section>

            <aside className="space-y-6 xl:col-span-4">
              <BudgetRuleCard
                rules={data.budget_rule_control}
                incomeTotal={data.kpis.income.amount}
              />
              <AccountsCard
                accounts={accounts}
                activeIndex={activeAccountIndex}
                onPrev={() =>
                  setActiveAccountIndex((prev) =>
                    prev === 0 ? accounts.length - 1 : prev - 1,
                  )
                }
                onNext={() =>
                  setActiveAccountIndex((prev) =>
                    prev === accounts.length - 1 ? 0 : prev + 1,
                  )
                }
                activeAccount={activeAccount}
              />
              <div className="app-card p-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">Gastos por tipo</h2>
                  <PieChart className="h-5 w-5 text-sky-500" />
                </div>
                <p className="mt-1 text-sm text-muted">
                  Compara gastos fijos, variables y otros compromisos.
                </p>
                <div className="mt-6 h-72">
                  {expenseTypeChartData ? (
                    <Doughnut data={expenseTypeChartData} options={doughnutOptions} />
                  ) : (
                    <EmptyState message="No hay datos de gastos para comparar." />
                  )}
                </div>
              </div>
            </aside>
          </div>
        </>
      )}
    </div>
  );
}

function MonthMultiSelect({ value, onChange }: MonthMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleMonth = (month: number) => {
    const exists = value.includes(month);
    let updated = exists
      ? value.filter((item) => item !== month)
      : [...value, month];
    updated = [...new Set(updated)].sort((a, b) => a - b);
    onChange(updated);
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
    if (value.length === 12) return "Todos los meses";
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
        className="flex items-center justify-between gap-3 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-4 py-2 text-sm font-medium text-slate-900 transition hover:border-sky-400 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
      >
        {label}
        <span className="text-xs text-muted">▼</span>
      </button>
      {isOpen && (
        <div className="absolute right-0 z-20 mt-2 w-56 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] p-4 shadow-xl">
          <button
            onClick={toggleAll}
            className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-muted transition hover:border-sky-400 hover:text-sky-600 dark:hover:text-sky-300"
          >
            {value.length === MONTH_OPTIONS.length
              ? "Limpiar selección"
              : "Seleccionar todo"}
          </button>
          <div className="mt-3 grid max-h-64 grid-cols-2 gap-2 overflow-y-auto pr-1 text-sm">
            {MONTH_OPTIONS.map((month) => (
              <label
                key={month.value}
                className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1 text-slate-900 hover:bg-sky-50 dark:text-slate-100 dark:hover:bg-slate-800"
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

function BudgetSummaryCard({
  title,
  summary,
  accentClass,
}: {
  title: string;
  summary: BudgetSummary;
  accentClass: string;
}) {
  const { formatCurrency, formatPercent } = useNumberFormatter();
  const formatSigned = (value: number) => {
    if (!Number.isFinite(value) || value === 0) {
      return formatCurrency(0);
    }
    const formatted = formatCurrency(Math.abs(value));
    return `${value > 0 ? "+" : "-"}${formatted}`;
  };
  const execution = summary.execution ?? 0;
  const progress = Math.max(0, Math.min(100, execution));

  return (
    <div className="app-card p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold">{title}</h3>
        <span className="text-xs font-medium text-muted">
          {summary.execution ? formatPercent(summary.execution) : "—"}
        </span>
      </div>
      <p className="mt-1 text-sm text-muted">
        Planificado: <span className="font-semibold">{formatCurrency(summary.budgeted)}</span>
      </p>
      <p className="mt-1 text-sm text-muted">
        Real: <span className="font-semibold">{formatCurrency(summary.actual)}</span>
      </p>
      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${accentClass}`}
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="mt-3 text-xs text-muted">
        Variación: <span className="font-semibold">{formatSigned(summary.difference)}</span>
      </div>
      <div className="mt-1 text-xs text-muted">
        Restante: <span className="font-semibold">{formatSigned(summary.remaining)}</span>
      </div>
    </div>
  );
}

function BudgetRuleCard({
  rules,
  incomeTotal,
}: {
  rules: BudgetRuleItem[];
  incomeTotal: number;
}) {
  const { formatCurrency, formatPercent } = useNumberFormatter();

  if (!rules.length) {
    return (
      <div className="app-card p-6">
        <h2 className="text-lg font-semibold">Control de gastos</h2>
        <EmptyState message="Aún no has configurado reglas de presupuesto." />
      </div>
    );
  }

  const stateClasses: Record<BudgetRuleItem["state"], string> = {
    ok: "bg-emerald-500/80",
    warning: "bg-amber-400/80",
    critical: "bg-rose-500/80",
    neutral: "bg-slate-500/60",
  };

  const stateLabels: Record<BudgetRuleItem["state"], string> = {
    ok: "En rango",
    warning: "Revisa",
    critical: "Excedido",
    neutral: "Sin datos",
  };

  return (
    <div className="app-card p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Control de gastos</h2>
        <span className="text-xs text-muted">Basado en {formatCurrency(incomeTotal)} de ingresos</span>
      </div>
      <div className="mt-5 space-y-4">
        {rules.map((rule) => {
          const percent = Math.min(150, Math.max(0, rule.actual_percent));
          return (
            <div key={rule.name} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-semibold">{rule.name}</span>
                <span className="text-xs text-muted">Ideal {rule.ideal_percent.toFixed(0)}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div
                  className={`h-full ${stateClasses[rule.state]}`}
                  style={{ width: `${percent}%` }}
                ></div>
              </div>
              <div className="flex items-center justify-between text-xs text-muted">
                <span>{formatCurrency(rule.actual_amount)}</span>
                <span className="font-semibold">
                  {formatPercent(rule.actual_percent)} • {stateLabels[rule.state]}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AccountsCard({
  accounts,
  activeIndex,
  activeAccount,
  onPrev,
  onNext,
}: {
  accounts: AccountSummary[];
  activeIndex: number;
  activeAccount: AccountSummary | null;
  onPrev: () => void;
  onNext: () => void;
}) {
  const { formatCurrency } = useNumberFormatter();
  const [showBalances, setShowBalances] = useState(true);

  const formatSigned = (value: number) => {
    if (!showBalances) {
      return "••••";
    }
    if (!Number.isFinite(value) || value === 0) {
      return formatCurrency(0);
    }
    const formatted = formatCurrency(Math.abs(value));
    return `${value > 0 ? "+" : "-"}${formatted}`;
  };

  const displayBalance = showBalances
    ? formatCurrency(activeAccount?.current_balance ?? 0)
    : "••••";

  return (
    <div className="app-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Cuentas</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBalances((prev) => !prev)}
            aria-label={showBalances ? "Ocultar saldos" : "Mostrar saldos"}
            aria-pressed={!showBalances}
            className="rounded-full border border-[var(--app-border)] p-2 text-muted transition hover:border-sky-400 hover:text-sky-500"
          >
            {showBalances ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
          <button
            onClick={onPrev}
            disabled={accounts.length <= 1}
            className="rounded-full border border-[var(--app-border)] p-2 text-muted transition hover:border-sky-400 hover:text-sky-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={onNext}
            disabled={accounts.length <= 1}
            className="rounded-full border border-[var(--app-border)] p-2 text-muted transition hover:border-sky-400 hover:text-sky-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
      {activeAccount ? (
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-sky-500 via-blue-500 to-indigo-500 p-6 text-white">
          <div className="text-sm uppercase tracking-wide text-white/70">
            {activeAccount.account_type}
          </div>
          <div className="mt-3 text-3xl font-semibold">{displayBalance}</div>
          <div className="mt-8 text-sm">
            <p className="font-medium">{activeAccount.name}</p>
            <p className="text-xs text-white/70">
              Variación {formatSigned(activeAccount.current_balance - activeAccount.initial_balance)}
            </p>
          </div>
          {accounts.length > 1 && (
            <span className="absolute bottom-4 right-6 text-xs font-medium text-white/70">
              {activeIndex + 1} / {accounts.length}
            </span>
          )}
        </div>
      ) : (
        <EmptyState message="Aún no has creado cuentas." />
      )}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)]/70 px-4 py-8 text-center text-sm text-muted">
      {message}
    </div>
  );
}
