import { NavLink } from "react-router-dom";

const navItems = [
  { path: "/", label: "Dashboard" },
  { path: "/transactions", label: "Transacciones" },
  { path: "/accounts", label: "Cuentas" },
  { path: "/budget", label: "Presupuesto" },
  { path: "/goals-and-debts", label: "Metas y Deudas" },
  { path: "/portfolio", label: "Portafolio" },
  { path: "/analysis", label: "Análisis" },
  { path: "/settings", label: "Configuración" },
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
              `px-4 py-2 rounded-lg transition-colors ${
                isActive
                  ? "bg-blue-600 text-white hover:text-lime-200"
                  : "text-gray-300 hover:bg-gray-700 hover:text-white"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
