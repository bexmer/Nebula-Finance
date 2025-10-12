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
  },
};
Modal.setAppElement("#root");

interface BudgetEntry {
  id?: number;
  category: string;
  amount: number;
  type: string;
  month?: number;
  year?: number;
  description?: string;
  due_date?: string | null;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  entry: BudgetEntry | null;
}

export function BudgetModal({ isOpen, onClose, onSave, entry }: ModalProps) {
  const [formData, setFormData] = useState<Omit<BudgetEntry, "id">>({
    category: "",
    type: "Gasto",
    amount: 0,
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
  });

  useEffect(() => {
    if (entry) {
      setFormData({
        category: entry.category,
        type: entry.type,
        amount: entry.amount,
        month: entry.month ?? new Date().getMonth() + 1,
        year: entry.year ?? new Date().getFullYear(),
        description: entry.description,
        due_date: entry.due_date,
      });
    } else {
      setFormData({
        category: "",
        type: "Gasto",
        amount: 0,
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
      });
    }
  }, [entry, isOpen]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const dataToSave = {
      ...formData,
      amount: parseFloat(String(formData.amount)),
    };
    try {
      if (entry) {
        await axios.put(
          `http://127.0.0.1:8000/api/budget/${entry.id}`,
          dataToSave
        );
      } else {
        await axios.post("http://127.0.0.1:8000/api/budget", dataToSave);
      }
      onSave();
      onClose();
    } catch (error) {
      console.error("Error al guardar la entrada del presupuesto:", error);
    }
  };

  return (
    <Modal isOpen={isOpen} onRequestClose={onClose} style={customStyles}>
      <h2 className="text-2xl font-bold mb-4">
        {entry ? "Editar" : "Añadir"} Entrada de Presupuesto
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Aquí irían los inputs para category, amount, type, month, year */}
        {/* Por ejemplo: */}
        <div>
          <label>Categoría</label>
          <input
            name="category"
            value={formData.category}
            onChange={handleChange}
            required
            className="mt-1 block w-full bg-gray-700 rounded-md p-2"
          />
        </div>
        <div>
          <label>Monto</label>
          <input
            name="amount"
            type="number"
            value={formData.amount}
            onChange={handleChange}
            required
            className="mt-1 block w-full bg-gray-700 rounded-md p-2"
          />
        </div>
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
