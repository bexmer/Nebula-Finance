import { useState, useEffect } from "react";
import axios from "axios";
import { AccountModal } from "../components/AccountModal"; // Importar el modal

// Interfaz para definir la forma de una cuenta
interface Account {
  id: number;
  name: string;
  account_type: string;
  current_balance: number;
}

export function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  const fetchAccounts = async () => {
    const response = await axios.get("http://127.0.0.1:8000/api/accounts");
    setAccounts(response.data);
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleOpenModal = (account: Account | null) => {
    setSelectedAccount(account);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedAccount(null);
  };

  const handleSave = () => {
    fetchAccounts(); // Refrescar la lista después de guardar
  };

  const handleDelete = async (accountId: number) => {
    if (window.confirm("¿Estás seguro de que quieres eliminar esta cuenta?")) {
      await axios.delete(`http://127.0.0.1:8000/api/accounts/${accountId}`);
      fetchAccounts();
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Cuentas</h1>
        <button
          onClick={() => handleOpenModal(null)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Añadir Cuenta
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg shadow-lg">
        <table className="w-full table-auto">
          {/* ... (la cabecera de la tabla se queda igual) ... */}
          <tbody>
            {accounts.map((account) => (
              <tr key={account.id} className="border-t border-gray-700">
                <td className="p-4 font-medium">{account.name}</td>
                <td className="p-4 text-gray-400">{account.account_type}</td>
                <td className="p-4 text-right font-mono ...">
                  ${account.current_balance.toFixed(2)}
                </td>
                <td className="p-4 text-right">
                  <button
                    onClick={() => handleOpenModal(account)}
                    className="text-blue-400 hover:text-blue-300 mr-4"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(account.id)}
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

      <AccountModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
        account={selectedAccount}
      />
    </div>
  );
}
