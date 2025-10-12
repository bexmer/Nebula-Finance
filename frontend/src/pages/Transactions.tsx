import { useEffect } from "react";
import { useStore, Transaction } from "../store/useStore";
import { TransactionModal } from "../components/TransactionModal";
import axios from "axios";

export function Transactions() {
  const { transactions, fetchTransactions, openTransactionModal } = useStore();

  useEffect(() => {
    fetchTransactions();
  }, []);

  const handleDelete = async (id: number) => {
    if (
      window.confirm("¿Estás seguro de que quieres eliminar esta transacción?")
    ) {
      try {
        await axios.delete(`http://127.0.0.1:8000/api/transactions/${id}`);
        fetchTransactions();
      } catch (err) {
        alert("No se pudo eliminar la transacción.");
      }
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Transacciones</h1>
        <button
          onClick={() => openTransactionModal(null)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md"
        >
          Añadir Transacción
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-700">
            <tr>
              <th className="p-3">Fecha</th>
              <th className="p-3">Descripción</th>
              <th className="p-3">Tipo</th>
              <th className="p-3">Categoría</th>
              <th className="p-3">Cuenta</th>
              <th className="p-3 text-right">Monto</th>
              <th className="p-3 text-center">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <tr
                key={t.id}
                className="border-b border-gray-700 hover:bg-gray-600"
              >
                <td className="p-3">{new Date(t.date).toLocaleDateString()}</td>
                <td className="p-3">{t.description}</td>
                <td className="p-3">{t.type}</td>
                <td className="p-3">{t.category}</td>
                <td className="p-3">{t.account?.name}</td>
                <td
                  className={`p-3 text-right font-semibold ${
                    t.type === "Ingreso" ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {new Intl.NumberFormat("es-MX", {
                    style: "currency",
                    currency: "MXN",
                  }).format(t.amount)}
                </td>
                <td className="p-3 text-center">
                  {/* --- ¡CAMBIO AQUÍ! --- */}
                  <button
                    onClick={() => openTransactionModal(t)}
                    className="text-blue-400 hover:text-blue-300 mr-3"
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
      <TransactionModal />
    </div>
  );
}
