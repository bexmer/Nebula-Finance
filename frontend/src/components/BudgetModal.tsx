import { useCallback, useEffect, useMemo, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import Modal from "react-modal";
import axios from "axios";
import {
  AlertCircle,
  CalendarDays,
  FileText,
  Loader2,
  Tag,
  Type as TypeIcon,
} from "lucide-react";

import { apiPath } from "../utils/api";

const customStyles = {
  content: {
    top: "50%",
    left: "50%",
    right: "auto",
    bottom: "auto",
    marginRight: "-50%",
    transform: "translate(-50%, -50%)",
    backgroundColor: "transparent",
    border: "none",
    padding: 0,
  },
  overlay: {
    backgroundColor: "rgba(15, 23, 42, 0.75)",
    zIndex: 50,
  },
};
Modal.setAppElement("#root");

interface BudgetEntry {
  id?: number;
  category: string;
  amount: number;
  budgeted_amount?: number;
  type: string;
  description?: string;
  due_date?: string | null;
  month?: number;
  year?: number;
  goal_id?: number | null;
  debt_id?: number | null;
}

interface ParameterOption {
  id: number;
  value: string;
}

interface SelectOption {
  id: number;
  name: string;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  entry: BudgetEntry | null;
}

interface BudgetFormState {
  description: string;
  amount: string;
  due_date: string;
  typeId: string;
  typeValue: string;
  categoryValue: string;
  goalId: string;
  debtId: string;
}

const createEmptyForm = (): BudgetFormState => ({
  description: "",
  amount: "",
  due_date: new Date().toISOString().split("T")[0],
  typeId: "",
  typeValue: "",
  categoryValue: "",
  goalId: "",
  debtId: "",
});

export function BudgetModal({ isOpen, onClose, onSave, entry }: ModalProps) {
  const [formData, setFormData] = useState<BudgetFormState>(createEmptyForm());
  const [transactionTypes, setTransactionTypes] = useState<ParameterOption[]>([]);
  const [categories, setCategories] = useState<ParameterOption[]>([]);
  const [goals, setGoals] = useState<SelectOption[]>([]);
  const [debts, setDebts] = useState<SelectOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogNotice, setCatalogNotice] = useState<string | null>(null);

  const sortedCategories = useMemo(
    () =>
      categories.slice().sort((a, b) => a.value.localeCompare(b.value, "es")),
    [categories]
  );

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
    return activeType.value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }, [activeType]);

  const requiresGoal = normalizedTypeName.includes("ahorro");
  const requiresDebt = normalizedTypeName.includes("deuda");
  const shouldShowGoalSelect = requiresGoal || Boolean(formData.goalId);
  const shouldShowDebtSelect = requiresDebt || Boolean(formData.debtId);

  const fetchCategoriesByType = useCallback(async (typeId: number) => {
    try {
      const response = await axios.get<ParameterOption[]>(
        apiPath(`/parameters/categories/${typeId}`)
      );
      return response.data;
    } catch (categoryError) {
      console.error("No se pudieron cargar las categorías:", categoryError);
      setCatalogNotice(
        "No encontramos categorías para este tipo. Revisa la sección de Configuración."
      );
      return [];
    }
  }, []);

  const resolveDueDate = (record: BudgetEntry | null) => {
    if (!record) {
      return new Date().toISOString().split("T")[0];
    }
    if (record.due_date) {
      return record.due_date.split("T")[0];
    }
    if (record.year && record.month) {
      const normalized = new Date(record.year, record.month - 1, 1);
      return normalized.toISOString().split("T")[0];
    }
    return new Date().toISOString().split("T")[0];
  };

  const loadModalData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setCatalogNotice(null);

    try {
      const [typesResponse, goalsResponse, debtsResponse] = await Promise.all([
        axios.get<ParameterOption[]>(apiPath("/parameters/transaction-types")),
        axios.get<SelectOption[]>(apiPath("/goals")),
        axios.get<SelectOption[]>(apiPath("/debts")),
      ]);

      const typeOptions = typesResponse.data;
      const goalOptions = goalsResponse.data.map((goal) => ({
        id: goal.id,
        name: goal.name,
      }));
      const debtOptions = debtsResponse.data.map((debt) => ({
        id: debt.id,
        name: debt.name,
      }));

      if (typeOptions.length === 0) {
        throw new Error("missing-types");
      }

      let selectedType = entry?.type ?? typeOptions[0].value;
      const matchedType = typeOptions.find((type) => type.value === selectedType);
      const fallbackType = matchedType ?? typeOptions[0];

      const categoryOptions = await fetchCategoriesByType(fallbackType.id);
      let nextCategories = categoryOptions;

      if (
        entry?.category &&
        !categoryOptions.some((option) => option.value === entry.category)
      ) {
        nextCategories = [
          ...categoryOptions,
          { id: -1, value: entry.category },
        ];
      }

      setTransactionTypes(typeOptions);
      setGoals(goalOptions);
      setDebts(debtOptions);
      setCategories(nextCategories);

      const amountValue = entry
        ? String(entry.amount ?? entry.budgeted_amount ?? "")
        : "";

      setFormData({
        description: entry?.description ?? "",
        amount: amountValue,
        due_date: resolveDueDate(entry),
        typeId: String(fallbackType.id),
        typeValue: fallbackType.value,
        categoryValue: entry?.category ?? (nextCategories[0]?.value ?? ""),
        goalId: entry?.goal_id ? String(entry.goal_id) : "",
        debtId: entry?.debt_id ? String(entry.debt_id) : "",
      });

      const normalizedDefault = fallbackType.value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
      if (normalizedDefault.includes("ahorro") && goalOptions.length === 0) {
        setCatalogNotice(
          "Para planear un ahorro necesitas crear una meta desde la sección Metas y deudas."
        );
      } else if (normalizedDefault.includes("deuda") && debtOptions.length === 0) {
        setCatalogNotice(
          "Para planear un pago de deuda necesitas registrar una deuda en Metas y deudas."
        );
      }

      if (categoryOptions.length === 0) {
        setCatalogNotice(
          "Configura categorías para este tipo de transacción en la sección de Configuración."
        );
      }
    } catch (loadError) {
      console.error("Error al preparar el formulario de presupuesto:", loadError);
      if (loadError instanceof Error && loadError.message === "missing-types") {
        setError(
          "Debes configurar al menos un tipo de transacción antes de crear presupuestos."
        );
      } else {
        setError(
          "No pudimos cargar los catálogos necesarios. Verifica tu conexión e intenta nuevamente."
        );
      }
    } finally {
      setIsLoading(false);
    }
  }, [entry, fetchCategoriesByType]);

  useEffect(() => {
    if (isOpen) {
      loadModalData();
    } else {
      setFormData(createEmptyForm());
      setTransactionTypes([]);
      setCategories([]);
      setError(null);
      setCatalogNotice(null);
      setIsSubmitting(false);
      setIsLoading(false);
    }
  }, [isOpen, loadModalData]);

  const handleTypeChange = async (event: ChangeEvent<HTMLSelectElement>) => {
    const nextTypeId = Number(event.target.value);
    const typeOption = transactionTypes.find((type) => type.id === nextTypeId);
    setFormData((prev) => ({
      ...prev,
      typeId: String(nextTypeId),
      typeValue: typeOption?.value ?? prev.typeValue,
      goalId: "",
      debtId: "",
    }));

    const nextCategories = await fetchCategoriesByType(nextTypeId);
    setCategories(nextCategories);
    setCatalogNotice(null);

    if (nextCategories.length === 0) {
      setCatalogNotice(
        "No encontramos categorías para este tipo. Revisa la sección de Configuración."
      );
    }

    if (typeOption) {
      const normalized = typeOption.value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
      if (normalized.includes("ahorro") && goals.length === 0) {
        setCatalogNotice(
          "Para planear un ahorro necesitas crear una meta desde la sección Metas y deudas."
        );
      }
      if (normalized.includes("deuda") && debts.length === 0) {
        setCatalogNotice(
          "Para planear un pago de deuda necesitas registrar una deuda en Metas y deudas."
        );
      }
    }

    setFormData((prev) => ({
      ...prev,
      categoryValue: nextCategories[0]?.value ?? "",
    }));
  };

  const handleInputChange = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCategoryChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, categoryValue: event.target.value }));
  };

  const handleGoalChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, goalId: event.target.value }));
  };

  const handleDebtChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, debtId: event.target.value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    const trimmedDescription = formData.description.trim();
    const parsedAmount = parseFloat(formData.amount);

    if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      setError("Ingresa un monto válido mayor que cero.");
      return;
    }

    if (!formData.typeValue) {
      setError("Selecciona un tipo de transacción para tu presupuesto.");
      return;
    }

    if (!formData.categoryValue) {
      setError("Selecciona una categoría para clasificar el presupuesto.");
      return;
    }

    if (requiresGoal && !formData.goalId) {
      setError("Selecciona la meta que deseas fondear con este presupuesto.");
      return;
    }

    if (requiresDebt && !formData.debtId) {
      setError("Selecciona la deuda a la que aplicarás este presupuesto.");
      return;
    }

    const payload = {
      description: trimmedDescription || formData.categoryValue,
      type: formData.typeValue,
      category: formData.categoryValue,
      budgeted_amount: parsedAmount,
      due_date: formData.due_date,
      goal_id: formData.goalId ? Number(formData.goalId) : null,
      debt_id: formData.debtId ? Number(formData.debtId) : null,
    };

    setIsSubmitting(true);

    try {
      if (entry?.id) {
        await axios.put(apiPath(`/budget/${entry.id}`), payload);
      } else {
        await axios.post(apiPath("/budget"), payload);
      }
      onSave();
      onClose();
    } catch (submitError) {
      console.error("Error al guardar la entrada del presupuesto:", submitError);
      const message =
        axios.isAxiosError(submitError) && submitError.response?.data?.detail
          ? String(submitError.response.data.detail)
          : "No pudimos guardar el presupuesto. Inténtalo de nuevo.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onRequestClose={onClose} style={customStyles}>
      <div className="w-full max-w-xl rounded-2xl border border-slate-200/10 bg-slate-900/95 p-6 shadow-2xl backdrop-blur dark:bg-slate-900/95">
        <div className="mb-5 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold text-white">
              {entry ? "Editar" : "Añadir"} entrada de presupuesto
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Define el compromiso, clasifícalo y fija cuándo debería ejecutarse.
            </p>
          </div>
          <CalendarDays className="h-6 w-6 text-slate-400" />
        </div>

        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            <AlertCircle className="mt-0.5 h-4 w-4" />
            <p>{error}</p>
          </div>
        )}

        {catalogNotice && !error && (
          <div className="mb-4 rounded-xl border border-amber-400/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            {catalogNotice}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                <TypeIcon className="h-3.5 w-3.5" /> Tipo
              </span>
              <select
                name="typeId"
                value={formData.typeId}
                onChange={handleTypeChange}
                disabled={isLoading || transactionTypes.length === 0}
                className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none disabled:cursor-not-allowed"
              >
                {transactionTypes.map((type) => (
                  <option key={type.id} value={String(type.id)}>
                    {type.value}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                <Tag className="h-3.5 w-3.5" /> Categoría
              </span>
              <select
                name="category"
                value={formData.categoryValue}
                onChange={handleCategoryChange}
                disabled={isLoading || sortedCategories.length === 0}
                className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none disabled:cursor-not-allowed"
              >
                {sortedCategories.map((category) => (
                  <option key={`${category.id}-${category.value}`} value={category.value}>
                    {category.value}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {(shouldShowGoalSelect || shouldShowDebtSelect) && (
            <div className="grid gap-4 sm:grid-cols-2">
              {shouldShowGoalSelect && (
                goals.length > 0 ? (
                  <label className="flex flex-col gap-2 text-sm text-slate-200">
                    <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Meta
                    </span>
                    <select
                      name="goalId"
                      value={formData.goalId}
                      onChange={handleGoalChange}
                      required={requiresGoal}
                      className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
                    >
                      <option value="">
                        {requiresGoal
                          ? "Selecciona una meta"
                          : "Asociar meta (opcional)"}
                      </option>
                      {goals.map((goal) => (
                        <option key={goal.id} value={goal.id}>
                          {goal.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <div className="rounded-lg border border-dashed border-slate-700/70 px-3 py-2 text-sm text-slate-400">
                    Crea una meta para vincular este presupuesto de ahorro.
                  </div>
                )
              )}

              {shouldShowDebtSelect && (
                debts.length > 0 ? (
                  <label className="flex flex-col gap-2 text-sm text-slate-200">
                    <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Deuda
                    </span>
                    <select
                      name="debtId"
                      value={formData.debtId}
                      onChange={handleDebtChange}
                      required={requiresDebt}
                      className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
                    >
                      <option value="">
                        {requiresDebt
                          ? "Selecciona una deuda"
                          : "Asociar deuda (opcional)"}
                      </option>
                      {debts.map((debt) => (
                        <option key={debt.id} value={debt.id}>
                          {debt.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <div className="rounded-lg border border-dashed border-slate-700/70 px-3 py-2 text-sm text-slate-400">
                    Registra una deuda para asignar este presupuesto de pago.
                  </div>
                )
              )}
            </div>
          )}

          <label className="flex flex-col gap-2 text-sm text-slate-200">
            <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              <FileText className="h-3.5 w-3.5" /> Descripción
            </span>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={2}
              placeholder="Ej. Pago de renta, seguro del auto, colegiatura..."
              className="min-h-[70px] w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
            />
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                <CalendarDays className="h-3.5 w-3.5" /> Fecha comprometida
              </span>
              <input
                type="date"
                name="due_date"
                value={formData.due_date}
                onChange={handleInputChange}
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
              />
            </label>

            <label className="flex flex-col gap-2 text-sm text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                $ Monto estimado
              </span>
              <input
                type="number"
                name="amount"
                min="0"
                step="0.01"
                value={formData.amount}
                onChange={handleInputChange}
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none"
              />
            </label>
          </div>

          <div className="flex flex-col-reverse gap-3 pt-4 sm:flex-row sm:items-center sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center justify-center rounded-lg border border-slate-600 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-400 hover:text-white"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting || isLoading}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-600/25 transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:bg-sky-700/50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Guardando
                </>
              ) : (
                "Guardar entrada"
              )}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
