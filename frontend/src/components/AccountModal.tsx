import { useState, useEffect } from "react";
import Modal from "react-modal";
import axios from 'axios';


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

interface Account {
  id?: number;
  name: string;
  account_type: string;
  current_balance: number;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  account: Account | null; // Si es null, es para crear. Si tiene datos, es para editar.
}

export function AccountModal({ isOpen, onClose, onSave, account }: ModalProps) {
  const [name, setName] = useState("");
  const [type, setType] = useState("");
  const [balance, setBalance] = useState("");

  useEffect(() => {
    if (account) {
      setName(account.name);
      setType(account.account_type);
      setBalance(String(account.current_balance));
    } else {
      // Resetear formulario para crear uno nuevo
      setName("");
      setType("");
      setBalance("");
    }
  }, [account, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const accountData = {
      name,
      account_type: type,
      current_balance: parseFloat(balance),
    };

    try {
      if (account) {
        // Editar
        await axios.put(
          `http://127.0.0.1:8000/api/accounts/${account.id}`,
          accountData
        );
      } else {
        // Crear
        await axios.post("http://127.0.0.1:8000/api/accounts", accountData);
      }
      onSave();
      onClose();
    } catch (error) {
      console.error("Error al guardar la cuenta:", error);
    }
  };

  return (
    <Modal isOpen={isOpen} onRequestClose={onClose} style={customStyles}>
      <h2 className="text-2xl font-bold mb-4">
        {account ? "Editar" : "Añadir"} Cuenta
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* ... Inputs para nombre, tipo y balance (similares al modal de transacciones) ... */}
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
