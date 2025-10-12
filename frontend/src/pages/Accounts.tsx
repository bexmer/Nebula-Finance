// frontend/src/pages/Accounts.tsx

import { useState, useEffect } from "react";
import axios from "axios";

// Definimos la "forma" que tendrán los datos de una cuenta
interface Account {
  id: number;
  name: string;
  account_type: string;
  current_balance: number;
}

export function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Esta función se ejecutará cuando el componente se cargue
    const fetchAccounts = async () => {
      try {
        setLoading(true);
        // ¡Aquí hacemos la llamada a nuestro backend de Python!
        const response = await axios.get("http://127.0.0.1:8000/api/accounts");
        setAccounts(response.data);
        setError(null);
      } catch (err) {
        console.error("Error al obtener las cuentas:", err);
        setError(
          "No se pudieron cargar las cuentas. Asegúrate de que el backend esté funcionando."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAccounts();
  }, []); // El array vacío asegura que esto se ejecute solo una vez

  if (loading) {
    return <div>Cargando cuentas...</div>;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Cuentas</h1>
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md">
          Añadir Cuenta
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg p-4">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="p-2">Nombre</th>
              <th className="p-2">Tipo</th>
              <th className="p-2 text-right">Saldo Actual</th>
              <th className="p-2 text-center">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((account) => (
              <tr
                key={account.id}
                className="border-b border-gray-700 hover:bg-gray-700"
              >
                <td className="p-2">{account.name}</td>
                <td className="p-2">{account.account_type}</td>
                <td className="p-2 text-right">
                  {/* Formateamos el número como moneda */}
                  {new Intl.NumberFormat("es-MX", {
                    style: "currency",
                    currency: "MXN",
                  }).format(account.current_balance)}
                </td>
                <td className="p-2 text-center">
                  <button className="text-blue-400 hover:text-blue-300 mr-2">
                    Editar
                  </button>
                  <button className="text-red-400 hover:text-red-300">
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
