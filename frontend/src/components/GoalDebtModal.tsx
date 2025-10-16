import { useState, useEffect, type CSSProperties } from "react";
import Modal from "react-modal";
import axios from "axios";

import { apiPath } from "../utils/api";

Modal.setAppElement("#root");

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
    const typed = detail as { message?: unknown; detail?: unknown };
    return resolveDetailMessage(typed.detail ?? typed.message);
  }
  return String(detail);
};

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  mode: "goal" | "debt";
  item: any | null;
}

export function GoalDebtModal({
  isOpen,
  onClose,
  onSave,
  mode,
  item,
}: ModalProps) {
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [minPayment, setMinPayment] = useState("");
  const [interest, setInterest] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [initialValues, setInitialValues] = useState({
    name: "",
    amount: "",
    minPayment: "",
    interest: "",
  });

  const enforceNumericLimit = (value: string) => {
    const digits = value.replace(/[^0-9]/g, "");
    if (digits.length > 10) {
      return false;
    }
    return true;
  };

  useEffect(() => {
    if (isOpen) {
      setError(null);
      if (item) {
        // Modo Editar
        setName(item.name);
        setAmount(
          String(mode === "goal" ? item.target_amount : item.total_amount)
        );
        if (mode === "debt") {
          setMinPayment(
            item.minimum_payment !== undefined && item.minimum_payment !== null
              ? String(item.minimum_payment)
              : ""
          );
          setInterest(
            item.interest_rate !== undefined && item.interest_rate !== null
              ? String(item.interest_rate)
              : ""
          );
        }
        setInitialValues({
          name: item.name,
          amount: String(mode === "goal" ? item.target_amount : item.total_amount),
          minPayment:
            mode === "debt"
              ? item.minimum_payment !== undefined && item.minimum_payment !== null
                ? String(item.minimum_payment)
                : ""
              : "",
          interest:
            mode === "debt"
              ? item.interest_rate !== undefined && item.interest_rate !== null
                ? String(item.interest_rate)
                : ""
              : "",
        });
      } else {
        // Modo Crear
        setName("");
        setAmount("");
        setMinPayment("");
        setInterest("");
        setInitialValues({ name: "", amount: "", minPayment: "", interest: "" });
      }
    }
  }, [isOpen, item, mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("El nombre es obligatorio.");
      return;
    }

    const parsedAmount = parseFloat(amount);
    if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      setError("Ingresa un monto válido mayor que cero.");
      return;
    }

    const isGoal = mode === "goal";
    const resource = isGoal ? "goals" : "debts";
    const url = apiPath(`/${resource}${item ? `/${item.id}` : ""}`);

    let data: Record<string, unknown>;
    let parsedMinPayment = 0;
    let parsedInterest = 0;

    if (isGoal) {
      data = { name: trimmedName, target_amount: parsedAmount };
    } else {
      parsedMinPayment = parseFloat(minPayment || "0");
      parsedInterest = parseFloat(interest || "0");

      if (!Number.isFinite(parsedMinPayment) || parsedMinPayment < 0) {
        setError("Ingresa un pago mínimo válido.");
        return;
      }

      if (parsedMinPayment >= parsedAmount) {
        setError("El pago mínimo debe ser menor que el monto total de la deuda.");
        return;
      }

      if (!Number.isFinite(parsedInterest) || parsedInterest < 0) {
        setError("Ingresa una tasa de interés válida.");
        return;
      }

      data = {
        name: trimmedName,
        total_amount: parsedAmount,
        minimum_payment: parsedMinPayment,
        interest_rate: parsedInterest,
      };
    }

    if (item) {
      const initialName = initialValues.name.trim();
      const initialAmount = parseFloat(initialValues.amount || "0");
      const unchangedName = initialName === trimmedName;
      const unchangedAmount =
        Number.isFinite(initialAmount) && initialAmount === parsedAmount;

      if (mode === "goal") {
        if (unchangedName && unchangedAmount) {
          setError("No has realizado cambios en esta meta.");
          return;
        }
      } else {
        const initialMinPayment = parseFloat(initialValues.minPayment || "0");
        const initialInterest = parseFloat(initialValues.interest || "0");
        const unchangedDebtFields =
          Number.isFinite(initialMinPayment) &&
          Number.isFinite(initialInterest) &&
          initialMinPayment === parsedMinPayment &&
          initialInterest === parsedInterest;

        if (unchangedName && unchangedAmount && unchangedDebtFields) {
          setError("No has realizado cambios en esta deuda.");
          return;
        }
      }
    }

    try {
      if (item) {
        await axios.put(url, data);
      } else {
        await axios.post(url, data);
      }
      onSave();
      onClose();
    } catch (error) {
      console.error(`Error al guardar ${mode}:`, error);
      const message =
        axios.isAxiosError(error) && error.response
          ? resolveDetailMessage(
              error.response.data?.detail ?? error.response.data
            )
          : null;
      setError(
        message ?? "No se pudo guardar la información. Inténtalo de nuevo."
      );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      className="nebula-modal__content"
      overlayClassName="nebula-modal__overlay"
      closeTimeoutMS={320}
    >
      <div
        className="nebula-modal__panel app-card p-6"
        style={{ "--modal-max-width": "min(90vw, 520px)" } as CSSProperties}
      >
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-4">
          {item ? "Editar" : "Añadir"} {mode === "goal" ? "Meta" : "Deuda"}
        </h2>
        {error && (
          <p className="mb-4 rounded-md border border-rose-400/60 bg-rose-500/10 px-3 py-2 text-sm text-rose-600 dark:text-rose-200">
            {error}
          </p>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
              Nombre
            </label>
            <input
              type="text"
              value={name}
              maxLength={100}
              onChange={(e) => setName(e.target.value)}
              required
              className="mt-1 block w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
              {mode === "goal" ? "Monto Objetivo" : "Monto Total"}
            </label>
            <input
              type="number"
              step="0.01"
              inputMode="decimal"
              value={amount}
              onChange={(e) => {
                if (enforceNumericLimit(e.target.value)) {
                  setAmount(e.target.value);
                }
              }}
              required
              className="mt-1 block w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            />
          </div>
          {mode === "debt" && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
                  Pago Mínimo
                </label>
                <input
                  type="number"
                  step="0.01"
                  inputMode="decimal"
                  value={minPayment}
                  onChange={(e) => {
                    if (enforceNumericLimit(e.target.value)) {
                      setMinPayment(e.target.value);
                    }
                  }}
                  required
                  className="mt-1 block w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
                  Tasa de Interés (%)
                </label>
                <input
                  type="number"
                  step="0.01"
                  inputMode="decimal"
                  value={interest}
                  onChange={(e) => {
                    if (enforceNumericLimit(e.target.value)) {
                      setInterest(e.target.value);
                    }
                  }}
                  required
                  className="mt-1 block w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-200 dark:text-slate-100"
                />
              </div>
            </>
          )}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-[var(--app-border)] px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-sky-400 hover:text-slate-900 dark:text-slate-200 dark:hover:text-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-sky-500"
            >
              Guardar
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
