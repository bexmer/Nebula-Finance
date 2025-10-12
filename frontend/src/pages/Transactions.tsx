import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useStore, TransactionFilters } from "../store/useStore";

// Interfaces para los selects de los filtros
interface ParameterOption {
  id: number;
  value: string;
}

const PAGE_SIZE = 10;

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

  // Carga inicial de datos para los filtros
  useEffect(() => {
    axios
      .get("http://127.0.0.1:8000/api/parameters/transaction-types")
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
          .get(`http://127.0.0.1:8000/api/parameters/categories/${typeObj.id}`)
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
    const totalPages = Math.max(1, Math.ceil(transactions.length / PAGE_SIZE));
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [transactions, currentPage]);

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

    try {
      await Promise.all(
        selectedTransactionIds.map((id) =>
          axios.delete(`http://127.0.0.1:8000/api/transactions/${id}`)
        )
      );

      setSelectedTransactionIds([]);
      await fetchTransactions();
    } catch (error) {
      console.error("Error al eliminar las transacciones:", error);
    }
  };

  const paginatedTransactions = useMemo(() => {
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    return transactions.slice(startIndex, startIndex + PAGE_SIZE);
  }, [transactions, currentPage]);

  const totalPages = Math.max(1, Math.ceil(transactions.length / PAGE_SIZE));
  const pageNumbers = useMemo(
    () => Array.from({ length: totalPages }, (_, index) => index + 1),
    [totalPages]
  );

  const isAllSelected =
    paginatedTransactions.length > 0 &&
    paginatedTransactions.every((t) => selectedTransactionIds.includes(t.id));

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Transacciones</h1>

      {/* --- CONTROLES DE FILTRO Y BÚSQUEDA --- */}
      <div className="bg-gray-800 p-4 rounded-lg mb-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 items-end">
        <input
          type="text"
          name="search"
          placeholder="Buscar por descripción..."
          value={filters.search}
          onChange={handleFilterChange}
          className="p-2 bg-gray-700 rounded col-span-2 lg:col-span-1"
        />
        <input
          type="date"
          name="start_date"
          value={filters.start_date}
          onChange={handleFilterChange}
          className="p-2 bg-gray-700 rounded"
        />
        <input
          type="date"
          name="end_date"
          value={filters.end_date}
          onChange={handleFilterChange}
          className="p-2 bg-gray-700 rounded"
        />
        <select
          name="type"
          value={filters.type}
          onChange={handleFilterChange}
          className="p-2 bg-gray-700 rounded"
        >
          <option value="">Todo Tipo</option>
          {transactionTypes.map((t) => (
            <option key={t.id} value={t.value}>
              {t.value}
            </option>
          ))}
        </select>
        <select
          name="category"
          value={filters.category}
          onChange={handleFilterChange}
          disabled={!filters.type}
          className="p-2 bg-gray-700 rounded disabled:opacity-50"
        >
          <option value="">Toda Categoría</option>
          {categories.map((c) => (
            <option key={c.id} value={c.value}>
              {c.value}
            </option>
          ))}
        </select>
        <select
          name="sort_by"
          value={filters.sort_by}
          onChange={handleFilterChange}
          className="p-2 bg-gray-700 rounded col-span-2 md:col-span-1"
        >
          <option value="date_desc">Más Recientes</option>
          <option value="date_asc">Más Antiguos</option>
          <option value="amount_desc">Monto (Mayor a Menor)</option>
          <option value="amount_asc">Monto (Menor a Mayor)</option>
        </select>
      </div>

      <div className="flex justify-end mb-4">
        <button
          type="button"
          onClick={handleDeleteSelected}
          disabled={selectedTransactionIds.length === 0}
          className="bg-red-600 hover:bg-red-500 disabled:bg-red-900 disabled:cursor-not-allowed font-semibold py-2 px-4 rounded"
        >
          Eliminar Seleccionadas
        </button>
      </div>

      {/* --- TABLA DE TRANSACCIONES --- */}
      <div className="bg-gray-800 rounded-lg overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-700/50">
            <tr>
              <th className="p-3 w-12">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  onChange={(e) => handleToggleAll(e.target.checked)}
                  className="h-4 w-4 cursor-pointer"
                />
              </th>
              <th className="p-3 font-semibold">Fecha</th>
              <th className="p-3 font-semibold">Descripción</th>
              <th className="p-3 font-semibold">Cuenta</th>
              <th className="p-3 font-semibold">Tipo</th>
              <th className="p-3 font-semibold">Categoría</th>
              <th className="p-3 font-semibold text-right">Monto</th>
            </tr>
          </thead>
          <tbody>
            {paginatedTransactions.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-4 text-center text-gray-400">
                  No se encontraron transacciones con los filtros seleccionados.
                </td>
              </tr>
            ) : (
              paginatedTransactions.map((t) => {
                const isSelected = selectedTransactionIds.includes(t.id);
                return (
                  <tr
                    key={t.id}
                    onDoubleClick={() => openTransactionModal(t)}
                    className={`border-b border-gray-700 hover:bg-gray-700/50 cursor-pointer transition-colors ${
                      isSelected ? "bg-gray-700/80" : ""
                    }`}
                  >
                    <td className="p-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => handleToggleTransaction(t.id, e.target.checked)}
                        onDoubleClick={(e) => e.stopPropagation()}
                        className="h-4 w-4 cursor-pointer"
                      />
                    </td>
                    <td className="p-3">{new Date(t.date).toLocaleDateString()}</td>
                    <td className="p-3">{t.description}</td>
                    <td className="p-3">{t.account?.name}</td>
                    <td className="p-3">{t.type}</td>
                    <td className="p-3">{t.category}</td>
                    <td
                      className={`p-3 text-right font-medium ${
                        t.type === "Ingreso" ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {new Intl.NumberFormat("es-MX", {
                        style: "currency",
                        currency: "MXN",
                      }).format(t.amount)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mt-4">
        <span className="text-sm text-gray-400">
          Página {currentPage} de {totalPages}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 disabled:bg-gray-900 disabled:text-gray-500 disabled:cursor-not-allowed"
          >
            Anterior
          </button>
          {pageNumbers.map((page) => (
            <button
              key={page}
              type="button"
              onClick={() => handlePageChange(page)}
              className={`px-3 py-1 rounded border ${
                currentPage === page
                  ? "bg-blue-600 border-blue-400"
                  : "bg-gray-700 border-gray-600 hover:bg-gray-600"
              }`}
            >
              {page}
            </button>
          ))}
          <button
            type="button"
            onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 disabled:bg-gray-900 disabled:text-gray-500 disabled:cursor-not-allowed"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}
