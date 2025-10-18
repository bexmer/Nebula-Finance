import { useCallback, useEffect, useState } from "react";
import axios from "axios";

import { apiPath } from "../utils/api";

interface AccountTypeOption {
  id: number;
  name: string;
}

interface QuickAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (accountId: number) => Promise<void> | void;
}

export function QuickAccountModal({ isOpen, onClose, onCreated }: QuickAccountModalProps) {
  const [name, setName] = useState("");
  const [typeId, setTypeId] = useState("");
  const [balance, setBalance] = useState("");
  const [types, setTypes] = useState<AccountTypeOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAccountTypes = useCallback(async () => {
    try {
      const response = await axios.get<AccountTypeOption[]>(apiPath("/config/account-types"));
      setTypes(response.data);
    } catch (fetchError) {
      console.error("Error al obtener los tipos de cuenta disponibles:", fetchError);
      setTypes([]);
    }
  }, []);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setError(null);
    setLoading(false);
    setName("");
    setTypeId("");
    setBalance("");
    fetchAccountTypes();
  }, [fetchAccountTypes, isOpen]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Ingresa un nombre para la cuenta.");
      return;
    }

    if (!typeId) {
      setError("Selecciona un tipo de cuenta.");
      return;
    }

    const parsedBalance = parseFloat(balance || "0");
    if (!Number.isFinite(parsedBalance)) {
      setError("Ingresa un saldo inicial válido.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        name: trimmedName,
        account_type: typeId,
        initial_balance: parsedBalance,
        annual_interest_rate: 0,
        compounding_frequency: "Mensual",
      };
      const response = await axios.post(apiPath("/accounts"), payload);
      const createdId = response?.data?.id;
      if (createdId) {
        await Promise.resolve(onCreated(createdId));
      }
      onClose();
    } catch (submitError) {
      console.error("No se pudo crear la cuenta:", submitError);
      setError("No se pudo crear la cuenta. Verifica la información e inténtalo nuevamente.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="app-modal-overlay">
      <div className="app-modal-panel app-card w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-[var(--app-text)]">Nueva cuenta</h2>
        <p className="mt-1 text-sm text-muted">
          Crea una cuenta rápidamente sin abandonar el registro de tu transacción.
        </p>

        <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--app-text)]" htmlFor="quick-account-name">
              Nombre
            </label>
            <input
              id="quick-account-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={60}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-[var(--app-text)] focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200"
              placeholder="Cuenta bancaria, tarjeta, efectivo..."
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--app-text)]" htmlFor="quick-account-type">
              Tipo de cuenta
            </label>
            <select
              id="quick-account-type"
              value={typeId}
              onChange={(event) => setTypeId(event.target.value)}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-[var(--app-text)] focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200"
            >
              <option value="">-- Selecciona un tipo --</option>
              {types.map((type) => (
                <option key={type.id} value={type.name}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--app-text)]" htmlFor="quick-account-balance">
              Saldo inicial
            </label>
            <input
              id="quick-account-balance"
              type="number"
              inputMode="decimal"
              step="0.01"
              value={balance}
              onChange={(event) => setBalance(event.target.value)}
              className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-[var(--app-text)] focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200"
              placeholder="0.00"
            />
          </div>

          {error ? (
            <div className="rounded-lg border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              className="w-full rounded-xl border border-[var(--app-border)] bg-transparent px-4 py-2 text-sm font-semibold text-muted transition hover:border-slate-400 hover:text-slate-700 sm:w-auto"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-gradient-to-r from-sky-500 via-indigo-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-500/30 transition hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            >
              {loading ? "Guardando..." : "Crear cuenta"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
