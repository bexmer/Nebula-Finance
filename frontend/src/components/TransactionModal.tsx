import { useEffect, useState, useCallback, useMemo, type CSSProperties } from "react";
import axios from "axios";

import { useStore, TransactionSplit as TransactionSplitData } from "../store/useStore";
import { apiPath } from "../utils/api";
import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import {
  formatDateForDisplay,
  getTodayDateInputValue,
  normalizeDateInputValue,
  parseDateOnly,
} from "../utils/date";

interface SelectOption {
  id: number;
  name: string;
}

interface BudgetEntryOption {
  id: number;
  description: string;
  category: string;
  type: string;
  frequency: string;
  start_date?: string | null;
  end_date?: string | null;
  due_date?: string | null;
  budgeted_amount: number;
  actual_amount: number;
  remaining_amount: number;
  over_budget_amount?: number;
  is_recurring?: boolean;
}

interface ParameterOption {
  id: number;
  value: string;
}

interface SplitRow {
  id: string;
  category: string;
  amount: string;
}

const createInitialState = () => ({
  description: "",
  amount: "",
  date: getTodayDateInputValue(),
  typeId: "",
  categoryValue: "",
  account_id: "",
  goal_id: "",
  debt_id: "",
  budget_entry_id: "",
  is_transfer: false,
  transfer_account_id: "",
});

const normalizeTypeLabel = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

export const TransactionModal = () => {
  const {
    isTransactionModalOpen,
    closeTransactionModal,
    editingTransaction,
    transactionPrefill,
    fetchTransactions,
    transactionSuccessHandler,
  } = useStore();

  const { formatCurrency } = useNumberFormatter();
  const [formData, setFormData] = useState(createInitialState);
  const [accounts, setAccounts] = useState<SelectOption[]>([]);
  const [transactionTypes, setTransactionTypes] = useState<ParameterOption[]>([]);
  const [categories, setCategories] = useState<ParameterOption[]>([]);
  const [goals, setGoals] = useState<SelectOption[]>([]);
  const [debts, setDebts] = useState<SelectOption[]>([]);
  const [budgetEntries, setBudgetEntries] = useState<BudgetEntryOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [catalogNotice, setCatalogNotice] = useState<string | null>(null);
  const [initialSnapshot, setInitialSnapshot] = useState<
    ReturnType<typeof createInitialState> | null
  >(
    null
  );
  const [splitMode, setSplitMode] = useState(false);
  const [splitItems, setSplitItems] = useState<SplitRow[]>([]);
  const [initialSplits, setInitialSplits] = useState<TransactionSplitData[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [initialTags, setInitialTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const todayInputValue = useMemo(() => getTodayDateInputValue(), []);

  const activeType = useMemo(() => {
    if (!formData.typeId) {
      return null;
    }
    const typeIdNumber = Number(formData.typeId);
    return transactionTypes.find((type) => type.id === typeIdNumber) ?? null;
  }, [formData.typeId, transactionTypes]);

  const normalizedTypeName = useMemo(() => {
    if (!activeType) {
      return "";
    }
    return normalizeTypeLabel(activeType.value);
  }, [activeType]);

  const requiresGoal = normalizedTypeName.includes("ahorro");
  const requiresDebt = normalizedTypeName.includes("deuda");
  const shouldShowGoalSelect = requiresGoal || Boolean(formData.goal_id);
  const shouldShowDebtSelect = requiresDebt || Boolean(formData.debt_id);
  const isTransfer = formData.is_transfer;

  const availableDestinationAccounts = useMemo(
    () =>
      accounts.filter((account) => String(account.id) !== formData.account_id),
    [accounts, formData.account_id]
  );

  const canUseSplit = useMemo(
    () => !isTransfer && Boolean(formData.typeId) && categories.length > 0,
    [categories.length, formData.typeId, isTransfer]
  );

  const normalizeTagValue = useCallback((value: string) => {
    return value.replace(/^#+/, "").trim();
  }, []);

  const splitTotal = useMemo(() => {
    return splitItems.reduce((sum, item) => {
      const value = parseFloat(item.amount || "0");
      if (Number.isNaN(value)) {
        return sum;
      }
      return sum + value;
    }, 0);
  }, [splitItems]);

  const amountValue = useMemo(() => {
    const parsed = parseFloat(formData.amount || "0");
    return Number.isNaN(parsed) ? 0 : parsed;
  }, [formData.amount]);

  const splitMismatch = useMemo(
    () => Math.abs(splitTotal - amountValue) > 0.01,
    [amountValue, splitTotal]
  );

  const splitDifference = useMemo(() => amountValue - splitTotal, [amountValue, splitTotal]);

  const tagSuggestions = useMemo(() => {
    if (availableTags.length === 0) {
      return [] as string[];
    }
    const normalizedSelected = new Set(
      selectedTags.map((tag) => normalizeTagValue(tag).toLowerCase())
    );
    const searchTerm = normalizeTagValue(tagInput).toLowerCase();
    return availableTags
      .filter((tag) => {
        const normalized = normalizeTagValue(tag).toLowerCase();
        if (!normalized) {
          return false;
        }
        if (normalizedSelected.has(normalized)) {
          return false;
        }
        if (!searchTerm) {
          return true;
        }
        return normalized.includes(searchTerm);
      })
      .slice(0, 8);
  }, [availableTags, normalizeTagValue, selectedTags, tagInput]);

  const selectedBudgetId = formData.budget_entry_id
    ? Number(formData.budget_entry_id)
    : null;

  const budgetOptions = useMemo(() => {
    if (budgetEntries.length === 0) {
      return [] as BudgetEntryOption[];
    }

    const targetType = activeType?.value ?? "";
    const normalizedTarget = normalizeTypeLabel(targetType);

    const parseDate = (entry: BudgetEntryOption) => {
      const dateValue = entry.due_date || entry.end_date || entry.start_date;
      const parsed = parseDateOnly(dateValue);
      return parsed ? parsed.getTime() : Number.MAX_SAFE_INTEGER;
    };

    return budgetEntries
      .filter((entry) => {
        if (selectedBudgetId && entry.id === selectedBudgetId) {
          return true;
        }
        if (!normalizedTarget) {
          return true;
        }

        if (normalizedTarget.includes("transferencia")) {
          return false;
        }

        const normalizedEntryType = normalizeTypeLabel(entry.type ?? "");

        if (normalizedEntryType === normalizedTarget) {
          return true;
        }

        if (normalizedTarget.includes("gasto")) {
          return (
            normalizedEntryType.includes("gasto") ||
            normalizedEntryType.includes("egreso")
          );
        }

        if (normalizedTarget.includes("ingreso")) {
          return normalizedEntryType.includes("ingreso");
        }

        if (normalizedTarget.includes("ahorro")) {
          return normalizedEntryType.includes("ahorro");
        }

        if (normalizedTarget.includes("deuda")) {
          return normalizedEntryType.includes("deuda");
        }

        return normalizedEntryType.includes(normalizedTarget);
      })
      .sort((a, b) => parseDate(a) - parseDate(b));
  }, [activeType, budgetEntries, selectedBudgetId]);

  const hasAnyBudgets = budgetEntries.length > 0;

  const selectedBudget = useMemo(() => {
    if (!selectedBudgetId) {
      return null;
    }
    const found = budgetEntries.find((entry) => entry.id === selectedBudgetId);
    if (!found) {
      return null;
    }
    const planned = found.budgeted_amount ?? 0;
    const actual = found.actual_amount ?? 0;
    const remaining =
      found.remaining_amount !== undefined && found.remaining_amount !== null
        ? found.remaining_amount
        : planned - actual;
    return {
      ...found,
      budgeted_amount: planned,
      actual_amount: actual,
      remaining_amount: remaining,
    };
  }, [budgetEntries, selectedBudgetId]);

  const fetchCategoriesByType = useCallback(async (typeId: number) => {
    try {
      const response = await axios.get<ParameterOption[]>(
        apiPath(`/parameters/categories/${typeId}`)
      );
      return response.data.map((item) => ({
        id: item.id,
        value: item.value,
      }));
    } catch (categoryError) {
      console.error("No se pudieron cargar las categorías:", categoryError);
      setCatalogNotice(
        "No encontramos categorías para este tipo. Revisa la sección de Configuración."
      );
      return [];
    }
  }, [setCatalogNotice]);

  const createSplitRow = useCallback((): SplitRow => {
    return {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      category: "",
      amount: "",
    };
  }, []);

  const handleToggleSplitMode = useCallback(() => {
    setSplitMode((previous) => {
      const next = !previous;
      if (next) {
        setSplitItems((rows) => (rows.length > 0 ? rows : [createSplitRow()]));
        setFormData((state) => ({
          ...state,
          categoryValue: state.categoryValue || "Múltiples categorías",
        }));
      } else {
        setSplitItems([]);
        setFormData((state) => ({
          ...state,
          categoryValue: "",
        }));
      }
      return next;
    });
  }, [createSplitRow]);

  const handleSplitFieldChange = useCallback(
    (id: string, field: "category" | "amount", value: string) => {
      setSplitItems((rows) =>
        rows.map((row) =>
          row.id === id
            ? {
                ...row,
                [field]: field === "amount" ? value.replace(/[^0-9.,]/g, "") : value,
              }
            : row
        )
      );
    },
    []
  );

  const handleAddSplitRow = useCallback(() => {
    setSplitItems((rows) => [...rows, createSplitRow()]);
  }, [createSplitRow]);

  const handleRemoveSplitRow = useCallback((id: string) => {
    setSplitItems((rows) => rows.filter((row) => row.id !== id));
  }, []);

  const handleAddTagValue = useCallback(
    (rawValue: string) => {
      const sanitized = normalizeTagValue(rawValue);
      if (!sanitized) {
        return;
      }
      const exists = selectedTags.some(
        (tag) => normalizeTagValue(tag).toLowerCase() === sanitized.toLowerCase()
      );
      if (exists) {
        return;
      }
      setSelectedTags((tags) => [...tags, sanitized]);
      setAvailableTags((tags) => {
        const normalizedExisting = tags.map((tag) => normalizeTagValue(tag).toLowerCase());
        if (normalizedExisting.includes(sanitized.toLowerCase())) {
          return tags;
        }
        return [...tags, sanitized];
      });
    },
    [normalizeTagValue, selectedTags]
  );

  const handleTagKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        if (tagInput.trim()) {
          handleAddTagValue(tagInput);
          setTagInput("");
        }
      } else if (event.key === "Backspace" && !tagInput && selectedTags.length > 0) {
        event.preventDefault();
        setSelectedTags((tags) => tags.slice(0, -1));
      }
    },
    [handleAddTagValue, selectedTags, tagInput]
  );

  const handleTagBlur = useCallback(() => {
    if (tagInput.trim()) {
      handleAddTagValue(tagInput);
      setTagInput("");
    }
  }, [handleAddTagValue, tagInput]);

  const handleRemoveTag = useCallback((tagToRemove: string) => {
    setSelectedTags((tags) =>
      tags.filter(
        (tag) => normalizeTagValue(tag).toLowerCase() !== normalizeTagValue(tagToRemove).toLowerCase()
      )
    );
  }, [normalizeTagValue]);

  const handleBudgetEntryChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    const numericId = value ? Number(value) : null;
    const matchedBudget =
      numericId && !Number.isNaN(numericId)
        ? budgetEntries.find((entry) => entry.id === numericId)
        : undefined;

    setFormData((prev) => ({
      ...prev,
      budget_entry_id: value,
      categoryValue: matchedBudget?.category ?? prev.categoryValue,
    }));
  };

  const loadModalData = useCallback(async () => {
    setIsLoading(true);
    setError("");
    setCatalogNotice(null);

    try {
      const todayIso = new Date().toISOString().slice(0, 10);
      const [
        accountsResult,
        typesResult,
        goalsResult,
        debtsResult,
        budgetsResult,
        tagsResult,
      ] = await Promise.allSettled([
        axios.get(apiPath("/accounts")),
        axios.get(apiPath("/parameters/transaction-types")),
        axios.get(apiPath("/goals")),
        axios.get(apiPath("/debts")),
        axios.get(apiPath("/budget"), {
          params: {
            status: "active",
            reference_date: todayIso,
          },
        }),
        axios.get(apiPath("/tags")),
      ]);

      if (
        accountsResult.status !== "fulfilled" ||
        typesResult.status !== "fulfilled" ||
        budgetsResult.status !== "fulfilled"
      ) {
        throw new Error("catalog-unavailable");
      }

      const accountList = (accountsResult.value.data as any[])
        .filter((account) => !account.is_virtual)
        .map((account) => ({
          id: account.id,
          name: account.name,
        }));
      const typeList = (typesResult.value.data as any[]).map((type) => ({
        id: type.id,
        value: type.value,
      }));

      let fetchedBudgets =
        budgetsResult.status === "fulfilled"
          ? (budgetsResult.value.data as BudgetEntryOption[])
          : [];

      if (
        editingTransaction?.budget_entry_id &&
        !fetchedBudgets.some(
          (entry) => entry.id === editingTransaction.budget_entry_id,
        )
      ) {
        try {
          const fallback = await axios.get<BudgetEntryOption[]>(
            apiPath("/budget"),
          );
          fetchedBudgets = fallback.data;
        } catch (fallbackError) {
          console.warn(
            "No fue posible cargar el presupuesto asociado a la transacción en edición:",
            fallbackError,
          );
        }
      }

      setAccounts(accountList);
      setTransactionTypes(typeList);
      setGoals(
        goalsResult.status === "fulfilled"
          ? (goalsResult.value.data as any[]).map((goal) => ({
              id: goal.id,
              name: goal.name,
            }))
          : []
      );
      setDebts(
        debtsResult.status === "fulfilled"
          ? (debtsResult.value.data as any[]).map((debt) => ({
              id: debt.id,
              name: debt.name,
            }))
          : []
      );

      const fetchedTags =
        tagsResult.status === "fulfilled"
          ? (tagsResult.value.data as { name: string }[])
              .map((tag) => normalizeTagValue(tag.name))
              .filter((tag) => Boolean(tag))
          : [];

      setBudgetEntries(fetchedBudgets);

      let nextCategories: ParameterOption[] = [];
      let nextFormState = createInitialState();
      let transactionTags: string[] = [];

      if (editingTransaction) {
        const typeObject = typeList.find(
          (type) => type.value === editingTransaction.type
        );

        if (typeObject) {
          nextCategories = await fetchCategoriesByType(typeObject.id);
          nextFormState = {
            ...nextFormState,
            description: editingTransaction.description,
            amount: String(editingTransaction.amount),
            date: normalizeDateInputValue(editingTransaction.date),
            account_id: String(editingTransaction.account_id),
            typeId: String(typeObject.id),
            categoryValue: editingTransaction.category,
            goal_id: String(editingTransaction.goal_id || ""),
            debt_id: String(editingTransaction.debt_id || ""),
            budget_entry_id: editingTransaction.budget_entry_id
              ? String(editingTransaction.budget_entry_id)
              : "",
            is_transfer: Boolean(editingTransaction.is_transfer),
            transfer_account_id: editingTransaction.transfer_account_id
              ? String(editingTransaction.transfer_account_id)
              : "",
          };
        } else {
          nextFormState = {
            ...nextFormState,
            description: editingTransaction.description,
            amount: String(editingTransaction.amount),
            date: normalizeDateInputValue(editingTransaction.date),
            account_id: String(editingTransaction.account_id),
            goal_id: String(editingTransaction.goal_id || ""),
            debt_id: String(editingTransaction.debt_id || ""),
            budget_entry_id: editingTransaction.budget_entry_id
              ? String(editingTransaction.budget_entry_id)
              : "",
            is_transfer: Boolean(editingTransaction.is_transfer),
            transfer_account_id: editingTransaction.transfer_account_id
              ? String(editingTransaction.transfer_account_id)
              : "",
          };
        }

        transactionTags = (editingTransaction.tags ?? []).map((tag) =>
          normalizeTagValue(tag)
        );
        setSelectedTags(transactionTags);
        setInitialTags(transactionTags);

        const splitsFromTransaction = editingTransaction.splits ?? [];
        if (splitsFromTransaction.length > 0) {
          setSplitMode(true);
          setSplitItems(
            splitsFromTransaction.map((split) => ({
              id: `${split.category}-${split.amount}-${Math.random()
                .toString(16)
                .slice(2)}`,
              category: split.category,
              amount: String(split.amount),
            }))
          );
        } else {
          setSplitMode(false);
          setSplitItems([]);
        }
        setInitialSplits(splitsFromTransaction as TransactionSplitData[]);
      } else if (transactionPrefill) {
        const normalizedDate = transactionPrefill.date
          ? normalizeDateInputValue(transactionPrefill.date, nextFormState.date)
          : nextFormState.date;

        nextFormState = {
          ...nextFormState,
          description: transactionPrefill.description || "",
          amount:
            transactionPrefill.amount !== undefined
              ? String(transactionPrefill.amount)
              : "",
          date: normalizedDate,
          account_id: transactionPrefill.account_id
            ? String(transactionPrefill.account_id)
            : "",
          goal_id: transactionPrefill.goal_id
            ? String(transactionPrefill.goal_id)
            : "",
          debt_id: transactionPrefill.debt_id
            ? String(transactionPrefill.debt_id)
            : "",
          budget_entry_id: transactionPrefill.budget_entry_id
            ? String(transactionPrefill.budget_entry_id)
            : "",
        };

        setSplitMode(false);
        setSplitItems([]);
        setInitialSplits([]);
        setSelectedTags([]);
        setInitialTags([]);

        if (transactionPrefill.type) {
          const typeObject = typeList.find(
            (type) => type.value === transactionPrefill.type
          );
          if (typeObject) {
            nextCategories = await fetchCategoriesByType(typeObject.id);
            nextFormState = {
              ...nextFormState,
              typeId: String(typeObject.id),
              categoryValue: transactionPrefill.category || "",
            };
          }
        }
      } else {
        setSplitMode(false);
        setSplitItems([]);
        setInitialSplits([]);
        setSelectedTags([]);
        setInitialTags([]);
      }

      const combinedTags = Array.from(
        new Set([...fetchedTags, ...transactionTags].filter((tag) => Boolean(tag)))
      );
      setAvailableTags(combinedTags);

      setCategories(nextCategories);
      setFormData(nextFormState);
      if (editingTransaction) {
        setInitialSnapshot(nextFormState);
        setTagInput("");
      } else {
        setInitialSnapshot(null);
        setTagInput("");
      }

      if (accountList.length === 0 || typeList.length === 0) {
        setCatalogNotice(
          "Configura al menos una cuenta y un tipo de transacción con categorías en Configuración antes de registrar movimientos."
        );
      }
    } catch (loadError) {
      console.error("Error al preparar el formulario de transacciones:", loadError);
      setError(
        "No pudimos cargar los catálogos del formulario. Verifica que el backend esté en ejecución y que exista al menos una cuenta, un tipo y una categoría configurados en Configuración."
      );
    } finally {
      setIsLoading(false);
    }
  }, [editingTransaction, transactionPrefill, fetchCategoriesByType]);

  useEffect(() => {
    if (isTransactionModalOpen) {
      loadModalData();
    } else {
      setFormData(createInitialState());
      setCatalogNotice(null);
      setError("");
      setInitialSnapshot(null);
      setSplitMode(false);
      setSplitItems([]);
      setInitialSplits([]);
      setSelectedTags([]);
      setInitialTags([]);
      setBudgetEntries([]);
      setTagInput("");
    }
  }, [isTransactionModalOpen, loadModalData]);

  const handleTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const typeId = event.target.value;
    const numericType = typeId ? Number(typeId) : null;
    let isTransferSelection = false;

    if (numericType) {
      const selectedType = transactionTypes.find((item) => item.id === numericType);
      if (selectedType) {
        const normalized = normalizeTypeLabel(selectedType.value);
        isTransferSelection = normalized.includes("transferencia");
        if (normalized.includes("ahorro") && goals.length === 0) {
          setCatalogNotice(
            "Para registrar un ahorro necesitas crear una meta desde la sección Metas y deudas."
          );
        } else if (normalized.includes("deuda") && debts.length === 0) {
          setCatalogNotice(
            "Para registrar un pago de deuda necesitas crear una deuda desde la sección Metas y deudas."
          );
        } else {
          setCatalogNotice(null);
        }
      }
    } else {
      setCatalogNotice(null);
    }

    setFormData((prev) => ({
      ...prev,
      typeId,
      categoryValue: isTransferSelection ? "Transferencia interna" : "",
      goal_id: "",
      debt_id: "",
      budget_entry_id: "",
      is_transfer: isTransferSelection,
      transfer_account_id: "",
    }));

    if (isTransferSelection) {
      setSplitMode(false);
      setSplitItems([]);
      setCategories([]);
    } else if (numericType) {
      fetchCategoriesByType(numericType).then((data) => setCategories(data));
    } else {
      setCategories([]);
    }
  };

  const LIMITED_NUMERIC_FIELDS = new Set(["amount"]);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = event.target;
    const checked = (event.target as HTMLInputElement).checked;

    if (type !== "checkbox") {
      if (name === "description" && value.length > 100) {
        event.preventDefault();
        setFormData((prev) => ({ ...prev, description: value.slice(0, 100) }));
        return;
      }

      if (LIMITED_NUMERIC_FIELDS.has(name)) {
        const digitsOnly = value.replace(/[^0-9]/g, "");
        if (digitsOnly.length > 10) {
          return;
        }
      }
    }

    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");

    const typeObject = transactionTypes.find(
      (type) => type.id === parseInt(formData.typeId, 10)
    );

    if (!typeObject) {
      setError("Selecciona un tipo de transacción para continuar.");
      return;
    }

    const trimmedDescription = formData.description.trim();
    const amountNumber = parseFloat(formData.amount);
    const accountIdNumber = parseInt(formData.account_id, 10);

    if (Number.isNaN(amountNumber) || amountNumber <= 0) {
      setError("Ingresa un monto válido y mayor a cero.");
      return;
    }

    const [yearStr, monthStr, dayStr] = formData.date.split("-");
    if (!yearStr || !monthStr || !dayStr) {
      setError("Selecciona una fecha válida.");
      return;
    }

    const parsedTransactionDate = new Date(
      Number(yearStr),
      Number(monthStr) - 1,
      Number(dayStr)
    );

    if (Number.isNaN(parsedTransactionDate.getTime())) {
      setError("La fecha proporcionada no es válida.");
      return;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    parsedTransactionDate.setHours(0, 0, 0, 0);

    if (parsedTransactionDate > today) {
      setError("La fecha no puede ser posterior al día de hoy.");
      return;
    }

    if (Number.isNaN(accountIdNumber)) {
      setError("Selecciona una cuenta para registrar la transacción.");
      return;
    }

    const goalIdNumber = formData.goal_id ? parseInt(formData.goal_id, 10) : null;
    const debtIdNumber = formData.debt_id ? parseInt(formData.debt_id, 10) : null;
    const budgetEntryIdNumber = formData.budget_entry_id
      ? parseInt(formData.budget_entry_id, 10)
      : null;

    if (requiresGoal && !goalIdNumber) {
      setError("Selecciona la meta a la que se asignará este ahorro.");
      return;
    }

    if (requiresDebt && !debtIdNumber) {
      setError("Selecciona la deuda que deseas pagar con esta transacción.");
      return;
    }

    if (
      !isTransfer &&
      !splitMode &&
      !formData.categoryValue &&
      !budgetEntryIdNumber
    ) {
      setError("Selecciona una categoría para la transacción.");
      return;
    }

    const transferAccountNumber =
      isTransfer && formData.transfer_account_id
        ? parseInt(formData.transfer_account_id, 10)
        : null;

    if (isTransfer) {
      if (transferAccountNumber === null || Number.isNaN(transferAccountNumber)) {
        setError("Selecciona la cuenta de destino de la transferencia.");
        return;
      }
      if (transferAccountNumber === accountIdNumber) {
        setError("Elige una cuenta de destino diferente a la de origen.");
        return;
      }
    }

    let splitPayload: { category: string; amount: number }[] = [];
    if (splitMode) {
      if (splitItems.length === 0) {
        setError("Agrega al menos una categoría para dividir la transacción.");
        return;
      }

      splitPayload = splitItems.map((item) => ({
        category: item.category.trim(),
        amount: parseFloat(item.amount.replace(/,/g, ".")),
      }));

      if (
        splitPayload.some(
          (item) => !item.category || Number.isNaN(item.amount) || item.amount <= 0
        )
      ) {
        setError("Completa la categoría y el monto de cada división con valores válidos.");
        return;
      }

      const totalSplit = splitPayload.reduce((sum, item) => sum + item.amount, 0);
      if (Math.abs(totalSplit - amountNumber) > 0.01) {
        setError("La suma de las divisiones debe coincidir con el monto total.");
        return;
      }
    }

    const submissionCategory = isTransfer
      ? "Transferencia interna"
      : splitMode
        ? "Múltiples categorías"
        : budgetEntryIdNumber && selectedBudget
          ? selectedBudget.category
          : formData.categoryValue;

    const submissionData = {
      description: trimmedDescription,
      amount: amountNumber,
      date: formData.date,
      account_id: accountIdNumber,
      type: typeObject.value,
      category: submissionCategory,
      goal_id: goalIdNumber,
      debt_id: debtIdNumber,
      budget_entry_id: isTransfer ? null : budgetEntryIdNumber,
      is_transfer: isTransfer,
      transfer_account_id: transferAccountNumber,
      splits: splitPayload,
      tags: selectedTags,
    };

    const normalizedCurrentTags = selectedTags
      .map((tag) => normalizeTagValue(tag).toLowerCase())
      .sort();
    const normalizedInitialTags = initialTags
      .map((tag) => normalizeTagValue(tag).toLowerCase())
      .sort();
    const tagsEqual =
      normalizedCurrentTags.length === normalizedInitialTags.length &&
      normalizedCurrentTags.every((tag, index) => tag === normalizedInitialTags[index]);

    const normalizedCurrentSplits = splitPayload
      .map((item) => ({ category: item.category, amount: item.amount }))
      .sort((a, b) => a.category.localeCompare(b.category) || a.amount - b.amount);
    const normalizedInitialSplits = (initialSplits ?? [])
      .map((item) => ({ category: item.category, amount: item.amount }))
      .sort((a, b) => a.category.localeCompare(b.category) || a.amount - b.amount);
    const splitsEqual =
      normalizedCurrentSplits.length === normalizedInitialSplits.length &&
      normalizedCurrentSplits.every((item, index) => {
        const reference = normalizedInitialSplits[index];
        return (
          item.category === reference.category && Math.abs(item.amount - reference.amount) < 0.01
        );
      });

    if (editingTransaction && initialSnapshot) {
      const initialAmount = parseFloat(initialSnapshot.amount);
      const initialAccount = parseInt(initialSnapshot.account_id || "", 10);
      const initialGoal = initialSnapshot.goal_id || "";
      const initialDebt = initialSnapshot.debt_id || "";
      const initialBudget = initialSnapshot.budget_entry_id || "";
      const currentGoal = formData.goal_id || "";
      const currentDebt = formData.debt_id || "";
      const currentBudget = formData.budget_entry_id || "";
      const unchanged =
        initialSnapshot.description.trim() === trimmedDescription &&
        Number.isFinite(initialAmount) &&
        initialAmount === submissionData.amount &&
        initialSnapshot.date === formData.date &&
        initialSnapshot.typeId === formData.typeId &&
        initialSnapshot.categoryValue === formData.categoryValue &&
        initialAccount === submissionData.account_id &&
        initialGoal === currentGoal &&
        initialDebt === currentDebt &&
        initialBudget === currentBudget &&
        initialSnapshot.is_transfer === submissionData.is_transfer &&
        (initialSnapshot.transfer_account_id || "") ===
          (formData.transfer_account_id || "") &&
        tagsEqual &&
        splitsEqual;

      if (unchanged) {
        setError("No has realizado cambios en esta transacción.");
        return;
      }
    }

    try {
      if (editingTransaction) {
        await axios.put(
          apiPath(`/transactions/${editingTransaction.id}`),
          submissionData
        );
      } else {
        await axios.post(apiPath("/transactions"), submissionData);
      }
      await fetchTransactions();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("nebula:goals-refresh"));
      }
      if (transactionSuccessHandler) {
        await Promise.resolve(transactionSuccessHandler());
      }
      closeTransactionModal();
    } catch (submitError) {
      console.error("Error al guardar la transacción:", submitError);
      setError("No se pudo guardar la transacción. Revisa los datos e inténtalo nuevamente.");
    }
  };

  if (!isTransactionModalOpen) {
    return null;
  }

  return (
    <div className="app-modal-overlay">
      <div
        className="app-modal-panel app-card w-full p-6"
        style={{ "--modal-max-width": "min(95vw, 760px)" } as CSSProperties}
      >
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          {editingTransaction ? "Editar transacción" : "Registrar transacción"}
        </h2>

        {isLoading ? (
          <p className="mt-6 text-center text-muted">Cargando catálogos...</p>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,360px)]"
          >
            {error && (
              <p className="rounded-xl border border-rose-300/60 bg-rose-50 px-4 py-2 text-sm text-rose-600 dark:border-rose-400/40 dark:bg-rose-500/10 dark:text-rose-200 lg:col-span-2">
                {error}
              </p>
            )}
            {catalogNotice && !error && (
              <p className="rounded-xl border border-amber-300/60 bg-amber-50 px-4 py-2 text-sm text-amber-600 dark:border-amber-400/40 dark:bg-amber-500/10 dark:text-amber-200 lg:col-span-2">
                {catalogNotice}
              </p>
            )}

            <div className="space-y-4 lg:col-start-1">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <input
                type="text"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Descripción"
                required
                maxLength={100}
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100 sm:col-span-3"
              />
              <input
                type="number"
                step="0.01"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                placeholder="Monto"
                required
                inputMode="decimal"
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              />
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                required
                max={todayInputValue}
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              />
              <select
                name="account_id"
                value={formData.account_id}
                onChange={handleChange}
                required
                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              >
                <option value="">-- Selecciona una Cuenta --</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-muted">
                  Tipo de movimiento
                </label>
                <select
                  name="typeId"
                  value={formData.typeId}
                  onChange={handleTypeChange}
                  required
                  className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                >
                  <option value="">-- Selecciona un Tipo --</option>
                  {transactionTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.value}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-muted">
                    {isTransfer ? "Transferencia" : splitMode ? "Divisiones por categoría" : "Categoría"}
                  </span>
                  {!isTransfer && (
                    <button
                      type="button"
                      onClick={handleToggleSplitMode}
                      disabled={!canUseSplit && !splitMode}
                      className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold transition ${
                        splitMode
                          ? "border-rose-400/70 text-rose-600 hover:border-rose-400 hover:text-rose-500"
                          : "border-sky-400/70 text-sky-600 hover:border-sky-500/80"
                      } disabled:cursor-not-allowed disabled:border-[var(--app-border)] disabled:text-muted`}
                    >
                      {splitMode ? "Usar una sola categoría" : "Dividir en categorías"}
                    </button>
                  )}
                </div>
                {isTransfer ? (
                  availableDestinationAccounts.length > 0 ? (
                    <>
                      <select
                        name="transfer_account_id"
                        value={formData.transfer_account_id}
                        onChange={handleChange}
                        required
                        className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                      >
                        <option value="">-- Cuenta de destino --</option>
                        {availableDestinationAccounts.map((account) => (
                          <option key={account.id} value={account.id}>
                            {account.name}
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-muted">
                        Las transferencias mueven saldo entre tus cuentas sin modificar tus reportes de ingresos o gastos.
                      </p>
                    </>
                  ) : (
                    <div className="rounded-xl border border-dashed border-[var(--app-border)] px-3 py-2 text-sm text-muted">
                      Agrega otra cuenta en Configuración para poder elegir un destino diferente.
                    </div>
                  )
                ) : splitMode ? (
                  categories.length > 0 ? (
                    <div className="space-y-3 rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface-muted)]/60 px-3 py-3">
                      <div className="space-y-3">
                        {splitItems.map((item, index) => (
                          <div key={item.id} className="grid grid-cols-1 gap-2 sm:grid-cols-7">
                            <select
                              value={item.category}
                              onChange={(event) =>
                                handleSplitFieldChange(item.id, "category", event.target.value)
                              }
                              className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100 sm:col-span-4"
                            >
                              <option value="">Categoría #{index + 1}</option>
                              {categories.map((category) => (
                                <option key={category.id} value={category.value}>
                                  {category.value}
                                </option>
                              ))}
                            </select>
                            <div className="flex items-center gap-2 sm:col-span-3">
                              <input
                                type="number"
                                step="0.01"
                                inputMode="decimal"
                                value={item.amount}
                                onChange={(event) =>
                                  handleSplitFieldChange(item.id, "amount", event.target.value)
                                }
                                placeholder="Monto"
                                className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                              />
                              <button
                                type="button"
                                onClick={() => handleRemoveSplitRow(item.id)}
                                disabled={splitItems.length <= 1}
                                className="inline-flex items-center rounded-lg border border-rose-400/70 px-3 py-1 text-xs font-semibold text-rose-600 transition hover:border-rose-400 hover:text-rose-500 disabled:cursor-not-allowed disabled:border-rose-200 disabled:text-rose-300 dark:text-rose-300"
                              >
                                Quitar
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={handleAddSplitRow}
                        className="inline-flex items-center gap-2 rounded-lg border border-dashed border-sky-400 px-3 py-1.5 text-xs font-semibold text-sky-600 transition hover:border-sky-500 hover:text-sky-500 dark:text-sky-300"
                      >
                        Agregar división
                      </button>
                      <div className="space-y-1 rounded-xl bg-[var(--app-surface)] px-3 py-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-muted">Total dividido</span>
                          <span
                            className={`font-semibold ${
                              splitMismatch
                                ? "text-rose-600 dark:text-rose-300"
                                : "text-sky-600 dark:text-sky-300"
                            }`}
                          >
                            {formatCurrency(splitTotal)}
                          </span>
                        </div>
                        <p
                          className={`text-xs ${
                            splitMismatch
                              ? "text-rose-600 dark:text-rose-300"
                              : "text-muted"
                          }`}
                        >
                          {splitMismatch
                            ? `Ajusta las cantidades: diferencia de ${formatCurrency(
                                Math.abs(splitDifference)
                              )}.`
                            : "Coincide con el monto total."}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-xl border border-dashed border-[var(--app-border)] px-3 py-2 text-sm text-muted">
                      No encontramos categorías para este tipo. Revisa Configuración antes de dividir el gasto.
                    </div>
                  )
                ) : (
                  <>
                    <select
                      name="categoryValue"
                      value={formData.categoryValue}
                      onChange={handleChange}
                      required={!formData.budget_entry_id && !splitMode && !isTransfer}
                      disabled={
                        !formData.typeId ||
                        categories.length === 0 ||
                        Boolean(formData.budget_entry_id) ||
                        isTransfer
                      }
                      className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-100"
                    >
                      <option value="">-- Selecciona una Categoría --</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.value}>
                          {category.value}
                        </option>
                      ))}
                    </select>
                    {Boolean(formData.budget_entry_id) && !splitMode && !isTransfer ? (
                      <p className="mt-1 text-xs text-muted">
                        La categoría se ajustará automáticamente según el presupuesto
                        seleccionado.
                      </p>
                    ) : null}
                  </>
                )}
              </div>
              </div>
            </div>

            <div className="space-y-4 lg:col-start-2">
              <div className="space-y-3 rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface-muted)]/60 px-4 py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-[var(--app-text)]">Etiquetas personalizadas</p>
                  <p className="text-xs text-muted">
                    Añade hashtags para agrupar viajes, proyectos o eventos especiales.
                  </p>
                </div>
                {selectedTags.length > 0 && (
                  <span className="inline-flex items-center rounded-full bg-sky-500/15 px-3 py-1 text-xs font-semibold text-sky-600 dark:text-sky-300">
                    {selectedTags.length} {selectedTags.length === 1 ? "etiqueta" : "etiquetas"}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2">
                {selectedTags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 rounded-full bg-sky-500/15 px-3 py-1 text-xs font-semibold text-sky-600 dark:text-sky-300"
                  >
                    #{tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="rounded-full px-1 text-[10px] font-bold text-sky-600 transition hover:text-rose-500 dark:text-sky-200"
                      aria-label={`Quitar etiqueta ${tag}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
                <input
                  type="text"
                  value={tagInput}
                  onChange={(event) => {
                    const nextValue = event.target.value.slice(0, 40);
                    setTagInput(nextValue);
                  }}
                  onKeyDown={handleTagKeyDown}
                  onBlur={handleTagBlur}
                  placeholder={selectedTags.length === 0 ? "Ej. viaje-playa-2024" : "Agregar otra etiqueta"}
                  className="min-w-[160px] flex-1 border-none bg-transparent text-sm text-[var(--app-text)] focus:outline-none"
                />
              </div>
              {tagSuggestions.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                  <span>Sugerencias:</span>
                  {tagSuggestions.map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => {
                        handleAddTagValue(tag);
                        setTagInput("");
                      }}
                      className="rounded-full border border-sky-400/70 px-2 py-1 font-semibold text-sky-600 transition hover:border-sky-400 hover:text-sky-500 dark:text-sky-300"
                    >
                      #{tag}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {(shouldShowGoalSelect || shouldShowDebtSelect) && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {shouldShowGoalSelect && (
                  goals.length > 0 ? (
                    <select
                      name="goal_id"
                      value={formData.goal_id}
                      onChange={handleChange}
                      required={requiresGoal}
                      className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                    >
                      <option value="">
                        {requiresGoal
                          ? "-- Selecciona una meta --"
                          : "-- Asociar meta (opcional) --"}
                      </option>
                      {goals.map((goal) => (
                        <option key={goal.id} value={goal.id}>
                          {goal.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <div className="rounded-xl border border-dashed border-[var(--app-border)] px-3 py-2 text-sm text-muted">
                      Crea una meta para poder registrar este ahorro.
                    </div>
                  )
                )}
                {shouldShowDebtSelect && (
                  debts.length > 0 ? (
                    <select
                      name="debt_id"
                      value={formData.debt_id}
                      onChange={handleChange}
                      required={requiresDebt}
                      className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                    >
                      <option value="">
                        {requiresDebt
                          ? "-- Selecciona una deuda --"
                          : "-- Asociar deuda (opcional) --"}
                      </option>
                      {debts.map((debt) => (
                        <option key={debt.id} value={debt.id}>
                          {debt.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <div className="rounded-xl border border-dashed border-[var(--app-border)] px-3 py-2 text-sm text-muted">
                      Registra una deuda para poder vincular este pago.
                    </div>
                  )
                )}
              </div>
            )}

            {!isTransfer && (
              <div className="space-y-2">
                <label className="text-sm font-semibold text-[var(--app-text)]">
                  Asociar a presupuesto (opcional)
                </label>
                <select
                  name="budget_entry_id"
                  value={formData.budget_entry_id}
                  onChange={handleBudgetEntryChange}
                  disabled={budgetOptions.length === 0}
                  className="w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-2 text-sm text-slate-900 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-100"
                >
                  <option value="">-- Sin asociación --</option>
                  {budgetOptions.map((entry) => {
                    const remaining = entry.remaining_amount ?? 0;
                    const overBudget =
                      entry.over_budget_amount ??
                      Math.max((entry.actual_amount ?? 0) - (entry.budgeted_amount ?? 0), 0);
                    const remainingText =
                      overBudget > 0
                        ? `Excedido ${formatCurrency(overBudget)}`
                        : remaining <= 0
                        ? "Completado"
                        : `${formatCurrency(Math.max(remaining, 0))} disponibles`;
                    const deadline = entry.due_date || entry.end_date || entry.start_date;
                    const deadlineDate = parseDateOnly(deadline);
                    const deadlineText = deadlineDate
                      ? formatDateForDisplay(deadlineDate)
                      : "sin fecha límite";
                    return (
                      <option key={entry.id} value={String(entry.id)}>
                        {(entry.description || entry.category) ?? "Presupuesto"} · {remainingText} · vence {deadlineText}
                      </option>
                    );
                  })}
                </select>
                {budgetOptions.length === 0 ? (
                  <p className="text-xs text-muted">
                    {hasAnyBudgets
                      ? "No hay presupuestos activos compatibles con el tipo seleccionado."
                      : "No hay presupuestos activos disponibles para este periodo."}
                  </p>
                ) : selectedBudget ? (
                  <div className="space-y-2 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-3 text-xs text-muted">
                    <div className="flex items-center justify-between text-[var(--app-text)]">
                      <span className="font-semibold">{selectedBudget.description || selectedBudget.category}</span>
                      <span className="rounded-full bg-sky-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-300">
                        {selectedBudget.frequency}
                      </span>
                    </div>
                    <div className="space-y-1 text-[var(--app-text)]">
                      <div className="flex items-center justify-between">
                        <span>Planificado</span>
                        <span className="font-semibold">{formatCurrency(selectedBudget.budgeted_amount)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Ejecutado</span>
                        <span className="font-semibold">{formatCurrency(selectedBudget.actual_amount)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>{selectedBudget.remaining_amount <= 0 ? "Restante" : "Disponible"}</span>
                        <span
                          className={`font-semibold ${
                            selectedBudget.remaining_amount < 0
                              ? "text-rose-600 dark:text-rose-300"
                              : ""
                          }`}
                        >
                          {formatCurrency(selectedBudget.remaining_amount)}
                        </span>
                      </div>
                    </div>
                    {selectedBudget.budgeted_amount > 0 ? (
                      <div className="h-2 rounded-full bg-[var(--app-border)]">
                        <div
                          className={`h-2 rounded-full ${
                            selectedBudget.remaining_amount < 0
                              ? "bg-rose-500"
                              : "bg-sky-500"
                          }`}
                          style={{
                            width: `${Math.min(
                              100,
                              Math.max(
                                0,
                                (selectedBudget.actual_amount /
                                  selectedBudget.budgeted_amount) *
                                  100,
                              ),
                            )}%`,
                          }}
                        />
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            )}
            </div>

            <div className="flex flex-col-reverse gap-3 pt-6 sm:flex-row sm:justify-end lg:col-span-2">
              <button
                type="button"
                onClick={closeTransactionModal}
                className="w-full rounded-xl border border-[var(--app-border)] bg-transparent px-4 py-2 text-sm font-semibold text-muted transition hover:border-slate-400 hover:text-slate-700 dark:hover:text-slate-200 sm:w-auto"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="w-full rounded-xl bg-gradient-to-r from-sky-500 via-indigo-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-500/30 transition hover:shadow-xl sm:w-auto"
              >
                Guardar
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
