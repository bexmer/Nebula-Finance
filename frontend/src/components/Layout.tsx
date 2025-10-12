import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { AddTransactionModal } from "./AddTransactionModal";
import { useStore } from "../store/useStore"; // <-- 1. Importar el store

export function Layout() {
  // 2. Obtener el estado y las acciones del store
  const {
    isTransactionModalOpen,
    openTransactionModal,
    closeTransactionModal,
    fetchTransactions,
  } = useStore();

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto relative">
        <Outlet />

        <button
          // 3. Usar la acción del store para abrir el modal en modo "crear"
          onClick={() => openTransactionModal(null)}
          className="absolute bottom-8 right-8 bg-blue-600 hover:bg-blue-700 text-white rounded-full w-14 h-14 flex items-center justify-center text-3xl shadow-lg"
        >
          +
        </button>
      </main>

      <AddTransactionModal
        // 4. Pasar el estado y las acciones al modal
        isOpen={isTransactionModalOpen}
        onClose={closeTransactionModal}
        onSave={fetchTransactions} // Al guardar, simplemente volvemos a pedir los datos
        transaction={null} // Modo "crear", no hay transacción seleccionada
      />
    </div>
  );
}
