import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  PiggyBank,
  Plus,
  Trash2,
} from "lucide-react";
import { BudgetModal } from "../components/BudgetModal";
import { useStore } from "../store/useStore";
import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { apiPath } from "../utils/api";
import {
  formatDateForDisplay,
  getTodayDateInputValue,
  parseDateOnly,
} from "../utils/date";

interface BudgetEntry {
  id: number;
  category: string;
  description?: string;
  type: string;
  frequency: string;
  budgeted_amount: number;
  actual_amount: number;
  remaining_amount: number;
  over_budget_amount: number;
  execution?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  due_date?: string | null;
  month?: number | null;
  year?: number | null;
  goal_id?: number | null;
  goal_name?: string | null;
  debt_id?: number | null;
  debt_name?: string | null;
  is_recurring: boolean;
  use_custom_schedule?: boolean;
}

interface ParameterOption {
  id: number;
  value: string;
}

type BudgetStatusFilter = "active" | "upcoming" | "archived" | "all";

interface BudgetSummary {
  planned: number;
  executed: number;
  available: number;
  upcoming: number;
  overdueCount: number;
  nextEntry: {
    amount: number;
    description: string;
    date: Date;
  } | null;
}

// Para mostrar el nombre del mes en lugar del número
const monthNames = [
  "Ene",
  "Feb",
  "Mar",
  "Abr",
  "May",
  "Jun",
  "Jul",
  "Ago",
  "Sep",
  "Oct",
  "Nov",
  "Dic",
];

export function Budget() {
  const [budgetEntries, setBudgetEntries] = useState<BudgetEntry[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<BudgetEntry | null>(null);
  const [selectedEntryIds, setSelectedEntryIds] = useState<number[]>([]);
  const [transactionTypes, setTransactionTypes] = useState<ParameterOption[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [monthFilter, setMonthFilter] = useState("all");
  const [yearFilter, setYearFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState<BudgetStatusFilter>("active");
  const [referenceDate, setReferenceDate] = useState<string>(
    getTodayDateInputValue(),
  );
  const { openTransactionModal } = useStore();
  const { formatCurrency } = useNumberFormatter();
  const [listPulse, setListPulse] = useState(false);
  const budgetInitialLoad = useRef(true);

  const fetchBudgetEntries = useCallback(async () => {
    const params: Record<string, string> = {};
    if (statusFilter !== "all") {
      params.status = statusFilter;
    }
    if (referenceDate) {
      params.reference_date = referenceDate;
    }

    try {
      const response = await axios.get<BudgetEntry[]>(apiPath("/budget"), {
        params,
      });

      const entries = response.data.map((entry) => {
        const planned = entry.budgeted_amount ?? (entry as any).amount ?? 0;
        const actual = entry.actual_amount ?? 0;
        const remaining =
          entry.remaining_amount !== undefined && entry.remaining_amount !== null
            ? entry.remaining_amount
            : planned - actual;
        const overBudget =
          entry.over_budget_amount !== undefined &&
          entry.over_budget_amount !== null
            ? entry.over_budget_amount
            : Math.max(actual - planned, 0);

        return {
          ...entry,
          budgeted_amount: planned,
          actual_amount: actual,
          remaining_amount: remaining,
          over_budget_amount: overBudget,
          frequency: entry.frequency || "Mensual",
          is_recurring: Boolean(entry.is_recurring),
        };
      });
      setBudgetEntries(entries);
      setSelectedEntryIds([]);
    } catch (budgetError) {
      console.error("Error al obtener las entradas de presupuesto:", budgetError);
    }
  }, [referenceDate, statusFilter]);

  useEffect(() => {
    fetchBudgetEntries();
  }, [fetchBudgetEntries]);

  useEffect(() => {
    setSelectedEntryIds((prev) =>
      prev.filter((id) => budgetEntries.some((entry) => entry.id === id))
    );
  }, [budgetEntries]);

  useEffect(() => {
    axios
      .get<ParameterOption[]>(apiPath("/parameters/transaction-types"))
      .then((res) => setTransactionTypes(res.data));
  }, []);

  const parseEntryDate = useCallback((entry: BudgetEntry) => {
    const reference = entry.due_date || entry.end_date || entry.start_date;
    const parsed = parseDateOnly(reference);
    if (parsed) {
      return parsed;
    }
    if (entry.year && entry.month) {
      return new Date(entry.year, (entry.month || 1) - 1, 1);
    }
    return new Date();
  }, []);

  const filteredEntries = useMemo(() => {
    return budgetEntries
      .filter((entry) => {
        const entryDate = parseEntryDate(entry);
        const entryMonth = entryDate.getMonth() + 1;
        const entryYear = entryDate.getFullYear();

        const matchesSearch =
          !searchTerm ||
          `${entry.description ?? ""} ${entry.category} ${entry.frequency}`
            .toLowerCase()
            .includes(searchTerm.toLowerCase());
        const matchesType = !typeFilter || entry.type === typeFilter;
        const matchesMonth =
          monthFilter === "all" || entryMonth === Number(monthFilter);
        const matchesYear =
          yearFilter === "all" || entryYear === Number(yearFilter);

        return matchesSearch && matchesType && matchesMonth && matchesYear;
      })
      .sort((a, b) => parseEntryDate(a).getTime() - parseEntryDate(b).getTime());
  }, [budgetEntries, monthFilter, parseEntryDate, searchTerm, typeFilter, yearFilter]);

  const totals = useMemo<BudgetSummary>(() => {
    let today = new Date();
    if (referenceDate) {
      const parsed = parseDateOnly(referenceDate);
      if (parsed) {
        today = parsed;
      }
    }
    const next30 = new Date(today.getTime());
    next30.setDate(today.getDate() + 30);

    let planned = 0;
    let executed = 0;
    let available = 0;
    let upcoming = 0;
    let overdueCount = 0;
    let nextEntry: { amount: number; description: string; date: Date } | null = null;

    budgetEntries.forEach((entry) => {
      const date = parseEntryDate(entry);
      const plannedAmount = entry.budgeted_amount ?? 0;
      const actualAmount = entry.actual_amount ?? 0;
      const remainingAmount = Math.max(plannedAmount - actualAmount, 0);
      const isOverBudget = (entry.over_budget_amount ?? 0) > 0.01;

      planned += plannedAmount;
      executed += actualAmount;
      available += Math.max(plannedAmount - actualAmount, 0);

      if (!isOverBudget && remainingAmount > 0 && date >= today && date <= next30) {
        upcoming += remainingAmount;
      }

      if (date < today && remainingAmount > 0) {
        overdueCount += 1;
      }

      if (!nextEntry || date < nextEntry.date) {
        nextEntry = {
          amount: remainingAmount > 0 ? remainingAmount : Math.max(actualAmount, plannedAmount),
          description: entry.description || entry.category,
          date,
        };
      }
    });

    return { planned, executed, available, upcoming, overdueCount, nextEntry };
  }, [budgetEntries, parseEntryDate, referenceDate]);

  const availableYears = useMemo(() => {
    const years = new Set<number>();
    budgetEntries.forEach((entry) => {
      years.add(parseEntryDate(entry).getFullYear());
    });
    return Array.from(years).sort((a, b) => b - a);
  }, [budgetEntries, parseEntryDate]);

  const availableMonths = useMemo(() => {
    const months = new Set<number>();
    budgetEntries.forEach((entry) => {
      months.add(parseEntryDate(entry).getMonth() + 1);
    });
    return Array.from(months).sort((a, b) => a - b);
  }, [budgetEntries, parseEntryDate]);

  const handleOpenModal = useCallback((entry: BudgetEntry | null) => {
    setSelectedEntry(entry);
    setIsModalOpen(true);
  }, []);

  const handleSave = () => {
    fetchBudgetEntries();
  };

  useEffect(() => {
    const handleNewBudgetEntry = () => handleOpenModal(null);
    window.addEventListener("nebula:budget-request-add", handleNewBudgetEntry);
    return () => {
      window.removeEventListener(
        "nebula:budget-request-add",
        handleNewBudgetEntry
      );
    };
  }, [handleOpenModal]);

  const handleToggleEntry = (entryId: number, checked: boolean) => {
    setSelectedEntryIds((prev) => {
      if (checked) {
        if (prev.includes(entryId)) {
          return prev;
        }
        return [...prev, entryId];
      }
      return prev.filter((id) => id !== entryId);
    });
  };

  const handleToggleAll = (checked: boolean) => {
    if (checked) {
      setSelectedEntryIds(filteredEntries.map((entry) => entry.id));
    } else {
      setSelectedEntryIds([]);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedEntryIds.length === 0) {
      return;
    }

    const confirmationMessage =
      selectedEntryIds.length === 1
        ? "¿Deseas eliminar esta entrada del presupuesto?"
        : `¿Deseas eliminar las ${selectedEntryIds.length} entradas seleccionadas?`;

    if (!window.confirm(confirmationMessage)) {
      return;
    }

    await Promise.all(
      selectedEntryIds.map((entryId) => axios.delete(apiPath(`/budget/${entryId}`)))
    );

    fetchBudgetEntries();
    setSelectedEntryIds([]);
  };

  const resetFilters = () => {
    setSearchTerm("");
    setTypeFilter("");
    setMonthFilter("all");
    setYearFilter("all");
    setStatusFilter("active");
    setReferenceDate(getTodayDateInputValue());
  };

  const getStatusPill = (entry: BudgetEntry) => {
    const reference = referenceDate ? new Date(referenceDate) : new Date();
    const date = parseEntryDate(entry);
    const remaining =
      entry.remaining_amount ?? entry.budgeted_amount - entry.actual_amount;
    const overBudget = entry.over_budget_amount ?? 0;

    if (overBudget > 0.01) {
      return {
        label: "Excedido",
        className: "bg-rose-500/15 text-rose-600 dark:text-rose-200",
        icon: <AlertCircle className="h-3.5 w-3.5" />,
      };
    }

    if (remaining <= 0.01) {
      return {
        label: "Completado",
        className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-200",
        icon: <CheckCircle2 className="h-3.5 w-3.5" />,
      };
    }

    const diffDays = Math.floor(
      (date.getTime() - reference.getTime()) / (1000 * 60 * 60 * 24),
    );

    if (diffDays < 0) {
      return {
        label: "Vencido",
        className: "bg-rose-500/10 text-rose-600 dark:text-rose-200",
        icon: <Clock className="h-3.5 w-3.5" />,
      };
    }
    if (diffDays <= 7) {
      return {
        label: "Esta semana",
        className: "bg-amber-500/10 text-amber-600 dark:text-amber-200",
        icon: <Clock className="h-3.5 w-3.5" />,
      };
    }
    if (diffDays <= 30) {
      return {
        label: "Próximos 30 días",
        className: "bg-blue-500/10 text-blue-600 dark:text-blue-200",
        icon: <Calendar className="h-3.5 w-3.5" />,
      };
    }
    return {
      label: "Planificado",
      className: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-200",
      icon: <Calendar className="h-3.5 w-3.5" />,
    };
  };

  const isAllSelected =
    filteredEntries.length > 0 &&
    filteredEntries.every((entry) => selectedEntryIds.includes(entry.id));

  useEffect(() => {
    if (budgetInitialLoad.current) {
      budgetInitialLoad.current = false;
      return;
    }
    setListPulse(true);
    const timeout = window.setTimeout(() => setListPulse(false), 650);
    return () => window.clearTimeout(timeout);
  }, [budgetEntries]);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="section-title">Presupuesto</h1>
          <p className="mt-1 max-w-2xl text-muted">
            Organiza tus compromisos financieros futuros y registra rápidamente los pagos
            cuando ocurran.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleOpenModal(null)}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-semibold shadow-lg shadow-blue-600/20 transition hover:bg-blue-500"
          >
            <Plus className="h-4 w-4" /> Añadir entrada
          </button>
          <button
            onClick={resetFilters}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--app-border)] px-4 py-2 text-sm font-semibold text-muted transition hover:border-sky-400 hover:text-slate-700 dark:hover:text-slate-200"
          >
            Reiniciar filtros
          </button>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="glow-card glow-card--emerald sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600 dark:text-emerald-300">
                Planificado
              </p>
              <p className="mt-2 text-3xl font-bold text-emerald-600 dark:text-emerald-200">
                {formatCurrency(totals.planned)}
              </p>
            </div>
            <span className="rounded-full bg-emerald-500/15 p-3 text-emerald-600 dark:text-emerald-300">
              <PiggyBank className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            Suma total de compromisos registrados.
          </p>
        </div>
        <div className="glow-card glow-card--sky sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-300">
                Ejecutado
              </p>
              <p className="mt-2 text-3xl font-bold text-sky-600 dark:text-sky-200">
                {formatCurrency(totals.executed)}
              </p>
            </div>
            <span className="rounded-full bg-sky-500/15 p-3 text-sky-600 dark:text-sky-300">
              <Calendar className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            Monto aplicado a transacciones vinculadas al presupuesto.
          </p>
        </div>
        <div className="glow-card glow-card--amber sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-600 dark:text-amber-300">
                Disponible
              </p>
              <p className="mt-2 text-3xl font-bold text-amber-600 dark:text-amber-200">
                {formatCurrency(totals.available)}
              </p>
            </div>
            <span className="rounded-full bg-amber-500/15 p-3 text-amber-600 dark:text-amber-300">
              <CheckCircle2 className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            Recursos aún libres dentro de tus límites presupuestados.
          </p>
        </div>
        <div className="glow-card glow-card--rose sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-rose-600 dark:text-rose-300">
                Próximos 30 días
              </p>
              <p className="mt-2 text-xl font-semibold text-rose-600 dark:text-rose-200">
                {formatCurrency(totals.upcoming)}
              </p>
            </div>
            <span className="rounded-full bg-rose-500/15 p-3 text-rose-600 dark:text-rose-300">
              <Clock className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            {totals.overdueCount > 0
              ? `Tienes ${totals.overdueCount} ${
                  totals.overdueCount === 1 ? "presupuesto vencido" : "presupuestos vencidos"
                } pendientes.`
              : "Sin pagos atrasados en el periodo analizado."}
            {totals.nextEntry
              ? ` Próxima referencia: ${totals.nextEntry.description} (${formatDateForDisplay(totals.nextEntry.date)}).`
              : ""}
          </p>
        </div>
      </section>

      <section className="app-card p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold">Filtrar presupuesto</h2>
          <p className="text-sm text-muted">
            Refina la lista por categoría, tipo, periodo o búsqueda libre.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-6">
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Buscar
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Categoría o descripción"
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Tipo
            </label>
            <select
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value)}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            >
              <option value="">Todos</option>
              {transactionTypes.map((type) => (
                <option key={type.id} value={type.value}>
                  {type.value}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Mes
            </label>
            <select
              value={monthFilter}
              onChange={(event) => setMonthFilter(event.target.value)}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            >
              <option value="all">Todos</option>
              {availableMonths.map((month) => (
                <option key={month} value={month}>
                  {monthNames[month - 1]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Año
            </label>
            <select
              value={yearFilter}
              onChange={(event) => setYearFilter(event.target.value)}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            >
              <option value="all">Todos</option>
              {availableYears.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Estado
            </label>
            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(event.target.value as BudgetStatusFilter)
              }
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            >
              <option value="active">Activos</option>
              <option value="upcoming">Próximos</option>
              <option value="archived">Cerrados</option>
              <option value="all">Todos</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Fecha de referencia
            </label>
            <input
              type="date"
              value={referenceDate}
              onChange={(event) => setReferenceDate(event.target.value)}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            />
          </div>
        </div>
      </section>

      <section
        className={`app-card overflow-hidden ${listPulse ? "list-highlight" : ""}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--app-border)] px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">Entradas planificadas</h2>
            <p className="text-sm text-muted">
              Selecciona filas para eliminarlas en lote o haz doble clic para editarlas.
            </p>
          </div>
          <div className="flex flex-col items-end gap-3 sm:flex-row sm:items-center">
            <span className="text-sm text-muted">
              {filteredEntries.length} registros · {selectedEntryIds.length} seleccionados
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleOpenModal(null)}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold shadow-lg shadow-blue-600/20 transition hover:bg-blue-500"
              >
                <Plus className="h-4 w-4" />
                Añadir entrada
              </button>
              <button
                onClick={handleDeleteSelected}
                disabled={selectedEntryIds.length === 0}
                className="inline-flex items-center gap-2 rounded-lg border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:border-rose-400 hover:bg-rose-50 focus:outline-none focus:ring-2 focus:ring-rose-200 disabled:cursor-not-allowed disabled:border-rose-100 disabled:text-rose-300 dark:border-rose-500/40 dark:text-rose-200 dark:hover:bg-rose-500/10"
              >
                <Trash2 className="h-4 w-4" />
                Eliminar seleccionadas
              </button>
            </div>
          </div>
        </div>
        <p className="mb-3 text-xs text-muted">
          Haz doble clic en cualquier fila para editar el presupuesto al instante.
        </p>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[var(--app-border)] table-animate">
            <thead className="bg-[var(--app-surface-muted)]">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    onChange={(event) => handleToggleAll(event.target.checked)}
                    className="h-4 w-4 cursor-pointer rounded border border-[var(--app-border)] bg-[var(--app-surface)]"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  Periodo
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  Presupuesto
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  Tipo
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                  Planificado
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                  Ejecutado
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                  Disponible
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  Estado
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--app-border)]">
              {filteredEntries.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-muted">
                    No hay presupuestos que coincidan con los filtros actuales.
                  </td>
                </tr>
              ) : (
                filteredEntries.map((entry) => {
                  const entryDate = parseEntryDate(entry);
                  const status = getStatusPill(entry);
                  const isSelected = selectedEntryIds.includes(entry.id);
                  const startDate = parseDateOnly(entry.start_date);
                  const dueDate = parseDateOnly(entry.due_date);
                  const periodLabel = startDate && dueDate
                    ? `${formatDateForDisplay(startDate)} – ${formatDateForDisplay(dueDate)}`
                    : dueDate
                      ? formatDateForDisplay(dueDate)
                      : formatDateForDisplay(entryDate);
                  const remainingAmount = entry.remaining_amount ?? entry.budgeted_amount - entry.actual_amount;
                  return (
                    <tr
                      key={entry.id}
                      onDoubleClick={() => handleOpenModal(entry)}
                      className={`group cursor-pointer transition hover:bg-sky-50 dark:hover:bg-slate-800/70 ${
                        isSelected
                          ? "bg-sky-100/60 dark:bg-slate-800/60"
                          : "bg-[var(--app-surface)]"
                      }`}
                    >
                      <td className="px-4 py-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(event) =>
                            handleToggleEntry(entry.id, event.target.checked)
                          }
                          onDoubleClick={(event) => event.stopPropagation()}
                          className="h-4 w-4 cursor-pointer rounded border border-[var(--app-border)] bg-[var(--app-surface)]"
                        />
                      </td>
                      <td className="px-4 py-4 text-sm text-slate-600 dark:text-slate-200">
                        <div>{periodLabel}</div>
                        <div className="text-xs text-muted">{entry.frequency}</div>
                      </td>
                      <td className="px-4 py-4 text-sm font-semibold text-slate-900 dark:text-slate-100">
                        <span className="block max-w-xs truncate" title={entry.description ?? entry.category}>
                          {entry.description || entry.category}
                        </span>
                        <span className="mt-1 block text-xs font-medium text-muted">
                          {entry.category}
                          {entry.goal_name ? ` · Meta: ${entry.goal_name}` : ""}
                          {entry.debt_name ? ` · Deuda: ${entry.debt_name}` : ""}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm">
                        <span className="inline-flex rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-600 dark:text-indigo-300">
                          {entry.type}
                        </span>
                        {entry.is_recurring ? (
                          <span className="mt-1 block text-xs text-muted">Se repite automáticamente</span>
                        ) : null}
                      </td>
                      <td className="px-4 py-4 text-right text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {formatCurrency(entry.budgeted_amount)}
                      </td>
                      <td className="px-4 py-4 text-right text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {formatCurrency(entry.actual_amount)}
                      </td>
                      <td className={`px-4 py-4 text-right text-sm font-semibold ${
                        remainingAmount < 0
                          ? "text-rose-600 dark:text-rose-300"
                          : "text-slate-900 dark:text-slate-100"
                      }`}>
                        {formatCurrency(remainingAmount)}
                      </td>
                      <td className="px-4 py-4 text-sm text-muted">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${status.className}`}
                        >
                          {status.icon}
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right text-sm">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            onClick={() => handleOpenModal(entry)}
                            className="inline-flex items-center gap-1 rounded-full border border-sky-300 px-3 py-1.5 text-xs font-semibold text-sky-600 transition hover:border-sky-400 hover:text-sky-700 dark:border-sky-500/60 dark:text-sky-200"
                          >
                            Editar
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      <BudgetModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        entry={selectedEntry}
      />
    </div>
  );
}
