import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  Filter,
  Plus,
  RefreshCw,
  Scale,
  Target,
  Trash2,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { KeyboardEvent } from "react";

import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { useStore, TransactionFilters } from "../store/useStore";
import { apiPath } from "../utils/api";
import { formatDateForDisplay } from "../utils/date";

// Interfaces para los selects de los filtros
interface ParameterOption {
  id: number;
  value: string;
}

interface RecurringRule {
  id: number;
  description: string;
  amount: number;
  type: string;
  category: string;
  frequency: string;
  day_of_month?: number | null;
  day_of_month_2?: number | null;
  start_date?: string | null;
  last_processed_date?: string | null;
  next_run?: string | null;
}

type TransactionsTab = "all" | "goals" | "debts" | "recurring";

interface TabOption {
  key: TransactionsTab;
  label: string;
  count: number;
  icon: LucideIcon;
}

export function Transactions() {
  const {
    transactions,
    fetchTransactions,
    openTransactionModal,
    filters,
    setFilters,
  } = useStore();

  // Estados para poblar los selects de los filtros
  const [transactionTypes, setTransactionTypes] = useState<ParameterOption[]>([]);
  const [categories, setCategories] = useState<ParameterOption[]>([]);
  const [selectedTransactionIds, setSelectedTransactionIds] = useState<number[]>(
    []
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [activeTab, setActiveTab] = useState<TransactionsTab>("all");
  const [recurringTransactions, setRecurringTransactions] = useState<RecurringRule[]>([]);
  const [recurringLoading, setRecurringLoading] = useState(false);
  const [recurringError, setRecurringError] = useState<string | null>(null);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [tagFilterInput, setTagFilterInput] = useState("");

  const normalizeTagValue = useCallback((value: string) => value.replace(/^#+/, "").trim(), []);

  const { formatCurrency } = useNumberFormatter();
  const [listPulse, setListPulse] = useState(false);
  const transactionsInitialLoad = useRef(true);

  const totals = useMemo(() => {
    const dataset =
      activeTab === "recurring"
        ? transactions
        : transactions.filter((transaction) => {
            if (activeTab === "goals") {
              return Boolean(transaction.goal_id);
            }
            if (activeTab === "debts") {
              return Boolean(transaction.debt_id);
            }
            return true;
          });
    let incomeTotal = 0;
    let expenseTotal = 0;
    let incomeCount = 0;
    let expenseCount = 0;
    dataset.forEach((transaction) => {
      if (transaction.is_transfer) {
        return;
      }
      if (transaction.type === "Ingreso") {
        incomeTotal += transaction.amount;
        incomeCount += 1;
      } else {
        expenseTotal += transaction.amount;
        expenseCount += 1;
      }
    });
    return {
      income: incomeTotal,
      expense: expenseTotal,
      balance: incomeTotal - expenseTotal,
      incomeCount,
      expenseCount,
    };
  }, [transactions, activeTab]);

  const transactionCounts = useMemo(
    () => ({
      total: transactions.length,
      goals: transactions.filter((transaction) => Boolean(transaction.goal_id)).length,
      debts: transactions.filter((transaction) => Boolean(transaction.debt_id)).length,
    }),
    [transactions]
  );

  const tabOptions = useMemo<TabOption[]>(
    () => [
      {
        key: "all",
        label: "Movimientos",
        count: transactionCounts.total,
        icon: Wallet,
      },
      {
        key: "goals",
        label: "Metas",
        count: transactionCounts.goals,
        icon: Target,
      },
      {
        key: "debts",
        label: "Deudas",
        count: transactionCounts.debts,
        icon: Scale,
      },
      {
        key: "recurring",
        label: "Recurrentes",
        count: recurringTransactions.length,
        icon: RefreshCw,
      },
    ],
    [transactionCounts, recurringTransactions.length]
  );

  const filteredTransactions = useMemo(() => {
    if (activeTab === "goals") {
      return transactions.filter((transaction) => Boolean(transaction.goal_id));
    }
    if (activeTab === "debts") {
      return transactions.filter((transaction) => Boolean(transaction.debt_id));
    }
    return transactions;
  }, [transactions, activeTab]);

  const showTable = activeTab !== "recurring";

  useEffect(() => {
    if (transactionsInitialLoad.current) {
      transactionsInitialLoad.current = false;
      return;
    }
    setListPulse(true);
    const timeout = window.setTimeout(() => setListPulse(false), 650);
    return () => window.clearTimeout(timeout);
  }, [transactions]);

  // Carga inicial de datos para los filtros
  useEffect(() => {
    axios
      .get<ParameterOption[]>(apiPath("/parameters/transaction-types"))
      .then((res) => setTransactionTypes(res.data));
  }, []);

  useEffect(() => {
    let isMounted = true;
    axios
      .get<{ id: number; name: string }[]>(apiPath("/tags"))
      .then((res) => {
        if (!isMounted) return;
        const fetched = res.data
          .map((tag) => normalizeTagValue(tag.name))
          .filter((tag) => Boolean(tag));
        setAvailableTags((prev) => {
          const combined = new Set(prev);
          fetched.forEach((tag) => {
            if (tag) {
              combined.add(tag);
            }
          });
          return combined.size === prev.length ? prev : Array.from(combined);
        });
      })
      .catch((error) => {
        console.error("Error al obtener etiquetas disponibles:", error);
      });
    return () => {
      isMounted = false;
    };
  }, [normalizeTagValue]);

  useEffect(() => {
    setAvailableTags((prev) => {
      const combined = new Set(prev);
      transactions.forEach((transaction) => {
        (transaction.tags ?? []).forEach((tag) => {
          const sanitized = normalizeTagValue(tag);
          if (sanitized) {
            combined.add(sanitized);
          }
        });
      });
      return combined.size === prev.length ? prev : Array.from(combined);
    });
  }, [transactions, normalizeTagValue]);

  useEffect(() => {
    let isMounted = true;
    const loadRecurring = async () => {
      setRecurringLoading(true);
      setRecurringError(null);
      try {
        const response = await axios.get<RecurringRule[]>(
          apiPath("/recurring-transactions"),
        );
        if (!isMounted) return;
        setRecurringTransactions(response.data);
      } catch (error) {
        if (!isMounted) return;
        console.error("Error al obtener transacciones recurrentes:", error);
        setRecurringError(
          "No pudimos obtener tus transacciones recurrentes. Intenta nuevamente.",
        );
      } finally {
        if (isMounted) {
          setRecurringLoading(false);
        }
      }
    };

    loadRecurring();

    return () => {
      isMounted = false;
    };
  }, []);

  // Carga inicial de transacciones
  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  // --- FILTRADO EN TIEMPO REAL ---
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchTransactions();
    }, 400);

    return () => {
      clearTimeout(handler);
    };
  }, [filters, fetchTransactions]);

  // Carga las categorías cuando se selecciona un tipo en los filtros
  useEffect(() => {
    if (filters.type) {
      const typeObj = transactionTypes.find((t) => t.value === filters.type);
      if (typeObj) {
        axios
          .get<ParameterOption[]>(apiPath(`/parameters/categories/${typeObj.id}`))
          .then((res) => setCategories(res.data));
      }
    } else {
      setCategories([]);
      if (filters.category) {
        setFilters({ category: "" });
      }
    }
  }, [filters.type, filters.category, setFilters, transactionTypes]);

  // Limpia la selección cuando cambian los filtros o el listado base
  useEffect(() => {
    setSelectedTransactionIds([]);
    setCurrentPage(1);
  }, [filters, activeTab]);

  // Mantiene la selección sólo con transacciones existentes tras recargar
  useEffect(() => {
    setSelectedTransactionIds((prev) =>
      prev.filter((id) => filteredTransactions.some((t) => t.id === id))
    );
  }, [filteredTransactions]);

  useEffect(() => {
    const totalPages = Math.max(
      1,
      Math.ceil(filteredTransactions.length / pageSize),
    );
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [filteredTransactions, currentPage, pageSize]);

  useEffect(() => {
    setCurrentPage(1);
  }, [pageSize]);

  const handleFilterChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    const typedName = name as keyof TransactionFilters;
    if (filters[typedName] === value) {
      return;
    }

    setFilters({ [typedName]: value } as Partial<TransactionFilters>);
  };

  const handleAddFilterTag = useCallback(
    (value: string) => {
      const sanitized = normalizeTagValue(value);
      if (!sanitized) {
        return false;
      }
      const exists = filters.tags.some(
        (tag) => normalizeTagValue(tag).toLowerCase() === sanitized.toLowerCase()
      );
      if (exists) {
        return false;
      }
      setFilters({ tags: [...filters.tags, sanitized] });
      return true;
    },
    [filters.tags, normalizeTagValue, setFilters]
  );

  const handleRemoveFilterTag = useCallback(
    (tagToRemove: string) => {
      const normalizedRemove = normalizeTagValue(tagToRemove).toLowerCase();
      const updated = filters.tags.filter(
        (tag) => normalizeTagValue(tag).toLowerCase() !== normalizedRemove
      );
      setFilters({ tags: updated });
    },
    [filters.tags, normalizeTagValue, setFilters]
  );

  const handleTagFilterKeyDown = useCallback(
    (event: KeyboardEvent<HTMLInputElement>) => {
      if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        if (handleAddFilterTag(tagFilterInput)) {
          setTagFilterInput("");
        }
      } else if (event.key === "Backspace" && !tagFilterInput && filters.tags.length > 0) {
        event.preventDefault();
        const updated = filters.tags.slice(0, -1);
        setFilters({ tags: updated });
      }
    },
    [filters.tags, handleAddFilterTag, setFilters, tagFilterInput]
  );

  const handleTagFilterBlur = useCallback(() => {
    if (handleAddFilterTag(tagFilterInput)) {
      setTagFilterInput("");
    }
  }, [handleAddFilterTag, tagFilterInput]);

  const tagFilterSuggestions = useMemo(() => {
    if (availableTags.length === 0) {
      return [] as string[];
    }
    const normalizedSelected = new Set(
      filters.tags.map((tag) => normalizeTagValue(tag).toLowerCase())
    );
    const searchTerm = normalizeTagValue(tagFilterInput).toLowerCase();
    return availableTags
      .filter((tag) => {
        const normalized = normalizeTagValue(tag).toLowerCase();
        if (!normalized || normalizedSelected.has(normalized)) {
          return false;
        }
        if (!searchTerm) {
          return true;
        }
        return normalized.includes(searchTerm);
      })
      .slice(0, 10);
  }, [availableTags, filters.tags, normalizeTagValue, tagFilterInput]);

  const handleTabChange = (tab: TransactionsTab) => {
    if (tab === activeTab) {
      return;
    }
    setActiveTab(tab);
    setCurrentPage(1);
    setSelectedTransactionIds([]);
  };

  const handleToggleTransaction = (id: number, checked: boolean) => {
    setSelectedTransactionIds((prev) => {
      if (checked) {
        if (prev.includes(id)) return prev;
        return [...prev, id];
      }
      return prev.filter((transactionId) => transactionId !== id);
    });
  };

  const handleToggleAll = (checked: boolean) => {
    setSelectedTransactionIds((prev) => {
      const pageIds = new Set(paginatedTransactions.map((t) => t.id));
      if (checked) {
        const merged = new Set([...prev, ...pageIds]);
        return Array.from(merged);
      }
      return prev.filter((id) => !pageIds.has(id));
    });
  };

  const handleDeleteSelected = async () => {
    if (selectedTransactionIds.length === 0) return;

    const confirmationMessage =
      selectedTransactionIds.length === 1
        ? "¿Seguro que quieres eliminar esta transacción?"
        : "¿Seguro que quieres eliminar las transacciones seleccionadas?";

    if (!window.confirm(confirmationMessage)) {
      return;
    }

    const adjustBalance = window.confirm(
      "¿Deseas ajustar los saldos de las cuentas asociadas a estas transacciones? Acepta para ajustar o cancela para mantener el saldo actual."
    );

    try {
      await Promise.all(
        selectedTransactionIds.map((id) =>
          axios.delete(apiPath(`/transactions/${id}`), {
            params: { adjust_balance: adjustBalance },
          })
        )
      );

      setSelectedTransactionIds([]);
      await fetchTransactions();
    } catch (error) {
      console.error("Error al eliminar las transacciones:", error);
    }
  };

  const paginatedTransactions = useMemo(() => {
    if (!showTable) {
      return [];
    }
    const startIndex = (currentPage - 1) * pageSize;
    return filteredTransactions.slice(startIndex, startIndex + pageSize);
  }, [filteredTransactions, currentPage, pageSize, showTable]);

  const totalPages = showTable
    ? Math.max(1, Math.ceil(filteredTransactions.length / pageSize))
    : 1;
  const pageNumbers = useMemo(
    () =>
      showTable
        ? Array.from({ length: totalPages }, (_, index) => index + 1)
        : [1],
    [showTable, totalPages]
  );

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPageSize(Number(e.target.value));
  };

  const isAllSelected =
    showTable &&
    paginatedTransactions.length > 0 &&
    paginatedTransactions.every((t) => selectedTransactionIds.includes(t.id));

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const formatRecurringDate = (value?: string | null) => {
    if (!value) {
      return "Sin fecha";
    }
    const formatted = formatDateForDisplay(value);
    return formatted || value;
  };

  const handleResetFilters = () => {
    setTagFilterInput("");
    setFilters({
      search: "",
      start_date: "",
      end_date: "",
      type: "",
      category: "",
      sort_by: "date_desc",
      tags: [],
    });
  };

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="section-title">Transacciones</h1>
        <p className="mt-1 max-w-2xl text-muted">
          Visualiza tus movimientos, aplica filtros avanzados y administra tu historial financiero sin perder el contexto del flujo de efectivo.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div className="glow-card glow-card--emerald sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600 dark:text-emerald-300">
                Ingresos
              </p>
              <p className="mt-2 text-3xl font-bold text-emerald-600 dark:text-emerald-200">
                {formatCurrency(totals.income)}
              </p>
            </div>
            <span className="rounded-full bg-emerald-500/15 p-3 text-emerald-600 dark:text-emerald-300">
              <TrendingUp className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            {totals.incomeCount} movimientos catalogados como ingresos.
          </p>
        </div>
        <div className="glow-card glow-card--rose sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-rose-600 dark:text-rose-300">
                Gastos
              </p>
              <p className="mt-2 text-3xl font-bold text-rose-600 dark:text-rose-200">
                {formatCurrency(totals.expense)}
              </p>
            </div>
            <span className="rounded-full bg-rose-500/15 p-3 text-rose-600 dark:text-rose-300">
              <TrendingDown className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            {totals.expenseCount} salidas registradas para el período filtrado.
          </p>
        </div>
        <div className="glow-card glow-card--slate sm:p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">
                Balance neto
              </p>
              <p
                className={`mt-2 text-3xl font-bold ${
                  totals.balance >= 0
                    ? "text-emerald-600 dark:text-emerald-200"
                    : "text-rose-600 dark:text-rose-200"
                }`}
              >
                {formatCurrency(totals.balance)}
              </p>
            </div>
            <span className="rounded-full bg-slate-500/15 p-3 text-slate-700 dark:text-slate-200">
              <Wallet className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-sm text-muted">
            Diferencia entre ingresos y gastos con los filtros aplicados.
          </p>
        </div>
      </section>

      <section className="app-card p-6">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Filtros inteligentes</h2>
            <p className="text-sm text-muted">
              Ajusta la búsqueda por descripción, fechas, tipo y ordenamiento.
            </p>
          </div>
          <Filter className="h-5 w-5 text-muted" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-6">
          <div className="xl:col-span-2">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Buscar
            </label>
            <input
              type="text"
              name="search"
              placeholder="Descripción o cuenta"
              value={filters.search}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200/60 dark:focus:ring-sky-500/40"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Desde
            </label>
            <input
              type="date"
              name="start_date"
              value={filters.start_date}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200/60 dark:focus:ring-sky-500/40"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Hasta
            </label>
            <input
              type="date"
              name="end_date"
              value={filters.end_date}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200/60 dark:focus:ring-sky-500/40"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Tipo
            </label>
            <select
              name="type"
              value={filters.type}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200/60 dark:focus:ring-sky-500/40"
            >
              <option value="">Todos</option>
              {transactionTypes.map((t) => (
                <option key={t.id} value={t.value}>
                  {t.value}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Categoría
            </label>
            <select
              name="category"
              value={filters.category}
              onChange={handleFilterChange}
              disabled={!filters.type}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200/60 dark:focus:ring-sky-500/40"
            >
              <option value="">Todas</option>
              {categories.map((c) => (
                <option key={c.id} value={c.value}>
                  {c.value}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Ordenar por
            </label>
            <select
              name="sort_by"
              value={filters.sort_by}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200/60 dark:focus:ring-sky-500/40"
            >
              <option value="date_desc">Más recientes</option>
              <option value="date_asc">Más antiguos</option>
              <option value="amount_desc">Monto (desc)</option>
              <option value="amount_asc">Monto (asc)</option>
            </select>
          </div>
          <div className="xl:col-span-2">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
              Etiquetas
            </label>
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2">
              {filters.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 rounded-full bg-sky-500/15 px-3 py-1 text-xs font-semibold text-sky-600 dark:text-sky-300"
                >
                  #{normalizeTagValue(tag)}
                  <button
                    type="button"
                    onClick={() => handleRemoveFilterTag(tag)}
                    className="rounded-full px-1 text-[10px] font-bold text-sky-600 transition hover:text-rose-500 dark:text-sky-200"
                    aria-label={`Quitar etiqueta ${tag}`}
                  >
                    ×
                  </button>
                </span>
              ))}
              <input
                type="text"
                value={tagFilterInput}
                onChange={(event) => setTagFilterInput(event.target.value.slice(0, 40))}
                onKeyDown={handleTagFilterKeyDown}
                onBlur={handleTagFilterBlur}
                placeholder={filters.tags.length === 0 ? "Ej. viaje-playa-2024" : "Agregar etiqueta"}
                className="min-w-[140px] flex-1 border-none bg-transparent text-sm text-[var(--app-text)] focus:outline-none"
              />
            </div>
            {tagFilterSuggestions.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
                <span>Sugerencias:</span>
                {tagFilterSuggestions.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => {
                      if (handleAddFilterTag(tag)) {
                        setTagFilterInput("");
                      }
                    }}
                    className="rounded-full border border-sky-400/70 px-2 py-1 font-semibold text-sky-600 transition hover:border-sky-400 hover:text-sky-500 dark:text-sky-300"
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={handleResetFilters}
            className="text-sm font-semibold text-sky-600 transition hover:text-sky-500 dark:text-sky-300 dark:hover:text-sky-200"
          >
            Limpiar filtros
          </button>
        </div>
      </section>

      <section
        className={`app-card overflow-hidden p-0 ${listPulse ? "list-highlight" : ""}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--app-border)] bg-[var(--app-surface-muted)] px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">Movimientos registrados</h2>
            <p className="text-sm text-muted">
              Selecciona filas para editarlas o eliminarlas rápidamente o haz doble clic para abrir una transacción al instante.
            </p>
          </div>
          <div className="flex flex-col items-end gap-3 sm:flex-row sm:items-center">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => openTransactionModal(null)}
                className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-500/30 transition hover:bg-sky-500"
              >
                <Plus className="h-4 w-4" />
                Nueva transacción
              </button>
              <button
                type="button"
                onClick={handleDeleteSelected}
                disabled={selectedTransactionIds.length === 0}
                className="inline-flex items-center gap-2 rounded-lg border border-rose-500/60 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:border-rose-400 hover:text-rose-500 disabled:cursor-not-allowed disabled:border-rose-200 disabled:text-rose-300 dark:text-rose-200 dark:hover:text-rose-100"
              >
                <Trash2 className="h-4 w-4" />
                Eliminar
                {selectedTransactionIds.length > 0 && (
                  <span className="ml-1 rounded-full bg-rose-500/20 px-2 py-0.5 text-xs">
                    {selectedTransactionIds.length}
                  </span>
                )}
              </button>
            </div>
            <span className="text-sm text-muted">
              {transactions.length} transacciones encontradas
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 border-b border-[var(--app-border)] bg-[var(--app-surface)] px-6 py-3">
          {tabOptions.map((option) => {
            const isActive = activeTab === option.key;
            const Icon = option.icon;
            return (
              <button
                key={option.key}
                type="button"
                onClick={() => handleTabChange(option.key)}
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/60 ${
                  isActive
                    ? "bg-sky-600 text-white shadow shadow-sky-500/30"
                    : "border border-[var(--app-border)] bg-[var(--app-surface-muted)] text-muted hover:border-sky-400 hover:text-sky-600 dark:hover:text-sky-300"
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? "text-white" : "text-sky-500 dark:text-sky-300"}`} />
                <span>{option.label}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                    isActive
                      ? "bg-white/20 text-white"
                      : "bg-[var(--app-surface)] text-muted"
                  }`}
                >
                  {option.count}
                </span>
              </button>
            );
          })}
        </div>
        <div key={activeTab} className="tab-transition">
          {showTable ? (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-[var(--app-border)] table-animate">
                <thead className="bg-[var(--app-surface-muted)]">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                      <input
                        type="checkbox"
                        checked={isAllSelected}
                        onChange={(e) => handleToggleAll(e.target.checked)}
                        className="h-4 w-4 cursor-pointer rounded border border-[var(--app-border)]"
                      />
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                      Fecha
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                      Descripción
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                      Cuenta
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                      Tipo
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                      Categoría
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                      Monto
                    </th>
                  </tr>
                </thead>
                  <tbody className="divide-y divide-[var(--app-border)]">
                  {paginatedTransactions.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-10 text-center text-muted">
                        No se encontraron transacciones con los filtros seleccionados.
                      </td>
                    </tr>
                  ) : (
                    paginatedTransactions.map((t) => {
                      const isSelected = selectedTransactionIds.includes(t.id);
                      const isIncome = t.type === "Ingreso";
                      const isTransfer = Boolean(t.is_transfer);
                      const splits = t.splits ?? [];
                      const hasSplits = splits.length > 0;
                      const amountClass = isTransfer
                        ? "text-muted"
                        : isIncome
                          ? "text-emerald-600 dark:text-emerald-300"
                          : "text-rose-600 dark:text-rose-300";
                      const typeBadgeClass = isTransfer
                        ? "bg-indigo-500/15 text-indigo-600 dark:text-indigo-300"
                        : isIncome
                          ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300"
                          : "bg-rose-500/15 text-rose-600 dark:text-rose-300";
                      return (
                        <tr
                          key={t.id}
                          onDoubleClick={() => openTransactionModal(t)}
                          className={`group cursor-pointer transition hover:bg-[var(--app-surface-muted)] ${
                            isSelected ? "bg-[var(--app-surface-muted)]" : ""
                          }`}
                        >
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) => handleToggleTransaction(t.id, e.target.checked)}
                              onDoubleClick={(e) => e.stopPropagation()}
                              className="h-4 w-4 cursor-pointer rounded border border-[var(--app-border)]"
                            />
                          </td>
                          <td className="px-4 py-3 text-sm text-muted">
                            {formatDateForDisplay(t.date) || t.date}
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-[var(--app-text)]">
                            <div className="flex flex-col gap-1">
                              <span className="block max-w-xs truncate" title={t.description}>
                                {t.description}
                              </span>
                              {(t.goal_name || t.debt_name) && (
                                <div className="flex flex-wrap gap-2 text-xs text-muted">
                                  {t.goal_name && (
                                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-emerald-600 dark:text-emerald-300">
                                      Meta: {t.goal_name}
                                    </span>
                                  )}
                                  {t.debt_name && (
                                    <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-rose-600 dark:text-rose-300">
                                      Deuda: {t.debt_name}
                                    </span>
                                  )}
                                </div>
                              )}
                              {isTransfer && t.transfer_account_name && (
                                <span className="text-xs text-muted">
                                  Transferencia hacia {t.transfer_account_name}
                                </span>
                              )}
                              {t.tags && t.tags.length > 0 && (
                                <div className="flex flex-wrap gap-2 text-xs text-muted">
                                  {t.tags.map((tag) => {
                                    const sanitized = normalizeTagValue(tag);
                                    return (
                                      <span
                                        key={tag}
                                        className="inline-flex items-center gap-1 rounded-full bg-sky-500/15 px-2 py-0.5 font-semibold text-sky-600 dark:text-sky-300"
                                      >
                                        #{sanitized || tag}
                                      </span>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-muted">
                            {t.account?.name ?? "-"}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span
                              className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${typeBadgeClass}`}
                            >
                              {isTransfer ? "Transferencia" : t.type}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-muted">
                            {isTransfer ? (
                              <div className="space-y-1">
                                <span className="inline-flex rounded-full bg-[var(--app-surface-muted)] px-3 py-1 text-xs font-semibold text-[var(--app-text)]">
                                  Transferencia interna
                                </span>
                                <span className="block text-xs text-muted">
                                  Destino: {t.transfer_account_name ?? "Sin cuenta definida"}
                                </span>
                              </div>
                            ) : hasSplits ? (
                              <div className="space-y-2">
                                <span className="inline-flex rounded-full bg-[var(--app-surface-muted)] px-3 py-1 text-xs font-semibold text-[var(--app-text)]">
                                  Múltiples categorías
                                </span>
                                <div className="space-y-1 text-xs">
                                  {splits.map((split, splitIndex) => (
                                    <div
                                      key={`${split.category}-${splitIndex}`}
                                      className="flex items-center justify-between gap-2 text-muted"
                                    >
                                      <span className="truncate">{split.category}</span>
                                      <span className="font-semibold text-[var(--app-text)]">
                                        {formatCurrency(split.amount)}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <span className="inline-flex rounded-full bg-[var(--app-surface-muted)] px-3 py-1 text-xs">
                                {t.category}
                              </span>
                            )}
                          </td>
                          <td
                            className={`px-4 py-3 text-right text-sm font-semibold ${amountClass}`}
                          >
                            {formatCurrency(t.amount)}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
                </table>
              </div>
              <div className="flex flex-col gap-4 border-t border-[var(--app-border)] bg-[var(--app-surface)] px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center gap-2 text-sm text-muted">
                <span>Mostrar</span>
                <select
                  value={pageSize}
                  onChange={handlePageSizeChange}
                  className="rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-2 py-1 text-sm focus:border-sky-400 focus:outline-none"
                >
                  {[5, 10, 20, 50].map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
                <span>por página</span>
              </div>
              <div className="flex flex-col items-center gap-3 text-sm text-muted md:flex-row md:gap-4">
                <span>
                  Página {currentPage} de {totalPages}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="rounded-lg border border-[var(--app-border)] px-3 py-1 transition hover:border-sky-400 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Anterior
                  </button>
                  {pageNumbers.map((page) => (
                    <button
                      key={page}
                      type="button"
                      onClick={() => handlePageChange(page)}
                      className={`rounded-lg px-3 py-1 text-sm font-semibold transition ${
                        currentPage === page
                          ? "bg-sky-600 text-white"
                          : "border border-[var(--app-border)] hover:border-sky-400"
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="rounded-lg border border-[var(--app-border)] px-3 py-1 transition hover:border-sky-400 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
              </div>
            </>
          ) : (
            <div className="px-6 py-6">
              {recurringLoading ? (
                <p className="text-sm text-muted">Cargando transacciones recurrentes...</p>
              ) : recurringError ? (
                <p className="rounded-xl border border-rose-300/60 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:border-rose-400/40 dark:bg-rose-500/10 dark:text-rose-200">
                  {recurringError}
                </p>
              ) : recurringTransactions.length === 0 ? (
                <p className="text-sm text-muted">
                  Aún no registras transacciones recurrentes. Marca una transacción como recurrente desde el formulario para que aparezca aquí.
                </p>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 card-animate">
                  {recurringTransactions.map((rule) => {
                    const isIncome = rule.type === "Ingreso";
                    return (
                      <div
                        key={rule.id}
                        className="rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] p-4"
                      >
                        <div className="flex items-center justify-between">
                          <h3 className="text-base font-semibold">{rule.description}</h3>
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${
                              isIncome
                                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300"
                                : "bg-rose-500/15 text-rose-600 dark:text-rose-300"
                            }`}
                          >
                            {rule.type}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-muted">
                          Monto: <span className="font-semibold">{formatCurrency(rule.amount)}</span>
                        </p>
                        <p className="text-sm text-muted">Categoría: {rule.category}</p>
                        <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
                          <span className="inline-flex items-center gap-2 rounded-full bg-[var(--app-surface)] px-3 py-1">
                            Frecuencia: {rule.frequency}
                          </span>
                          <span className="inline-flex items-center gap-2 rounded-full bg-[var(--app-surface)] px-3 py-1">
                            Próxima ejecución: {formatRecurringDate(rule.next_run)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
