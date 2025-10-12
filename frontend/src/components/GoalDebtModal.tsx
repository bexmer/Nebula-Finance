import { useState, useEffect } from "react";
import Modal from "react-modal";
import axios from "axios";

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

  useEffect(() => {
    if (isOpen) {
      if (item) {
        // Modo Editar
        setName(item.name);
        setAmount(
          String(mode === "goal" ? item.target_amount : item.total_amount)
        );
        if (mode === "debt") {
          setMinPayment(String(item.minimum_payment));
          setInterest(String(item.interest_rate));
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
    const isGoal = mode === "goal";
    const endpoint = isGoal ? `/api/goals` : `/api/debts`;
    const fullEndpoint = item ? `${endpoint}/${item.id}` : endpoint;

    const data = isGoal
      ? { name, target_amount: parseFloat(amount) }
      : {
          name,
          total_amount: parseFloat(amount),
          minimum_payment: parseFloat(minPayment),
          interest_rate: parseFloat(interest),
        };

    try {
      if (item) {
        await axios.put(`http://127.0.0.1:8000${fullEndpoint}`, data);
      } else {
        await axios.post(`http://127.0.0.1:8000${fullEndpoint}`, data);
      }
      onSave();
      onClose();
    } catch (error) {
      console.error(`Error al guardar ${mode}:`, error);
    }
  };

  return (
    <Modal isOpen={isOpen} onRequestClose={onClose} style={customStyles}>
      <h2 className="text-2xl font-bold mb-4">
        {item ? "Editar" : "Añadir"} {mode === "goal" ? "Meta" : "Deuda"}
      </h2>
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
