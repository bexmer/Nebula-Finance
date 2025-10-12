import { useState, useEffect } from "react";
import { useStore } from "../store/useStore"; // <-- 1. Importar el store
import axios from "axios";

interface Transaction {
  id: number;
  date: string;
  description: string;
  amount: number;
  type: string;
  category: string;
}

export function Transactions() {
  // 2. Obtener el estado y las acciones del store
  const { transactions, fetchTransactions, openTransactionModal } = useStore();

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const handleDelete = async (transactionId: number) => {
    if (
      window.confirm("¿Estás seguro de que quieres eliminar esta transacción?")
    ) {
      await axios.delete(
        `http://127.0.0.1:8000/api/transactions/${transactionId}`
      );
      fetchTransactions(); // Refrescar la lista
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Transacciones</h1>
      <div className="bg-gray-800 rounded-lg shadow-lg">
        <table className="w-full table-auto">
          {/* ... (cabecera de la tabla) ... */}
          <tbody>
            {transactions.map((t) => (
              <tr key={t.id} className="border-t border-gray-700">
                {/* ... (celdas de datos) ... */}
                <td className="p-4 text-right">
                  {/* 3. Usar la acción del store para abrir el modal en modo "editar" */}
                  <button
                    onClick={() => openTransactionModal(t)}
                    className="text-blue-400 hover:text-blue-300 mr-4"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(t.id)}
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
    </div>
  );
}
