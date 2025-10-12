import { useState, useEffect } from "react";
import axios from "axios";

interface PortfolioSummary {
  symbol: string;
  name: string;
  quantity: number;
  avg_cost: number;
  market_value: number;
  unrealized_pnl: number;
}

interface TradeHistory {
  id: number;
  date: string;
  symbol: string;
  type: string;
  quantity: number;
  price: number;
}

export function Portfolio() {
  const [summary, setSummary] = useState<PortfolioSummary[]>([]);
  const [history, setHistory] = useState<TradeHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [summaryRes, historyRes] = await Promise.all([
          axios.get("http://127.0.0.1:8000/api/portfolio/summary"),
          axios.get("http://127.0.0.1:8000/api/portfolio/history"),
        ]);
        setSummary(summaryRes.data);
        setHistory(historyRes.data);
      } catch (error) {
        console.error("Error al obtener datos del portafolio:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <p>Cargando datos del portafolio...</p>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-6">Resumen de Portafolio</h1>
        <div className="bg-gray-800 rounded-lg shadow-lg overflow-x-auto">
          <table className="w-full table-auto">
            <thead className="border-b border-gray-700">
              <tr>
                <th className="p-4 text-left font-semibold text-gray-400">
                  Activo
                </th>
                <th className="p-4 text-right font-semibold text-gray-400">
                  Cantidad
                </th>
                <th className="p-4 text-right font-semibold text-gray-400">
                  Costo Prom.
                </th>
                <th className="p-4 text-right font-semibold text-gray-400">
                  Valor de Mercado
                </th>
                <th className="p-4 text-right font-semibold text-gray-400">
                  G/P No Realizada
                </th>
              </tr>
            </thead>
            <tbody>
              {summary.map((asset) => (
                <tr key={asset.symbol} className="border-t border-gray-700">
                  <td className="p-4 font-medium">
                    {asset.symbol}{" "}
                    <span className="text-gray-400 text-sm">{asset.name}</span>
                  </td>
                  <td className="p-4 text-right text-gray-300">
                    {asset.quantity.toFixed(4)}
                  </td>
                  <td className="p-4 text-right font-mono text-gray-300">
                    ${asset.avg_cost.toFixed(2)}
                  </td>
                  <td className="p-4 text-right font-mono font-semibold text-sky-400">
                    ${asset.market_value.toFixed(2)}
                  </td>
                  <td
                    className={`p-4 text-right font-mono font-semibold ${
                      asset.unrealized_pnl >= 0
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    ${asset.unrealized_pnl.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-6">Historial de Transacciones</h2>
        <div className="bg-gray-800 rounded-lg shadow-lg overflow-x-auto">
          <table className="w-full table-auto">
            <thead className="border-b border-gray-700">
              <tr>
                <th className="p-4 text-left font-semibold text-gray-400">
                  Fecha
                </th>
                <th className="p-4 text-left font-semibold text-gray-400">
                  Activo
                </th>
                <th className="p-4 text-left font-semibold text-gray-400">
                  Tipo
                </th>
                <th className="p-4 text-right font-semibold text-gray-400">
                  Cantidad
                </th>
                <th className="p-4 text-right font-semibold text-gray-400">
                  Precio
                </th>
              </tr>
            </thead>
            <tbody>
              {history.map((trade) => (
                <tr key={trade.id} className="border-t border-gray-700">
                  <td className="p-4 text-gray-300">{trade.date}</td>
                  <td className="p-4 font-medium">{trade.symbol}</td>
                  <td
                    className={`p-4 font-semibold ${
                      trade.type === "buy" ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {trade.type.toUpperCase()}
                  </td>
                  <td className="p-4 text-right text-gray-300">
                    {trade.quantity}
                  </td>
                  <td className="p-4 text-right font-mono text-gray-300">
                    ${trade.price.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
