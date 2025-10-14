import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

import { API_BASE_URL } from "../utils/api";
import { useDisplayPreferences } from "../context/DisplayPreferencesContext";

type FeedbackType = "success" | "error";
type Feedback = { type: FeedbackType; message: string } | null;

interface TransactionTypeItem {
  id: number;
  name: string;
  budget_rule_id: number | null;
  budget_rule_name: string | null;
  is_deletable: boolean;
  inherit_category_ids: number[];
  inherit_category_names: string[];
}

interface BudgetRuleItem {
  id: number;
  name: string;
  percentage: number;
  is_deletable: boolean;
}

interface AccountTypeItem {
  id: number;
  name: string;
  is_deletable: boolean;
}

interface CategoryItem {
  id: number;
  name: string;
  parent_id: number;
  parent_name: string;
  is_deletable: boolean;
}

interface DisplayPreferences {
  abbreviate_numbers: boolean;
  threshold: number;
}

type TransactionTypeFormState = {
  id: number | null;
  name: string;
  budgetRuleId: string;
  inheritCategoryIds: number[];
};

type BudgetRuleFormState = {
  id: number | null;
  name: string;
  percentage: string;
};

type AccountTypeFormState = {
  id: number | null;
  name: string;
};

type CategoryFormState = {
  id: number | null;
  name: string;
  parentId: string;
};

const TABS = [
  { id: "transaction-types", label: "Tipos de Transacción y Reglas" },
  { id: "account-types", label: "Tipos de Cuenta" },
  { id: "categories", label: "Categorías" },
  { id: "visualization", label: "Visualización" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const THRESHOLD_OPTIONS = [
  { label: "A partir de miles (1,000)", value: 1_000 },
  { label: "A partir de diez miles (10,000)", value: 10_000 },
  { label: "A partir de cien miles (100,000)", value: 100_000 },
  { label: "A partir de millones (1,000,000)", value: 1_000_000 },
  { label: "A partir de diez millones (10,000,000)", value: 10_000_000 },
];

const resolveErrorMessage = (error: unknown): string => {
  if (!error) {
    return "Ocurrió un error inesperado.";
  }
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail ?? error.message;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((item) => resolveErrorMessage(item)).join(" ").trim() || "Error de validación.";
    }
    if (typeof detail === "object") {
      return resolveErrorMessage((detail as { message?: unknown; detail?: unknown }).detail);
    }
  }
  if (typeof error === "string") {
    return error;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Ocurrió un error inesperado.";
};

export function Settings() {
  const [activeTab, setActiveTab] = useState<TabId>("transaction-types");
  const [initializing, setInitializing] = useState(true);

  const [transactionTypes, setTransactionTypes] = useState<TransactionTypeItem[]>([]);
  const [budgetRules, setBudgetRules] = useState<BudgetRuleItem[]>([]);
  const [accountTypes, setAccountTypes] = useState<AccountTypeItem[]>([]);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [displayPreferences, setDisplayPreferences] = useState<DisplayPreferences | null>(null);
  const [displayInitial, setDisplayInitial] = useState<DisplayPreferences | null>(null);
  const { refresh: refreshDisplayContext, preferences: displayContextPreferences } =
    useDisplayPreferences();

  const [transactionForm, setTransactionForm] = useState<TransactionTypeFormState>({
    id: null,
    name: "",
    budgetRuleId: "",
    inheritCategoryIds: [],
  });
  const [budgetRuleForm, setBudgetRuleForm] = useState<BudgetRuleFormState>({
    id: null,
    name: "",
    percentage: "",
  });
  const [accountTypeForm, setAccountTypeForm] = useState<AccountTypeFormState>({
    id: null,
    name: "",
  });
  const [categoryForm, setCategoryForm] = useState<CategoryFormState>({
    id: null,
    name: "",
    parentId: "",
  });

  const [transactionFeedback, setTransactionFeedback] = useState<Feedback>(null);
  const [budgetRuleFeedback, setBudgetRuleFeedback] = useState<Feedback>(null);
  const [accountFeedback, setAccountFeedback] = useState<Feedback>(null);
  const [categoryFeedback, setCategoryFeedback] = useState<Feedback>(null);
  const [visualFeedback, setVisualFeedback] = useState<Feedback>(null);

  const timeoutRefs = useRef<number[]>([]);

  const haveSameElements = useCallback((a: number[], b: number[]) => {
    if (a.length !== b.length) {
      return false;
    }
    const sortedA = [...a].sort((x, y) => x - y);
    const sortedB = [...b].sort((x, y) => x - y);
    return sortedA.every((value, index) => value === sortedB[index]);
  }, []);

  const pushTimeout = useCallback((id: number) => {
    timeoutRefs.current.push(id);
  }, []);

  const showFeedback = useCallback(
    (setter: React.Dispatch<React.SetStateAction<Feedback>>, type: FeedbackType, message: string) => {
      setter({ type, message });
      const timeoutId = window.setTimeout(() => setter(null), 3600);
      pushTimeout(timeoutId);
    },
    [pushTimeout]
  );

  useEffect(() => {
    return () => {
      timeoutRefs.current.forEach((id) => window.clearTimeout(id));
    };
  }, []);

  const refreshTransactionConfig = useCallback(async () => {
    const [typesResponse, rulesResponse] = await Promise.all([
      axios.get<TransactionTypeItem[]>(`${API_BASE_URL}/config/transaction-types`),
      axios.get<BudgetRuleItem[]>(`${API_BASE_URL}/config/budget-rules`),
    ]);
    setTransactionTypes(typesResponse.data);
    setBudgetRules(rulesResponse.data);
  }, []);

  const refreshAccountTypes = useCallback(async () => {
    const response = await axios.get<AccountTypeItem[]>(`${API_BASE_URL}/config/account-types`);
    setAccountTypes(response.data);
  }, []);

  const refreshCategories = useCallback(async () => {
    const response = await axios.get<CategoryItem[]>(`${API_BASE_URL}/config/categories`);
    setCategories(response.data);
  }, []);

  const refreshDisplayPreferences = useCallback(async () => {
    await refreshDisplayContext();
  }, [refreshDisplayContext]);

  useEffect(() => {
    let isMounted = true;
    const initialize = async () => {
      try {
        await Promise.all([
          refreshTransactionConfig(),
          refreshAccountTypes(),
          refreshCategories(),
          refreshDisplayPreferences(),
        ]);
      } catch (error) {
        console.error("Error al cargar la configuración:", error);
        if (isMounted) {
          setVisualFeedback({ type: "error", message: resolveErrorMessage(error) });
        }
      } finally {
        if (isMounted) {
          setInitializing(false);
        }
      }
    };

    initialize();
    return () => {
      isMounted = false;
    };
  }, [refreshAccountTypes, refreshCategories, refreshDisplayPreferences, refreshTransactionConfig]);

  useEffect(() => {
    if (transactionTypes.length > 0 && !categoryForm.id && !categoryForm.parentId) {
      setCategoryForm((prev) => ({ ...prev, parentId: String(transactionTypes[0].id) }));
    }
  }, [transactionTypes, categoryForm.id, categoryForm.parentId]);

  useEffect(() => {
    if (!displayContextPreferences) {
      return;
    }
    const nextDisplay = {
      abbreviate_numbers: displayContextPreferences.abbreviateNumbers,
      threshold: displayContextPreferences.threshold,
    };
    setDisplayPreferences(nextDisplay);
    setDisplayInitial(nextDisplay);
  }, [displayContextPreferences]);

  const selectedTransactionType = useMemo(
    () => transactionTypes.find((item) => item.id === transactionForm.id) ?? null,
    [transactionForm.id, transactionTypes]
  );

  const selectedBudgetRule = useMemo(
    () => budgetRules.find((item) => item.id === budgetRuleForm.id) ?? null,
    [budgetRuleForm.id, budgetRules]
  );

  const selectedAccountType = useMemo(
    () => accountTypes.find((item) => item.id === accountTypeForm.id) ?? null,
    [accountTypeForm.id, accountTypes]
  );

  const selectedCategory = useMemo(
    () => categories.find((item) => item.id === categoryForm.id) ?? null,
    [categoryForm.id, categories]
  );

  const inheritanceOptions = useMemo(
    () =>
      transactionTypes.filter((type) =>
        transactionForm.id === null ? true : type.id !== transactionForm.id
      ),
    [transactionForm.id, transactionTypes]
  );

  useEffect(() => {
    setTransactionForm((prev) => {
      if (prev.inheritCategoryIds.length === 0) {
        return prev;
      }
      const allowed = new Set(inheritanceOptions.map((option) => option.id));
      const nextIds = prev.inheritCategoryIds.filter((id) => allowed.has(id));
      if (nextIds.length === prev.inheritCategoryIds.length) {
        return prev;
      }
      return { ...prev, inheritCategoryIds: nextIds };
    });
  }, [inheritanceOptions]);

  const resetTransactionForm = useCallback(() => {
    setTransactionForm({
      id: null,
      name: "",
      budgetRuleId: "",
      inheritCategoryIds: [],
    });
  }, []);

  const resetBudgetRuleForm = useCallback(() => {
    setBudgetRuleForm({ id: null, name: "", percentage: "" });
  }, []);

  const resetAccountTypeForm = useCallback(() => {
    setAccountTypeForm({ id: null, name: "" });
  }, []);

  const resetCategoryForm = useCallback(() => {
    setCategoryForm({ id: null, name: "", parentId: transactionTypes[0] ? String(transactionTypes[0].id) : "" });
  }, [transactionTypes]);

  const handleTransactionTypeSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = transactionForm.name.trim();
    if (!trimmedName) {
      showFeedback(setTransactionFeedback, "error", "Ingresa un nombre para el tipo de transacción.");
      return;
    }

    const budgetRuleIdValue = transactionForm.budgetRuleId
      ? Number(transactionForm.budgetRuleId)
      : null;

    if (transactionForm.id !== null && selectedTransactionType) {
      const existingRuleId = selectedTransactionType.budget_rule_id ?? null;
      const unchanged =
        selectedTransactionType.name === trimmedName &&
        existingRuleId === budgetRuleIdValue &&
        haveSameElements(
          selectedTransactionType.inherit_category_ids ?? [],
          transactionForm.inheritCategoryIds
        );
      if (unchanged) {
        showFeedback(
          setTransactionFeedback,
          "error",
          "No has realizado cambios en este tipo."
        );
        return;
      }
    }

    const payload = {
      name: trimmedName,
      budget_rule_id: budgetRuleIdValue,
      inherit_category_ids: transactionForm.inheritCategoryIds,
    };

    try {
      if (transactionForm.id === null) {
        await axios.post(`${API_BASE_URL}/config/transaction-types`, payload);
        showFeedback(setTransactionFeedback, "success", "Tipo de transacción añadido correctamente.");
      } else {
        await axios.put(`${API_BASE_URL}/config/transaction-types/${transactionForm.id}`, payload);
        showFeedback(setTransactionFeedback, "success", "Tipo de transacción actualizado.");
      }
      await refreshTransactionConfig();
      resetTransactionForm();
      await refreshCategories();
    } catch (error) {
      showFeedback(setTransactionFeedback, "error", resolveErrorMessage(error));
    }
  };

  const handleDeleteTransactionType = async () => {
    if (transactionForm.id === null) {
      return;
    }
    try {
      await axios.delete(`${API_BASE_URL}/config/transaction-types/${transactionForm.id}`);
      showFeedback(setTransactionFeedback, "success", "Tipo de transacción eliminado.");
      resetTransactionForm();
      await refreshTransactionConfig();
      await refreshCategories();
    } catch (error) {
      showFeedback(setTransactionFeedback, "error", resolveErrorMessage(error));
    }
  };

  const handleBudgetRuleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = budgetRuleForm.name.trim();
    if (!trimmedName) {
      showFeedback(setBudgetRuleFeedback, "error", "El nombre de la regla es obligatorio.");
      return;
    }

    const percentageValue = budgetRuleForm.percentage ? Number(budgetRuleForm.percentage) : 0;
    if (Number.isNaN(percentageValue)) {
      showFeedback(setBudgetRuleFeedback, "error", "Ingresa un porcentaje válido.");
      return;
    }

    if (budgetRuleForm.id !== null && selectedBudgetRule) {
      const unchanged =
        selectedBudgetRule.name === trimmedName &&
        Number(selectedBudgetRule.percentage) === Number(percentageValue);
      if (unchanged) {
        showFeedback(
          setBudgetRuleFeedback,
          "error",
          "No has realizado cambios en esta regla."
        );
        return;
      }
    }

    const payload = { name: trimmedName, percentage: percentageValue };

    try {
      if (budgetRuleForm.id === null) {
        await axios.post(`${API_BASE_URL}/config/budget-rules`, payload);
        showFeedback(setBudgetRuleFeedback, "success", "Regla de presupuesto añadida.");
      } else {
        await axios.put(`${API_BASE_URL}/config/budget-rules/${budgetRuleForm.id}`, payload);
        showFeedback(setBudgetRuleFeedback, "success", "Regla de presupuesto actualizada.");
      }
      await refreshTransactionConfig();
      resetBudgetRuleForm();
    } catch (error) {
      showFeedback(setBudgetRuleFeedback, "error", resolveErrorMessage(error));
    }
  };

  const handleDeleteBudgetRule = async () => {
    if (budgetRuleForm.id === null) {
      return;
    }
    try {
      await axios.delete(`${API_BASE_URL}/config/budget-rules/${budgetRuleForm.id}`);
      showFeedback(setBudgetRuleFeedback, "success", "Regla eliminada correctamente.");
      resetBudgetRuleForm();
      await refreshTransactionConfig();
    } catch (error) {
      showFeedback(setBudgetRuleFeedback, "error", resolveErrorMessage(error));
    }
  };

  const handleAccountTypeSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = accountTypeForm.name.trim();
    if (!trimmedName) {
      showFeedback(setAccountFeedback, "error", "El nombre del tipo de cuenta es obligatorio.");
      return;
    }

    if (accountTypeForm.id !== null && selectedAccountType) {
      if (selectedAccountType.name === trimmedName) {
        showFeedback(
          setAccountFeedback,
          "error",
          "No has realizado cambios en este tipo de cuenta."
        );
        return;
      }
    }

    try {
      if (accountTypeForm.id === null) {
        await axios.post(`${API_BASE_URL}/config/account-types`, { name: trimmedName });
        showFeedback(setAccountFeedback, "success", "Tipo de cuenta añadido.");
      } else {
        await axios.put(`${API_BASE_URL}/config/account-types/${accountTypeForm.id}`, {
          name: trimmedName,
        });
        showFeedback(setAccountFeedback, "success", "Tipo de cuenta actualizado.");
      }
      await refreshAccountTypes();
      resetAccountTypeForm();
    } catch (error) {
      showFeedback(setAccountFeedback, "error", resolveErrorMessage(error));
    }
  };

  const handleDeleteAccountType = async () => {
    if (accountTypeForm.id === null) {
      return;
    }
    try {
      await axios.delete(`${API_BASE_URL}/config/account-types/${accountTypeForm.id}`);
      showFeedback(setAccountFeedback, "success", "Tipo de cuenta eliminado.");
      resetAccountTypeForm();
      await refreshAccountTypes();
    } catch (error) {
      showFeedback(setAccountFeedback, "error", resolveErrorMessage(error));
    }
  };

  const handleCategorySubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = categoryForm.name.trim();
    if (!trimmedName) {
      showFeedback(setCategoryFeedback, "error", "Ingresa un nombre para la categoría.");
      return;
    }
    if (!categoryForm.parentId) {
      showFeedback(setCategoryFeedback, "error", "Selecciona un tipo padre.");
      return;
    }

    const parentIdNumber = Number(categoryForm.parentId);

    if (categoryForm.id !== null && selectedCategory) {
      const unchanged =
        selectedCategory.name === trimmedName &&
        selectedCategory.parent_id === parentIdNumber;
      if (unchanged) {
        showFeedback(
          setCategoryFeedback,
          "error",
          "No has realizado cambios en esta categoría."
        );
        return;
      }
    }

    const payload = {
      name: trimmedName,
      parent_id: parentIdNumber,
    };

    try {
      if (categoryForm.id === null) {
        await axios.post(`${API_BASE_URL}/config/categories`, payload);
        showFeedback(setCategoryFeedback, "success", "Categoría añadida.");
      } else {
        await axios.put(`${API_BASE_URL}/config/categories/${categoryForm.id}`, payload);
        showFeedback(setCategoryFeedback, "success", "Categoría actualizada.");
      }
      await refreshCategories();
      resetCategoryForm();
    } catch (error) {
      showFeedback(setCategoryFeedback, "error", resolveErrorMessage(error));
    }
  };

  const handleDeleteCategory = async () => {
    if (categoryForm.id === null) {
      return;
    }
    try {
      await axios.delete(`${API_BASE_URL}/config/categories/${categoryForm.id}`);
      showFeedback(setCategoryFeedback, "success", "Categoría eliminada.");
      resetCategoryForm();
      await refreshCategories();
    } catch (error) {
      showFeedback(setCategoryFeedback, "error", resolveErrorMessage(error));
    }
  };

  const handleVisualizationSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!displayPreferences) {
      return;
    }
    if (displayInitial) {
      const unchanged =
        displayInitial.abbreviate_numbers === displayPreferences.abbreviate_numbers &&
        displayInitial.threshold === displayPreferences.threshold;
      if (unchanged) {
        showFeedback(
          setVisualFeedback,
          "error",
          "No has realizado cambios en la visualización."
        );
        return;
      }
    }
    try {
      const response = await axios.put<DisplayPreferences>(`${API_BASE_URL}/config/display`, displayPreferences);
      setDisplayPreferences(response.data);
      await refreshDisplayContext();
      setDisplayInitial(response.data);
      showFeedback(setVisualFeedback, "success", "Preferencias guardadas correctamente.");
    } catch (error) {
      showFeedback(setVisualFeedback, "error", resolveErrorMessage(error));
    }
  };

  const renderFeedback = (feedback: Feedback) => {
    if (!feedback) {
      return null;
    }
    const color = feedback.type === "success" ? "text-emerald-400" : "text-rose-400";
    return <p className={`text-sm font-medium ${color}`}>{feedback.message}</p>;
  };

  if (initializing) {
    return (
      <div className="flex h-full items-center justify-center py-24">
        <p className="text-slate-400">Cargando configuración...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <h1 className="section-title">Configuración de Parámetros</h1>
        <p className="text-sm text-muted">
          Administra los catálogos que alimentan el dashboard, las transacciones y los reportes financieros.
        </p>
      </div>

      <div className="app-card p-0">
        <div className="flex flex-wrap gap-2 border-b border-[var(--app-border)] bg-[var(--app-surface-muted)] px-6 py-4">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/70 ${
                  isActive
                    ? "bg-gradient-to-r from-sky-500 to-indigo-500 text-white shadow"
                    : "border border-[var(--app-border)] bg-[var(--app-surface)] text-muted hover:border-sky-400 hover:text-sky-600"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {activeTab === "transaction-types" && (
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white">Tipos de transacción</h2>
                    <p className="text-sm text-slate-400">Asocia cada tipo con la regla de presupuesto adecuada.</p>
                  </div>
                  {renderFeedback(transactionFeedback)}
                </div>

                <form onSubmit={handleTransactionTypeSubmit} className="mt-4 space-y-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-slate-300" htmlFor="transaction-type-name">
                      Nombre del tipo
                    </label>
                    <input
                      id="transaction-type-name"
                      type="text"
                      value={transactionForm.name}
                      onChange={(event) =>
                        setTransactionForm((prev) => ({ ...prev, name: event.target.value }))
                      }
                      className="w-full rounded-lg border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm text-white outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
                      placeholder="Ej. Gasto Variable"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-slate-300" htmlFor="transaction-type-rule">
                      Regla de presupuesto
                    </label>
                    <select
                      id="transaction-type-rule"
                      value={transactionForm.budgetRuleId}
                      onChange={(event) =>
                        setTransactionForm((prev) => ({ ...prev, budgetRuleId: event.target.value }))
                      }
                      className="w-full rounded-lg border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm text-white outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
                    >
                      <option value="">(Ninguna)</option>
                      {budgetRules.map((rule) => (
                        <option key={rule.id} value={rule.id}>
                          {rule.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm font-medium text-slate-300">
                      Heredar categorías de otros tipos
                    </span>
                    <p className="text-xs text-slate-500">
                      Selecciona los tipos cuyas categorías también estarán disponibles para este tipo en transacciones y presupuestos.
                    </p>
                    <div className="max-h-36 space-y-2 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                      {inheritanceOptions.length === 0 ? (
                        <p className="text-xs text-slate-500">
                          {transactionTypes.length <= 1
                            ? "Registra más tipos para poder heredar sus categorías."
                            : "No hay otros tipos disponibles para heredar."}
                        </p>
                      ) : (
                        inheritanceOptions.map((option) => {
                          const isChecked = transactionForm.inheritCategoryIds.includes(option.id);
                          return (
                            <label
                              key={option.id}
                              className="flex items-center gap-2 text-sm text-slate-200"
                            >
                              <input
                                type="checkbox"
                                className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-sky-500 focus:ring-sky-500"
                                checked={isChecked}
                                onChange={(event) => {
                                  const checked = event.target.checked;
                                  setTransactionForm((prev) => {
                                    const next = new Set(prev.inheritCategoryIds);
                                    if (checked) {
                                      next.add(option.id);
                                    } else {
                                      next.delete(option.id);
                                    }
                                    return {
                                      ...prev,
                                      inheritCategoryIds: Array.from(next).sort((a, b) => a - b),
                                    };
                                  });
                                }}
                              />
                              <span>{option.name}</span>
                            </label>
                          );
                        })
                      )}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      type="submit"
                      className="inline-flex items-center justify-center rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-400"
                    >
                      {transactionForm.id === null ? "Añadir tipo de transacción" : "Actualizar tipo"}
                    </button>
                    {transactionForm.id !== null && (
                      <button
                        type="button"
                        onClick={resetTransactionForm}
                        className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-400 hover:text-white"
                      >
                        Cancelar
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={handleDeleteTransactionType}
                      disabled={transactionForm.id === null || selectedTransactionType?.is_deletable === false}
                      className="ml-auto inline-flex items-center justify-center rounded-lg border border-rose-500/60 px-4 py-2 text-sm font-semibold text-rose-400 transition disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500 hover:border-rose-400 hover:text-rose-300"
                    >
                      Eliminar selección
                    </button>
                  </div>
                </form>

                <div className="mt-6">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                    Tipos registrados
                  </h3>
                  <div className="mt-3 max-h-80 space-y-2 overflow-y-auto pr-1">
                    {transactionTypes.map((item) => {
                      const isSelected = transactionForm.id === item.id;
                      return (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() =>
                            setTransactionForm({
                              id: item.id,
                              name: item.name,
                              budgetRuleId: item.budget_rule_id ? String(item.budget_rule_id) : "",
                              inheritCategoryIds: [...(item.inherit_category_ids ?? [])],
                            })
                          }
                          className={`w-full rounded-lg border px-3 py-3 text-left text-sm transition ${
                            isSelected
                              ? "border-sky-500/70 bg-sky-500/10 text-white"
                              : "border-slate-800 bg-slate-950/60 text-slate-200 hover:border-slate-700 hover:bg-slate-900/80"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium">{item.name}</span>
                            <span className="text-xs uppercase tracking-wide text-slate-400">
                              {item.budget_rule_name ?? "Sin regla"}
                            </span>
                          </div>
                          {item.inherit_category_names.length > 0 && (
                            <p className="mt-1 text-xs text-slate-400">
                              Hereda: {item.inherit_category_names.join(", ")}
                            </p>
                          )}
                          {!item.is_deletable && (
                            <p className="mt-1 text-xs text-slate-500">Tipo protegido, no se puede eliminar.</p>
                          )}
                        </button>
                      );
                    })}
                    {transactionTypes.length === 0 && (
                      <p className="rounded-lg border border-dashed border-slate-800 bg-slate-950/50 px-4 py-6 text-center text-sm text-slate-500">
                        Aún no has registrado tipos adicionales.
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white">Reglas de presupuesto</h2>
                    <p className="text-sm text-slate-400">Define la distribución ideal de tu dinero por categoría.</p>
                  </div>
                  {renderFeedback(budgetRuleFeedback)}
                </div>

                <form onSubmit={handleBudgetRuleSubmit} className="mt-4 space-y-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-slate-300" htmlFor="budget-rule-name">
                      Nombre de la regla
                    </label>
                    <input
                      id="budget-rule-name"
                      type="text"
                      value={budgetRuleForm.name}
                      onChange={(event) =>
                        setBudgetRuleForm((prev) => ({ ...prev, name: event.target.value }))
                      }
                      className="w-full rounded-lg border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm text-white outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/40"
                      placeholder="Ej. Esenciales"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-slate-300" htmlFor="budget-rule-percentage">
                      Porcentaje
                    </label>
                    <input
                      id="budget-rule-percentage"
                      type="number"
                      step="0.01"
                      min="0"
                      value={budgetRuleForm.percentage}
                      onChange={(event) =>
                        setBudgetRuleForm((prev) => ({ ...prev, percentage: event.target.value }))
                      }
                      className="w-full rounded-lg border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm text-white outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/40"
                      placeholder="Ej. 50"
                    />
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      type="submit"
                      className="inline-flex items-center justify-center rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-400"
                    >
                      {budgetRuleForm.id === null ? "Añadir regla" : "Actualizar regla"}
                    </button>
                    {budgetRuleForm.id !== null && (
                      <button
                        type="button"
                        onClick={resetBudgetRuleForm}
                        className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-400 hover:text-white"
                      >
                        Cancelar
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={handleDeleteBudgetRule}
                      disabled={budgetRuleForm.id === null || selectedBudgetRule?.is_deletable === false}
                      className="ml-auto inline-flex items-center justify-center rounded-lg border border-rose-500/60 px-4 py-2 text-sm font-semibold text-rose-400 transition hover:border-rose-400 hover:text-rose-300 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500"
                    >
                      Eliminar selección
                    </button>
                  </div>
                </form>

                <div className="mt-6">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                    Reglas activas
                  </h3>
                  <div className="mt-3 max-h-80 space-y-2 overflow-y-auto pr-1">
                    {budgetRules.map((rule) => {
                      const isSelected = budgetRuleForm.id === rule.id;
                      return (
                        <button
                          key={rule.id}
                          type="button"
                          onClick={() =>
                            setBudgetRuleForm({
                              id: rule.id,
                              name: rule.name,
                              percentage: rule.percentage.toString(),
                            })
                          }
                          className={`w-full rounded-lg border px-3 py-3 text-left text-sm transition ${
                            isSelected
                              ? "border-emerald-500/70 bg-emerald-500/10 text-white"
                              : "border-slate-800 bg-slate-950/60 text-slate-200 hover:border-slate-700 hover:bg-slate-900/80"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium">{rule.name}</span>
                            <span className="text-xs font-semibold text-emerald-400">{rule.percentage.toFixed(2)}%</span>
                          </div>
                          {!rule.is_deletable && (
                            <p className="mt-1 text-xs text-slate-500">En uso por tipos de transacción.</p>
                          )}
                        </button>
                      );
                    })}
                    {budgetRules.length === 0 && (
                      <p className="rounded-lg border border-dashed border-slate-800 bg-slate-950/50 px-4 py-6 text-center text-sm text-slate-500">
                        No hay reglas registradas aún.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "account-types" && (
            <div className="grid gap-6 lg:grid-cols-[2fr,3fr]">
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white">Tipos de cuenta</h2>
                    <p className="text-sm text-slate-400">Gestiona los tipos disponibles al crear nuevas cuentas.</p>
                  </div>
                  {renderFeedback(accountFeedback)}
                </div>
                <form onSubmit={handleAccountTypeSubmit} className="mt-4 space-y-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-slate-300" htmlFor="account-type-name">
                      Nombre del tipo
                    </label>
                    <input
                      id="account-type-name"
                      type="text"
                      value={accountTypeForm.name}
                      onChange={(event) =>
                        setAccountTypeForm((prev) => ({ ...prev, name: event.target.value }))
                      }
                      className="w-full rounded-lg border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm text-white outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
                      placeholder="Ej. Cuenta Corriente"
                    />
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      type="submit"
                      className="inline-flex items-center justify-center rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-400"
                    >
                      {accountTypeForm.id === null ? "Añadir tipo de cuenta" : "Actualizar tipo"}
                    </button>
                    {accountTypeForm.id !== null && (
                      <button
                        type="button"
                        onClick={resetAccountTypeForm}
                        className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-400 hover:text-white"
                      >
                        Cancelar
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={handleDeleteAccountType}
                      disabled={accountTypeForm.id === null || selectedAccountType?.is_deletable === false}
                      className="ml-auto inline-flex items-center justify-center rounded-lg border border-rose-500/60 px-4 py-2 text-sm font-semibold text-rose-400 transition hover:border-rose-400 hover:text-rose-300 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500"
                    >
                      Eliminar selección
                    </button>
                  </div>
                </form>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                  Tipos registrados
                </h3>
                <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
                  {accountTypes.map((item) => {
                    const isSelected = accountTypeForm.id === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setAccountTypeForm({ id: item.id, name: item.name })}
                        className={`rounded-lg border px-3 py-3 text-left text-sm transition ${
                          isSelected
                            ? "border-sky-500/70 bg-sky-500/10 text-white"
                            : "border-slate-800 bg-slate-950/60 text-slate-200 hover:border-slate-700 hover:bg-slate-900/80"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium">{item.name}</span>
                          {!item.is_deletable && (
                            <span className="text-xs text-slate-500">En uso</span>
                          )}
                        </div>
                      </button>
                    );
                  })}
                  {accountTypes.length === 0 && (
                    <p className="rounded-lg border border-dashed border-slate-800 bg-slate-950/50 px-4 py-6 text-center text-sm text-slate-500">
                      No hay tipos configurados.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === "categories" && (
            <div className="space-y-6">
              <div className="app-card p-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold">Categorías</h2>
                    <p className="text-sm text-muted">
                      Organiza tus ingresos y gastos agrupándolos en categorías específicas.
                    </p>
                  </div>
                  {renderFeedback(categoryFeedback)}
                </div>
                <form onSubmit={handleCategorySubmit} className="mt-4 grid gap-4 md:grid-cols-2">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted" htmlFor="category-name">
                      Nombre de la categoría
                    </label>
                    <input
                      id="category-name"
                      type="text"
                      value={categoryForm.name}
                      onChange={(event) =>
                        setCategoryForm((prev) => ({ ...prev, name: event.target.value }))
                      }
                      className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 transition focus:border-violet-400 focus:outline-none focus:ring-2 focus:ring-violet-200 dark:text-slate-100"
                      placeholder="Ej. Servicios"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted" htmlFor="category-parent">
                      Pertenece al tipo
                    </label>
                    <select
                      id="category-parent"
                      value={categoryForm.parentId}
                      onChange={(event) =>
                        setCategoryForm((prev) => ({ ...prev, parentId: event.target.value }))
                      }
                      className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 transition focus:border-violet-400 focus:outline-none focus:ring-2 focus:ring-violet-200 dark:text-slate-100"
                    >
                      <option value="">Selecciona un tipo...</option>
                      {transactionTypes.map((type) => (
                        <option key={type.id} value={type.id}>
                          {type.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 md:col-span-2">
                    <button
                      type="submit"
                      className="inline-flex items-center justify-center rounded-lg bg-gradient-to-r from-violet-500 to-indigo-500 px-4 py-2 text-sm font-semibold text-white transition hover:from-violet-400 hover:to-indigo-500"
                    >
                      {categoryForm.id === null ? "Añadir categoría" : "Actualizar categoría"}
                    </button>
                    {categoryForm.id !== null && (
                      <button
                        type="button"
                        onClick={resetCategoryForm}
                        className="rounded-lg border border-[var(--app-border)] px-4 py-2 text-sm font-semibold text-muted transition hover:border-violet-400 hover:text-slate-700 dark:hover:text-slate-100"
                      >
                        Cancelar
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={handleDeleteCategory}
                      disabled={categoryForm.id === null || selectedCategory?.is_deletable === false}
                      className="ml-auto inline-flex items-center justify-center rounded-lg border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:border-rose-400 hover:bg-rose-50 disabled:cursor-not-allowed disabled:border-rose-100 disabled:text-rose-300 dark:border-rose-500/50 dark:text-rose-200 dark:hover:bg-rose-500/10"
                    >
                      Eliminar selección
                    </button>
                  </div>
                </form>
              </div>

              <div className="app-card overflow-hidden">
                <table className="min-w-full divide-y divide-[var(--app-border)] text-sm">
                  <thead className="bg-[var(--app-surface-muted)] text-muted">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Categoría</th>
                      <th className="px-4 py-3 text-left font-semibold">Tipo padre</th>
                      <th className="px-4 py-3 text-right font-semibold">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--app-border)] text-slate-700 dark:text-slate-200">
                    {categories.map((category) => {
                      const isSelected = categoryForm.id === category.id;
                      return (
                        <tr
                          key={category.id}
                          onClick={() =>
                            setCategoryForm({
                              id: category.id,
                              name: category.name,
                              parentId: String(category.parent_id),
                            })
                          }
                          className={`cursor-pointer transition hover:bg-sky-50 dark:hover:bg-slate-800/70 ${
                            isSelected ? "bg-violet-100/60 dark:bg-violet-500/10" : ""
                          }`}
                        >
                          <td className="px-4 py-3 font-semibold">{category.name}</td>
                          <td className="px-4 py-3 text-muted">{category.parent_name}</td>
                          <td className="px-4 py-3 text-right">
                            {category.is_deletable ? (
                              <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-200">
                                Editable
                              </span>
                            ) : (
                              <span className="rounded-full bg-slate-300/40 px-3 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-700/50 dark:text-slate-300">
                                En uso
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                    {categories.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-4 py-6 text-center text-muted">
                          Aún no tienes categorías registradas.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "visualization" && (
            displayPreferences ? (
              <div className="max-w-2xl space-y-6">
                <div className="app-card p-6">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-[var(--app-text)]">Visualización de números</h2>
                      <p className="text-sm text-muted">
                        Controla cómo se muestran las cantidades grandes en reportes y tarjetas.
                      </p>
                    </div>
                    {renderFeedback(visualFeedback)}
                  </div>

                  <form onSubmit={handleVisualizationSubmit} className="mt-4 space-y-5">
                    <div className="flex flex-col gap-4 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm font-semibold text-[var(--app-text)]">Abreviar números grandes</p>
                        <p className="text-xs text-muted">Ejemplo: $1,250,000 → $1.25M</p>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          setDisplayPreferences((prev) =>
                            prev ? { ...prev, abbreviate_numbers: !prev.abbreviate_numbers } : prev
                          )
                        }
                        className={`relative inline-flex h-9 w-16 items-center rounded-full border border-transparent transition ${
                          displayPreferences.abbreviate_numbers
                            ? "bg-sky-500 shadow-lg shadow-sky-500/30"
                            : "bg-[var(--app-surface)]"
                        }`}
                        aria-pressed={displayPreferences.abbreviate_numbers}
                      >
                        <span
                          className={`ml-1 inline-block h-7 w-7 transform rounded-full bg-white shadow transition-transform ${
                            displayPreferences.abbreviate_numbers ? "translate-x-6" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>

                    <div className="space-y-1">
                      <label className="text-sm font-medium text-[var(--app-text)]" htmlFor="threshold-select">
                        Abreviar a partir de
                      </label>
                      <select
                        id="threshold-select"
                        value={displayPreferences.threshold}
                        onChange={(event) =>
                          setDisplayPreferences((prev) =>
                            prev ? { ...prev, threshold: Number(event.target.value) } : prev
                          )
                        }
                        className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-[var(--app-text)] outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/30 dark:text-slate-100"
                      >
                        {THRESHOLD_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                      <button
                        type="submit"
                        className="inline-flex items-center justify-center rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-400"
                      >
                        Guardar configuración de visualización
                      </button>
                      <p className="text-xs text-muted">
                        Los cambios se aplican inmediatamente a los reportes y tarjetas monetarias.
                      </p>
                    </div>
                  </form>
                </div>
              </div>
            ) : (
              <div className="app-card p-8 text-center text-sm text-muted">
                No fue posible cargar las preferencias de visualización. Intenta recargar la página.
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
