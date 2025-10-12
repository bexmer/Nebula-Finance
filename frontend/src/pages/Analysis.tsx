import { useState, useEffect } from "react";
import axios from "axios";
import { CategoryBarChart } from "../components/CategoryBarChart";

interface CashFlowData {
  income: { category: string; amount: number }[];
  expenses: { category: string; amount: number }[];
}

export function Analysis() {
  const [data, setData] = useState<CashFlowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await axios.get(
          "http://127.0.0.1:8000/api/analysis/cash-flow",
          {
            params: { year, month },
          }
        );
        setData(response.data);
      } catch (error) {
        console.error("Error al obtener datos de análisis:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [year, month]); // Se vuelve a ejecutar si el año o el mes cambian

  const years = Array.from(
    { length: 10 },
    (_, i) => new Date().getFullYear() - i
  );
  const monthNames = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
  ];

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Análisis de Flujo de Efectivo</h1>
        <div className="flex items-center space-x-4">
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="bg-gray-700 p-2 rounded"
          >
            {monthNames.map((name, index) => (
              <option key={name} value={index + 1}>
                {name}
              </option>
            ))}
          </select>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="bg-gray-700 p-2 rounded"
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <p>Cargando gráficos...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {data && (
            <CategoryBarChart
              title="Ingresos por Categoría"
              data={data.income}
              barColor="rgba(54, 162, 235, 0.7)"
            />
          )}
          {data && (
            <CategoryBarChart
              title="Gastos por Categoría"
              data={data.expenses}
              barColor="rgba(255, 99, 132, 0.7)"
            />
          )}
        </div>
      )}
    </div>
  );
}
