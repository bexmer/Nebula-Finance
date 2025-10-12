import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Suspense } from "react";
import { Plus } from "lucide-react";
import { useStore } from "../store/useStore"; // Importar el store
import { TransactionModal } from "./TransactionModal"; // Importar el modal

export function Layout() {
  // Obtenemos la función para abrir el modal desde nuestro store global
  const { openTransactionModal } = useStore();

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar />
      <main className="flex-grow p-6 overflow-auto">
        <Suspense
          fallback={<div className="text-center">Cargando página...</div>}
        >
          <Outlet />
        </Suspense>
      </main>

      {/* --- BOTÓN FLOTANTE GLOBAL Y ÚNICO --- */}
      <button
        onClick={() => openTransactionModal(null)}
        className="fixed bottom-8 right-8 bg-blue-600 hover:bg-blue-700 text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg z-40 transition-transform hover:scale-110"
        aria-label="Añadir Transacción"
      >
        <Plus size={28} />
      </button>

      {/* --- MODAL GLOBAL Y ÚNICO --- */}
      {/* El modal ahora vive aquí para poder ser llamado desde cualquier página */}
      <TransactionModal />
    </div>
  );
}
