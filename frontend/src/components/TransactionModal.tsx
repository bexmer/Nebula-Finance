import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { useStore } from "../store/useStore";

interface SelectOption {
  id: number;
  name: string;
}

interface ParameterOption {
  id: number;
  value: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

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
    transactionPrefill,
    fetchTransactions,
  } = useStore();

  const [formData, setFormData] = useState(initialState);
  const [accounts, setAccounts] = useState<SelectOption[]>([]);
  const [transactionTypes, setTransactionTypes] = useState<ParameterOption[]>([]);
  const [categories, setCategories] = useState<ParameterOption[]>([]);
  const [goals, setGoals] = useState<SelectOption[]>([]);
  const [debts, setDebts] = useState<SelectOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [catalogNotice, setCatalogNotice] = useState<string | null>(null);

  const fetchCategoriesByType = useCallback(async (typeId: number) => {
    try {
      const response = await axios.get<ParameterOption[]>(
        `${API_BASE_URL}/api/parameters/categories/${typeId}`
      );
      return response.data;
    } catch (categoryError) {
      console.error("No se pudieron cargar las categorías:", categoryError);
      setCatalogNotice(
        "No encontramos categorías para este tipo. Revisa la sección de Configuración."
      );
      return [];
    }
  }, [setCatalogNotice]);

  const loadModalData = useCallback(async () => {
    setIsLoading(true);
    setError("");
    setCatalogNotice(null);

    try {
      const [accountsResult, typesResult, goalsResult, debtsResult] =
        await Promise.allSettled([
          axios.get<SelectOption[]>(`${API_BASE_URL}/api/accounts`),
          axios.get<ParameterOption[]>(
            `${API_BASE_URL}/api/parameters/transaction-types`
          ),
          axios.get<SelectOption[]>(`${API_BASE_URL}/api/goals`),
          axios.get<SelectOption[]>(`${API_BASE_URL}/api/debts`),
        ]);

      if (
        accountsResult.status !== "fulfilled" ||
        typesResult.status !== "fulfilled"
      ) {
        throw new Error("catalog-unavailable");
      }

      const accountList = accountsResult.value.data;
      const typeList = typesResult.value.data;

      setAccounts(accountList);
      setTransactionTypes(typeList);
      setGoals(goalsResult.status === "fulfilled" ? goalsResult.value.data : []);
      setDebts(debtsResult.status === "fulfilled" ? debtsResult.value.data : []);

      let nextCategories: ParameterOption[] = [];
      let nextFormState = {
        ...initialState,
        date: new Date().toISOString().split("T")[0],
      };

      if (editingTransaction) {
        const typeObject = typeList.find(
          (type) => type.value === editingTransaction.type
        );

        if (typeObject) {
          nextCategories = await fetchCategoriesByType(typeObject.id);
          nextFormState = {
            ...nextFormState,
            description: editingTransaction.description,
            amount: String(editingTransaction.amount),
            date: new Date(editingTransaction.date).toISOString().split("T")[0],
            account_id: String(editingTransaction.account_id),
            typeId: String(typeObject.id),
            categoryValue: editingTransaction.category,
            goal_id: String(editingTransaction.goal_id || ""),
            debt_id: String(editingTransaction.debt_id || ""),
          };
        } else {
          nextFormState = {
            ...nextFormState,
            description: editingTransaction.description,
            amount: String(editingTransaction.amount),
            date: new Date(editingTransaction.date).toISOString().split("T")[0],
            account_id: String(editingTransaction.account_id),
            goal_id: String(editingTransaction.goal_id || ""),
            debt_id: String(editingTransaction.debt_id || ""),
          };
        }
      } else if (transactionPrefill) {
        const normalizedDate = transactionPrefill.date
          ? new Date(transactionPrefill.date).toISOString().split("T")[0]
          : nextFormState.date;

        nextFormState = {
          ...nextFormState,
          description: transactionPrefill.description || "",
          amount:
            transactionPrefill.amount !== undefined
              ? String(transactionPrefill.amount)
              : "",
          date: normalizedDate,
          account_id: transactionPrefill.account_id
            ? String(transactionPrefill.account_id)
            : "",
          goal_id: transactionPrefill.goal_id
            ? String(transactionPrefill.goal_id)
            : "",
          debt_id: transactionPrefill.debt_id
            ? String(transactionPrefill.debt_id)
            : "",
        };

        if (transactionPrefill.type) {
          const typeObject = typeList.find(
            (type) => type.value === transactionPrefill.type
          );
          if (typeObject) {
            nextCategories = await fetchCategoriesByType(typeObject.id);
            nextFormState = {
              ...nextFormState,
              typeId: String(typeObject.id),
              categoryValue: transactionPrefill.category || "",
            };
          }
        }
      }

      setCategories(nextCategories);
      setFormData(nextFormState);

      if (accountList.length === 0 || typeList.length === 0) {
        setCatalogNotice(
          "Configura al menos una cuenta y un tipo de transacción con categorías en Configuración antes de registrar movimientos."
        );
      }
    } catch (loadError) {
      console.error("Error al preparar el formulario de transacciones:", loadError);
      setError(
        "No pudimos obtener todos los catálogos necesarios. Verifica tu conexión y la configuración de cuentas, tipos y categorías."
      );
    } finally {
      setIsLoading(false);
    }
  }, [editingTransaction, transactionPrefill, fetchCategoriesByType]);

  useEffect(() => {
    if (isTransactionModalOpen) {
      loadModalData();
    } else {
      setFormData(initialState);
      setCatalogNotice(null);
      setError("");
    }
  }, [isTransactionModalOpen, loadModalData]);

  const handleTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const typeId = event.target.value;
    setFormData((prev) => ({
      ...prev,
      typeId,
      categoryValue: "",
      goal_id: "",
      debt_id: "",
    }));
    setCatalogNotice(null);
    if (typeId) {
      fetchCategoriesByType(Number(typeId)).then((data) => setCategories(data));
    } else {
      setCategories([]);
    }
  };

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = event.target;
    const checked = (event.target as HTMLInputElement).checked;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");

    const typeName = transactionTypes.find(
      (type) => type.id === parseInt(formData.typeId, 10)
    )?.value;

    if (!typeName) {
      setError("Selecciona un tipo de transacción para continuar.");
      return;
    }

    const submissionData = {
      description: formData.description,
      amount: parseFloat(formData.amount),
      date: formData.date,
      account_id: parseInt(formData.account_id, 10),
      type: typeName,
      category: formData.categoryValue,
      goal_id: formData.goal_id ? parseInt(formData.goal_id, 10) : null,
      debt_id: formData.debt_id ? parseInt(formData.debt_id, 10) : null,
      is_recurring: formData.is_recurring,
      frequency: formData.frequency,
      day_of_month: formData.day_of_month,
    };

    if (Number.isNaN(submissionData.amount) || Number.isNaN(submissionData.account_id)) {
      setError("Ingresa un monto válido y selecciona una cuenta.");
      return;
    }

    try {
      if (editingTransaction) {
        await axios.put(
          `${API_BASE_URL}/api/transactions/${editingTransaction.id}`,
          submissionData
        );
      } else {
        await axios.post(`${API_BASE_URL}/api/transactions`, submissionData);
      }
      await fetchTransactions();
      closeTransactionModal();
    } catch (submitError) {
      console.error("Error al guardar la transacción:", submitError);
      setError("No se pudo guardar la transacción. Revisa los datos e inténtalo nuevamente.");
    }
  };

  if (!isTransactionModalOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-6">
      <div className="app-card w-full max-w-2xl p-6">
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          {editingTransaction ? "Editar transacción" : "Registrar transacción"}
        </h2>

        {isLoading ? (
          <p className="mt-6 text-center text-muted">Cargando catálogos...</p>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {error && (
              <p className="rounded-xl border border-rose-300/60 bg-rose-50 px-4 py-2 text-sm text-rose-600 dark:border-rose-400/40 dark:bg-rose-500/10 dark:text-rose-200">
                {error}
              </p>
            )}
            {catalogNotice && !error && (
              <p className="rounded-xl border border-amber-300/60 bg-amber-50 px-4 py-2 text-sm text-amber-600 dark:border-amber-400/40 dark:bg-amber-500/10 dark:text-amber-200">
                {catalogNotice}
              </p>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <input
                type="text"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Descripción"
                required
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100 sm:col-span-2"
              />
              <input
                type="number"
                step="0.01"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                placeholder="Monto"
                required
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              />
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                required
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              />
            </div>

            <select
              name="account_id"
              value={formData.account_id}
              onChange={handleChange}
              required
              className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            >
              <option value="">-- Selecciona una Cuenta --</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <select
                name="typeId"
                value={formData.typeId}
                onChange={handleTypeChange}
                required
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
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
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-100"
              >
                <option value="">-- Selecciona una Categoría --</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.value}>
                    {category.value}
                  </option>
                ))}
              </select>
            </div>

            {(goals.length > 0 || debts.length > 0) && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {goals.length > 0 && (
                  <select
                    name="goal_id"
                    value={formData.goal_id}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  >
                    <option value="">-- Asociar meta (opcional) --</option>
                    {goals.map((goal) => (
                      <option key={goal.id} value={goal.id}>
                        {goal.name}
                      </option>
                    ))}
                  </select>
                )}
                {debts.length > 0 && (
                  <select
                    name="debt_id"
                    value={formData.debt_id}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  >
                    <option value="">-- Asociar deuda (opcional) --</option>
                    {debts.map((debt) => (
                      <option key={debt.id} value={debt.id}>
                        {debt.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}

            <div className="rounded-2xl border border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)]/70 px-4 py-4">
              <label className="flex cursor-pointer items-center gap-3">
                <input
                  type="checkbox"
                  name="is_recurring"
                  checked={formData.is_recurring}
                  onChange={handleChange}
                  className="h-5 w-5 rounded border-slate-400 text-sky-500 focus:ring-sky-400"
                />
                <span className="text-sm text-muted">Es una transacción recurrente</span>
              </label>
              {formData.is_recurring && (
                <div className="grid grid-cols-1 gap-4 pt-4 sm:grid-cols-2">
                  <select
                    name="frequency"
                    value={formData.frequency}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
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
                    className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  />
                </div>
              )}
            </div>

            <div className="flex flex-col-reverse gap-3 pt-6 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={closeTransactionModal}
                className="w-full rounded-xl border border-[var(--app-border)] bg-transparent px-4 py-2 text-sm font-semibold text-muted transition hover:border-slate-400 hover:text-slate-700 dark:hover:text-slate-200 sm:w-auto"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="w-full rounded-xl bg-gradient-to-r from-sky-500 via-indigo-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-500/30 transition hover:shadow-xl sm:w-auto"
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
