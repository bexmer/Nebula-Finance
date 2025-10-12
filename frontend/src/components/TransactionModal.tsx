import { useEffect, useState, useCallback } from "react";
import { useStore } from "../store/useStore";
import axios from "axios";

interface SelectOption {
  id: number;
  name: string;
}
interface ParameterOption {
  id: number;
  value: string;
}

const initialState = {
  description: "",
  amount: "",
  date: new Date().toISOString().split("T")[0],
  typeId: "",
  categoryValue: "",
  account_id: "",
  goal_id: "",
  debt_id: "",
  is_recurring: false,
  frequency: "Mensual",
  day_of_month: 1,
};

export const TransactionModal = () => {
  const {
    isTransactionModalOpen,
    closeTransactionModal,
    editingTransaction,
    fetchTransactions,
  } = useStore();

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

  const loadModalData = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const [accRes, typesRes, goalsRes, debtsRes] = await Promise.all([
        axios.get<SelectOption[]>("http://127.0.0.1:8000/api/accounts"),
        axios.get<ParameterOption[]>(
          "http://127.0.0.1:8000/api/parameters/transaction-types"
        ),
        axios.get<SelectOption[]>("http://127.0.0.1:8000/api/goals"),
        axios.get<SelectOption[]>("http://127.0.0.1:8000/api/debts"),
      ]);
      setAccounts(accRes.data);
      setTransactionTypes(typesRes.data);
      setGoals(goalsRes.data);
      setDebts(debtsRes.data);

      if (editingTransaction) {
        const typeObject = typesRes.data.find(
          (t: ParameterOption) => t.value === editingTransaction.type
        );
        if (typeObject) {
          const catRes = await axios.get<ParameterOption[]>(
            `http://127.0.0.1:8000/api/parameters/categories/${typeObject.id}`
          );
          setCategories(catRes.data);
          setFormData({
            ...initialState,
            description: editingTransaction.description,
            amount: String(editingTransaction.amount),
            date: new Date(editingTransaction.date).toISOString().split("T")[0],
            account_id: String(editingTransaction.account_id),
            typeId: String(typeObject.id),
            categoryValue: editingTransaction.category,
            goal_id: String(editingTransaction.goal_id || ""),
            debt_id: String(editingTransaction.debt_id || ""),
          });
        }
      }
    } catch (err) {
      setError("No se pudieron cargar los datos del formulario.");
    } finally {
      setIsLoading(false);
    }
  }, [editingTransaction]);

  useEffect(() => {
    if (isTransactionModalOpen) {
      loadModalData();
    } else {
      setFormData(initialState);
    }
  }, [isTransactionModalOpen, loadModalData]);

  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const typeId = e.target.value;
    setFormData((prev) => ({
      ...prev,
      typeId,
      categoryValue: "",
      goal_id: "",
      debt_id: "",
    }));
    if (typeId) {
      axios
        .get<ParameterOption[]>(
          `http://127.0.0.1:8000/api/parameters/categories/${typeId}`
        )
        .then((res) => setCategories(res.data));
    } else {
      setCategories([]);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const typeName = transactionTypes.find(
      (t) => t.id === parseInt(formData.typeId)
    )?.value;
    if (!typeName) {
      setError("Por favor, selecciona un tipo.");
      return;
    }

    const submissionData = {
      description: formData.description,
      amount: parseFloat(formData.amount),
      date: formData.date,
      account_id: parseInt(formData.account_id),
      type: typeName,
      category: formData.categoryValue,
      goal_id: formData.goal_id ? parseInt(formData.goal_id) : null,
      debt_id: formData.debt_id ? parseInt(formData.debt_id) : null,
      is_recurring: formData.is_recurring,
      frequency: formData.frequency,
      day_of_month: formData.day_of_month,
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
      await fetchTransactions(); // Recarga con los filtros actuales
      closeTransactionModal();
    } catch (err) {
      setError("No se pudo guardar la transacción. Revisa los datos.");
    }
  };

  if (!isTransactionModalOpen) return null;

  const selectedTypeName = transactionTypes.find(
    (t) => t.id === parseInt(formData.typeId)
  )?.value;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg w-full max-w-lg text-white">
        <h2 className="text-2xl font-bold mb-4">
          {editingTransaction ? "Editar" : "Añadir"} Transacción
        </h2>
        {isLoading ? (
          <p className="text-center">Cargando...</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <p className="text-red-400 bg-red-900/50 p-2 rounded">{error}</p>
            )}

            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Descripción"
                required
                className="col-span-2 w-full p-2 bg-gray-700 rounded"
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
            </div>

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

            <div className="grid grid-cols-2 gap-4">
              <select
                name="typeId"
                value={formData.typeId}
                onChange={handleTypeChange}
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
            </div>

            <div className="bg-gray-700/50 p-3 rounded-lg">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  name="is_recurring"
                  checked={formData.is_recurring}
                  onChange={handleChange}
                  className="form-checkbox h-5 w-5 text-blue-500 rounded bg-gray-800 border-gray-600"
                />
                <span>Es una transacción recurrente</span>
              </label>
              {formData.is_recurring && (
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <select
                    name="frequency"
                    value={formData.frequency}
                    onChange={handleChange}
                    className="w-full p-2 bg-gray-600 rounded"
                  >
                    <option>Mensual</option>
                    <option>Quincenal</option>
                    <option>Semanal</option>
                    <option>Anual</option>
                  </select>
                  <input
                    type="number"
                    name="day_of_month"
                    value={formData.day_of_month}
                    onChange={handleChange}
                    placeholder="Día del mes"
                    min="1"
                    max="31"
                    className="w-full p-2 bg-gray-600 rounded"
                  />
                </div>
              )}
            </div>

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
