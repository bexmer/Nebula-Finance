import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import type { ChangeEvent, FormEvent } from "react";
import axios from "axios";
import { Pencil, RefreshCcw, Trash2 } from "lucide-react";

import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { apiPath } from "../utils/api";
import {
  formatDateForDisplay,
  getTodayDateInputValue,
  normalizeDateInputValue,
} from "../utils/date";

interface PortfolioSummary {
  symbol: string;
  name: string;
  asset_type: string;
  quantity: number;
  avg_cost: number;
  market_value: number;
  unrealized_pnl: number;
  annual_yield_rate?: number;
  monthly_yield?: number;
  linked_account_id?: number | null;
  linked_account_name?: string | null;
  linked_goal_id?: number | null;
  linked_goal_name?: string | null;
}

interface TradeHistory {
  id: number;
  date: string;
  symbol: string;
  asset_type: string;
  type: "buy" | "sell";
  quantity: number;
  price: number;
  annual_yield_rate?: number;
  linked_account_id?: number | null;
  linked_goal_id?: number | null;
}

interface TradeFormState {
  id: number | null;
  symbol: string;
  asset_type: string;
  type: "buy" | "sell";
  quantity: string;
  price: string;
  date: string;
  annual_yield_rate: string;
  linked_account_id: string;
  linked_goal_id: string;
}

interface SelectOption {
  id: number;
  name: string;
}

export function Portfolio() {
  const resolveDetailMessage = useCallback((detail: unknown): string | null => {
    if (!detail) {
      return null;
    }
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((item) => resolveDetailMessage(item) ?? "").join(" ").trim() || null;
    }
    if (typeof detail === "object") {
      const typed = detail as { detail?: unknown; message?: unknown };
      return resolveDetailMessage(typed.detail ?? typed.message);
    }
    return String(detail);
  }, []);

  const createDefaultFormState = (): TradeFormState => ({
    id: null,
    symbol: "",
    asset_type: "",
    type: "buy",
    quantity: "",
    price: "",
    date: getTodayDateInputValue(),
    annual_yield_rate: "",
    linked_account_id: "",
    linked_goal_id: "",
  });

  const [summary, setSummary] = useState<PortfolioSummary[]>([]);
  const [history, setHistory] = useState<TradeHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [formState, setFormState] = useState<TradeFormState>(() =>
    createDefaultFormState()
  );
  const [initialSnapshot, setInitialSnapshot] = useState<TradeFormState | null>(
    null
  );
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [assetTypes, setAssetTypes] = useState<string[]>([]);
  const [accountOptions, setAccountOptions] = useState<SelectOption[]>([]);
  const [goalOptions, setGoalOptions] = useState<SelectOption[]>([]);
  const formRef = useRef<HTMLFormElement | null>(null);
  const symbolInputRef = useRef<HTMLInputElement | null>(null);

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

  const assetTypeSelection = useMemo(() => {
    if (!formState.asset_type) {
      return "";
    }
    return assetTypes.includes(formState.asset_type)
      ? formState.asset_type
      : "__custom";
  }, [assetTypes, formState.asset_type]);

  const showCustomAssetInput = assetTypeSelection === "__custom";

  const sortedAssetTypes = useMemo(
    () => assetTypes.slice().sort((a, b) => a.localeCompare(b, "es")),
    [assetTypes]
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

  useEffect(() => {
    const handleNewTradeRequest = () => {
      setFormState(createDefaultFormState());
      setFormError(null);
      setInitialSnapshot(null);
      requestAnimationFrame(() => {
        formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        symbolInputRef.current?.focus();
      });
    };
    window.addEventListener(
      "nebula:portfolio-request-add",
      handleNewTradeRequest
    );
    return () => {
      window.removeEventListener(
        "nebula:portfolio-request-add",
        handleNewTradeRequest
      );
    };
  }, []);

  useEffect(() => {
    let active = true;

    const loadCatalogs = async () => {
      try {
        const [typesRes, accountsRes, goalsRes] = await Promise.all([
          axios.get<string[]>(apiPath("/parameters/asset-types")),
          axios.get(apiPath("/accounts")),
          axios.get<SelectOption[]>(apiPath("/goals")),
        ]);

        if (!active) {
          return;
        }

        setAssetTypes(typesRes.data);

        const accountItems = (accountsRes.data as { id: number; name: string; is_virtual: boolean }[])
          .filter((account) => !account.is_virtual)
          .map((account) => ({ id: account.id, name: account.name }));
        setAccountOptions(accountItems);

        const goalItems = (goalsRes.data as SelectOption[]).map((goal) => ({
          id: goal.id,
          name: goal.name,
        }));
        setGoalOptions(goalItems);
      } catch (error) {
        console.error("Error al cargar catálogos del portafolio:", error);
      }
    };

    loadCatalogs();

    return () => {
      active = false;
    };
  }, []);

  const resetForm = () => {
    setFormState(createDefaultFormState());
    setFormError(null);
    setInitialSnapshot(null);
  };

  const handleFieldChange =
    (field: keyof TradeFormState) =>
    (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const value = event.target.value;
      if (field === "quantity" || field === "price") {
        const digitsOnly = value.replace(/[^0-9]/g, "");
        if (digitsOnly.length > 10) {
          return;
        }
      }
      setFormState((prev) => {
        if (field === "symbol") {
          const normalized = value.toUpperCase();
          const nextState = { ...prev, symbol: normalized };
          if (prev.type === "sell") {
            const holding = holdingsBySymbol.get(normalized);
            if (holding) {
              nextState.asset_type = holding.asset_type;
              nextState.annual_yield_rate = holding.annual_yield_rate
                ? String(holding.annual_yield_rate)
                : "";
              nextState.linked_account_id = holding.linked_account_id
                ? String(holding.linked_account_id)
                : "";
              nextState.linked_goal_id = holding.linked_goal_id
                ? String(holding.linked_goal_id)
                : "";
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
              annual_yield_rate: holding?.annual_yield_rate
                ? String(holding.annual_yield_rate)
                : prev.annual_yield_rate,
              linked_account_id: holding?.linked_account_id
                ? String(holding.linked_account_id)
                : "",
              linked_goal_id: holding?.linked_goal_id
                ? String(holding.linked_goal_id)
                : "",
            };
          }

          return {
            ...prev,
            type: nextType,
          };
        }

        if (field === "annual_yield_rate") {
          const cleaned = value.replace(/[^0-9.]/g, "");
          const parts = cleaned.split(".");
          const normalized =
            parts.length > 2 ? `${parts[0]}.${parts.slice(1).join("")}` : cleaned;
          if (normalized.length > 6) {
            return prev;
          }
          return { ...prev, annual_yield_rate: normalized };
        }

        return { ...prev, [field]: value };
      });
    };

  const handleEdit = (trade: TradeHistory) => {
    const nextState = {
      id: trade.id,
      symbol: trade.symbol.toUpperCase(),
      asset_type: trade.asset_type ?? "",
      type: trade.type,
      quantity: trade.quantity.toString(),
      price: trade.price.toString(),
      date: normalizeDateInputValue(trade.date),
      annual_yield_rate: trade.annual_yield_rate
        ? String(trade.annual_yield_rate)
        : "",
      linked_account_id: trade.linked_account_id
        ? String(trade.linked_account_id)
        : "",
      linked_goal_id: trade.linked_goal_id
        ? String(trade.linked_goal_id)
        : "",
    };
    setFormState(nextState);
    setInitialSnapshot(nextState);
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
        formState.symbol !== normalized ||
        formState.annual_yield_rate !== String(holding.annual_yield_rate ?? "") ||
        formState.linked_account_id !== String(holding.linked_account_id ?? "") ||
        formState.linked_goal_id !== String(holding.linked_goal_id ?? "")
      ) {
        setFormState((prev) => ({
          ...prev,
          symbol: normalized,
          asset_type: holding.asset_type,
          annual_yield_rate: holding.annual_yield_rate
            ? String(holding.annual_yield_rate)
            : "",
          linked_account_id: holding.linked_account_id
            ? String(holding.linked_account_id)
            : "",
          linked_goal_id: holding.linked_goal_id
            ? String(holding.linked_goal_id)
            : "",
        }));
      }
    } else if (!normalized && holdingSymbols.length > 0) {
      const fallbackSymbol = holdingSymbols[0];
      const holding = holdingsBySymbol.get(fallbackSymbol);
      setFormState((prev) => ({
        ...prev,
        symbol: fallbackSymbol,
        asset_type: holding?.asset_type ?? prev.asset_type,
        annual_yield_rate: holding?.annual_yield_rate
          ? String(holding.annual_yield_rate)
          : prev.annual_yield_rate,
        linked_account_id: holding?.linked_account_id
          ? String(holding.linked_account_id)
          : "",
        linked_goal_id: holding?.linked_goal_id
          ? String(holding.linked_goal_id)
          : "",
      }));
    }
  }, [
    formState.type,
    formState.symbol,
    formState.asset_type,
    formState.annual_yield_rate,
    formState.linked_account_id,
    formState.linked_goal_id,
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
      const detailMessage =
        axios.isAxiosError(error) && error.response
          ? resolveDetailMessage(error.response.data?.detail ?? error.response.data)
          : null;
      setFormError(detailMessage ?? "No se pudo eliminar la operación.");
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

    const annualYieldRate = parseFloat(formState.annual_yield_rate || "0");
    if (!Number.isFinite(annualYieldRate) || annualYieldRate < 0) {
      setFormError("La tasa anual debe ser un número mayor o igual a cero.");
      return;
    }

    const linkedAccountId = formState.linked_account_id
      ? Number.parseInt(formState.linked_account_id, 10)
      : null;
    const linkedGoalId = formState.linked_goal_id
      ? Number.parseInt(formState.linked_goal_id, 10)
      : null;

    const payload = {
      symbol: normalizedSymbol,
      asset_type: resolvedAssetType,
      trade_type: formState.type,
      quantity,
      price,
      date: formState.date,
      annual_yield_rate: annualYieldRate,
      linked_account_id: linkedAccountId,
      linked_goal_id: linkedGoalId,
    };

    if (formState.id && initialSnapshot && initialSnapshot.id === formState.id) {
      const initialQuantity = parseFloat(initialSnapshot.quantity);
      const initialPrice = parseFloat(initialSnapshot.price);
      const initialSymbol = initialSnapshot.symbol.trim().toUpperCase();
      const initialAssetType = initialSnapshot.asset_type.trim();
      const initialType = initialSnapshot.type;
      const initialDate = initialSnapshot.date;
      const initialYield = parseFloat(initialSnapshot.annual_yield_rate || "0");
      const initialAccount = initialSnapshot.linked_account_id || "";
      const initialGoal = initialSnapshot.linked_goal_id || "";

      const unchanged =
        initialSymbol === normalizedSymbol &&
        initialType === formState.type &&
        initialDate === formState.date &&
        initialAssetType === resolvedAssetType.trim() &&
        Number.isFinite(initialQuantity) &&
        Number.isFinite(initialPrice) &&
        initialQuantity === quantity &&
        initialPrice === price &&
        initialYield === annualYieldRate &&
        initialAccount === (formState.linked_account_id || "") &&
        initialGoal === (formState.linked_goal_id || "");

      if (unchanged) {
        setFormError("No has realizado cambios en esta operación.");
        return;
      }
    }

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
      if (axios.isAxiosError(error) && error.response) {
        const detail = resolveDetailMessage(
          error.response.data?.detail ?? error.response.data
        );
        setFormError(detail ?? "No se pudo registrar la operación.");
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
          acc.yield += asset.monthly_yield ?? 0;
          return acc;
        },
        { market: 0, cost: 0, pnl: 0, yield: 0 }
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
    const formatted = formatDateForDisplay(value);
    return formatted || value;
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
          <h1 className="section-title">Portafolio</h1>
          <p className="text-sm text-muted">
            Visualiza el rendimiento de tus inversiones y registra nuevas
            operaciones en segundos.
          </p>
        </div>
        <button
          onClick={() => fetchPortfolio()}
          className="self-start inline-flex items-center gap-2 rounded-lg border border-[var(--app-border)] px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-sky-400 hover:text-slate-900 dark:text-slate-200 dark:hover:text-slate-50"
        >
          <RefreshCcw className="h-4 w-4" />
          Actualizar datos
        </button>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <article className="glow-card glow-card--sky sm:p-6">
          <p className="text-xs uppercase tracking-wide text-sky-600 dark:text-sky-300">Valor actual</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">
            {formatCurrency(totals.market)}
          </p>
          <p className="mt-1 text-xs text-muted">
            {summary.length} posiciones activas
          </p>
        </article>
        <article className="glow-card glow-card--emerald sm:p-6">
          <p className="text-xs uppercase tracking-wide text-emerald-600 dark:text-emerald-300">Capital invertido</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">
            {formatCurrency(totals.cost)}
          </p>
          <p className="mt-1 text-xs text-muted">Costos acumulados de compra</p>
        </article>
        <article className="glow-card glow-card--rose sm:p-6">
          <p className="text-xs uppercase tracking-wide text-rose-600 dark:text-rose-300">Ganancia latente</p>
          <p
            className={`mt-2 text-3xl font-semibold ${
              totals.pnl >= 0
                ? "text-emerald-600 dark:text-emerald-200"
                : "text-rose-600 dark:text-rose-200"
            }`}
          >
            {formatCurrency(totals.pnl)}
          </p>
          <p className="mt-1 text-xs text-muted">Sin considerar comisiones</p>
        </article>
        <article className="glow-card glow-card--violet sm:p-6">
          <p className="text-xs uppercase tracking-wide text-violet-600 dark:text-violet-300">Rendimiento</p>
          <p
            className={`mt-2 text-3xl font-semibold ${
              pnlPercentage >= 0
                ? "text-emerald-600 dark:text-emerald-200"
                : "text-rose-600 dark:text-rose-200"
            }`}
          >
            {formatPercent(pnlPercentage)}
          </p>
          <p className="mt-1 text-xs text-muted">Sobre el capital invertido</p>
        </article>
        <article className="glow-card glow-card--amber sm:p-6">
          <p className="text-xs uppercase tracking-wide text-amber-600 dark:text-amber-300">Ingreso mensual</p>
          <p className="mt-2 text-3xl font-semibold text-amber-600 dark:text-amber-200">
            {formatCurrency(totals.yield)}
          </p>
          <p className="mt-1 text-xs text-muted">Basado en las tasas anuales registradas.</p>
        </article>
      </section>

      {fetchError && (
        <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-700 dark:text-rose-100">
          {fetchError}
        </div>
      )}

      <div className="flex flex-col gap-6 xl:flex-row">
        <section className="flex-1 space-y-6">
          <div className="app-card p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Composición actual</h2>
              {loading && <span className="text-xs text-muted">Actualizando...</span>}
            </div>
            <div className="mt-4 overflow-x-auto">
              {enrichedSummary.length ? (
                <table className="min-w-full divide-y divide-[var(--app-border)] text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-muted">
                      <th className="py-2 pr-4">Activo</th>
                      <th className="py-2 pr-4">Cantidad</th>
                      <th className="py-2 pr-4 text-right">Costo prom.</th>
                      <th className="py-2 pr-4 text-right">Valor mercado</th>
                      <th className="py-2 pr-4 text-right">G/P</th>
                      <th className="py-2 pr-4 text-right">ROI</th>
                      <th className="py-2 pr-4 text-right">Rend. mensual</th>
                      <th className="py-2 text-right">Vinculado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enrichedSummary.map((asset) => (
                      <tr
                        key={asset.symbol}
                        className="border-b border-[var(--app-border)] text-sm text-slate-700 dark:text-slate-200"
                      >
                        <td className="py-3 pr-4">
                          <div className="font-semibold text-slate-900 dark:text-white">
                            {asset.symbol}
                          </div>
                          <div className="text-xs text-muted">
                            {asset.asset_type || asset.name}
                          </div>
                        </td>
                        <td className="py-3 pr-4">{asset.quantity.toFixed(4)}</td>
                        <td className="py-3 pr-4 text-right font-mono text-slate-600 dark:text-slate-200">
                          {formatCurrency(asset.avg_cost)}
                        </td>
                        <td className="py-3 pr-4 text-right font-mono text-sky-600 dark:text-sky-300">
                          {formatCurrency(asset.market_value)}
                        </td>
                        <td
                          className={`py-3 pr-4 text-right font-mono ${
                            asset.unrealized_pnl >= 0
                              ? "text-emerald-600 dark:text-emerald-300"
                              : "text-rose-600 dark:text-rose-300"
                          }`}
                        >
                          {formatCurrency(asset.unrealized_pnl)}
                        </td>
                        <td
                          className={`py-3 pr-4 text-right font-semibold ${
                            asset.roi >= 0
                              ? "text-emerald-600 dark:text-emerald-300"
                              : "text-rose-600 dark:text-rose-300"
                          }`}
                        >
                          {formatPercent(asset.roi)}
                        </td>
                        <td className="py-3 pr-4 text-right font-mono text-amber-600 dark:text-amber-300">
                          {formatCurrency(asset.monthly_yield ?? 0)}
                        </td>
                        <td className="py-3 text-right text-xs text-muted">
                          {asset.linked_account_name || asset.linked_goal_name
                            ? (
                                <div className="space-y-1 text-right">
                                  {asset.linked_account_name && (
                                    <div className="font-medium text-slate-700 dark:text-slate-200">
                                      Cuenta: {asset.linked_account_name}
                                    </div>
                                  )}
                                  {asset.linked_goal_name && (
                                    <div className="text-slate-600 dark:text-slate-300">
                                      Meta: {asset.linked_goal_name}
                                    </div>
                                  )}
                                </div>
                              )
                            : (
                                <span>—</span>
                              )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="rounded-lg border border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)] p-4 text-sm text-muted">
                  Aún no tienes posiciones activas registradas.
                </p>
              )}
            </div>
          </div>

          <div className="app-card p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Distribución por activo</h3>
            {diversification.length ? (
              <ul className="mt-4 space-y-3">
                {diversification.map((item) => (
                  <li key={item.symbol} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-900 dark:text-white">{item.symbol}</span>
                      <span className="text-slate-600 dark:text-slate-300">{item.weight.toFixed(1)}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-[var(--app-border)]/60">
                      <div
                        className={`h-full rounded-full ${
                          item.pnl >= 0 ? "bg-emerald-500" : "bg-rose-500"
                        }`}
                        style={{ width: `${Math.min(item.weight, 100)}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-muted">{item.asset_type}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-muted">
                Registra operaciones para visualizar la distribución de tu
                portafolio.
              </p>
            )}
          </div>

          <div className="app-card p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Historial de operaciones</h2>
            <div className="mt-4 overflow-x-auto">
              {history.length ? (
                <table className="min-w-full divide-y divide-[var(--app-border)] text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-muted">
                      <th className="py-2 pr-4">Fecha</th>
                      <th className="py-2 pr-4">Activo</th>
                      <th className="py-2 pr-4">Tipo</th>
                      <th className="py-2 pr-4 text-right">Cantidad</th>
                      <th className="py-2 pr-4 text-right">Precio</th>
                      <th className="py-2 pr-4">Vinculado</th>
                      <th className="py-2 text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((trade) => (
                      <tr
                        key={trade.id}
                        className="border-b border-[var(--app-border)] text-sm text-slate-700 dark:text-slate-200"
                      >
                        <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                          {formatDate(trade.date)}
                        </td>
                        <td className="py-3 pr-4">
                          <div className="font-semibold text-slate-900 dark:text-white">
                            {trade.symbol}
                          </div>
                          <div className="text-xs text-muted">
                            {trade.asset_type}
                          </div>
                        </td>
                        <td className="py-3 pr-4">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              trade.type === "buy"
                                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-300"
                                : "bg-rose-500/10 text-rose-600 dark:text-rose-300"
                            }`}
                          >
                            {trade.type === "buy" ? "Compra" : "Venta"}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-right text-slate-600 dark:text-slate-200">
                          {trade.quantity}
                        </td>
                        <td className="py-3 pr-4 text-right font-mono text-slate-600 dark:text-slate-200">
                          {formatCurrency(trade.price)}
                        </td>
                        <td className="py-3 pr-4 text-xs text-muted">
                          {trade.linked_account_id || trade.linked_goal_id ? (
                            <div className="space-y-1">
                              {trade.linked_account_id && (
                                <div className="font-medium text-slate-700 dark:text-slate-200">
                                  Cuenta #{trade.linked_account_id}
                                </div>
                              )}
                              {trade.linked_goal_id && (
                                <div className="text-slate-600 dark:text-slate-300">
                                  Meta #{trade.linked_goal_id}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span>—</span>
                          )}
                        </td>
                        <td className="py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleEdit(trade)}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-sky-200 bg-[var(--app-surface-muted)] text-sky-600 transition hover:border-sky-400 hover:text-sky-700 dark:border-sky-400/40 dark:bg-slate-900/70 dark:text-sky-200"
                              aria-label="Editar operación"
                            >
                              <Pencil className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(trade.id)}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-rose-200 bg-[var(--app-surface-muted)] text-rose-600 transition hover:border-rose-400 hover:text-rose-700 dark:border-rose-400/40 dark:bg-slate-900/70 dark:text-rose-200"
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
              <p className="rounded-lg border border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)] p-4 text-sm text-muted">
                  No hay operaciones registradas todavía.
                </p>
              )}
            </div>
          </div>
        </section>

        <aside className="w-full space-y-6 xl:w-96">
          <div className="app-card p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {isEditing ? "Actualizar operación" : "Registrar operación"}
            </h3>
            <p className="mt-1 text-xs text-muted">
              Completa los campos para guardar una compra o venta en tu
              portafolio.
            </p>
            <form ref={formRef} onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                  Símbolo
                </label>
                <input
                  type="text"
                  value={formState.symbol}
                  onChange={handleFieldChange("symbol")}
                  list={isSale && holdingSymbols.length ? "portfolio-holdings" : undefined}
                  ref={symbolInputRef}
                  className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
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
                  <p className="text-xs text-muted">
                    Registra compras antes de capturar ventas.
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                  Tipo de activo
                </label>
                <select
                  value={symbolMatchesHolding ? formState.asset_type : assetTypeSelection}
                  onChange={(event) => {
                    const value = event.target.value;
                    if (value === "__custom") {
                      setFormState((prev) => ({ ...prev, asset_type: "" }));
                    } else {
                      setFormState((prev) => ({ ...prev, asset_type: value }));
                    }
                  }}
                  disabled={symbolMatchesHolding}
                  className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-100"
                >
                  <option value="">Selecciona un tipo</option>
                  {sortedAssetTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                  <option value="__custom">Otro / Personalizado</option>
                </select>
                {showCustomAssetInput && !symbolMatchesHolding && (
                  <input
                    type="text"
                    value={formState.asset_type}
                    onChange={handleFieldChange("asset_type")}
                    className="w-full rounded-lg border border-dashed border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                    placeholder="Ej. Cuenta de Ahorro"
                  />
                )}
                {assetTypes.length === 0 && (
                  <p className="text-xs text-muted">
                    Configura los tipos de activo desde la sección de Configuración.
                  </p>
                )}
                {symbolMatchesHolding && (
                  <p className="text-xs text-muted">
                    Tipo asignado automáticamente según tu posición actual.
                  </p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                    Tipo de operación
                  </label>
                  <select
                    value={formState.type}
                    onChange={handleFieldChange("type")}
                    className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  >
                    <option value="buy">Compra</option>
                    <option value="sell">Venta</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                    Fecha
                  </label>
                  <input
                    type="date"
                    value={formState.date}
                    onChange={handleFieldChange("date")}
                    className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                    Cantidad
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0"
                    value={formState.quantity}
                    onChange={handleFieldChange("quantity")}
                    className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                    Precio unitario
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formState.price}
                    onChange={handleFieldChange("price")}
                    className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                    Tasa anual estimada (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formState.annual_yield_rate}
                    onChange={handleFieldChange("annual_yield_rate")}
                    className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                    placeholder="0.00"
                  />
                  <p className="text-xs text-muted">
                    Calcularemos el rendimiento mensual automáticamente a partir de esta tasa.
                  </p>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                    Cuenta vinculada (opcional)
                  </label>
                  <select
                    value={formState.linked_account_id}
                    onChange={handleFieldChange("linked_account_id")}
                    className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  >
                    <option value="">Sin vincular</option>
                    {accountOptions.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">
                  Meta vinculada (opcional)
                </label>
                <select
                  value={formState.linked_goal_id}
                  onChange={handleFieldChange("linked_goal_id")}
                  className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                >
                  <option value="">Sin vincular</option>
                  {goalOptions.map((goal) => (
                    <option key={goal.id} value={goal.id}>
                      {goal.name}
                    </option>
                  ))}
                </select>
              </div>

              {formError && (
                <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-700 dark:text-rose-100">
                  {formError}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                {isEditing && (
                  <button
                    type="button"
                    onClick={resetForm}
                    className="rounded-lg border border-[var(--app-border)] px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-sky-400 hover:text-slate-900 dark:text-slate-200 dark:hover:text-slate-50"
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

          <div className="app-card p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Insights rápidos</h3>
            {enrichedSummary.length ? (
              <div className="mt-4 space-y-4 text-sm text-slate-700 dark:text-slate-300">
                {bestPerformer && (
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted">
                      Mejor desempeño
                    </p>
                    <p className="text-base font-semibold text-slate-900 dark:text-white">
                      {bestPerformer.symbol} · {formatPercent(bestPerformer.roi)}
                    </p>
                    <p className="text-xs text-muted">
                      {formatCurrency(bestPerformer.unrealized_pnl)} sin
                      realizar
                    </p>
                  </div>
                )}
                {worstPerformer && (
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted">
                      Mayor oportunidad
                    </p>
                    <p className="text-base font-semibold text-slate-900 dark:text-white">
                      {worstPerformer.symbol} · {formatPercent(worstPerformer.roi)}
                    </p>
                    <p className="text-xs text-muted">
                      {formatCurrency(worstPerformer.unrealized_pnl)} latente
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-xs uppercase tracking-wide text-muted">
                    Concentración
                  </p>
                  <p className="text-base font-semibold text-slate-900 dark:text-white">
                    {diversification[0]
                      ? `${diversification[0].symbol} concentra ${diversification[0].weight.toFixed(1)}%`
                      : "Diversificación equilibrada"}
                  </p>
                </div>
              </div>
            ) : (
              <p className="mt-3 text-sm text-muted">
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
