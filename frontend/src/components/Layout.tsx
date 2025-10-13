import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Suspense, useEffect } from "react";
import { Plus } from "lucide-react";
import { useStore } from "../store/useStore";
import { TransactionModal } from "./TransactionModal";

export function Layout() {
  const { openTransactionModal, theme, initializePreferences } = useStore(
    (state) => ({
      openTransactionModal: state.openTransactionModal,
      theme: state.theme,
      initializePreferences: state.initializePreferences,
    })
  );

  useEffect(() => {
    initializePreferences();
  }, [initializePreferences]);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = theme;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  return (
    <div className="bg-app text-slate-900 transition-colors duration-300 dark:text-slate-100">
      <div className="flex min-h-screen w-full flex-col md:flex-row">
        <Sidebar />
        <div className="flex min-h-screen flex-1 flex-col">
          <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-10">
            <Suspense
              fallback={
                <div className="app-card mx-auto max-w-xl p-6 text-center text-muted">
                  Cargando contenido...
                </div>
              }
            >
              <Outlet />
            </Suspense>
          </main>
        </div>
      </div>

      <button
        onClick={() => openTransactionModal(null)}
        className="fixed bottom-6 right-6 z-40 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-r from-sky-500 via-indigo-500 to-fuchsia-500 text-white shadow-xl shadow-sky-500/30 ring-4 ring-sky-200/30 transition-transform duration-200 hover:scale-110 focus:outline-none focus:ring-4 focus:ring-indigo-300 dark:ring-offset-0 dark:focus:ring-indigo-500"
        aria-label="Añadir transacción"
      >
        <Plus className="h-7 w-7" />
      </button>

      <TransactionModal />
    </div>
  );
}
