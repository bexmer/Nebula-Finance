// frontend/src/pages/Accounts.tsx

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { apiPath } from "../utils/api";
import { getTodayDateInputValue } from "../utils/date";

interface Account {
  id: number;
  name: string;
  account_type: string;
  initial_balance: number;
  current_balance: number;
  is_virtual: boolean;
}

interface AccountFormState {
  name: string;
  accountType: string;
  initialBalance: string;
}

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
  const [transferState, setTransferState] = useState({
    fromAccountId: "",
    toAccountId: "",
    amount: "",
    note: "",
    date: getTodayDateInputValue(),
  });
  const [transferFeedback, setTransferFeedback] = useState<string | null>(null);
  const [transferring, setTransferring] = useState(false);
  const formRef = useRef<HTMLFormElement | null>(null);
  const nameInputRef = useRef<HTMLInputElement | null>(null);
  const { formatCurrency } = useNumberFormatter();

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

  const resetTransferForm = useCallback(() => {
    setTransferState({
      fromAccountId: "",
      toAccountId: "",
      amount: "",
      note: "",
      date: getTodayDateInputValue(),
    });
    setTransferFeedback(null);
  }, []);

  useEffect(() => {
    let isMounted = true;

    const fetchInitialData = async () => {
      try {
        const [accountsResponse, typesResponse] = await Promise.all([
          axios.get<Account[]>(apiPath("/accounts")),
          axios.get<string[]>(apiPath("/parameters/account-types")),
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

  useEffect(() => {
    const handleNewAccountRequest = () => {
      resetForm();
      setFeedback(null);
      requestAnimationFrame(() => {
        formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        nameInputRef.current?.focus();
      });
    };

    window.addEventListener(
      "nebula:accounts-request-new",
      handleNewAccountRequest
    );
    return () => {
      window.removeEventListener(
        "nebula:accounts-request-new",
        handleNewAccountRequest
      );
    };
  }, [resetForm]);

  const handleInputChange = (field: keyof AccountFormState, value: string) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  const startEditing = (account: Account) => {
    if (account.is_virtual) {
      setFeedback(
        "La cuenta virtual de presupuesto se calcula automáticamente y no puede editarse."
      );
      setSelectedAccountId(null);
      return;
    }
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

    const basePayload = {
      name: formState.name.trim(),
      account_type: formState.accountType,
    };

    const initialBalanceValue = formState.initialBalance
      ? parseFloat(formState.initialBalance)
      : 0;

    if (selectedAccountId === null && Number.isNaN(initialBalanceValue)) {
      setFeedback("Ingresa un saldo inicial válido.");
      return;
    }

    if (selectedAccountId !== null) {
      const existing = accounts.find(
        (account) => account.id === selectedAccountId
      );
      if (existing) {
        const unchanged =
          existing.name === basePayload.name &&
          existing.account_type === basePayload.account_type;
        if (unchanged) {
          setFeedback("No has realizado cambios en esta cuenta.");
          return;
        }
      }
    }

    try {
      setSubmitting(true);
      if (selectedAccountId === null) {
        const response = await axios.post<Account>(apiPath("/accounts"), {
          ...basePayload,
          initial_balance: initialBalanceValue,
        });
        setAccounts((prev) => [...prev, response.data]);
        setFeedback("Cuenta añadida correctamente.");
      } else {
        const response = await axios.put<Account>(
          apiPath(`/accounts/${selectedAccountId}`),
          basePayload
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

    const accountToDelete = accounts.find(
      (account) => account.id === selectedAccountId,
    );

    if (accountToDelete?.is_virtual) {
      setFeedback("La cuenta virtual no puede eliminarse.");
      return;
    }

    try {
      await axios.delete(apiPath(`/accounts/${selectedAccountId}`));
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

  const transferableAccounts = useMemo(
    () => accounts.filter((account) => !account.is_virtual),
    [accounts]
  );

  const handleTransferFieldChange = (
    field: "fromAccountId" | "toAccountId" | "amount" | "note" | "date",
    value: string
  ) => {
    setTransferState((prev) => ({ ...prev, [field]: value }));
  };

  const handleTransferSubmit = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    setTransferFeedback(null);

    if (!transferState.fromAccountId || !transferState.toAccountId) {
      setTransferFeedback("Selecciona la cuenta de origen y la de destino.");
      return;
    }

    if (transferState.fromAccountId === transferState.toAccountId) {
      setTransferFeedback("Elige cuentas diferentes para la transferencia.");
      return;
    }

    const parsedAmount = parseFloat(transferState.amount.replace(/,/g, "."));
    if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      setTransferFeedback("Ingresa un monto válido mayor que cero.");
      return;
    }

    if (!transferState.date) {
      setTransferFeedback("Selecciona la fecha en la que se realizó la transferencia.");
      return;
    }

    const [yearStr, monthStr, dayStr] = transferState.date.split("-");
    const year = Number.parseInt(yearStr ?? "", 10);
    const month = Number.parseInt(monthStr ?? "", 10) - 1;
    const day = Number.parseInt(dayStr ?? "", 10);
    const parsedDate = new Date(year, month, day);

    if (Number.isNaN(parsedDate.getTime())) {
      setTransferFeedback("La fecha seleccionada no es válida.");
      return;
    }

    const today = new Date();
    parsedDate.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);
    if (parsedDate > today) {
      setTransferFeedback("La fecha no puede ser posterior al día de hoy.");
      return;
    }

    const fromAccountId = Number.parseInt(transferState.fromAccountId, 10);
    const toAccountId = Number.parseInt(transferState.toAccountId, 10);
    const fromAccount = accounts.find((account) => account.id === fromAccountId);
    const toAccount = accounts.find((account) => account.id === toAccountId);
    const description = transferState.note.trim()
      ? transferState.note.trim()
      : `Transferencia de ${fromAccount?.name ?? "Cuenta origen"} a ${
          toAccount?.name ?? "Cuenta destino"
        }`;

    try {
      setTransferring(true);
      await axios.post(apiPath("/transactions"), {
        description,
        amount: parsedAmount,
        date: transferState.date,
        account_id: fromAccountId,
        type: "Transferencia",
        category: "Transferencia interna",
        is_transfer: true,
        transfer_account_id: toAccountId,
      });

      const accountsResponse = await axios.get<Account[]>(apiPath("/accounts"));
      setAccounts(accountsResponse.data);
      resetTransferForm();
      setTransferFeedback("Transferencia registrada correctamente.");
    } catch (err) {
      console.error("Error al registrar la transferencia:", err);
      const detailMessage =
        axios.isAxiosError(err) && err.response
          ? resolveDetailMessage(err.response.data?.detail ?? err.response.data)
          : null;
      setTransferFeedback(
        detailMessage ?? "No se pudo registrar la transferencia. Intenta de nuevo."
      );
    } finally {
      setTransferring(false);
    }
  };

  if (loading) {
    return <div className="app-card p-6 text-muted">Cargando cuentas...</div>;
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-rose-500/40 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-200">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6 text-slate-900 dark:text-slate-100">
      <h1 className="section-title">Cuentas</h1>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,360px)_1fr]">
        <div className="app-card p-6">
          <h2 className="text-xl font-semibold">
            {isEditing ? "Editar Cuenta" : "Añadir Cuenta"}
          </h2>
          <p className="mt-1 text-sm text-muted">
            Completa el formulario para {isEditing ? "actualizar" : "registrar"} una cuenta.
          </p>

          <form ref={formRef} onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-muted">
                Nombre de la Cuenta
              </label>
              <input
                type="text"
                value={formState.name}
                onChange={(event) => handleInputChange("name", event.target.value)}
                ref={nameInputRef}
                className="mt-1 w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                placeholder="Ej. Cuenta Nómina"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-muted">
                Tipo de Cuenta
              </label>
              <select
                value={formState.accountType}
                onChange={(event) => handleInputChange("accountType", event.target.value)}
                className="mt-1 w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
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
              <label className="block text-sm font-medium text-muted">
                Saldo Inicial
              </label>
              <input
                type="number"
                value={formState.initialBalance}
                onChange={(event) => handleInputChange("initialBalance", event.target.value)}
                className="mt-1 w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:bg-[var(--app-surface)] dark:text-slate-100"
                placeholder="0.00"
                step="0.01"
                disabled={isEditing}
              />
              {isEditing && (
                <p className="mt-1 text-xs text-muted">
                  El saldo inicial solo se define al crear la cuenta.
                </p>
              )}
            </div>

            {feedback && (
              <div className="rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-muted">
                {feedback}
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-sky-500 to-indigo-500 px-4 py-2 text-sm font-semibold text-white shadow transition hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-200 disabled:cursor-not-allowed disabled:opacity-70"
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
                  className="inline-flex items-center justify-center rounded-xl border border-[var(--app-border)] px-4 py-2 text-sm font-semibold text-muted shadow-sm transition hover:border-sky-400 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:hover:text-slate-200"
                >
                  Cancelar
                </button>
              )}
            </div>
          </form>
        </div>

        <div className="space-y-6">
          <div className="app-card space-y-4 p-6">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-xl font-semibold">
                  Cuentas registradas
                </h2>
                <p className="text-sm text-muted">
                  Haz doble clic sobre una fila para editarla.
                  {selectedAccountName ? ` Seleccionado: ${selectedAccountName}` : ""}
                </p>
              </div>

              <button
                type="button"
                onClick={handleDelete}
                disabled={selectedAccountId === null}
                className="self-start rounded-xl border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-200 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-500/40 dark:text-red-300 dark:hover:bg-red-500/10"
              >
                Eliminar Selección
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-[var(--app-border)]">
              <table className="min-w-full divide-y divide-[var(--app-border)] text-sm">
                <thead className="bg-[var(--app-surface-muted)]">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-muted">
                      Nombre
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted">
                      Tipo
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-muted">
                      Saldo Actual
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--app-border)]">
                  {accounts.length === 0 ? (
                    <tr>
                      <td
                        colSpan={3}
                        className="px-4 py-6 text-center text-sm text-muted"
                      >
                        No hay cuentas registradas.
                      </td>
                    </tr>
                  ) : (
                    accounts.map((account) => {
                      const isSelected = account.id === selectedAccountId;
                      const rowClass = account.is_virtual
                        ? "cursor-not-allowed bg-indigo-50/70 text-slate-700 dark:bg-slate-800/80 dark:text-slate-200"
                        : `cursor-pointer transition hover:bg-sky-50 dark:hover:bg-slate-800/70 ${
                            isSelected
                              ? "bg-sky-100/70 dark:bg-blue-500/20"
                              : "bg-[var(--app-surface)]"
                          }`;
                      const accountTypeLabel = account.is_virtual
                        ? "Virtual"
                        : account.account_type;
                      return (
                        <tr
                          key={account.id}
                          onClick={() => startEditing(account)}
                          onDoubleClick={() => startEditing(account)}
                          className={rowClass}
                        >
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-slate-900 dark:text-slate-100">
                                {account.name}
                              </span>
                              {account.is_virtual && (
                                <span className="rounded-full bg-sky-500/15 px-2 py-0.5 text-xs font-semibold text-sky-600 dark:text-sky-300">
                                  Virtual
                                </span>
                              )}
                            </div>
                            {account.is_virtual && (
                              <p className="mt-1 text-xs text-muted">
                                Saldo disponible según tus presupuestos activos.
                              </p>
                            )}
                          </td>
                          <td className="px-4 py-3 text-muted">
                            {accountTypeLabel}
                          </td>
                          <td className="px-4 py-3 text-right font-semibold">
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

          <div className="app-card space-y-4 p-6">
            <div>
              <h3 className="text-lg font-semibold">Transferir entre cuentas</h3>
              <p className="mt-1 text-sm text-muted">
                Mueve saldo entre tus cuentas reales. Las transferencias no afectan tus reportes de ingresos o gastos.
              </p>
            </div>
            <form onSubmit={handleTransferSubmit} className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
                    Cuenta de origen
                  </label>
                  <select
                    value={transferState.fromAccountId}
                    onChange={(event) =>
                      handleTransferFieldChange("fromAccountId", event.target.value)
                    }
                    className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  >
                    <option value="">Selecciona una cuenta</option>
                    {transferableAccounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
                    Cuenta de destino
                  </label>
                  <select
                    value={transferState.toAccountId}
                    onChange={(event) =>
                      handleTransferFieldChange("toAccountId", event.target.value)
                    }
                    className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  >
                    <option value="">Selecciona una cuenta</option>
                    {transferableAccounts
                      .filter((account) => account.id !== Number(transferState.fromAccountId))
                      .map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.name}
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
                    Monto
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={transferState.amount}
                    onChange={(event) =>
                      handleTransferFieldChange("amount", event.target.value)
                    }
                    className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                    placeholder="0.00"
                    inputMode="decimal"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
                    Fecha
                  </label>
                  <input
                    type="date"
                    max={getTodayDateInputValue()}
                    value={transferState.date}
                    onChange={(event) =>
                      handleTransferFieldChange("date", event.target.value)
                    }
                    className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
                  Nota (opcional)
                </label>
                <input
                  type="text"
                  value={transferState.note}
                  onChange={(event) =>
                    handleTransferFieldChange("note", event.target.value.slice(0, 80))
                  }
                  placeholder="Ej. Ajuste mensual o reembolso"
                  className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                />
              </div>

              {transferableAccounts.length < 2 ? (
                <div className="rounded-xl border border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-xs text-muted">
                  Registra al menos dos cuentas reales para habilitar las transferencias internas.
                </div>
              ) : transferFeedback ? (
                <div className="rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-muted">
                  {transferFeedback}
                </div>
              ) : null}

              <div className="flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={resetTransferForm}
                  className="rounded-xl border border-[var(--app-border)] px-4 py-2 text-sm font-semibold text-muted transition hover:border-sky-400 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:hover:text-slate-200"
                >
                  Limpiar
                </button>
                <button
                  type="submit"
                  disabled={transferring || transferableAccounts.length < 2}
                  className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {transferring ? "Registrando..." : "Registrar transferencia"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
