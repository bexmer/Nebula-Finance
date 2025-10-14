import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  Calendar,
  CheckCircle2,
  Clock,
  PiggyBank,
  Plus,
  Target,
  Trash2,
} from "lucide-react";
import { BudgetModal } from "../components/BudgetModal";
import { useStore } from "../store/useStore";
import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { apiPath } from "../utils/api";
import { normalizeDateInputValue } from "../utils/date";

interface BudgetEntry {
  id: number;
  category: string;
  amount: number;
  budgeted_amount?: number;
  type: string;
  month?: number;
  year?: number;
  description?: string;
  due_date?: string | null;
  goal_id?: number | null;
  goal_name?: string | null;
  debt_id?: number | null;
  debt_name?: string | null;
}

interface ParameterOption {
  id: number;
  value: string;
}

interface BudgetSummary {
  planned: number;
  upcoming: number;
  overdue: number;
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
  const { openTransactionModal } = useStore();
  const { formatCurrency } = useNumberFormatter();
  const [listPulse, setListPulse] = useState(false);
  const budgetInitialLoad = useRef(true);

  const fetchBudgetEntries = async () => {
    const response = await axios.get<BudgetEntry[]>(apiPath("/budget"));
    const entries = response.data.map((entry) => ({
      ...entry,
      amount: entry.amount ?? entry.budgeted_amount ?? 0,
    }));
    setBudgetEntries(entries);
    setSelectedEntryIds([]);
  };

  useEffect(() => {
    fetchBudgetEntries();
  }, []);

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
    if (entry.due_date) {
      return new Date(entry.due_date);
    }
    if (entry.year && entry.month) {
      return new Date(entry.year, entry.month - 1, 1);
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
          `${entry.description ?? ""} ${entry.category}`
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
    const today = new Date();
    const next30 = new Date();
    next30.setDate(today.getDate() + 30);

    let planned = 0;
    let upcoming = 0;
    let overdue = 0;
    let nextEntry: { amount: number; description: string; date: Date } | null = null;

    budgetEntries.forEach((entry) => {
      const date = parseEntryDate(entry);
      const amount = entry.amount ?? 0;
      planned += amount;
      if (date < today) {
        overdue += 1;
      } else if (date <= next30) {
        upcoming += amount;
      }

      if (!nextEntry || date < nextEntry.date) {
        nextEntry = {
          amount,
          description: entry.description || entry.category,
          date,
        };
      }
    });

    return { planned, upcoming, overdue, nextEntry };
  }, [budgetEntries, parseEntryDate]);

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

  const handleRegisterPayment = (entry: BudgetEntry) => {
    const entryDate = parseEntryDate(entry);
    const shouldDelete = window.confirm(
      "¿Deseas eliminar esta entrada de presupuesto después de registrar el pago?"
    );

    openTransactionModal(
      null,
      {
        description: entry.description || `Pago de ${entry.category}`,
        amount: entry.amount,
        date: normalizeDateInputValue(entryDate),
        type: entry.type || "Gasto",
        category: entry.category,
        goal_id: entry.goal_id ?? undefined,
        debt_id: entry.debt_id ?? undefined,
      },
      async () => {
        try {
          if (shouldDelete) {
            await axios.delete(apiPath(`/budget/${entry.id}`));
          }
        } catch (error) {
          console.error("Error al eliminar la entrada de presupuesto:", error);
        } finally {
          await fetchBudgetEntries();
        }
      }
    );
  };

  const resetFilters = () => {
    setSearchTerm("");
    setTypeFilter("");
    setMonthFilter("all");
    setYearFilter("all");
  };

  const getStatusPill = (entry: BudgetEntry) => {
    const date = parseEntryDate(entry);
    const today = new Date();
    const diffDays = Math.floor(
      (date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
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
      className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-200",
      icon: <CheckCircle2 className="h-3.5 w-3.5" />,
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
                Próximos 30 días
              </p>
              <p className="mt-2 text-3xl font-bold text-sky-600 dark:text-sky-200">
                {formatCurrency(totals.upcoming)}
              </p>
            </div>
            <span className="rounded-full bg-sky-500/15 p-3 text-sky-600 dark:text-sky-300">
              <Calendar className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            Pagos que vencen durante el siguiente mes.
          </p>
        </div>
        <div className="glow-card glow-card--amber sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-600 dark:text-amber-300">
                Vencidos
              </p>
              <p className="mt-2 text-3xl font-bold text-amber-600 dark:text-amber-200">{totals.overdue}</p>
            </div>
            <span className="rounded-full bg-amber-500/15 p-3 text-amber-600 dark:text-amber-300">
              <Clock className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            Entradas cuya fecha comprometida ya pasó.
          </p>
        </div>
        <div className="glow-card glow-card--rose sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-rose-600 dark:text-rose-300">
                Próxima salida
              </p>
              <p className="mt-2 text-xl font-semibold text-rose-600 dark:text-rose-200">
                {totals.nextEntry
                  ? formatCurrency(totals.nextEntry.amount)
                  : "Sin registros"}
              </p>
            </div>
            <span className="rounded-full bg-rose-500/15 p-3 text-rose-600 dark:text-rose-300">
              <Target className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            {totals.nextEntry
              ? `${totals.nextEntry.description} · ${totals.nextEntry.date.toLocaleDateString()}`
              : "Registra tu primer presupuesto"}
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
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
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
                  Fecha
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  Descripción
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  Categoría
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  Tipo
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                  Estado
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                  Monto
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
                        {entryDate.toLocaleDateString()}
                      </td>
                      <td className="px-4 py-4 text-sm font-semibold text-slate-900 dark:text-slate-100">
                        <span className="block max-w-xs truncate" title={entry.description ?? entry.category}>
                          {entry.description || entry.category}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm text-muted">
                        <span className="inline-flex rounded-full bg-[var(--app-surface-muted)] px-3 py-1 text-xs font-medium text-muted">
                          {entry.category}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm">
                        <span className="inline-flex rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-600 dark:text-indigo-300">
                          {entry.type}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm text-muted">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${status.className}`}
                        >
                          {status.icon}
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {formatCurrency(entry.amount)}
                      </td>
                      <td className="px-4 py-4 text-right text-sm">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            onClick={() => handleRegisterPayment(entry)}
                            className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-600 transition hover:bg-emerald-500/15 dark:text-emerald-300"
                          >
                            Registrar pago
                          </button>
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
