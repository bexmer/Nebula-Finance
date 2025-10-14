import { useState, useEffect } from "react";
import Modal from "react-modal";
import axios from "axios";
import { Transaction } from "../store/useStore";

import { apiPath } from "../utils/api";
import {
  getTodayDateInputValue,
  normalizeDateInputValue,
} from "../utils/date";

// --- Interfaces para los datos que cargaremos para los desplegables ---
interface Account {
  id: number;
  name: string;
}
interface Goal {
  id: number;
  name: string;
}
interface Debt {
  id: number;
  name: string;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void; // Función para refrescar la lista
  transaction: Transaction | null; // Si es null -> Crear, si tiene datos -> Editar
}

// Estilos para el modal
const customStyles = {
  content: {
    top: "50%",
    left: "50%",
    right: "auto",
    bottom: "auto",
    marginRight: "-50%",
    transform: "translate(-50%, -50%)",
    backgroundColor: "#1f2937", // bg-gray-800
    border: "1px solid #374151", // border-gray-700
    borderRadius: "0.5rem",
    padding: "2rem",
    width: "90%",
    maxWidth: "500px",
  },
  overlay: {
    backgroundColor: "rgba(0, 0, 0, 0.75)",
  },
};

Modal.setAppElement("#root"); // Mejora la accesibilidad

export function AddTransactionModal({
  isOpen,
  onClose,
  onSave,
  transaction,
}: ModalProps) {
  // Estados para cada campo del formulario
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(getTodayDateInputValue());
  const [type, setType] = useState("Gasto");
  const [category, setCategory] = useState("");
  const [accountId, setAccountId] = useState<number | string>("");
  const [goalId, setGoalId] = useState<number | string>("");
  const [debtId, setDebtId] = useState<number | string>("");

  // Estados para los datos de los menús desplegables
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [debts, setDebts] = useState<Debt[]>([]);

  // Efecto para cargar los datos de los desplegables cuando el modal se abre
  useEffect(() => {
    if (isOpen) {
      Promise.all([
        axios.get(apiPath("/accounts")),
        axios.get(apiPath("/dashboard-goals")),
        axios.get(apiPath("/debts")),
      ])
        .then(([accountsRes, goalsRes, debtsRes]) => {
          setAccounts(accountsRes.data);
          setGoals(goalsRes.data);
          setDebts(debtsRes.data);
        })
        .catch((error) =>
          console.error("Error al cargar datos para el modal:", error)
        );
    }
  }, [isOpen]);

  // Efecto para llenar el formulario si estamos en modo "Editar"
  useEffect(() => {
    if (transaction) {
      setDescription(transaction.description);
      setAmount(String(transaction.amount));
      setDate(normalizeDateInputValue(transaction.date));
      setType(transaction.type);
      setCategory(transaction.category);
      setAccountId(transaction.account_id);
      setGoalId(transaction.goal_id ?? "");
      setDebtId(transaction.debt_id ?? "");
    } else {
      // Resetea el formulario si estamos en modo "Crear"
      setDescription("");
      setAmount("");
      setDate(getTodayDateInputValue());
      setType("Gasto");
      setCategory("");
      setAccountId("");
      setGoalId("");
      setDebtId("");
    }
  }, [transaction, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountId) {
      alert("Por favor, selecciona una cuenta.");
      return;
    }

    const transactionData = {
      date,
      description,
      amount: parseFloat(amount),
      type,
      category: category || "Sin categoría",
      account_id: Number(accountId),
      goal_id: goalId ? Number(goalId) : null,
      debt_id: debtId ? Number(debtId) : null,
    };

    try {
      if (transaction) {
        // Modo Editar (PUT)
        await axios.put(
          apiPath(`/transactions/${transaction.id}`),
          transactionData
        );
      } else {
        // Modo Crear (POST)
        await axios.post(apiPath("/transactions"), transactionData);
      }
      onSave(); // Llama a la función para refrescar la lista de transacciones
      onClose(); // Cierra el modal
    } catch (error) {
      console.error("Error al guardar la transacción:", error);
      alert("Hubo un error al guardar la transacción.");
    }
  };

  return (
    <Modal isOpen={isOpen} onRequestClose={onClose} style={customStyles}>
      <h2 className="text-2xl font-bold mb-6">
        {transaction ? "Editar" : "Añadir"} Transacción
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300">
            Descripción
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md p-2 text-white"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Monto
            </label>
            <input
              type="number"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
              className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md p-2 text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Fecha
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md p-2 text-white"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Tipo
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md p-2 text-white"
            >
              <option>Gasto</option>
              <option>Ingreso</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Categoría
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="(Opcional)"
              className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md p-2 text-white"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300">
            Cuenta
          </label>
          <select
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            required
            className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md p-2 text-white"
          >
            <option value="">-- Selecciona una cuenta --</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Asociar a Meta
            </label>
            <select
              value={goalId}
              onChange={(e) => setGoalId(e.target.value)}
              className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md p-2 text-white"
            >
              <option value="">-- Ninguna --</option>
              {goals.map((goal) => (
                <option key={goal.id} value={goal.id}>
                  {goal.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Asociar a Deuda
            </label>
            <select
              value={debtId}
              onChange={(e) => setDebtId(e.target.value)}
              className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md p-2 text-white"
            >
              <option value="">-- Ninguna --</option>
              {debts.map((debt) => (
                <option key={debt.id} value={debt.id}>
                  {debt.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-end space-x-4 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-md transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-md transition-colors"
          >
            Guardar
          </button>
        </div>
      </form>
    </Modal>
  );
}
