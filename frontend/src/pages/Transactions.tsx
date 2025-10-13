import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Filter, Plus, Trash2, TrendingDown, TrendingUp, Wallet } from "lucide-react";

import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { useStore, TransactionFilters } from "../store/useStore";
import { apiPath } from "../utils/api";

// Interfaces para los selects de los filtros
interface ParameterOption {
  id: number;
  value: string;
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

  const { formatCurrency } = useNumberFormatter();

  const totals = useMemo(() => {
    let incomeTotal = 0;
    let expenseTotal = 0;
    transactions.forEach((transaction) => {
      if (transaction.type === "Ingreso") {
        incomeTotal += transaction.amount;
      } else {
        expenseTotal += transaction.amount;
      }
    });
    return {
      income: incomeTotal,
      expense: expenseTotal,
      balance: incomeTotal - expenseTotal,
      incomeCount: transactions.filter((t) => t.type === "Ingreso").length,
      expenseCount: transactions.filter((t) => t.type !== "Ingreso").length,
    };
  }, [transactions]);

  // Carga inicial de datos para los filtros
  useEffect(() => {
    axios
      .get<ParameterOption[]>(apiPath("/parameters/transaction-types"))
      .then((res) => setTransactionTypes(res.data));
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
  }, [filters]);

  // Mantiene la selección sólo con transacciones existentes tras recargar
  useEffect(() => {
    setSelectedTransactionIds((prev) =>
      prev.filter((id) => transactions.some((t) => t.id === id))
    );
  }, [transactions]);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(transactions.length / pageSize));
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [transactions, currentPage, pageSize]);

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
    const startIndex = (currentPage - 1) * pageSize;
    return transactions.slice(startIndex, startIndex + pageSize);
  }, [transactions, currentPage, pageSize]);

  const totalPages = Math.max(1, Math.ceil(transactions.length / pageSize));
  const pageNumbers = useMemo(
    () => Array.from({ length: totalPages }, (_, index) => index + 1),
    [totalPages]
  );

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPageSize(Number(e.target.value));
  };

  const isAllSelected =
    paginatedTransactions.length > 0 &&
    paginatedTransactions.every((t) => selectedTransactionIds.includes(t.id));

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleResetFilters = () => {
    setFilters({
      search: "",
      start_date: "",
      end_date: "",
      type: "",
      category: "",
      sort_by: "date_desc",
    });
  };

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold">Transacciones</h1>
        <p className="text-gray-400 mt-1 max-w-2xl">
          Visualiza tus movimientos, aplica filtros avanzados y administra tu historial financiero sin perder el contexto del flujo de efectivo.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-2xl border border-emerald-500/40 bg-gray-900/60 p-5 shadow-xl shadow-emerald-500/10">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm uppercase tracking-wide text-emerald-300/80">Ingresos</p>
              <p className="mt-2 text-3xl font-bold text-emerald-300">
                {formatCurrency(totals.income)}
              </p>
            </div>
            <span className="rounded-full bg-emerald-500/15 p-3">
              <TrendingUp className="h-5 w-5 text-emerald-300" />
            </span>
          </div>
          <p className="mt-3 text-sm text-gray-400">
            {totals.incomeCount} movimientos catalogados como ingresos.
          </p>
        </div>
        <div className="rounded-2xl border border-rose-500/40 bg-gray-900/60 p-5 shadow-xl shadow-rose-500/10">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm uppercase tracking-wide text-rose-300/80">Gastos</p>
              <p className="mt-2 text-3xl font-bold text-rose-300">
                {formatCurrency(totals.expense)}
              </p>
            </div>
            <span className="rounded-full bg-rose-500/15 p-3">
              <TrendingDown className="h-5 w-5 text-rose-300" />
            </span>
          </div>
          <p className="mt-3 text-sm text-gray-400">
            {totals.expenseCount} salidas registradas para el período filtrado.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-500/40 bg-gray-900/60 p-5 shadow-xl shadow-slate-500/10">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm uppercase tracking-wide text-slate-300/80">Balance neto</p>
              <p
                className={`mt-2 text-3xl font-bold ${
                  totals.balance >= 0 ? "text-emerald-200" : "text-rose-200"
                }`}
              >
                {formatCurrency(totals.balance)}
              </p>
            </div>
            <span className="rounded-full bg-slate-500/15 p-3">
              <Wallet className="h-5 w-5 text-slate-200" />
            </span>
          </div>
          <p className="mt-3 text-sm text-gray-400">
            Diferencia entre ingresos y gastos con los filtros aplicados.
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-gray-700/60 bg-gray-900/70 p-6 shadow-xl shadow-black/30">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Filtros inteligentes</h2>
            <p className="text-sm text-gray-400">
              Ajusta la búsqueda por descripción, fechas, tipo y ordenamiento.
            </p>
          </div>
          <Filter className="h-5 w-5 text-gray-500" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-6">
          <div className="xl:col-span-2">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-400">
              Buscar
            </label>
            <input
              type="text"
              name="search"
              placeholder="Descripción o cuenta"
              value={filters.search}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-gray-700 bg-gray-800/80 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-400">
              Desde
            </label>
            <input
              type="date"
              name="start_date"
              value={filters.start_date}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-gray-700 bg-gray-800/80 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-400">
              Hasta
            </label>
            <input
              type="date"
              name="end_date"
              value={filters.end_date}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-gray-700 bg-gray-800/80 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-400">
              Tipo
            </label>
            <select
              name="type"
              value={filters.type}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-gray-700 bg-gray-800/80 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
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
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-400">
              Categoría
            </label>
            <select
              name="category"
              value={filters.category}
              onChange={handleFilterChange}
              disabled={!filters.type}
              className="w-full rounded-lg border border-gray-700 bg-gray-800/80 px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40 focus:border-blue-500 focus:outline-none"
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
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-400">
              Ordenar por
            </label>
            <select
              name="sort_by"
              value={filters.sort_by}
              onChange={handleFilterChange}
              className="w-full rounded-lg border border-gray-700 bg-gray-800/80 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="date_desc">Más recientes</option>
              <option value="date_asc">Más antiguos</option>
              <option value="amount_desc">Monto (desc)</option>
              <option value="amount_asc">Monto (asc)</option>
            </select>
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={handleResetFilters}
            className="text-sm font-semibold text-blue-300 transition hover:text-blue-200"
          >
            Limpiar filtros
          </button>
        </div>
      </section>

      <section className="rounded-2xl border border-gray-700/60 bg-gray-900/70 shadow-xl shadow-black/20">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-700/60 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">Movimientos registrados</h2>
            <p className="text-sm text-gray-400">
              Selecciona filas para editarlas o eliminarlas rápidamente.
            </p>
          </div>
          <div className="flex flex-col items-end gap-3 sm:flex-row sm:items-center">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => openTransactionModal(null)}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold shadow-lg shadow-blue-600/20 transition hover:bg-blue-500"
              >
                <Plus className="h-4 w-4" />
                Nueva transacción
              </button>
              <button
                type="button"
                onClick={handleDeleteSelected}
                disabled={selectedTransactionIds.length === 0}
                className="inline-flex items-center gap-2 rounded-lg border border-red-500/50 px-4 py-2 text-sm font-semibold text-red-200 transition hover:border-red-400 hover:text-red-100 disabled:cursor-not-allowed disabled:border-red-900 disabled:text-red-700"
              >
                <Trash2 className="h-4 w-4" />
                Eliminar
                {selectedTransactionIds.length > 0 && (
                  <span className="ml-1 rounded-full bg-red-500/20 px-2 py-0.5 text-xs">
                    {selectedTransactionIds.length}
                  </span>
                )}
              </button>
            </div>
            <span className="text-sm text-gray-400">
              {transactions.length} transacciones encontradas
            </span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-800">
            <thead className="bg-gray-800/80">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-400">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    onChange={(e) => handleToggleAll(e.target.checked)}
                    className="h-4 w-4 cursor-pointer rounded border border-gray-600 bg-gray-900"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Fecha
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Descripción
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Cuenta
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Tipo
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Categoría
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Monto
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {paginatedTransactions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-gray-500">
                    No se encontraron transacciones con los filtros seleccionados.
                  </td>
                </tr>
              ) : (
                paginatedTransactions.map((t) => {
                  const isSelected = selectedTransactionIds.includes(t.id);
                  const isIncome = t.type === "Ingreso";
                  return (
                    <tr
                      key={t.id}
                      onDoubleClick={() => openTransactionModal(t)}
                      className={`group cursor-pointer bg-gradient-to-r from-transparent via-transparent to-transparent transition hover:from-gray-800/40 hover:to-gray-800/20 ${
                        isSelected ? "bg-gray-800/50" : ""
                      }`}
                    >
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => handleToggleTransaction(t.id, e.target.checked)}
                          onDoubleClick={(e) => e.stopPropagation()}
                          className="h-4 w-4 cursor-pointer rounded border border-gray-600 bg-gray-900"
                        />
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-200">
                        {new Date(t.date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-100">
                        <div className="flex flex-col gap-1">
                          <span className="block max-w-xs truncate" title={t.description}>
                            {t.description}
                          </span>
                          {(t.goal_name || t.debt_name) && (
                            <div className="flex flex-wrap gap-2 text-xs text-slate-400">
                              {t.goal_name && (
                                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-emerald-300">
                                  Meta: {t.goal_name}
                                </span>
                              )}
                              {t.debt_name && (
                                <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-rose-300">
                                  Deuda: {t.debt_name}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">
                        {t.account?.name ?? "-"}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                            isIncome
                              ? "bg-emerald-500/15 text-emerald-300"
                              : "bg-rose-500/15 text-rose-300"
                          }`}
                        >
                          {t.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">
                        <span className="inline-flex rounded-full bg-gray-800/80 px-3 py-1 text-xs">
                          {t.category}
                        </span>
                      </td>
                      <td
                        className={`px-4 py-3 text-right text-sm font-semibold ${
                          isIncome ? "text-emerald-300" : "text-rose-300"
                        }`}
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

        <div className="flex flex-col gap-4 border-t border-gray-700/60 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-300">
            <span>Mostrar</span>
            <select
              value={pageSize}
              onChange={handlePageSizeChange}
              className="rounded-lg border border-gray-700 bg-gray-800/80 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none"
            >
              {[5, 10, 20, 50].map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
            <span>por página</span>
          </div>
          <div className="flex flex-col items-center gap-3 text-sm text-gray-400 md:flex-row md:gap-4">
            <span>
              Página {currentPage} de {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="rounded-lg border border-gray-700 px-3 py-1 transition hover:border-gray-500 disabled:cursor-not-allowed disabled:border-gray-800 disabled:text-gray-600"
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
                      ? "bg-blue-600 text-white"
                      : "border border-gray-700 hover:border-gray-500"
                  }`}
                >
                  {page}
                </button>
              ))}
              <button
                type="button"
                onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="rounded-lg border border-gray-700 px-3 py-1 transition hover:border-gray-500 disabled:cursor-not-allowed disabled:border-gray-800 disabled:text-gray-600"
              >
                Siguiente
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
