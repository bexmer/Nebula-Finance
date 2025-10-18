import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

import { apiPath } from "../utils/api";
import { formatDateForDisplay } from "../utils/date";
import { useNumberFormatter } from "../context/DisplayPreferencesContext";

export interface BudgetPickerItem {
  id: number;
  description?: string;
  category: string;
  type: string;
  frequency: string;
  budgeted_amount: number;
  actual_amount: number;
  remaining_amount: number;
  over_budget_amount: number;
  start_date?: string | null;
  end_date?: string | null;
  due_date?: string | null;
  goal_id?: number | null;
  goal_name?: string | null;
  debt_id?: number | null;
  debt_name?: string | null;
  is_recurring?: boolean;
}

type BudgetStatusFilter = "all" | "active" | "upcoming" | "archived";

type BudgetPickerMode = "select" | "pay";

interface BudgetPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (entry: BudgetPickerItem | null) => void;
  selectedId?: number | null;
  title?: string;
  actionLabel?: string;
  mode?: BudgetPickerMode;
}

const STATUS_OPTIONS: { value: BudgetStatusFilter; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "active", label: "Activos" },
  { value: "upcoming", label: "Próximos" },
  { value: "archived", label: "Archivados" },
];

const PAGE_SIZE_OPTIONS = [5, 10, 20, 50];

export function BudgetPickerModal({
  isOpen,
  onClose,
  onSelect,
  selectedId = null,
  title = "Seleccionar presupuesto",
  actionLabel,
  mode = "select",
}: BudgetPickerModalProps) {
  const { formatCurrency } = useNumberFormatter();
  const [statusFilter, setStatusFilter] = useState<BudgetStatusFilter>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [entries, setEntries] = useState<BudgetPickerItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [internalSelection, setInternalSelection] = useState<number | null>(selectedId);

  useEffect(() => {
    if (isOpen) {
      setInternalSelection(selectedId ?? null);
    }
  }, [isOpen, selectedId]);

  const fetchBudgets = useCallback(async () => {
    if (!isOpen) {
      return;
    }
    setLoading(true);
    setError(null);

    const params: Record<string, string> = {};
    if (statusFilter !== "all") {
      params.status = statusFilter;
    }

    try {
      const response = await axios.get<BudgetPickerItem[]>(apiPath("/budget"), {
        params,
      });
      const normalized = response.data.map((entry) => {
        const planned = entry.budgeted_amount ?? (entry as any).amount ?? 0;
        const actual = entry.actual_amount ?? 0;
        const remaining =
          entry.remaining_amount !== undefined && entry.remaining_amount !== null
            ? entry.remaining_amount
            : planned - actual;
        const overBudget =
          entry.over_budget_amount !== undefined && entry.over_budget_amount !== null
            ? entry.over_budget_amount
            : Math.max(actual - planned, 0);
        return {
          ...entry,
          budgeted_amount: planned,
          actual_amount: actual,
          remaining_amount: remaining,
          over_budget_amount: overBudget,
        };
      });
      setEntries(normalized);
    } catch (requestError) {
      console.error("Error al obtener los presupuestos disponibles:", requestError);
      setError("No pudimos cargar los presupuestos. Inténtalo más tarde.");
    } finally {
      setLoading(false);
    }
  }, [isOpen, statusFilter]);

  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, searchTerm, pageSize]);

  useEffect(() => {
    fetchBudgets();
  }, [fetchBudgets]);

  const filteredEntries = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    if (!normalizedSearch) {
      return entries;
    }
    return entries.filter((entry) => {
      const haystack = `${entry.description ?? ""} ${entry.category} ${entry.type}`.toLowerCase();
      return haystack.includes(normalizedSearch);
    });
  }, [entries, searchTerm]);

  const totalPages = Math.max(1, Math.ceil(filteredEntries.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const offset = (safePage - 1) * pageSize;
  const pageEntries = filteredEntries.slice(offset, offset + pageSize);

  const activeSelection = useMemo(() => {
    if (internalSelection == null) {
      return null;
    }
    return entries.find((entry) => entry.id === internalSelection) ?? null;
  }, [entries, internalSelection]);

  const handleConfirm = () => {
    onSelect(activeSelection ?? null);
    onClose();
  };

  const handleClear = () => {
    setInternalSelection(null);
    onSelect(null);
    onClose();
  };

  const handleCancel = () => {
    if (mode === "pay") {
      onClose();
      return;
    }
    handleClear();
  };

  const cancelLabel = mode === "pay" ? "Cancelar" : "Quitar asociación";

  if (!isOpen) {
    return null;
  }

  return (
    <div className="app-modal-overlay">
      <div className="app-modal-panel app-card w-full max-w-4xl p-6">
        <div className="flex items-start justify-between gap-4 border-b border-[var(--app-border)] pb-4">
          <div>
            <h2 className="text-xl font-semibold text-[var(--app-text)]">{title}</h2>
            <p className="text-sm text-muted">
              {mode === "pay"
                ? "Selecciona el presupuesto que deseas pagar sin importar su fecha."
                : "Busca y elige el presupuesto adecuado para vincularlo con la transacción."}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[var(--app-border)] px-3 py-1 text-sm font-semibold text-muted transition hover:border-slate-400 hover:text-slate-700"
          >
            Cerrar
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <p className="text-sm text-muted">
            {mode === "pay"
              ? "Selecciona el presupuesto que deseas pagar, sin importar su estado o fecha programada."
              : "Explora tus presupuestos disponibles y vincula el que corresponda a tu movimiento."}
          </p>
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div className="flex flex-wrap gap-3">
              {STATUS_OPTIONS.map((option) => {
                const isActive = option.value === statusFilter;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setStatusFilter(option.value)}
                    className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                      isActive
                        ? "bg-sky-600 text-white shadow shadow-sky-500/30"
                        : "border border-[var(--app-border)] bg-[var(--app-surface-muted)] text-muted hover:border-sky-400 hover:text-sky-600"
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
            <div className="flex flex-col gap-2 md:flex-row md:items-center">
              <label className="text-xs font-semibold uppercase tracking-wide text-muted" htmlFor="budget-picker-search">
                Buscar
              </label>
              <input
                id="budget-picker-search"
                type="text"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Descripción, categoría o tipo"
                className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-[var(--app-text)] focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 md:w-80"
              />
            </div>
          </div>

          {error ? (
            <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-[var(--app-border)]">
              <thead className="bg-[var(--app-surface-muted)]">
                <tr>
                  <th className="w-12 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                    Seleccionar
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
                    Periodo
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--app-border)]">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted">
                      Cargando presupuestos...
                    </td>
                  </tr>
                ) : pageEntries.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted">
                      No encontramos presupuestos con los filtros actuales.
                    </td>
                  </tr>
                ) : (
                  pageEntries.map((entry) => {
                    const isSelected = entry.id === internalSelection;
                    const statusLabel =
                      entry.remaining_amount < 0
                        ? "Excedido"
                        : entry.remaining_amount === 0
                        ? "Completado"
                        : "Disponible";
                    const periodDate = entry.due_date || entry.end_date || entry.start_date;
                    const periodText = periodDate
                      ? formatDateForDisplay(periodDate)
                      : "Sin fecha";
                    return (
                      <tr
                        key={entry.id}
                        onDoubleClick={() => {
                          setInternalSelection(entry.id);
                          onSelect(entry);
                          onClose();
                        }}
                        className="cursor-pointer transition hover:bg-[var(--app-surface-muted)]"
                      >
                        <td className="px-4 py-3">
                          <input
                            type="radio"
                            name="budget-picker-selection"
                            checked={isSelected}
                            onChange={() => setInternalSelection(entry.id)}
                            className="h-4 w-4"
                          />
                        </td>
                        <td className="px-4 py-3 text-sm text-[var(--app-text)]">
                          <span className="font-semibold">{entry.description || entry.category}</span>
                          <span className="mt-1 block text-xs text-muted">
                            {entry.category}
                            {entry.goal_name ? ` · Meta: ${entry.goal_name}` : ""}
                            {entry.debt_name ? ` · Deuda: ${entry.debt_name}` : ""}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-[var(--app-text)]">
                          <span className="inline-flex rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-600 dark:text-indigo-300">
                            {entry.type}
                          </span>
                          {entry.is_recurring ? (
                            <span className="mt-1 block text-xs text-muted">Se repite automáticamente</span>
                          ) : null}
                        </td>
                        <td className="px-4 py-3 text-right text-sm font-semibold text-[var(--app-text)]">
                          {formatCurrency(entry.budgeted_amount)}
                        </td>
                        <td className="px-4 py-3 text-right text-sm font-semibold text-[var(--app-text)]">
                          {formatCurrency(entry.actual_amount)}
                        </td>
                        <td
                          className={`px-4 py-3 text-right text-sm font-semibold ${
                            entry.remaining_amount < 0
                              ? "text-rose-600 dark:text-rose-300"
                              : "text-[var(--app-text)]"
                          }`}
                        >
                          {formatCurrency(entry.remaining_amount)}
                          <span className="mt-1 block text-xs text-muted">{statusLabel}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-muted">{periodText}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-4 border-t border-[var(--app-border)] bg-[var(--app-surface)] px-4 py-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-2 text-sm text-muted">
              <span>Mostrar</span>
              <select
                value={pageSize}
                onChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setCurrentPage(1);
                }}
                className="rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-2 py-1 text-sm focus:border-sky-400 focus:outline-none"
              >
                {PAGE_SIZE_OPTIONS.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
              <span>por página</span>
            </div>
            <div className="flex items-center justify-between gap-3 text-sm text-muted md:justify-end">
              <span>
                Página {safePage} de {totalPages}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                  disabled={safePage === 1}
                  className="rounded-lg border border-[var(--app-border)] px-3 py-1 transition hover:border-sky-400 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Anterior
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                  disabled={safePage === totalPages}
                  className="rounded-lg border border-[var(--app-border)] px-3 py-1 transition hover:border-sky-400 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Siguiente
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 border-t border-[var(--app-border)] pt-4 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={handleCancel}
            className="w-full rounded-xl border border-[var(--app-border)] bg-transparent px-4 py-2 text-sm font-semibold text-muted transition hover:border-slate-400 hover:text-slate-700 sm:w-auto"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!activeSelection}
            className="w-full rounded-xl bg-gradient-to-r from-sky-500 via-indigo-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-500/30 transition hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
          >
            {actionLabel ?? (mode === "pay" ? "Registrar pago" : "Seleccionar presupuesto")}
          </button>
        </div>
      </div>
    </div>
  );
}
