import { useEffect, useState, useCallback } from "react";
import { useStore } from "../store/useStore";
import axios from "axios";

// Interfaces para los datos que cargaremos en los selects
interface SelectOption {
  id: number;
  name: string;
}
interface ParameterOption {
  id: number;
  value: string;
}

// Estado inicial del formulario para poder resetearlo
const initialState = {
  description: "",
  amount: "",
  date: new Date().toISOString().split("T")[0],
  typeId: "", // Usaremos IDs para manejar el estado de los selects
  categoryValue: "", // Usaremos el valor de texto para la categoría
  account_id: "",
  goal_id: "",
  debt_id: "",
};

export const TransactionModal = () => {
  const {
    isTransactionModalOpen,
    closeTransactionModal,
    editingTransaction,
    fetchTransactions,
  } = useStore();

  // Estados del formulario y para los datos de los selects
  const [formData, setFormData] = useState(initialState);
  const [accounts, setAccounts] = useState<SelectOption[]>([]);
  const [transactionTypes, setTransactionTypes] = useState<ParameterOption[]>(
    []
  );
  const [categories, setCategories] = useState<ParameterOption[]>([]);
  const [goals, setGoals] = useState<SelectOption[]>([]);
  const [debts, setDebts] = useState<SelectOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // Obtenemos el nombre del tipo seleccionado para mostrar/ocultar los selects de Metas/Deudas
  const selectedTypeName = transactionTypes.find(
    (t) => t.id === parseInt(formData.typeId)
  )?.value;

  // --- LÓGICA DE CARGA DE DATOS (CORREGIDA) ---
  // Esta función se encarga de cargar TODA la información para los menús desplegables
  const loadDependencies = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const [accRes, typesRes, goalsRes, debtsRes] = await Promise.all([
        axios.get("http://127.0.0.1:8000/api/accounts"),
        axios.get("http://127.0.0.1:8000/api/parameters/transaction-types"),
        axios.get("http://127.0.0.1:8000/api/goals"),
        axios.get("http://127.0.0.1:8000/api/debts"),
      ]);
      setAccounts(accRes.data);
      setTransactionTypes(typesRes.data);
      setGoals(goalsRes.data);
      setDebts(debtsRes.data);
      // Devolvemos los tipos para que el siguiente paso pueda usarlos inmediatamente
      return { types: typesRes.data };
    } catch (err) {
      console.error("Error al cargar dependencias del modal:", err);
      setError("No se pudieron cargar los datos. Inténtalo de nuevo.");
      return { types: [] };
    } finally {
      setIsLoading(false);
    }
  }, []);

  // --- EFECTO PRINCIPAL PARA ABRIR/CERRAR EL MODAL ---
  useEffect(() => {
    if (isTransactionModalOpen) {
      // 1. LLAMAMOS A CARGAR LOS DATOS
      loadDependencies().then(({ types }) => {
        // 2. SOLO CUANDO LA CARGA TERMINA, rellenamos el formulario si estamos editando
        if (editingTransaction && types.length > 0) {
          const typeObject = types.find(
            (t) => t.value === editingTransaction.type
          );
          if (typeObject) {
            setFormData({
              description: editingTransaction.description,
              amount: String(editingTransaction.amount),
              date: new Date(editingTransaction.date)
                .toISOString()
                .split("T")[0],
              account_id: String(editingTransaction.account_id),
              typeId: String(typeObject.id), // ¡Clave! Asignamos el ID del tipo
              categoryValue: editingTransaction.category,
              goal_id: String(editingTransaction.goal_id || ""),
              debt_id: String(editingTransaction.debt_id || ""),
            });
          }
        }
      });
    } else {
      setFormData(initialState); // Resetear el formulario al cerrar
    }
  }, [isTransactionModalOpen, editingTransaction, loadDependencies]);

  // --- EFECTO PARA CARGAR CATEGORÍAS CUANDO CAMBIA EL TIPO ---
  useEffect(() => {
    if (formData.typeId) {
      axios
        .get(
          `http://127.0.0.1:8000/api/parameters/categories/${formData.typeId}`
        )
        .then((res) => {
          setCategories(res.data);
        });
    } else {
      setCategories([]);
    }
  }, [formData.typeId]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    if (name === "typeId") {
      setFormData((prev) => ({
        ...prev,
        typeId: value,
        categoryValue: "",
        goal_id: "",
        debt_id: "",
      }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    // "Traducimos" el ID del tipo a su nombre en texto antes de enviar
    const typeName = transactionTypes.find(
      (t) => t.id === parseInt(formData.typeId)
    )?.value;

    if (!typeName) {
      setError("Tipo de transacción inválido. Por favor, selecciona uno.");
      return;
    }

    const submissionData = {
      description: formData.description,
      amount: parseFloat(formData.amount),
      date: formData.date,
      account_id: parseInt(formData.account_id),
      type: typeName, // Enviamos el nombre en texto, como espera el backend
      category: formData.categoryValue,
      goal_id: formData.goal_id ? parseInt(formData.goal_id) : null,
      debt_id: formData.debt_id ? parseInt(formData.debt_id) : null,
    };

    try {
      if (editingTransaction) {
        await axios.put(
          `http://127.0.0.1:8000/api/transactions/${editingTransaction.id}`,
          submissionData
        );
      } else {
        await axios.post(
          "http://127.0.0.1:8000/api/transactions",
          submissionData
        );
      }
      fetchTransactions(); // Recargamos la lista de transacciones
      closeTransactionModal();
    } catch (err) {
      console.error("Error al guardar la transacción:", err);
      setError(
        "No se pudo guardar. Revisa la conexión o los datos del formulario."
      );
    }
  };

  if (!isTransactionModalOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md text-white">
        <h2 className="text-2xl font-bold mb-4">
          {editingTransaction ? "Editar" : "Añadir"} Transacción
        </h2>
        {isLoading && !formData.description ? (
          <p>Cargando datos...</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <p className="text-red-400 bg-red-900/50 p-3 rounded">{error}</p>
            )}

            <input
              type="text"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Descripción"
              required
              className="w-full p-2 bg-gray-700 rounded"
            />
            <input
              type="number"
              step="0.01"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              placeholder="Monto"
              required
              className="w-full p-2 bg-gray-700 rounded"
            />
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              required
              className="w-full p-2 bg-gray-700 rounded"
            />

            <select
              name="account_id"
              value={formData.account_id}
              onChange={handleChange}
              required
              className="w-full p-2 bg-gray-700 rounded"
            >
              <option value="">-- Selecciona una Cuenta --</option>
              {accounts.map((acc) => (
                <option key={acc.id} value={acc.id}>
                  {acc.name}
                </option>
              ))}
            </select>

            <select
              name="typeId"
              value={formData.typeId}
              onChange={handleChange}
              required
              className="w-full p-2 bg-gray-700 rounded"
            >
              <option value="">-- Selecciona un Tipo --</option>
              {transactionTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.value}
                </option>
              ))}
            </select>

            <select
              name="categoryValue"
              value={formData.categoryValue}
              onChange={handleChange}
              required
              disabled={!formData.typeId || categories.length === 0}
              className="w-full p-2 bg-gray-700 rounded disabled:opacity-50"
            >
              <option value="">-- Selecciona una Categoría --</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.value}>
                  {cat.value}
                </option>
              ))}
            </select>

            {selectedTypeName === "Ahorro Meta" && (
              <select
                name="goal_id"
                value={formData.goal_id}
                onChange={handleChange}
                required
                className="w-full p-2 bg-gray-700 rounded"
              >
                <option value="">-- Selecciona una Meta --</option>
                {goals.map((goal) => (
                  <option key={goal.id} value={goal.id}>
                    {goal.name}
                  </option>
                ))}
              </select>
            )}
            {selectedTypeName === "Pago Deuda" && (
              <select
                name="debt_id"
                value={formData.debt_id}
                onChange={handleChange}
                required
                className="w-full p-2 bg-gray-700 rounded"
              >
                <option value="">-- Selecciona una Deuda --</option>
                {debts.map((debt) => (
                  <option key={debt.id} value={debt.id}>
                    {debt.name}
                  </option>
                ))}
              </select>
            )}

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={closeTransactionModal}
                className="bg-gray-600 hover:bg-gray-500 font-bold py-2 px-4 rounded"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 font-bold py-2 px-4 rounded"
              >
                Guardar
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
