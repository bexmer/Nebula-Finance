import { useState, useEffect, useMemo, useCallback } from "react";
import type { ChangeEvent, FormEvent } from "react";
import axios from "axios";
import { Pencil, RefreshCcw, Trash2 } from "lucide-react";

import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { apiPath } from "../utils/api";

interface PortfolioSummary {
  symbol: string;
  name: string;
  asset_type: string;
  quantity: number;
  avg_cost: number;
  market_value: number;
  unrealized_pnl: number;
}

interface TradeHistory {
  id: number;
  date: string;
  symbol: string;
  asset_type: string;
  type: "buy" | "sell";
  quantity: number;
  price: number;
}

interface TradeFormState {
  id: number | null;
  symbol: string;
  asset_type: string;
  type: "buy" | "sell";
  quantity: string;
  price: string;
  date: string;
}

export function Portfolio() {
  const createDefaultFormState = (): TradeFormState => ({
    id: null,
    symbol: "",
    asset_type: "",
    type: "buy",
    quantity: "",
    price: "",
    date: new Date().toISOString().slice(0, 10),
  });

  const [summary, setSummary] = useState<PortfolioSummary[]>([]);
  const [history, setHistory] = useState<TradeHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [formState, setFormState] = useState<TradeFormState>(() =>
    createDefaultFormState()
  );
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { formatCurrency, formatPercent } = useNumberFormatter();

  const holdingsBySymbol = useMemo(() => {
    const map = new Map<string, PortfolioSummary>();
    summary.forEach((asset) => {
      map.set(asset.symbol.toUpperCase(), asset);
    });
    return map;
  }, [summary]);

  const holdingSymbols = useMemo(
    () => Array.from(holdingsBySymbol.keys()).sort(),
    [holdingsBySymbol]
  );

  const fetchPortfolio = useCallback(async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const [summaryRes, historyRes] = await Promise.all([
        axios.get(apiPath("/portfolio/summary")),
        axios.get(apiPath("/portfolio/history")),
      ]);
      setSummary(summaryRes.data);
      setHistory(historyRes.data);
    } catch (error) {
      console.error("Error al obtener datos del portafolio:", error);
      setFetchError("No pudimos cargar tu portafolio. Intenta nuevamente.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  const resetForm = () => {
    setFormState(createDefaultFormState());
    setFormError(null);
  };

  const handleFieldChange =
    (field: keyof TradeFormState) =>
    (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const value = event.target.value;
      setFormState((prev) => {
        if (field === "symbol") {
          const normalized = value.toUpperCase();
          const nextState = { ...prev, symbol: normalized };
          if (prev.type === "sell") {
            const holding = holdingsBySymbol.get(normalized);
            if (holding) {
              nextState.asset_type = holding.asset_type;
            }
          }
          return nextState;
        }

        if (field === "type") {
          const nextType = value as TradeFormState["type"];
          if (nextType === "sell") {
            const normalizedSymbol = prev.symbol.trim().toUpperCase();
            const fallbackSymbol = holdingsBySymbol.has(normalizedSymbol)
              ? normalizedSymbol
              : holdingSymbols[0] ?? normalizedSymbol;
            const holding = fallbackSymbol
              ? holdingsBySymbol.get(fallbackSymbol)
              : undefined;
            return {
              ...prev,
              type: nextType,
              symbol: fallbackSymbol,
              asset_type: holding?.asset_type ?? prev.asset_type,
            };
          }

          return { ...prev, type: nextType };
        }

        return { ...prev, [field]: value };
      });
    };

  const handleEdit = (trade: TradeHistory) => {
    setFormState({
      id: trade.id,
      symbol: trade.symbol.toUpperCase(),
      asset_type: trade.asset_type ?? "",
      type: trade.type,
      quantity: trade.quantity.toString(),
      price: trade.price.toString(),
      date: trade.date,
    });
    setFormError(null);
  };

  useEffect(() => {
    if (formState.type !== "sell") {
      return;
    }

    const normalized = formState.symbol.trim().toUpperCase();
    if (normalized && holdingsBySymbol.has(normalized)) {
      const holding = holdingsBySymbol.get(normalized)!;
      if (
        formState.asset_type !== holding.asset_type ||
        formState.symbol !== normalized
      ) {
        setFormState((prev) => ({
          ...prev,
          symbol: normalized,
          asset_type: holding.asset_type,
        }));
      }
    } else if (!normalized && holdingSymbols.length > 0) {
      const fallbackSymbol = holdingSymbols[0];
      const holding = holdingsBySymbol.get(fallbackSymbol);
      setFormState((prev) => ({
        ...prev,
        symbol: fallbackSymbol,
        asset_type: holding?.asset_type ?? prev.asset_type,
      }));
    }
  }, [
    formState.type,
    formState.symbol,
    formState.asset_type,
    holdingSymbols,
    holdingsBySymbol,
  ]);

  const handleDelete = async (tradeId: number) => {
    if (!window.confirm("¿Deseas eliminar esta operación?")) {
      return;
    }
    try {
      await axios.delete(apiPath(`/portfolio/trades/${tradeId}`));
      if (formState.id === tradeId) {
        resetForm();
      }
      await fetchPortfolio();
    } catch (error) {
      console.error("Error al eliminar la operación:", error);
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        setFormError(
          typeof detail === "string"
            ? detail
            : "No se pudo eliminar la operación."
        );
      } else {
        setFormError("No se pudo eliminar la operación.");
      }
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);

    const quantity = parseFloat(formState.quantity);
    const price = parseFloat(formState.price);

    const normalizedSymbol = formState.symbol.trim().toUpperCase();

    if (!normalizedSymbol) {
      setFormError("El símbolo del activo es obligatorio.");
      return;
    }

    if (!formState.date) {
      setFormError("Selecciona una fecha válida.");
      return;
    }

    if (!Number.isFinite(quantity) || quantity <= 0) {
      setFormError("Ingresa una cantidad mayor a cero.");
      return;
    }

    if (!Number.isFinite(price) || price <= 0) {
      setFormError("Ingresa un precio mayor a cero.");
      return;
    }

    if (formState.type === "sell" && !holdingsBySymbol.has(normalizedSymbol)) {
      setFormError(
        "Selecciona un activo existente de tu portafolio para registrar una venta."
      );
      return;
    }

    const resolvedAssetType =
      formState.type === "sell"
        ? holdingsBySymbol.get(normalizedSymbol)!.asset_type
        : formState.asset_type.trim();

    if (!resolvedAssetType) {
      setFormError("Define el tipo de activo para esta operación.");
      return;
    }

    const payload = {
      symbol: normalizedSymbol,
      asset_type: resolvedAssetType,
      trade_type: formState.type,
      quantity,
      price,
      date: formState.date,
    };

    setIsSubmitting(true);
    try {
      if (formState.id) {
        await axios.put(apiPath(`/portfolio/trades/${formState.id}`), payload);
      } else {
        await axios.post(apiPath("/portfolio/trades"), payload);
      }
      resetForm();
      await fetchPortfolio();
    } catch (error) {
      console.error("Error al registrar la operación:", error);
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        setFormError(
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
            ? detail.join(" ")
            : "No se pudo registrar la operación."
        );
      } else {
        setFormError("No se pudo registrar la operación.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const totals = useMemo(
    () =>
      summary.reduce(
        (acc, asset) => {
          const cost = asset.avg_cost * asset.quantity;
          acc.market += asset.market_value;
          acc.cost += cost;
          acc.pnl += asset.unrealized_pnl;
          return acc;
        },
        { market: 0, cost: 0, pnl: 0 }
      ),
    [summary]
  );

  const pnlPercentage = totals.cost > 0 ? (totals.pnl / totals.cost) * 100 : 0;

  const enrichedSummary = useMemo(
    () =>
      summary.map((asset) => {
        const cost = asset.avg_cost * asset.quantity;
        const roi = cost > 0 ? (asset.unrealized_pnl / cost) * 100 : 0;
        return { ...asset, roi };
      }),
    [summary]
  );

  const diversification = useMemo(
    () =>
      summary
        .map((asset) => {
          const weight =
            totals.market > 0 ? (asset.market_value / totals.market) * 100 : 0;
          return {
            symbol: asset.symbol,
            asset_type: asset.asset_type || asset.name,
            weight,
            pnl: asset.unrealized_pnl,
          };
        })
        .sort((a, b) => b.weight - a.weight)
        .slice(0, 5),
    [summary, totals.market]
  );

  const bestPerformer = useMemo(() => {
    if (!enrichedSummary.length) return null;
    return enrichedSummary
      .slice()
      .sort((a, b) => b.roi - a.roi)[0];
  }, [enrichedSummary]);

  const worstPerformer = useMemo(() => {
    if (!enrichedSummary.length) return null;
    return enrichedSummary
      .slice()
      .sort((a, b) => a.roi - b.roi)[0];
  }, [enrichedSummary]);

  const formatDate = (value: string) => {
    try {
      return new Date(value).toLocaleDateString("es-MX", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch (error) {
      return value;
    }
  };

  const isEditing = formState.id !== null;
  const isSale = formState.type === "sell";
  const normalizedSymbolState = formState.symbol.trim().toUpperCase();
  const symbolMatchesHolding =
    isSale && normalizedSymbolState
      ? holdingsBySymbol.has(normalizedSymbolState)
      : false;

  return (
    <div className="space-y-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Portafolio</h1>
          <p className="text-sm text-slate-400">
            Visualiza el rendimiento de tus inversiones y registra nuevas
            operaciones en segundos.
          </p>
        </div>
        <button
          onClick={() => fetchPortfolio()}
          className="self-start inline-flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:text-white"
        >
          <RefreshCcw className="h-4 w-4" />
          Actualizar datos
        </button>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Valor actual</p>
          <p className="mt-2 text-3xl font-semibold text-white">
            {formatCurrency(totals.market)}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            {summary.length} posiciones activas
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Capital invertido</p>
          <p className="mt-2 text-3xl font-semibold text-white">
            {formatCurrency(totals.cost)}
          </p>
          <p className="mt-1 text-xs text-slate-400">Costos acumulados de compra</p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Ganancia latente</p>
          <p
            className={`mt-2 text-3xl font-semibold ${
              totals.pnl >= 0 ? "text-emerald-300" : "text-rose-300"
            }`}
          >
            {formatCurrency(totals.pnl)}
          </p>
          <p className="mt-1 text-xs text-slate-400">Sin considerar comisiones</p>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Rendimiento</p>
          <p
            className={`mt-2 text-3xl font-semibold ${
              pnlPercentage >= 0 ? "text-emerald-300" : "text-rose-300"
            }`}
          >
            {formatPercent(pnlPercentage)}
          </p>
          <p className="mt-1 text-xs text-slate-400">Sobre el capital invertido</p>
        </article>
      </section>

      {fetchError && (
        <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-100">
          {fetchError}
        </div>
      )}

      <div className="flex flex-col gap-6 xl:flex-row">
        <section className="flex-1 space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Composición actual</h2>
              {loading && <span className="text-xs text-slate-400">Actualizando...</span>}
            </div>
            <div className="mt-4 overflow-x-auto">
              {enrichedSummary.length ? (
                <table className="min-w-full divide-y divide-slate-800 text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                      <th className="py-2 pr-4">Activo</th>
                      <th className="py-2 pr-4">Cantidad</th>
                      <th className="py-2 pr-4 text-right">Costo prom.</th>
                      <th className="py-2 pr-4 text-right">Valor mercado</th>
                      <th className="py-2 pr-4 text-right">G/P</th>
                      <th className="py-2 text-right">ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enrichedSummary.map((asset) => (
                      <tr
                        key={asset.symbol}
                        className="border-b border-slate-800/60 text-sm text-slate-200"
                      >
                        <td className="py-3 pr-4">
                          <div className="font-semibold text-white">
                            {asset.symbol}
                          </div>
                          <div className="text-xs text-slate-400">
                            {asset.asset_type || asset.name}
                          </div>
                        </td>
                        <td className="py-3 pr-4">{asset.quantity.toFixed(4)}</td>
                        <td className="py-3 pr-4 text-right font-mono text-slate-300">
                          {formatCurrency(asset.avg_cost)}
                        </td>
                        <td className="py-3 pr-4 text-right font-mono text-sky-300">
                          {formatCurrency(asset.market_value)}
                        </td>
                        <td
                          className={`py-3 pr-4 text-right font-mono ${
                            asset.unrealized_pnl >= 0
                              ? "text-emerald-300"
                              : "text-rose-300"
                          }`}
                        >
                          {formatCurrency(asset.unrealized_pnl)}
                        </td>
                        <td
                          className={`py-3 text-right font-semibold ${
                            asset.roi >= 0 ? "text-emerald-300" : "text-rose-300"
                          }`}
                        >
                          {formatPercent(asset.roi)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="rounded-lg border border-dashed border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-400">
                  Aún no tienes posiciones activas registradas.
                </p>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h3 className="text-lg font-semibold text-white">Distribución por activo</h3>
            {diversification.length ? (
              <ul className="mt-4 space-y-3">
                {diversification.map((item) => (
                  <li key={item.symbol} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-white">{item.symbol}</span>
                      <span className="text-slate-300">{item.weight.toFixed(1)}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-800">
                      <div
                        className={`h-full rounded-full ${
                          item.pnl >= 0 ? "bg-emerald-500" : "bg-rose-500"
                        }`}
                        style={{ width: `${Math.min(item.weight, 100)}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-slate-400">{item.asset_type}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-400">
                Registra operaciones para visualizar la distribución de tu
                portafolio.
              </p>
            )}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="text-lg font-semibold text-white">Historial de operaciones</h2>
            <div className="mt-4 overflow-x-auto">
              {history.length ? (
                <table className="min-w-full divide-y divide-slate-800 text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                      <th className="py-2 pr-4">Fecha</th>
                      <th className="py-2 pr-4">Activo</th>
                      <th className="py-2 pr-4">Tipo</th>
                      <th className="py-2 pr-4 text-right">Cantidad</th>
                      <th className="py-2 pr-4 text-right">Precio</th>
                      <th className="py-2 text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((trade) => (
                      <tr
                        key={trade.id}
                        className="border-b border-slate-800/60 text-sm text-slate-200"
                      >
                        <td className="py-3 pr-4 text-slate-300">
                          {formatDate(trade.date)}
                        </td>
                        <td className="py-3 pr-4">
                          <div className="font-semibold text-white">
                            {trade.symbol}
                          </div>
                          <div className="text-xs text-slate-400">
                            {trade.asset_type}
                          </div>
                        </td>
                        <td className="py-3 pr-4">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              trade.type === "buy"
                                ? "bg-emerald-500/10 text-emerald-300"
                                : "bg-rose-500/10 text-rose-300"
                            }`}
                          >
                            {trade.type === "buy" ? "Compra" : "Venta"}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-right text-slate-300">
                          {trade.quantity}
                        </td>
                        <td className="py-3 pr-4 text-right font-mono text-slate-300">
                          {formatCurrency(trade.price)}
                        </td>
                        <td className="py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleEdit(trade)}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-sky-400/40 bg-slate-800 text-sky-200 transition hover:border-sky-300 hover:text-sky-100"
                              aria-label="Editar operación"
                            >
                              <Pencil className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(trade.id)}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-rose-400/40 bg-slate-800 text-rose-200 transition hover:border-rose-300 hover:text-rose-100"
                              aria-label="Eliminar operación"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="rounded-lg border border-dashed border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-400">
                  No hay operaciones registradas todavía.
                </p>
              )}
            </div>
          </div>
        </section>

        <aside className="w-full xl:w-96 space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h3 className="text-lg font-semibold text-white">
              {isEditing ? "Actualizar operación" : "Registrar operación"}
            </h3>
            <p className="mt-1 text-xs text-slate-400">
              Completa los campos para guardar una compra o venta en tu
              portafolio.
            </p>
            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-300">
                  Símbolo
                </label>
                <input
                  type="text"
                  value={formState.symbol}
                  onChange={handleFieldChange("symbol")}
                  list={isSale && holdingSymbols.length ? "portfolio-holdings" : undefined}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
                  placeholder="Ej. AAPL"
                />
                {isSale && holdingSymbols.length > 0 && (
                  <datalist id="portfolio-holdings">
                    {holdingSymbols.map((symbol) => (
                      <option key={symbol} value={symbol} />
                    ))}
                  </datalist>
                )}
                {isSale && holdingSymbols.length === 0 && (
                  <p className="text-xs text-slate-400">
                    Registra compras antes de capturar ventas.
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-300">
                  Tipo de activo
                </label>
                <input
                  type="text"
                  value={formState.asset_type}
                  onChange={handleFieldChange("asset_type")}
                  disabled={symbolMatchesHolding}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
                  placeholder="Acción, ETF, Cripto..."
                />
                {symbolMatchesHolding && (
                  <p className="text-xs text-slate-400">
                    Tipo asignado automáticamente según tu posición actual.
                  </p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-300">
                    Tipo de operación
                  </label>
                  <select
                    value={formState.type}
                    onChange={handleFieldChange("type")}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
                  >
                    <option value="buy">Compra</option>
                    <option value="sell">Venta</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-300">
                    Fecha
                  </label>
                  <input
                    type="date"
                    value={formState.date}
                    onChange={handleFieldChange("date")}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-300">
                    Cantidad
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0"
                    value={formState.quantity}
                    onChange={handleFieldChange("quantity")}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-300">
                    Precio unitario
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formState.price}
                    onChange={handleFieldChange("price")}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              {formError && (
                <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-100">
                  {formError}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                {isEditing && (
                  <button
                    type="button"
                    onClick={resetForm}
                    className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-300 transition hover:border-slate-500 hover:text-white"
                  >
                    Cancelar
                  </button>
                )}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white shadow transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting
                    ? "Guardando..."
                    : isEditing
                    ? "Actualizar"
                    : "Registrar"}
                </button>
              </div>
            </form>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h3 className="text-lg font-semibold text-white">Insights rápidos</h3>
            {enrichedSummary.length ? (
              <div className="mt-4 space-y-4 text-sm text-slate-300">
                {bestPerformer && (
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      Mejor desempeño
                    </p>
                    <p className="text-base font-semibold text-white">
                      {bestPerformer.symbol} · {formatPercent(bestPerformer.roi)}
                    </p>
                    <p className="text-xs text-slate-400">
                      {formatCurrency(bestPerformer.unrealized_pnl)} sin
                      realizar
                    </p>
                  </div>
                )}
                {worstPerformer && (
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      Mayor oportunidad
                    </p>
                    <p className="text-base font-semibold text-white">
                      {worstPerformer.symbol} · {formatPercent(worstPerformer.roi)}
                    </p>
                    <p className="text-xs text-slate-400">
                      {formatCurrency(worstPerformer.unrealized_pnl)} latente
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400">
                    Concentración
                  </p>
                  <p className="text-base font-semibold text-white">
                    {diversification[0]
                      ? `${diversification[0].symbol} concentra ${diversification[0].weight.toFixed(1)}%`
                      : "Diversificación equilibrada"}
                  </p>
                </div>
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-400">
                Registra tus primeras operaciones para activar los insights de
                rendimiento.
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
