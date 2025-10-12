// frontend/src/pages/Accounts.tsx

import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

interface Account {
  id: number;
  name: string;
  account_type: string;
  initial_balance: number;
  current_balance: number;
}

interface AccountFormState {
  name: string;
  accountType: string;
  initialBalance: string;
}

const API_BASE_URL = "http://127.0.0.1:8000";

const resolveDetailMessage = (detail: unknown): string | null => {
  if (!detail) {
    return null;
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => resolveDetailMessage(item) ?? "").join(" ").trim() || null;
  }
  if (typeof detail === "object") {
    const typedDetail = detail as { message?: unknown; detail?: unknown };
    const maybeMessage = typedDetail.message ?? typedDetail.detail;
    return resolveDetailMessage(maybeMessage);
  }
  return String(detail);
};

export function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountTypes, setAccountTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formState, setFormState] = useState<AccountFormState>({
    name: "",
    accountType: "",
    initialBalance: "",
  });
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const formatCurrency = useCallback((value: number) => {
    return new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency: "MXN",
      minimumFractionDigits: 2,
    }).format(value);
  }, []);

  const resetForm = useCallback(
    (availableTypes: string[] = accountTypes) => {
      setFormState({
        name: "",
        accountType: availableTypes[0] ?? "",
        initialBalance: "",
      });
      setSelectedAccountId(null);
    },
    [accountTypes]
  );

  useEffect(() => {
    let isMounted = true;

    const fetchInitialData = async () => {
      try {
        const [accountsResponse, typesResponse] = await Promise.all([
          axios.get<Account[]>(`${API_BASE_URL}/api/accounts`),
          axios.get<string[]>(`${API_BASE_URL}/api/parameters/account-types`),
        ]);

        if (!isMounted) {
          return;
        }

        setAccounts(accountsResponse.data);
        setAccountTypes(typesResponse.data);
        setError(null);
        setFormState({
          name: "",
          accountType: typesResponse.data[0] ?? "",
          initialBalance: "",
        });
        setSelectedAccountId(null);
      } catch (err) {
        console.error("Error al inicializar cuentas:", err);
        if (isMounted) {
          setError(
            "No se pudieron cargar las cuentas. Asegúrate de que el backend esté funcionando."
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchInitialData();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleInputChange = (field: keyof AccountFormState, value: string) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  const startEditing = (account: Account) => {
    setSelectedAccountId(account.id);
    setFormState({
      name: account.name,
      accountType: account.account_type,
      initialBalance: account.initial_balance.toString(),
    });
    setFeedback(null);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formState.name.trim()) {
      setFeedback("El nombre de la cuenta es obligatorio.");
      return;
    }
    if (!formState.accountType) {
      setFeedback("Selecciona un tipo de cuenta.");
      return;
    }

    const payload = {
      name: formState.name.trim(),
      account_type: formState.accountType,
      initial_balance: formState.initialBalance ? parseFloat(formState.initialBalance) : 0,
    };

    if (Number.isNaN(payload.initial_balance)) {
      setFeedback("Ingresa un saldo inicial válido.");
      return;
    }

    try {
      setSubmitting(true);
      if (selectedAccountId === null) {
        const response = await axios.post<Account>(`${API_BASE_URL}/api/accounts`, payload);
        setAccounts((prev) => [...prev, response.data]);
        setFeedback("Cuenta añadida correctamente.");
      } else {
        const response = await axios.put<Account>(
          `${API_BASE_URL}/api/accounts/${selectedAccountId}`,
          payload
        );
        setAccounts((prev) =>
          prev.map((account) => (account.id === selectedAccountId ? response.data : account))
        );
        setFeedback("Cuenta actualizada correctamente.");
      }
      resetForm();
    } catch (err: unknown) {
      console.error("Error al guardar la cuenta:", err);
      const detailMessage =
        axios.isAxiosError(err) && err.response
          ? resolveDetailMessage(err.response.data?.detail ?? err.response.data)
          : null;
      setFeedback(detailMessage ?? "No se pudo guardar la cuenta. Inténtalo nuevamente.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (selectedAccountId === null) {
      setFeedback("Selecciona una cuenta para eliminar.");
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/accounts/${selectedAccountId}`);
      setAccounts((prev) => prev.filter((account) => account.id !== selectedAccountId));
      setFeedback("Cuenta eliminada correctamente.");
      resetForm();
    } catch (err: unknown) {
      console.error("Error al eliminar la cuenta:", err);
      const detailMessage =
        axios.isAxiosError(err) && err.response
          ? resolveDetailMessage(err.response.data?.detail ?? err.response.data)
          : null;
      setFeedback(detailMessage ?? "No se pudo eliminar la cuenta. Inténtalo nuevamente.");
    }
  };

  const isEditing = selectedAccountId !== null;

  const selectedAccountName = useMemo(() => {
    if (selectedAccountId === null) {
      return null;
    }
    const account = accounts.find((item) => item.id === selectedAccountId);
    return account?.name ?? null;
  }, [accounts, selectedAccountId]);

  if (loading) {
    return <div className="text-slate-500">Cargando cuentas...</div>;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold text-slate-800 dark:text-slate-100">
        Cuentas
      </h1>

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <div className="rounded-xl bg-slate-100 p-6 shadow-sm dark:bg-slate-800/60">
          <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-100">
            {isEditing ? "Editar Cuenta" : "Añadir Cuenta"}
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
            Completa el formulario para {isEditing ? "actualizar" : "registrar"} una cuenta.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-600 dark:text-slate-200">
                Nombre de la Cuenta
              </label>
              <input
                type="text"
                value={formState.name}
                onChange={(event) => handleInputChange("name", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                placeholder="Ej. Cuenta Nómina"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-600 dark:text-slate-200">
                Tipo de Cuenta
              </label>
              <select
                value={formState.accountType}
                onChange={(event) => handleInputChange("accountType", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              >
                <option value="" disabled>
                  Selecciona un tipo
                </option>
                {accountTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-600 dark:text-slate-200">
                Saldo Inicial
              </label>
              <input
                type="number"
                value={formState.initialBalance}
                onChange={(event) => handleInputChange("initialBalance", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                placeholder="0.00"
                step="0.01"
              />
            </div>

            {feedback && (
              <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-200">
                {feedback}
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isEditing ? "Guardar Cambios" : "Añadir Cuenta"}
              </button>

              {isEditing && (
                <button
                  type="button"
                  onClick={() => {
                    resetForm();
                    setFeedback(null);
                  }}
                  className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                >
                  Cancelar
                </button>
              )}
            </div>
          </form>
        </div>

        <div className="space-y-4 rounded-xl bg-white p-6 shadow-sm dark:bg-slate-900/60">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-100">
                Cuentas registradas
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-300">
                Selecciona una fila para editarla.
                {selectedAccountName ? ` Seleccionado: ${selectedAccountName}` : ""}
              </p>
            </div>

            <button
              type="button"
              onClick={handleDelete}
              disabled={selectedAccountId === null}
              className="self-start rounded-lg border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-200 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-500/40 dark:text-red-300 dark:hover:bg-red-500/10"
            >
              Eliminar Selección
            </button>
          </div>

          <div className="overflow-hidden rounded-lg border border-slate-200 shadow-sm dark:border-slate-700">
            <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
              <thead className="bg-slate-50 dark:bg-slate-800/60">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-200">
                    Nombre
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-200">
                    Tipo
                  </th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-200">
                    Saldo Actual
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {accounts.length === 0 ? (
                  <tr>
                    <td
                      colSpan={3}
                      className="px-4 py-6 text-center text-sm text-slate-500 dark:text-slate-300"
                    >
                      No hay cuentas registradas.
                    </td>
                  </tr>
                ) : (
                  accounts.map((account) => {
                    const isSelected = account.id === selectedAccountId;
                    return (
                      <tr
                        key={account.id}
                        onClick={() => startEditing(account)}
                        className={`cursor-pointer transition hover:bg-blue-50 dark:hover:bg-slate-800/70 ${
                          isSelected
                            ? "bg-blue-100/70 dark:bg-blue-500/20"
                            : "bg-white dark:bg-transparent"
                        }`}
                      >
                        <td className="px-4 py-3 text-slate-700 dark:text-slate-100">
                          {account.name}
                        </td>
                        <td className="px-4 py-3 text-slate-600 dark:text-slate-200">
                          {account.account_type}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-100">
                          {formatCurrency(account.current_balance)}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
