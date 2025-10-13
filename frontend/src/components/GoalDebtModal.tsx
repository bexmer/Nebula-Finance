import { useState, useEffect } from "react";
import Modal from "react-modal";
import axios from "axios";

import { apiPath } from "../utils/api";

const customStyles = {
  content: {
    top: "50%",
    left: "50%",
    right: "auto",
    bottom: "auto",
    marginRight: "-50%",
    transform: "translate(-50%, -50%)",
    backgroundColor: "#1f2937",
    border: "1px solid #374151",
    borderRadius: "0.5rem",
    padding: "2rem",
    width: "90%",
    maxWidth: "500px",
  },
  overlay: { backgroundColor: "rgba(0, 0, 0, 0.75)" },
};

Modal.setAppElement("#root");

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
      } else {
        // Modo Crear
        setName("");
        setAmount("");
        setMinPayment("");
        setInterest("");
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

    if (isGoal) {
      data = { name: trimmedName, target_amount: parsedAmount };
    } else {
      const parsedMinPayment = parseFloat(minPayment || "0");
      const parsedInterest = parseFloat(interest || "0");

      if (!Number.isFinite(parsedMinPayment) || parsedMinPayment < 0) {
        setError("Ingresa un pago mínimo válido.");
        return;
      }

      if (parsedMinPayment > parsedAmount) {
        setError("El pago mínimo no puede ser mayor que el monto total.");
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
        axios.isAxiosError(error) && error.response?.data?.detail
          ? String(error.response.data.detail)
          : "No se pudo guardar la información. Inténtalo de nuevo.";
      setError(message);
    }
  };

  return (
    <Modal isOpen={isOpen} onRequestClose={onClose} style={customStyles}>
      <h2 className="text-2xl font-bold mb-4">
        {item ? "Editar" : "Añadir"} {mode === "goal" ? "Meta" : "Deuda"}
      </h2>
      {error && (
        <p className="mb-4 rounded-md border border-rose-400/60 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300">
            Nombre
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="mt-1 block w-full bg-gray-700 rounded-md p-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300">
            {mode === "goal" ? "Monto Objetivo" : "Monto Total"}
          </label>
          <input
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
            className="mt-1 block w-full bg-gray-700 rounded-md p-2"
          />
        </div>
        {mode === "debt" && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Pago Mínimo
              </label>
              <input
                type="number"
                step="0.01"
                value={minPayment}
                onChange={(e) => setMinPayment(e.target.value)}
                required
                className="mt-1 block w-full bg-gray-700 rounded-md p-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Tasa de Interés (%)
              </label>
              <input
                type="number"
                step="0.01"
                value={interest}
                onChange={(e) => setInterest(e.target.value)}
                required
                className="mt-1 block w-full bg-gray-700 rounded-md p-2"
              />
            </div>
          </>
        )}
        <div className="flex justify-end space-x-4 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-md"
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-md"
          >
            Guardar
          </button>
        </div>
      </form>
    </Modal>
  );
}
