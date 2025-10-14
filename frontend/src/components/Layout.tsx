import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Suspense, useEffect, useMemo } from "react";
import { Plus } from "lucide-react";
import { useStore } from "../store/useStore";
import { TransactionModal } from "./TransactionModal";

export function Layout() {
  const openTransactionModal = useStore((state) => state.openTransactionModal);
  const theme = useStore((state) => state.theme);
  const sidebarCollapsed = useStore((state) => state.sidebarCollapsed);
  const location = useLocation();

  const floatingButtonClasses =
    "fixed bottom-6 right-6 z-40 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-r from-sky-500 via-indigo-500 to-fuchsia-500 text-white shadow-xl shadow-sky-500/30 ring-4 ring-sky-200/30 transition-transform duration-200 hover:scale-110 focus:outline-none focus:ring-4 focus:ring-indigo-300 dark:ring-offset-0 dark:focus:ring-indigo-500";

  const layoutOffsetClass = sidebarCollapsed ? "md:pl-20" : "md:pl-72";

  const floatingButtonConfig = useMemo(() => {
    const path = location.pathname.replace(/\/+$/, "") || "/";

    const emit = (eventName: string) => {
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent(eventName));
      }
    };

    const transactionRoutes = new Set(["/", "/transactions", "/dashboard-goals"]);
    if (transactionRoutes.has(path)) {
      return {
        onClick: () => openTransactionModal(null),
        ariaLabel: "Añadir transacción",
        title: "Registrar una nueva transacción",
      };
    }

    if (path === "/accounts") {
      return {
        onClick: () => emit("nebula:accounts-request-new"),
        ariaLabel: "Añadir cuenta",
        title: "Crear una nueva cuenta",
      };
    }

    if (path === "/budget") {
      return {
        onClick: () => emit("nebula:budget-request-add"),
        ariaLabel: "Añadir presupuesto",
        title: "Planificar un nuevo presupuesto",
      };
    }

    if (path === "/portfolio") {
      return {
        onClick: () => emit("nebula:portfolio-request-add"),
        ariaLabel: "Registrar operación",
        title: "Registrar una nueva operación",
      };
    }

    return null;
  }, [location.pathname, openTransactionModal]);

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
    <div className="min-h-screen bg-app text-slate-900 transition-colors duration-300 dark:text-slate-100">
      <Sidebar />
      <div
        className={`flex min-h-screen flex-col transition-[padding] duration-300 ${layoutOffsetClass}`}
      >
        <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-10">
          <Suspense
            fallback={
              <div className="app-card mx-auto max-w-xl p-6 text-center text-muted">
                Cargando contenido...
              </div>
            }
          >
            <div key={location.pathname} className="page-transition">
              <Outlet />
            </div>
          </Suspense>
        </main>
      </div>

      {floatingButtonConfig && (
        <button
          onClick={floatingButtonConfig.onClick}
          className={floatingButtonClasses}
          aria-label={floatingButtonConfig.ariaLabel}
          title={floatingButtonConfig.title}
          type="button"
        >
          <Plus className="h-7 w-7" />
        </button>
      )}

      <TransactionModal />
    </div>
  );
}
