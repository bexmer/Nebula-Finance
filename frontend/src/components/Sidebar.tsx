import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Wallet,
  ArrowRightLeft,
  Target,
  Goal,
  Briefcase,
  Settings,
  AreaChart,
  Menu,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useStore } from "../store/useStore";
import nebulaLogoFull from "../assets/logo-nb-ligth.png";
import nebulaLogoMark from "../assets/logo-mini-nb-ligth.png";
import nebulaLogoFullD from "../assets/logo-nb.png";
import nebulaLogoMarkD from "../assets/logo-mini-nb.png";

const themeLogos = {
  light: {
    full: nebulaLogoFullD,
    mark: nebulaLogoMarkD,
  },
  dark: {
    full: nebulaLogoFull,
    mark: nebulaLogoMark,
  },
};

const navItems = [
  {
    name: "Dashboard",
    icon: <LayoutDashboard className="h-5 w-5" />,
    path: "/",
  },
  { name: "Cuentas", icon: <Wallet className="h-5 w-5" />, path: "/accounts" },
  {
    name: "Transacciones",
    icon: <ArrowRightLeft className="h-5 w-5" />,
    path: "/transactions",
  },
  {
    name: "Presupuesto",
    icon: <Target className="h-5 w-5" />,
    path: "/budget",
  },
  {
    name: "Metas y Deudas",
    icon: <Goal className="h-5 w-5" />,
    path: "/dashboard-goals",
  },
  {
    name: "Portafolio",
    icon: <Briefcase className="h-5 w-5" />,
    path: "/portfolio",
  },
  {
    name: "Análisis",
    icon: <AreaChart className="h-5 w-5" />,
    path: "/analysis",
  },
  {
    name: "Configuración",
    icon: <Settings className="h-5 w-5" />,
    path: "/settings",
  },
];

export function Sidebar() {
  const theme = useStore((state) => state.theme);
  const toggleTheme = useStore((state) => state.toggleTheme);
  const sidebarCollapsed = useStore((state) => state.sidebarCollapsed);
  const toggleSidebar = useStore((state) => state.toggleSidebar);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const collapseWidthClass = sidebarCollapsed ? "md:w-20" : "md:w-72";
  const navLabelClass = sidebarCollapsed ? "md:hidden" : "md:inline";

  const logoSrc = useMemo(() => {
    const palette = theme === "dark" ? themeLogos.dark : themeLogos.light;
    return sidebarCollapsed ? palette.mark : palette.full;
  }, [sidebarCollapsed, theme]);

  return (
    <aside
      className={`z-50 w-full flex-shrink-0 border-b border-[var(--app-border)] bg-[var(--app-surface)]/95 backdrop-blur transition-all duration-300 supports-[backdrop-filter]:bg-[var(--app-surface)]/80 md:fixed md:inset-y-0 md:left-0 md:z-40 md:border-b-0 md:border-r md:bg-[var(--app-surface)]/90 ${collapseWidthClass}`}
    >
      <div className="flex h-full flex-col md:h-screen">
        <div className="flex items-center justify-between gap-3 px-4 py-4 md:justify-center md:py-6">
          <img
            src={logoSrc}
            alt="Nebula Finance"
            className={`transition-all duration-500 ease-out motion-reduce:duration-0 ${
              sidebarCollapsed ? "h-10 w-10" : "h-10 w-auto"
            }`}
          />
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] p-2 text-muted transition hover:text-sky-500 md:hidden"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label="Alternar navegación"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>

        <nav
          className={`flex flex-col gap-1 px-2 pb-4 md:flex md:flex-1 md:overflow-y-auto md:px-3 ${
            mobileMenuOpen ? "flex" : "hidden"
          } md:block`}
        >
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all ${
                  sidebarCollapsed ? "md:justify-center" : ""
                } ${
                  isActive
                    ? "border border-sky-500/30 bg-gradient-to-r from-sky-500/15 to-indigo-500/20 text-sky-600 shadow-sm shadow-sky-500/20 dark:text-sky-300"
                    : "text-muted hover:bg-[var(--app-surface-muted)] hover:text-sky-600 dark:hover:text-sky-300"
                }`
              }
              onClick={() => setMobileMenuOpen(false)}
            >
              {item.icon}
              <span
                className={`truncate transition-opacity duration-200 ${navLabelClass}`}
              >
                {item.name}
              </span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto space-y-3 border-t border-[var(--app-border)] px-4 py-4">
          <button
            type="button"
            className={`hidden w-full items-center gap-2 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-4 py-3 text-sm font-semibold transition hover:border-sky-400/60 hover:text-sky-600 dark:hover:text-sky-300 md:flex ${
              sidebarCollapsed ? "md:justify-center" : "justify-between"
            }`}
            onClick={toggleSidebar}
            aria-label={
              sidebarCollapsed
                ? "Expandir barra lateral"
                : "Contraer barra lateral"
            }
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-5 w-5" />
            ) : (
              <>
                <span className="text-sm font-semibold">Contraer menú</span>
                <ChevronLeft className="h-5 w-5" />
              </>
            )}
          </button>
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={
              theme === "dark"
                ? "Cambiar a modo claro"
                : "Cambiar a modo oscuro"
            }
            className={`flex w-full items-center gap-3 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-4 py-3 text-sm font-semibold transition hover:border-sky-400/60 hover:text-sky-600 dark:hover:text-sky-300 ${
              sidebarCollapsed ? "md:justify-center md:px-2" : "justify-between"
            }`}
          >
            {theme === "dark" ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
            {!sidebarCollapsed && (
              <span className="hidden md:inline">
                {theme === "dark" ? "Modo oscuro" : "Modo claro"}
              </span>
            )}
            <span className="md:hidden">
              {theme === "dark" ? "Modo oscuro" : "Modo claro"}
            </span>
          </button>
        </div>
      </div>
    </aside>
  );
}
