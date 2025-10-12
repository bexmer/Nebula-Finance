import { useState, useEffect } from "react";
import axios from "axios";
import { BudgetModal } from "../components/BudgetModal";

interface BudgetEntry {
  id: number;
  category: string;
  amount: number;
  type: string;
  month: number;
  year: number;
}

// Para mostrar el nombre del mes en lugar del número
const monthNames = [
  "Ene",
  "Feb",
  "Mar",
  "Abr",
  "May",
  "Jun",
  "Jul",
  "Ago",
  "Sep",
  "Oct",
  "Nov",
  "Dic",
];

export function Budget() {
  const [budgetEntries, setBudgetEntries] = useState<BudgetEntry[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<BudgetEntry | null>(null);

  const fetchBudgetEntries = async () => {
    const response = await axios.get("http://127.0.0.1:8000/api/budget");
    setBudgetEntries(response.data);
  };

  useEffect(() => {
    fetchBudgetEntries();
  }, []);

  const handleOpenModal = (entry: BudgetEntry | null) => {
    setSelectedEntry(entry);
    setIsModalOpen(true);
  };

  const handleSave = () => {
    fetchBudgetEntries();
  };

  const handleDelete = async (entryId: number) => {
    if (window.confirm("¿Estás seguro de que quieres eliminar esta entrada?")) {
      await axios.delete(`http://127.0.0.1:8000/api/budget/${entryId}`);
      fetchBudgetEntries();
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Presupuesto</h1>
        <button
          onClick={() => handleOpenModal(null)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Añadir Entrada
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg shadow-lg">
        <table className="w-full table-auto">
          {/* ... (la cabecera de la tabla se queda igual) ... */}
          <tbody>
            {budgetEntries.map((entry) => (
              <tr key={entry.id} className="border-t border-gray-700">
                {/* ... (las celdas de datos se quedan igual) ... */}
                <td className="p-4 text-right">
                  <button
                    onClick={() => handleOpenModal(entry)}
                    className="text-blue-400 hover:text-blue-300 mr-4"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(entry.id)}
                    className="text-red-400 hover:text-red-300"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <BudgetModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        entry={selectedEntry}
      />
    </div>
  );
}
