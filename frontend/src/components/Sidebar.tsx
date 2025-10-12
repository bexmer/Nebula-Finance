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
} from "lucide-react";
import { useStore } from "../store/useStore";

const navItems = [
  { name: "Dashboard", icon: <LayoutDashboard />, path: "/" },
  { name: "Cuentas", icon: <Wallet />, path: "/accounts" },
  { name: "Transacciones", icon: <ArrowRightLeft />, path: "/transactions" },
  { name: "Presupuesto", icon: <Target />, path: "/budget" },
  // 👇 Esta es la línea que hay que corregir
  { name: "Metas y Deudas", icon: <Goal />, path: "/dashboard-goals" },
  { name: "Portafolio", icon: <Briefcase />, path: "/portfolio" },
  { name: "Análisis", icon: <AreaChart />, path: "/analysis" },
  { name: "Configuración", icon: <Settings />, path: "/settings" },
];

export function Sidebar() {
  return (
    <div className="w-64 bg-gray-800 text-white p-4 flex flex-col">
      <h1 className="text-2xl font-bold mb-8">Nebula Finance</h1>
      <nav className="flex flex-col space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                isActive
                  ? "bg-blue-600 text-white hover:text-lime-200"
                  : "text-gray-300 hover:bg-gray-700 hover:text-white"
              }`
            }
          >
            {item.icon}
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
