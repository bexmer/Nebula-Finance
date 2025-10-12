import { useState, useEffect, useCallback } from "react";
import { useStore, Transaction } from "../store/useStore";
import axios from "axios";

// Interfaces para los selects de los filtros
interface ParameterOption {
  id: number;
  value: string;
}

export function Transactions() {
  const { transactions, fetchTransactions, openTransactionModal } = useStore();

  // Estado para manejar todos los filtros
  const [filters, setFilters] = useState({
    search: "",
    start_date: "",
    end_date: "",
    type: "",
    category: "",
    sort_by: "date_desc",
  });

  // Estados para poblar los selects de los filtros
  const [transactionTypes, setTransactionTypes] = useState<ParameterOption[]>(
    []
  );
  const [categories, setCategories] = useState<ParameterOption[]>([]);

  // Carga inicial de datos para los filtros
  useEffect(() => {
    axios
      .get("http://127.0.0.1:8000/api/parameters/transaction-types")
      .then((res) => setTransactionTypes(res.data));
  }, []);

  // --- FILTRADO EN TIEMPO REAL (LA CLAVE) ---
  useEffect(() => {
    // Usamos un "debounce" para no hacer una llamada a la API en cada letra que se escribe
    const handler = setTimeout(() => {
      fetchTransactions(filters);
    }, 500); // Espera 500ms después de que el usuario deja de cambiar los filtros

    return () => {
      clearTimeout(handler);
    };
  }, [filters, fetchTransactions]); // Se ejecuta cada vez que el objeto 'filters' cambia

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
      // Si se deselecciona el tipo, también se limpia la categoría del filtro
      if (filters.category) {
        setFilters((f) => ({ ...f, category: "" }));
      }
    }
  }, [filters.type, transactionTypes]);

  const handleFilterChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFilters((prevFilters) => ({
      ...prevFilters,
      [e.target.name]: e.target.value,
    }));
  };

  const handleDelete = async (id: number) => {
    if (window.confirm("¿Seguro que quieres eliminar esta transacción?")) {
      await axios.delete(`http://127.0.0.1:8000/api/transactions/${id}`);
      fetchTransactions(filters); // Recarga con los filtros actuales
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Transacciones</h1>

      {/* --- CONTROLES DE FILTRO Y BÚSQUEDA --- */}
      <div className="bg-gray-800 p-4 rounded-lg mb-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 items-end">
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

      {/* --- TABLA DE TRANSACCIONES (CORREGIDA) --- */}
      <div className="bg-gray-800 rounded-lg overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-700/50">
            <tr>
              <th className="p-3 font-semibold">Fecha</th>
              <th className="p-3 font-semibold">Descripción</th>
              <th className="p-3 font-semibold">Cuenta</th>
              <th className="p-3 font-semibold">Tipo</th>
              <th className="p-3 font-semibold">Categoría</th>
              <th className="p-3 font-semibold text-right">Monto</th>
              <th className="p-3 font-semibold text-center">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <tr
                key={t.id}
                className="border-b border-gray-700 hover:bg-gray-700/50"
              >
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
                <td className="p-3 text-center">
                  <button
                    onClick={() => openTransactionModal(t)}
                    className="text-blue-400 hover:text-blue-300 mr-3"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(t.id)}
                    className="text-red-400 hover:text-red-300"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
